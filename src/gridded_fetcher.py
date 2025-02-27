from typing import Dict, List
import pandas as pd
import ee
from pathlib import Path
from datetime import datetime, timedelta
from src.base_fetcher import DataFetcher, MetadataProvider
from config import GriddedDataConfig, GriddedDatasetConfig
from tqdm.notebook import tqdm

class GriddedMetadataProvider(MetadataProvider):
    """Metadata provider for gridded data"""
    
    def get_metadata(self) -> pd.DataFrame:
        """Load metadata from ground data file"""
        raise NotImplementedError("Gridded data requires existing metadata")

    def save_metadata(self, metadata: pd.DataFrame, path: str) -> None:
        """Save metadata to file"""
        metadata.to_csv(path)

    def load_metadata(self, path: str) -> pd.DataFrame:
        """Load metadata from file"""
        if not Path(path).exists():
            raise FileNotFoundError(
                f"Metadata file not found at {path}. "
                "Please run ground data fetch first or provide metadata file."
            )
        df = pd.read_csv(path)
        df.set_index(df.columns[0], inplace=True)
        return df

class GriddedDataFetcher(DataFetcher):
    """Base class for gridded data fetchers"""
    
    def __init__(self, config: GriddedDataConfig):
        self.config = config
        self.metadata_provider = GriddedMetadataProvider()
        self.ee_initialized = False
        self.chunk_size_days = 365  # Process one year at a time

    def initialize_ee(self):
        """Initialize Earth Engine with error handling"""
        if not self.ee_initialized:
            try:
                ee.Initialize(project = "ee-sauravbhattarai1999")
                self.ee_initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Earth Engine: {str(e)}")

    def get_date_chunks(self, start_date: str, end_date: str) -> List[tuple]:
        """Split date range into chunks to handle EE query limits"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        chunks = []
        chunk_start = start
        
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=self.chunk_size_days), end)
            chunks.append((
                chunk_start.strftime('%Y-%m-%d'),
                chunk_end.strftime('%Y-%m-%d')
            ))
            chunk_start = chunk_end + timedelta(days=1)
            
        return chunks

    def get_timeseries(self, dataset_config: GriddedDatasetConfig,
                      lat: float, lon: float, start_date: str, end_date: str,
                      scale: int = 11132) -> pd.Series:
        """Extract data for a location and date range"""
        self.initialize_ee()
        point = ee.Geometry.Point([lon, lat])
        
        # Split request into chunks
        chunks = self.get_date_chunks(start_date, end_date)
        all_dates = []
        all_values = []
        
        for chunk_start, chunk_end in chunks:
            try:
                collection = ee.ImageCollection(dataset_config.collection_name) \
                    .filterDate(chunk_start, chunk_end) \
                    .select(dataset_config.variable_name)
                
                def extract_value(image):
                    value = image.reduceRegion(
                        reducer=ee.Reducer.first(),
                        geometry=point,
                        scale=scale
                    )
                    return ee.Feature(None, {
                        'value': value.get(dataset_config.variable_name),
                        'date': image.date().format('YYYY-MM-dd')
                    })
                
                points = collection.map(extract_value)
                data = points.getInfo()
                
                dates = [feature['properties']['date'] for feature in data['features']]
                values = [feature['properties']['value'] for feature in data['features']]
                
                all_dates.extend(dates)
                all_values.extend(values)
                
            except Exception as e:
                print(f"Error processing chunk {chunk_start} to {chunk_end}: {e}")
                continue
        
        if not all_dates:
            raise ValueError("No data retrieved for this location")
            
        return pd.Series(all_values, index=pd.to_datetime(all_dates))

    def process_dataset(self, dataset_config: GriddedDatasetConfig, 
                       metadata_df: pd.DataFrame) -> pd.DataFrame:
        """Process a single gridded dataset"""
        start_date = f'{self.config.start_year}-01-01'
        end_date = f'{self.config.end_year}-12-31'
        series_dict = {}
        
        for station_id, row in tqdm(metadata_df.iterrows(), 
                                  desc=f"Processing {dataset_config.name}",
                                  total=len(metadata_df)):
            try:
                values = self.get_timeseries(
                    dataset_config,
                    row['latitude'], row['longitude'],
                    start_date, end_date
                )
                series_dict[str(station_id)] = values * dataset_config.conversion_factor
            except Exception as e:
                print(f"Error processing station {station_id}: {e}")
                continue
                
        if not series_dict:
            raise ValueError(f"No data retrieved for {dataset_config.name}")
            
        result_df = pd.DataFrame(series_dict)
        result_df.index = pd.to_datetime(result_df.index)
        return result_df

    def fetch_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch all enabled gridded datasets"""
        metadata_path = str(Path(self.config.data_dir) / "stations_metadata.csv")
        metadata_df = self.metadata_provider.load_metadata(metadata_path)
        
        results = {}
        for dataset in self.config.get_enabled_datasets():
            print(f"\nFetching {dataset.name} data...")
            try:
                data = self.process_dataset(dataset, metadata_df)
                results[dataset.name] = data
                # Save each dataset as we go to prevent data loss
                self.save_data({dataset.name: data})
            except Exception as e:
                print(f"Error processing {dataset.name}: {e}")
                continue
            
        return results

    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Validate all datasets"""
        return all(
            not df.empty and 
            isinstance(df.index, pd.DatetimeIndex) and 
            df.index.is_monotonic_increasing
            for df in data.values()
        )

    def save_data(self, data: Dict[str, pd.DataFrame], path: str = None) -> None:
        """Save all datasets"""
        for name, df in data.items():
            output_path = str(Path(self.config.data_dir) / f"{name.lower()}_precipitation.csv")
            df.to_csv(output_path)
            print(f"Saved {name} data to {output_path}")

    def process(self) -> Dict[str, pd.DataFrame]:
        """Main processing method"""
        if not self.config.is_valid():
            raise ValueError("No gridded datasets selected")
            
        print("\nFetching gridded data...")
        data = self.fetch_data()
        
        if not self.validate_data(data):
            raise ValueError("Gridded data validation failed")
            
        return data