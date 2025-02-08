import numpy as np
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import pandas as pd
from typing import Dict, Optional, Union
import numpy.typing as npt

class StatisticsCalculator:
    """Calculator for comparing ground truth and ERA5 weather data statistics."""
    
    SEASON_MAPPING = {
        12:'winter', 1:'winter', 2:'winter',
        3:'spring', 4:'spring', 5:'spring',
        6:'summer', 7:'summer', 8:'summer',
        9:'fall', 10:'fall', 11:'fall'
    }

    def calculate_basic_stats(self, ground_values: npt.ArrayLike, era5_values: npt.ArrayLike) -> Optional[Dict]:
        """Calculate basic performance statistics between ground truth and ERA5 values.
        
        Args:
            ground_values: Array of ground truth measurements
            era5_values: Array of ERA5 predictions
            
        Returns:
            Dictionary of statistics or None if no valid data pairs
        """
        if not isinstance(ground_values, (np.ndarray, pd.Series)) or not isinstance(era5_values, (np.ndarray, pd.Series)):
            raise TypeError("Inputs must be numpy arrays or pandas series")
            
        if len(ground_values) != len(era5_values):
            raise ValueError("Input arrays must have same length")

        # Remove NaN pairs
        mask = ~(np.isnan(ground_values) | np.isnan(era5_values))
        ground = ground_values[mask]
        era5 = era5_values[mask]
        
        if len(ground) <= 365:
            return None
            
        return {
            'r2': r2_score(ground, era5),
            'rmse': np.sqrt(mean_squared_error(ground, era5)),
            'mae': mean_absolute_error(ground, era5),
            'pbias': self._percent_bias(ground, era5),
            'sample_size': len(ground)
        }

    def calculate_seasonal_stats(self, ground_data: pd.DataFrame, era5_data: pd.DataFrame, 
                               station: str) -> Dict:
        """Calculate statistics by season."""
        if not {'date', station}.issubset(ground_data.columns):
            raise ValueError("ground_data missing required columns")
            
        # Add season column
        merged = pd.merge(
            ground_data[['date', station]], 
            era5_data[['date', station]],
            on='date',
            suffixes=('_ground', '_era5')
        )
        merged['season'] = merged['date'].dt.month.map(self.SEASON_MAPPING)
        
        seasonal_stats = {}
        for season in ['winter', 'spring', 'summer', 'fall']:
            season_data = merged[merged['season'] == season]
            if len(season_data) > 90:  # Minimum 90 days per season
                stats = self.calculate_basic_stats(
                    season_data[f'{station}_ground'],
                    season_data[f'{station}_era5']
                )
                seasonal_stats[season] = stats
            else:
                seasonal_stats[season] = None
                
        return seasonal_stats

    def _percent_bias(self, observed: npt.ArrayLike, simulated: npt.ArrayLike) -> float:
        """Calculate percent bias between observed and simulated values.
        
        Args:
            observed: Array of observed values
            simulated: Array of simulated values
            
        Returns:
            Percent bias as float
            
        Raises:
            ZeroDivisionError: If sum of observed values is zero
        """
        sum_observed = np.sum(observed)
        if sum_observed == 0:
            raise ZeroDivisionError("Sum of observed values is zero")
        return 100 * np.sum(simulated - observed) / sum_observed
    
    def get_seasonal_stats_df(self, seasonal_results: Dict) -> pd.DataFrame:
        """Convert seasonal results dictionary to DataFrame"""
        seasonal_rows = []
        for station, seasons in seasonal_results.items():
            for season, stats in seasons.items():
                if stats:  # Check if stats exist
                    row = {
                        'station_id': station,
                        'season': season,
                        **stats  # Unpack all statistics
                    }
                    seasonal_rows.append(row)
        return pd.DataFrame(seasonal_rows)

if __name__ == "__main__":
    import argparse
    from datetime import datetime, timedelta
    
    def generate_sample_data(days=1460):  # 4 years of data
        dates = pd.date_range(start='2020-01-01', periods=days)
        
        # Generate seasonal patterns
        ground_values = []
        for date in dates:
            if date.month in [12, 1, 2]:  # Winter
                base = 15
            elif date.month in [3, 4, 5]:  # Spring
                base = 8
            elif date.month in [6, 7, 8]:  # Summer
                base = 2
            else:  # Fall
                base = 10
            ground_values.append(max(0, np.random.normal(base, base/3)))
            
        ground_data = pd.DataFrame({
            'date': dates,
            'station1': ground_values
        })
        
        era5_data = pd.DataFrame({
            'date': dates,
            'station1': ground_data['station1'] + np.random.normal(0, 1, days)
        })
        
        return ground_data, era5_data
    
    try:
        # Generate test data
        print("Generating 4 years of sample data...")
        ground_data, era5_data = generate_sample_data()
        
        calculator = StatisticsCalculator()
        
        # Test seasonal statistics
        seasonal_stats = calculator.calculate_seasonal_stats(
            ground_data,
            era5_data,
            'station1'
        )
        
        print("\nSeasonal Statistics:")
        for season, stats in seasonal_stats.items():
            print(f"\n{season.upper()}:")
            if stats:
                for metric, value in stats.items():
                    print(f"  {metric}: {value:.4f}")
            else:
                print("  Insufficient data")
                
    except Exception as e:
        print(f"Error: {str(e)}")
