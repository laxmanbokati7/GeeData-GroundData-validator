from src.data_loader import DataLoader
from src.get_statistics import StatisticsCalculator 
from src.plotting import Plotter
import pandas as pd
from src.data_fetcher import fetch_all_data

def main():
    try:
        # Fetch new data if needed
        print("Do you want to fetch new data? (y/n)")
        if input().lower() == 'y':
            print("Fetching new data...")
            ground_data, era5_data, metadata = fetch_all_data()
            if ground_data is None:
                print("Error fetching data. Using existing data...")
        
        # Continue with existing pipeline
        loader = DataLoader()
        stats = StatisticsCalculator()
        plotter = Plotter()
        
        # Load data
        print("Loading data...")
        ground_data, era5_data, matching_stations = loader.load_data(
            "Data/ca_daily_precipitation.csv",
            "Data/era5_daily_precipitation.csv",
            "Data/ca_stations_metadata.csv"
        )
        
        print(f"Found {len(matching_stations)} matching stations")
        
        if not matching_stations:
            print("No matching stations found. Exiting.")
            return
            
        # Calculate statistics for each station
        results = []
        seasonal_results = {}
        
        for station in matching_stations:
            try:
                # Verify data exists for this station
                if station not in ground_data.columns or station not in era5_data.columns:
                    print(f"Missing data for station {station}")
                    continue
                    
                # Basic statistics
                basic_stats = stats.calculate_basic_stats(
                    ground_data[station].values,  # Convert to numpy array
                    era5_data[station].values     # Convert to numpy array
                )
                
                if basic_stats:
                    basic_stats['station_id'] = station
                    results.append(basic_stats)
                    
                # Seasonal statistics
                seasonal_stats = stats.calculate_seasonal_stats(
                    ground_data, era5_data, station
                )
                seasonal_results[station] = seasonal_stats
                
            except Exception as e:
                print(f"Error processing station {station}: {str(e)}")
                continue
        
        if not results:
            print("No valid results generated. Exiting.")
            return
            
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results before plotting
        results_df.to_csv('Results/precipitation_comparison_results.csv', index=False)
        print("Results saved to Results/precipitation_comparison_results.csv")
        
        # Convert results to DataFrames
        results_df = pd.DataFrame(results)
        seasonal_df = stats.get_seasonal_stats_df(seasonal_results)
        
        # Save results
        results_df.to_csv('Results/station_statistics.csv', index=False)
        seasonal_df.to_csv('Results/seasonal_statistics.csv', index=False)
        print("Results saved to Results/station_statistics.csv")
        print("Seasonal results saved to Results/seasonal_statistics.csv")
        
       # Load metadata
        metadata_df = pd.read_csv('Data/ca_stations_metadata.csv')
        
        # Generate plots
        if len(results_df) > 0:
            try:
                # Create spatial plots
                plotter.create_all_spatial_plots(results_df, seasonal_df, metadata_df)
                print("Spatial distribution plots saved")
                
                # Create seasonal boxplot
                plotter.create_seasonal_boxplot(seasonal_df)
                print("Seasonal boxplot saved")
                
            except Exception as e:
                print(f"Warning: Error generating plots: {str(e)}")
                
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()

