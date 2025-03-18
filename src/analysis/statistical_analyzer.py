from typing import Dict, List, Tuple, Callable, Optional, Any
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import logging
from utils.statistical_utils import (
    calculate_stats_for_all_stations,
    calculate_percentile_stats_by_station,
    aggregate_to_monthly,
    aggregate_to_yearly,
    validate_data_length
)
from utils.seasonal_utils import (
    calculate_seasonal_stats,
    save_seasonal_stats,
    get_seasonal_summary
)

# Temporarily suppress the FutureWarning about parse_dates
warnings.filterwarnings("ignore", message="Support for nested sequences for 'parse_dates'", category=FutureWarning)

logger = logging.getLogger(__name__)

class GriddedDataAnalyzer:
    """Analyzer for comparing gridded datasets with ground observations"""
    
    def __init__(self, data_dir: str = 'Data', results_dir: str = 'Results'):
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.ground_data = None
        self.gridded_datasets = {}
        self.progress_callback = None
        self.status_callback = None
        
    def set_progress_callback(self, callback: Callable[[int], None]) -> None:
        """Set callback for progress updates"""
        self.progress_callback = callback
        
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for status message updates"""
        self.status_callback = callback
        
    def _update_progress(self, value: int) -> None:
        """Update progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(value)
            
    def _update_status(self, message: str) -> None:
        """Update status if callback is set"""
        if self.status_callback:
            self.status_callback(message)
        logger.info(message)
        
    def load_data(self):
        """Load ground and gridded datasets"""
        self._update_status("Loading data...")
        
        # Load ground data
        ground_path = self.data_dir / 'ground_daily_precipitation.csv'
        if not ground_path.exists():
            raise FileNotFoundError("Ground data file not found")
        
        # Properly load without parse_dates, then convert index
        self.ground_data = pd.read_csv(ground_path, index_col=0)
        self.ground_data.index = pd.to_datetime(self.ground_data.index)
        
        self._update_status(f"Loaded ground data: {self.ground_data.shape}")
        self._update_progress(10)
        
        # Load gridded datasets
        for file in self.data_dir.glob('*_precipitation.csv'):
            if 'ground' not in file.name:
                dataset_name = file.name.split('_')[0].upper()
                # Properly load without parse_dates, then convert index
                data = pd.read_csv(file, index_col=0)
                data.index = pd.to_datetime(data.index)
                self.gridded_datasets[dataset_name] = data
                
                self._update_status(f"Loaded {dataset_name} data: {data.shape}")
                
        self._update_progress(20)
                
        if not self.gridded_datasets:
            raise FileNotFoundError("No gridded datasets found")
            
    def create_dataset_folder(self, dataset_name: str) -> Path:
        """Create and return dataset results folder"""
        dataset_dir = self.results_dir / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir
            
    def preprocess_data(self, ground: pd.DataFrame, gridded: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Preprocess and align datasets"""
        # Get common stations
        common_stations = list(set(ground.columns) & set(gridded.columns))
        if not common_stations:
            raise ValueError("No common stations found")
            
        self._update_status(f"Found {len(common_stations)} common stations")
            
        # Select common stations and align time periods
        ground = ground[common_stations].copy()
        gridded = gridded[common_stations].copy()
        
        # Align indices
        ground, gridded = ground.align(gridded, join='inner')
        
        if ground.empty or gridded.empty:
            raise ValueError("No overlapping data found")
            
        return ground, gridded
            
    def analyze_dataset(self, dataset_name: str, gridded_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a single gridded dataset"""
        self._update_status(f"Analyzing {dataset_name}...")
        
        try:
            # Preprocess data
            ground, gridded = self.preprocess_data(self.ground_data, gridded_data)
            
            # Create output directory
            output_dir = self.create_dataset_folder(dataset_name)
            
            # Validate data length for each station
            self._update_status("Validating data length for each station...")
            validations = validate_data_length(ground)
            
            # Save validation results
            validation_df = pd.DataFrame.from_dict(validations, orient='index')
            validation_df.to_csv(output_dir / 'data_validation.csv')
            
            # Calculate and save regular statistics
            self._update_status("Calculating daily statistics...")
            daily_stats = calculate_stats_for_all_stations(ground, gridded)
            daily_stats.to_csv(output_dir / 'daily_stats.csv')
            
            self._update_status("Calculating extreme value statistics...")
            low_extreme_stats = calculate_percentile_stats_by_station(ground, gridded, 10, False)
            high_extreme_stats = calculate_percentile_stats_by_station(ground, gridded, 90, True)
            low_extreme_stats.to_csv(output_dir / 'low_extreme_stats.csv')
            high_extreme_stats.to_csv(output_dir / 'high_extreme_stats.csv')
            
            self._update_status("Calculating monthly statistics...")
            ground_monthly = aggregate_to_monthly(ground)
            gridded_monthly = aggregate_to_monthly(gridded)
            monthly_stats = calculate_stats_for_all_stations(ground_monthly, gridded_monthly)
            monthly_stats.to_csv(output_dir / 'monthly_stats.csv')
            
            self._update_status("Calculating yearly statistics...")
            ground_yearly = aggregate_to_yearly(ground)
            gridded_yearly = aggregate_to_yearly(gridded)
            yearly_stats = calculate_stats_for_all_stations(ground_yearly, gridded_yearly)
            yearly_stats.to_csv(output_dir / 'yearly_stats.csv')
            
            # Calculate and save seasonal statistics
            self._update_status("Calculating seasonal statistics...")
            seasonal_stats = calculate_seasonal_stats(ground, gridded)
            save_seasonal_stats(seasonal_stats, output_dir)
            
            # Create summary for seasons
            seasonal_summary = get_seasonal_summary(seasonal_stats)
            seasonal_summary.to_csv(output_dir / 'seasonal_summary.csv', index=False)
            
            self._update_status(f"Results saved to {output_dir}")
            
            # Create analysis summary
            summary = {
                'n_stations': len(ground.columns),
                'start_date': ground.index.min(),
                'end_date': ground.index.max(),
                'total_days': len(ground),
                'stations_with_sufficient_data': sum(1 for v in validations.values() 
                                                   if v['daily'] and v['monthly'] and v['yearly'])
            }
            
            summary_df = pd.DataFrame([summary])
            summary_df.to_csv(output_dir / 'analysis_summary.csv', index=False)
            
            return summary
                    
        except Exception as e:
            logger.error(f"Error analyzing {dataset_name}: {str(e)}", exc_info=True)
            self._update_status(f"Error analyzing {dataset_name}: {str(e)}")
            return {}
        
    def run_analysis(self):
        """Run analysis for all datasets"""
        self._update_status("Starting statistical analysis...")
        self._update_progress(0)
        
        try:
            # Load data
            self.load_data()
            
            # Create results directory if it doesn't exist
            self.results_dir.mkdir(parents=True, exist_ok=True)
            
            # Calculate total steps for progress tracking
            total_datasets = len(self.gridded_datasets)
            current_dataset = 0
            
            # Analyze each dataset
            results = {}
            for dataset_name, data in self.gridded_datasets.items():
                # Update progress before starting analysis
                progress = 20 + ((current_dataset / total_datasets) * 80)
                self._update_progress(int(progress))
                
                # Analyze dataset
                summary = self.analyze_dataset(dataset_name, data)
                results[dataset_name] = summary
                
                # Update progress after analysis
                current_dataset += 1
                progress = 20 + ((current_dataset / total_datasets) * 80)
                self._update_progress(int(progress))
                
            self._update_status("Analysis complete!")
            self._update_progress(100)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            self._update_status(f"Error during analysis: {str(e)}")
            raise