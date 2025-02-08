import pandas as pd
import geopandas as gpd

class DataLoader:
    def load_data(self, ground_file, era5_file, metadata_file=None):
        """Load ground and ERA5 precipitation data
        
        Args:
            ground_file (str): Path to ground data CSV
            era5_file (str): Path to ERA5 data CSV 
            metadata_file (str, optional): Path to station metadata
            
        Returns:
            tuple: (ground_data, era5_data, matching_stations)
        """
        try:
            # Load ground data
            ground_data = pd.read_csv(ground_file)
            if 'date' not in ground_data.columns:
                if 'Date' in ground_data.columns:
                    ground_data = ground_data.rename(columns={'Date': 'date'})
                else:
                    raise ValueError("No date column found in ground data")
                    
            # Load ERA5 data    
            era5_data = pd.read_csv(era5_file)
            if 'date' not in era5_data.columns:
                if 'Date' in era5_data.columns:
                    era5_data = era5_data.rename(columns={'Date': 'date'})
                else:
                    raise ValueError("No date column found in ERA5 data")

            # Convert dates to datetime
            ground_data['date'] = pd.to_datetime(ground_data['date'])
            era5_data['date'] = pd.to_datetime(era5_data['date'])
            
            # Find matching stations (excluding date columns)
            ground_stations = set(ground_data.columns) - {'date', 'Date'}
            era5_stations = set(era5_data.columns) - {'date', 'Date'}
            matching_stations = sorted(list(ground_stations.intersection(era5_stations)))
            
            if not matching_stations:
                raise ValueError("No matching station IDs found between datasets")

            # Align data on matching dates
            merged_dates = pd.merge(ground_data[['date']], era5_data[['date']], how='inner')
            ground_data = ground_data[ground_data['date'].isin(merged_dates['date'])]
            era5_data = era5_data[era5_data['date'].isin(merged_dates['date'])]
            
            # Sort both datasets by date
            ground_data = ground_data.sort_values('date').reset_index(drop=True)
            era5_data = era5_data.sort_values('date').reset_index(drop=True)
            
            return ground_data, era5_data, matching_stations
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise

    def add_metadata(self, data, metadata_file):
        """Add station metadata if available"""
        if metadata_file:
            metadata = pd.read_csv(metadata_file)
            return pd.merge(data, 
                          metadata[['id', 'latitude', 'longitude', 'elevation']],
                          left_on='station_id',
                          right_on='id')
        return data

if __name__ == "__main__":
    import argparse
    import os
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Load and validate precipitation data files')
    parser.add_argument('--ground-file', default='Data/ca_daily_precipitation.csv', 
                       help='Path to ground station data CSV')
    parser.add_argument('--era5-file', default='Data/era5_daily_precipitation.csv',
                       help='Path to ERA5 data CSV')
    parser.add_argument('--metadata-file', default='Data/ca_stations_metadata.csv',
                       help='Path to station metadata CSV')
    args = parser.parse_args()
    
    # Check if files exist
    for filepath in [args.ground_file, args.era5_file, args.metadata_file]:
        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}")
            exit(1)
    
    # Test data loading
    try:
        loader = DataLoader()
        ground_data, era5_data, matching_stations = loader.load_data(
            args.ground_file,
            args.era5_file,
            args.metadata_file
        )
        
        print("\nData loading successful!")
        print(f"Ground data shape: {ground_data.shape}")
        print(f"ERA5 data shape: {era5_data.shape}")
        print(f"Number of matching stations: {len(matching_stations)}")
        print(f"\nFirst few matching stations: {matching_stations[:5]}")
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        exit(1)