# Add this to utils/huc_utils.py

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class HUCDataProvider:
    """Provider for HUC watershed data from Earth Engine"""
    
    def __init__(self, cache_dir: str = "Data/HUC", project_id: str = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.huc_metadata = None
        self.huc_boundaries = None
        self.project_id = project_id
        
    def fetch_huc_metadata(self, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch HUC metadata from Earth Engine or load from cache"""
        cache_file = self.cache_dir / "huc_metadata.csv"
        
        if not force_refresh and cache_file.exists():
            logger.info(f"Loading HUC metadata from cache: {cache_file}")
            return pd.read_csv(cache_file)
        
        try:
            # Initialize Earth Engine
            import ee
            if self.project_id:
                ee.Initialize(project=self.project_id)
            else:
                ee.Initialize()
            
            # Get HUC data
            huc_collection = ee.FeatureCollection("USGS/WBD/2017/HUC04")
            
            # Get metadata: HUC ID, name, state, etc.
            huc_list = huc_collection.getInfo()['features']
            
            # Extract relevant properties
            metadata = []
            for feature in huc_list:
                props = feature['properties']
                metadata.append({
                    'huc_id': props.get('huc4', ''),
                    'name': props.get('name', ''),
                    'states': props.get('states', ''),
                    'area_sqkm': props.get('areasqkm', 0)
                })
                
            # Create DataFrame
            metadata_df = pd.DataFrame(metadata)
            
            # Save to cache
            metadata_df.to_csv(cache_file, index=False)
            logger.info(f"Saved HUC metadata to cache: {cache_file}")
            
            return metadata_df
            
        except Exception as e:
            logger.error(f"Error fetching HUC metadata: {str(e)}", exc_info=True)
            raise
    
    def get_huc_boundary(self, huc_id: str, simplify_tolerance: float = 0.01) -> Optional[gpd.GeoDataFrame]:
        """Get simplified boundary for a specific HUC"""
        cache_file = self.cache_dir / f"huc_{huc_id}_boundary.geojson"
        
        if cache_file.exists():
            logger.info(f"Loading HUC boundary from cache: {cache_file}")
            return gpd.read_file(cache_file)
        
        try:
            # Initialize Earth Engine
            import ee
            ee.Initialize()
            
            # Get the specific HUC feature
            huc_collection = ee.FeatureCollection("USGS/WBD/2017/HUC08")
            huc_feature = huc_collection.filter(ee.Filter.eq('huc8', huc_id)).first()
            
            # Get the geometry
            huc_geom = huc_feature.geometry()
            
            # Simplify the geometry in Earth Engine for better performance
            simplified_geom = huc_geom.simplify(maxError=simplify_tolerance)
            
            # Get GeoJSON representation
            geojson = simplified_geom.getInfo()
            
            # Convert to GeoDataFrame
            geometry = Polygon(geojson['coordinates'][0])
            gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[geometry])
            
            # Save to cache
            gdf.to_file(cache_file, driver="GeoJSON")
            logger.info(f"Saved HUC boundary to cache: {cache_file}")
            
            return gdf
            
        except Exception as e:
            logger.error(f"Error fetching HUC boundary: {str(e)}", exc_info=True)
            return None
    
    def filter_stations_by_huc(self, stations_df: pd.DataFrame, huc_id: str) -> pd.DataFrame:
        """Filter stations dataframe to only include stations within the given HUC boundary"""
        # Get the HUC boundary
        huc_boundary = self.get_huc_boundary(huc_id)
        
        if huc_boundary is None or huc_boundary.empty:
            logger.error(f"No boundary available for HUC {huc_id}")
            return pd.DataFrame()
            
        # Convert stations to GeoDataFrame
        stations_gdf = gpd.GeoDataFrame(
            stations_df, 
            geometry=gpd.points_from_xy(stations_df.longitude, stations_df.latitude),
            crs="EPSG:4326"
        )
        
        # Perform spatial join
        stations_in_huc = gpd.sjoin(stations_gdf, huc_boundary, predicate='within')
        
        # Return filtered stations dataframe
        return stations_df.loc[stations_in_huc.index]