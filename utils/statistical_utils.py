from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def calculate_station_stats(observed: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """Calculate statistical parameters for a single station"""
    # Remove any pairs where either value is NaN
    mask = ~(np.isnan(observed) | np.isnan(predicted))
    obs_clean = observed[mask]
    pred_clean = predicted[mask]
    
    # Need at least 10 points for meaningful statistics
    if len(obs_clean) < 10:
        return {}
        
    stats = {}
    
    # Basic statistics
    stats['count'] = len(obs_clean)
    stats['obs_mean'] = np.mean(obs_clean)
    stats['pred_mean'] = np.mean(pred_clean)
    
    # Error metrics
    stats['bias'] = np.mean(pred_clean - obs_clean)
    stats['mae'] = mean_absolute_error(obs_clean, pred_clean)
    stats['rmse'] = np.sqrt(mean_squared_error(obs_clean, pred_clean))
    stats['r2'] = r2_score(obs_clean, pred_clean)
    
    # Relative errors
    stats['rel_bias'] = stats['bias'] / stats['obs_mean'] if stats['obs_mean'] != 0 else np.nan
    stats['rel_rmse'] = stats['rmse'] / stats['obs_mean'] if stats['obs_mean'] != 0 else np.nan
    
    # Nash-Sutcliffe Efficiency
    mean_obs = np.mean(obs_clean)
    numerator = np.sum((obs_clean - pred_clean) ** 2)
    denominator = np.sum((obs_clean - mean_obs) ** 2)
    stats['nse'] = 1 - (numerator / denominator) if denominator != 0 else np.nan
    
    # Correlation coefficient
    if np.std(obs_clean) > 0 and np.std(pred_clean) > 0:
        stats['corr'] = np.corrcoef(obs_clean, pred_clean)[0, 1]
    else:
        stats['corr'] = np.nan
    
    # Percent Bias
    obs_sum = np.sum(obs_clean)
    stats['pbias'] = 100 * np.sum(pred_clean - obs_clean) / obs_sum if obs_sum != 0 else np.nan
    
    return stats

def calculate_stats_for_all_stations(df_obs: pd.DataFrame, df_pred: pd.DataFrame) -> pd.DataFrame:
    """Calculate statistics for each station"""
    stats_list = []
    
    for station in df_obs.columns:
        stats = calculate_station_stats(
            df_obs[station].values,
            df_pred[station].values
        )
        if stats:  # Only include if we got valid statistics
            stats['station'] = station
            stats_list.append(stats)
    
    return pd.DataFrame(stats_list).set_index('station')

def calculate_percentile_stats_by_station(df_obs: pd.DataFrame, df_pred: pd.DataFrame, 
                                        percentile: float, higher: bool = True) -> pd.DataFrame:
    """Calculate extreme value statistics for each station"""
    stats_list = []
    
    for station in df_obs.columns:
        # Calculate threshold for this station
        threshold = df_obs[station].quantile(percentile/100)
        
        # Create mask for extreme values
        if higher:
            mask = df_obs[station] >= threshold
        else:
            mask = df_obs[station] <= threshold
        
        # Calculate statistics for extreme values
        stats = calculate_station_stats(
            df_obs[station][mask].values,
            df_pred[station][mask].values
        )
        
        if stats:  # Only include if we got valid statistics
            stats['station'] = station
            stats_list.append(stats)
    
    return pd.DataFrame(stats_list).set_index('station')

def aggregate_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily data to monthly"""
    # Calculate required days for each month (80% threshold)
    days_in_month = df.resample('ME').size()
    min_required = (days_in_month * 0.8).astype(int)
    
    # Calculate monthly sums and counts
    monthly_sum = df.resample('ME').sum()
    monthly_count = df.resample('ME').count()
    
    # Create mask for insufficient data
    insufficient_mask = monthly_count < min_required.values.reshape(-1, 1)
    
    # Apply mask
    monthly_sum[insufficient_mask] = np.nan
    
    return monthly_sum

def aggregate_to_yearly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily data to yearly"""
    # Calculate yearly sums
    yearly_sum = df.resample('YE').sum()
    
    # Count number of valid months per year
    monthly_valid = df.resample('ME').count() > 0
    months_per_year = monthly_valid.resample('YE').sum()
    
    # Mask years with insufficient months (less than 9)
    insufficient_mask = months_per_year < 9
    yearly_sum[insufficient_mask] = np.nan
    
    return yearly_sum

def validate_station_data(data: pd.Series) -> Dict[str, bool]:
    """Check if data length is sufficient for a single station"""
    # Count years with any data
    yearly_counts = data.resample('YE').count()
    years_with_data = (yearly_counts > 0).sum()
    
    # Count total valid observations
    total_valid = (~data.isna()).sum()
    
    return {
        'daily': total_valid >= 365,  # At least one year of daily data
        'monthly': years_with_data >= 2,   # At least two years for monthly analysis
        'yearly': years_with_data >= 5     # At least five years for yearly analysis
    }

def validate_data_length(df: pd.DataFrame) -> Dict[str, Dict[str, bool]]:
    """Check if data length is sufficient for each station"""
    return {col: validate_station_data(df[col]) for col in df.columns}