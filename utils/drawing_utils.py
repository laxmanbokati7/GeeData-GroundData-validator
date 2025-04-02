#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path

logger = logging.getLogger(__name__)

def filter_stations_by_polygon(stations_df, feature):
    """
    Filter stations dataframe to only include stations within the given polygon
    
    Args:
        stations_df: DataFrame with station metadata including latitude and longitude
        feature: GeoJSON feature representing the polygon
        
    Returns:
        DataFrame with filtered stations
    """
    if not feature:
        return stations_df
        
    try:
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(
            stations_df, 
            geometry=gpd.points_from_xy(stations_df.longitude, stations_df.latitude),
            crs="EPSG:4326"
        )
        
        # Extract polygon from feature
        coordinates = feature['geometry']['coordinates']
        
        if feature['geometry']['type'] == 'Polygon':
            polygon = Polygon(coordinates[0])
        else:
            # Handle multipolygon or other geometry types
            return stations_df
        
        # Create polygon GeoDataFrame
        polygon_gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[polygon])
        
        # Spatial join to get stations within polygon
        stations_in_poly = gpd.sjoin(gdf, polygon_gdf, predicate='within')
        
        # Return filtered stations dataframe
        return stations_df.loc[stations_in_poly.index]
        
    except Exception as e:
        logger.error(f"Error filtering stations: {str(e)}", exc_info=True)
        return stations_df

def save_polygon_feature(feature, file_path):
    """
    Save polygon feature to a GeoJSON file
    
    Args:
        feature: GeoJSON feature representing the polygon
        file_path: Path to save the GeoJSON file
    """
    if not feature:
        return
        
    try:
        # Extract coordinates from feature
        coordinates = feature['geometry']['coordinates']
        
        # Create a shapely polygon
        if feature['geometry']['type'] == 'Polygon':
            polygon = Polygon(coordinates[0])
        else:
            # Handle multipolygon or other geometry types
            return
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[polygon])
        
        # Save to file
        gdf.to_file(file_path, driver='GeoJSON')
        logger.info(f"Saved polygon to {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving polygon: {str(e)}", exc_info=True)

def load_polygon_feature(file_path):
    """
    Load polygon feature from a GeoJSON file
    
    Args:
        file_path: Path to the GeoJSON file
        
    Returns:
        GeoJSON feature representing the polygon
    """
    try:
        # Check if file exists
        if not Path(file_path).exists():
            logger.warning(f"Polygon file {file_path} does not exist")
            return None
            
        # Load GeoDataFrame
        gdf = gpd.read_file(file_path)
        
        if len(gdf) == 0:
            logger.warning(f"No polygon found in {file_path}")
            return None
            
        # Convert to GeoJSON feature
        polygon = gdf.geometry[0]
        
        # Create feature
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [list(polygon.exterior.coords)]
            },
            'properties': {}
        }
        
        return feature
        
    except Exception as e:
        logger.error(f"Error loading polygon: {str(e)}", exc_info=True)
        return None

def get_polygon_stats(feature):
    """
    Get statistics about the polygon
    
    Args:
        feature: GeoJSON feature representing the polygon
        
    Returns:
        Dictionary with polygon statistics (area in sq km, perimeter in km)
    """
    if not feature:
        return {}
        
    try:
        # Extract coordinates from feature
        coordinates = feature['geometry']['coordinates']
        
        # Create a shapely polygon
        if feature['geometry']['type'] == 'Polygon':
            polygon = Polygon(coordinates[0])
        else:
            # Handle multipolygon or other geometry types
            return {}
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[polygon])
        
        # Convert to equal area projection for accurate measurements
        gdf_projected = gdf.to_crs('+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs')
        
        # Calculate area in sq km
        area_sq_km = gdf_projected.area[0] / 1e6
        
        # Calculate perimeter in km
        perimeter_km = gdf_projected.boundary.length[0] / 1000
        
        return {
            'area_sq_km': round(area_sq_km, 2),
            'perimeter_km': round(perimeter_km, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating polygon stats: {str(e)}", exc_info=True)
        return {}