#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Callable, Dict, Any
import pandas as pd
from datetime import datetime
from meteostat import Stations, Daily
from src.base_fetcher import DataFetcher, MetadataProvider
from config import GroundDataConfig
from tqdm.auto import tqdm
import warnings
import logging
from pathlib import Path
from utils.huc_utils import HUCDataProvider

logger = logging.getLogger(__name__)

# Temporarily suppress the FutureWarning about parse_dates
warnings.filterwarnings("ignore", message="Support for nested sequences for 'parse_dates'", category=FutureWarning)

class GroundMetadataProvider(MetadataProvider):
    """Provides metadata for ground stations using Meteostat"""
    
    def __init__(self, config: GroundDataConfig):
        self.config = config

    def get_metadata(self) -> pd.DataFrame:
        """Get weather stations for specified states or all US states"""
        stations = Stations()
        try:
            if self.config.huc_id:
                stations_df = stations.region('US').fetch()

                return stations_df

            elif self.config.states:
                all_stations = []
                for state in self.config.states:
                    state_stations = stations.region('US', state)
                    all_stations.append(state_stations.fetch())
                stations_df = pd.concat(all_stations)
            else:
                stations_df = stations.region('US').fetch()
            return stations_df
            
        except Exception as e:
            raise RuntimeError(f"Error fetching station metadata: {str(e)}")

    def save_metadata(self, metadata: pd.DataFrame, path: str) -> None:
        """Save metadata to CSV file"""
        metadata.to_csv(path)
        logger.info(f"Saved station metadata to {path}")

    def load_metadata(self, path: str) -> pd.DataFrame:
        """Load metadata from CSV file"""
        # Read CSV without parsing dates
        df = pd.read_csv(path)
        
        # Convert date columns after loading if they exist
        date_columns = ['start', 'end']  # Add any other date columns here
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                
        return df.set_index(df.columns[0])

class GroundDataFetcher(DataFetcher):
    """Fetches ground data using Meteostat with progress reporting capability"""
    
    def __init__(self, config: GroundDataConfig):
        self.config = config
        self.metadata_provider = GroundMetadataProvider(config)
        self.progress_callback = None
        
    def set_progress_callback(self, callback: Callable[[str, int], None]) -> None:
        """
        Set a callback function for progress reporting
        
        Args:
            callback: Function that takes dataset_name and progress percentage
        """
        self.progress_callback = callback

    def set_filter_polygon(self, polygon_feature):
        """
        Set a polygon feature to filter stations
        
        Args:
            polygon_feature (dict): GeoJSON feature for filtering stations
        """
        self.filter_polygon = polygon_feature

    def fetch_data(self) -> pd.DataFrame:
        """Fetch ground precipitation data with progress reporting"""
        # Get or load metadata
        try:
            metadata = self.metadata_provider.load_metadata(self.config.get_metadata_path())
            logger.info("Using existing metadata file")
            
            if self.progress_callback:
                self.progress_callback("Ground", 10)
        except FileNotFoundError:
            logger.info("Fetching new station metadata...")
            metadata = self.metadata_provider.get_metadata()

            # Apply HUC filtering if specified
            if self.config.huc_id:
                logger.info(f"Filtering stations by HUC: {self.config.huc_id}")
                huc_provider = HUCDataProvider()
                metadata = huc_provider.filter_stations_by_huc(metadata, self.config.huc_id)
                
                if metadata.empty:
                    raise ValueError(f"No stations found within HUC {self.config.huc_id}")
                    
                logger.info(f"Filtered to {len(metadata)} stations within HUC")
                
            # Apply polygon filtering if specified
            if hasattr(self, 'filter_polygon') and self.filter_polygon:
                logger.info("Filtering stations by custom polygon")
                from utils.drawing_utils import filter_stations_by_polygon
                metadata = filter_stations_by_polygon(metadata, self.filter_polygon)
                
                if metadata.empty:
                    raise ValueError("No stations found within the specified polygon")
                    
                logger.info(f"Filtered to {len(metadata)} stations within polygon")
                
            self.metadata_provider.save_metadata(metadata, self.config.get_metadata_path())
            
            if self.progress_callback:
                self.progress_callback("Ground", 20)

        start = datetime(self.config.start_year, 1, 1)
        end = datetime(self.config.end_year, 12, 31)
        
        precipitation_data = {}
        
        # Calculate total stations for progress tracking
        total_stations = len(metadata.index)
        current_station = 0
        
        # Use tqdm for progress bar (will be visible in CLI, disabled in GUI when callback is set)
        for idx, station_id in enumerate(tqdm(metadata.index, desc="Processing stations", 
                                             disable=self.progress_callback is not None)):
            try:
                data = Daily(station_id, start, end)
                df = data.fetch()
                if not df.empty and 'prcp' in df.columns:
                    precipitation_data[station_id] = df['prcp']
            except Exception as e:
                logger.error(f"Error with station {station_id}: {e}")
                continue
                
            # Update progress
            current_station += 1
            if self.progress_callback:
                progress = 20 + (current_station / total_stations * 70)
                self.progress_callback("Ground", int(progress))
        
        if not precipitation_data:
            raise RuntimeError("No valid data was fetched from any station")
            
        # Create DataFrame and ensure proper datetime index
        result = pd.DataFrame(precipitation_data)
        result.index = pd.to_datetime(result.index)
        
        # Final progress update
        if self.progress_callback:
            self.progress_callback("Ground", 100)
            
        return result

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate the fetched data"""
        if data.empty:
            return False
        if not isinstance(data.index, pd.DatetimeIndex):
            return False
        if not data.index.is_monotonic_increasing:
            return False
        return True

    def save_data(self, data: pd.DataFrame, path: str) -> None:
        """Save the data to CSV file"""
        # Save with datetime index properly formatted
        data.to_csv(path)
        logger.info(f"Saved ground data to {path}")

    def process(self) -> pd.DataFrame:
        """Main processing method with progress reporting"""
        logger.info("Fetching ground data...")
        
        if self.progress_callback:
            self.progress_callback("Ground", 0)
            
        data = self.fetch_data()
        
        if not self.validate_data(data):
            raise ValueError("Ground data validation failed")
            
        self.save_data(data, self.config.get_data_path())
        
        if self.progress_callback:
            self.progress_callback("Ground", 100)
            
        return data

    def get_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary information for the fetched data"""
        return {
            'n_stations': len(data.columns),
            'n_rows': len(data),
            'start_date': data.index.min().strftime('%Y-%m-%d'),
            'end_date': data.index.max().strftime('%Y-%m-%d'),
            'data_type': 'Ground',
            'missing_percentage': (data.isna().sum().sum() / (data.shape[0] * data.shape[1])) * 100
        }

    def fetch_ground_data(self, config, drawn_feature=None):
        """
        Fetch ground data based on the configuration and optional drawn feature.
        
        Args:
            config (GroundDataConfig): Configuration for ground data fetching
            drawn_feature (dict, optional): GeoJSON feature for filtering stations
        """
        logger.info("Fetching ground data...")
        if drawn_feature:
            logger.info(f"Using drawn feature for filtering: {drawn_feature}")
            # Apply filtering logic using the drawn feature
            self.filter_stations_by_drawn_feature(drawn_feature)

        # Proceed with fetching ground data
        self._fetch_station_metadata(config)
        self._fetch_station_data(config)