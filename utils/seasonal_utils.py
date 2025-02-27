from typing import Dict, List
import pandas as pd
import numpy as np
from pathlib import Path
from utils.statistical_utils import calculate_stats_for_all_stations

def get_season(month: int) -> str:
    """Get season name for given month"""
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:  # 9, 10, 11
        return 'Fall'

def split_by_season(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Split DataFrame into seasonal DataFrames"""
    # Add season column
    df = df.copy()
    df['season'] = df.index.month.map(get_season)
    
    # Split into seasons
    seasons = {}
    for season in ['Winter', 'Spring', 'Summer', 'Fall']:
        season_data = df[df['season'] == season].drop('season', axis=1)
        if not season_data.empty:
            seasons[season] = season_data
            
    return seasons

def calculate_seasonal_stats(ground_data: pd.DataFrame, gridded_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Calculate statistics for each season"""
    # Ensure data is aligned
    ground_data, gridded_data = ground_data.align(gridded_data, join='inner')
    
    # Split into seasons
    ground_seasons = split_by_season(ground_data)
    gridded_seasons = split_by_season(gridded_data)
    
    # Calculate statistics for each season
    seasonal_stats = {}
    for season in ['Winter', 'Spring', 'Summer', 'Fall']:
        if season in ground_seasons and season in gridded_seasons:
            stats = calculate_stats_for_all_stations(
                ground_seasons[season],
                gridded_seasons[season]
            )
            stats['season'] = season
            seasonal_stats[season] = stats
            
    return seasonal_stats

def save_seasonal_stats(seasonal_stats: Dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Save seasonal statistics to CSV files"""
    # Combine all seasons into one DataFrame
    all_stats = pd.concat(seasonal_stats.values(), keys=seasonal_stats.keys())
    all_stats.index.names = ['season', 'station']
    
    # Save combined stats
    output_path = output_dir / 'seasonal_stats.csv'
    all_stats.to_csv(output_path)
    print(f"Saved seasonal statistics to {output_path}")
    
    # Also save individual season files if needed
    for season, stats in seasonal_stats.items():
        season_path = output_dir / f'{season.lower()}_stats.csv'
        stats.to_csv(season_path)
        
def get_seasonal_summary(seasonal_stats: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create summary statistics for each season"""
    summary = []
    
    for season, stats in seasonal_stats.items():
        season_summary = {
            'season': season,
            'n_stations': len(stats),
            'mean_r2': stats['r2'].mean(),
            'mean_rmse': stats['rmse'].mean(),
            'mean_bias': stats['bias'].mean(),
            'mean_mae': stats['mae'].mean()
        }
        summary.append(season_summary)
        
    return pd.DataFrame(summary)