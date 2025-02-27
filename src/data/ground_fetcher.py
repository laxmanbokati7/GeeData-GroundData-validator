from typing import Optional
import pandas as pd
from datetime import datetime
from meteostat import Stations, Daily
from src.base_fetcher import DataFetcher, MetadataProvider
from config import GroundDataConfig
from tqdm.notebook import tqdm
import warnings

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
            if self.config.states:
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
        print(f"Saved station metadata to {path}")

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
    """Fetches ground data using Meteostat"""
    
    def __init__(self, config: GroundDataConfig):
        self.config = config
        self.metadata_provider = GroundMetadataProvider(config)

    def fetch_data(self) -> pd.DataFrame:
        """Fetch ground precipitation data"""
        # Get or load metadata
        try:
            metadata = self.metadata_provider.load_metadata(self.config.get_metadata_path())
            print("Using existing metadata file")
        except FileNotFoundError:
            print("Fetching new station metadata...")
            metadata = self.metadata_provider.get_metadata()
            self.metadata_provider.save_metadata(metadata, self.config.get_metadata_path())

        start = datetime(self.config.start_year, 1, 1)
        end = datetime(self.config.end_year, 12, 31)
        
        precipitation_data = {}
        
        # Use tqdm for progress bar
        for idx, station_id in enumerate(tqdm(metadata.index, desc="Processing stations")):
            try:
                data = Daily(station_id, start, end)
                df = data.fetch()
                if not df.empty and 'prcp' in df.columns:
                    precipitation_data[station_id] = df['prcp']
            except Exception as e:
                print(f"Error with station {station_id}: {e}")
                continue
        
        if not precipitation_data:
            raise RuntimeError("No valid data was fetched from any station")
            
        # Create DataFrame and ensure proper datetime index
        result = pd.DataFrame(precipitation_data)
        result.index = pd.to_datetime(result.index)
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
        print(f"Saved ground data to {path}")

    def process(self) -> pd.DataFrame:
        """Main processing method"""
        print("\nFetching ground data...")
        data = self.fetch_data()
        
        if not self.validate_data(data):
            raise ValueError("Ground data validation failed")
            
        self.save_data(data, self.config.get_data_path())
        return data