import ee
import pandas as pd
from datetime import datetime
from meteostat import Stations, Daily
import geemap
import numpy as np

class ERA5Fetcher:
    def __init__(self):
        # Initialize Earth Engine
        try:
            ee.Initialize(project='ee-sauravbhattarai1999')
        except Exception as e:
            print(f"Error initializing Earth Engine: {e}")

    def get_era5_timeseries_by_year(self, lat, lon, year):
        """Extract ERA5 precipitation data for a location and year"""
        point = ee.Geometry.Point([lon, lat])
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        
        era5_collection = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR") \
            .filterDate(start_date, end_date) \
            .select('total_precipitation_sum')
        
        def extract_value(image):
            value = image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=11132
            )
            return ee.Feature(None, {
                'precipitation': value.get('total_precipitation_sum'),
                'date': image.date().format('YYYY-MM-dd')
            })
        
        points = era5_collection.map(extract_value)
        data = points.getInfo()
        
        dates, temps = [], []
        for feature in data['features']:
            dates.append(feature['properties']['date'])
            temps.append(feature['properties']['precipitation'])
        
        return pd.Series(temps, index=pd.DatetimeIndex(dates))

    def get_era5_data(self, metadata_df, start_year=1980, end_year=2024):
        """Get ERA5 data for all stations"""
        temp_series = {}
        
        for i, row in metadata_df.iterrows():
            uid = str(row['id'])
            lat = row['latitude']
            lon = row['longitude']
            
            print(f"Processing station {uid} ({i+1}/{len(metadata_df)})")
            
            try:
                all_series = []
                for year in range(start_year, end_year + 1):
                    year_series = self.get_era5_timeseries_by_year(lat, lon, year)
                    all_series.append(year_series)
                
                if all_series:
                    temps = pd.concat(all_series)
                    temp_series[uid] = temps * 1000  # Convert to mm
            except Exception as e:
                print(f"Error processing station {uid}: {e}")
                
        return pd.DataFrame(temp_series)

class GroundDataFetcher:
    def get_california_stations(self):
        """Get California weather stations"""
        stations = Stations()
        stations = stations.region('US', 'CA')
        return stations.fetch()

    def get_ground_data(self, start_year=1980, end_year=2024):
        """Get ground precipitation data"""
        start = datetime(start_year, 1, 1)
        end = datetime(end_year, 12, 31)
        
        stations_df = self.get_california_stations()
        stations_df.to_csv('Data/ca_stations_metadata.csv')
        
        precipitation_data = {}
        for station_id in stations_df.index:
            try:
                data = Daily(station_id, start, end)
                df = data.fetch()
                if not df.empty and 'prcp' in df.columns:
                    precipitation_data[station_id] = df['prcp']
                    print(f"Retrieved data for station {station_id}")
            except Exception as e:
                print(f"Error with station {station_id}: {e}")
        
        return pd.DataFrame(precipitation_data), stations_df

def fetch_all_data(start_year=1980, end_year=2024):
    """Main function to fetch both ERA5 and ground data"""
    try:
        # Get ground data first
        ground_fetcher = GroundDataFetcher()
        ground_data, stations_metadata = ground_fetcher.get_ground_data(start_year, end_year)
        ground_data.to_csv('Data/ca_daily_precipitation.csv')
        
        # Get ERA5 data using station metadata
        era5_fetcher = ERA5Fetcher()
        era5_data = era5_fetcher.get_era5_data(stations_metadata, start_year, end_year)
        era5_data.to_csv('Data/era5_daily_precipitation.csv')
        
        return ground_data, era5_data, stations_metadata
        
    except Exception as e:
        print(f"Error in data fetching: {e}")
        return None, None, None

if __name__ == "__main__":
    import argparse
    from tqdm import tqdm
    import os
    
    # Create Data directory if it doesn't exist
    if not os.path.exists('Data'):
        os.makedirs('Data')
        print("Created Data directory")
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch ERA5 and ground station data for California')
    parser.add_argument('--start-year', type=int, default=1980, help='Start year for data collection')
    parser.add_argument('--end-year', type=int, default=2024, help='End year for data collection')
    args = parser.parse_args()
    
    print(f"Fetching data from {args.start_year} to {args.end_year}")
    try:
        ground_data, era5_data, metadata = fetch_all_data(args.start_year, args.end_year)
        
        if ground_data is not None and era5_data is not None and metadata is not None:
            print("Data fetching completed successfully!")
            print(f"Ground stations: {ground_data.shape[1]}")
            print(f"ERA5 stations: {era5_data.shape[1]}")
            print(f"Data saved in Data/ directory")
        else:
            print("Data fetching failed! Check error messages above.")
            
    except Exception as e:
        print(f"Critical error during execution: {str(e)}")
        raise