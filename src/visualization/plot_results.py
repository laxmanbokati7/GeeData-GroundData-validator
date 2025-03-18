import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import logging
from typing import Callable, Optional, Dict, Any, List

from utils.plotting_utils import (
    load_metadata,
    load_stats_file,
    create_spatial_figure,
    create_boxplots,
    create_seasonal_comparison,
    get_plot_parameters
)

logger = logging.getLogger(__name__)

class ResultPlotter:
    """Class to generate plots for all results with progress reporting"""
    
    def __init__(self, data_dir: str = 'Data', results_dir: str = 'Results', plots_dir: str = 'Plots'):
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.plots_dir = Path(plots_dir)
        self.metadata = None
        self.progress_callback = None
        self.status_callback = None
        self.visualization_callback = None
        
    def set_progress_callback(self, callback: Callable[[int], None]) -> None:
        """Set callback for progress updates"""
        self.progress_callback = callback
        
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for status message updates"""
        self.status_callback = callback
        
    def set_visualization_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for visualization creation updates"""
        self.visualization_callback = callback
        
    def _update_progress(self, value: int) -> None:
        """Update progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(value)
            
    def _update_status(self, message: str) -> None:
        """Update status if callback is set"""
        if self.status_callback:
            self.status_callback(message)
        logger.info(message)
        
    def _notify_visualization(self, message: str) -> None:
        """Notify about visualization creation if callback is set"""
        if self.visualization_callback:
            self.visualization_callback(message)
        logger.info(message)
        
    def setup(self):
        """Setup necessary directories and load metadata"""
        self._update_status("Setting up visualization environment...")
        
        # Create plots directory if it doesn't exist
        self.plots_dir.mkdir(exist_ok=True)
        
        # Load metadata
        self._update_status("Loading station metadata...")
        self.metadata = load_metadata(self.data_dir)
        
        self._update_status("Metadata loaded successfully")
        self._update_progress(10)
        
    def process_regular_stats(self, dataset_dir: Path, dataset_plots_dir: Path, 
                             vis_type: Optional[str] = None) -> List[str]:
        """Process regular statistics files (daily, monthly, yearly)"""
        created_files = []
        
        for stats_file in dataset_dir.glob('*_stats.csv'):
            if 'seasonal' not in stats_file.name:
                stats_type = stats_file.stem.replace('_stats', '')
                
                # Skip if vis_type is specified and doesn't match
                if vis_type and not self._matches_vis_type(stats_type, vis_type):
                    continue
                
                self._update_status(f"Creating plots for {stats_type} statistics...")
                
                try:
                    # Load statistics
                    stats_df = load_stats_file(stats_file)
                    parameters = get_plot_parameters(stats_type)
                    
                    # Create spatial plots if requested
                    if not vis_type or vis_type in ['all', 'spatial']:
                        self._update_status(f"Creating spatial plots for {stats_type}...")
                        
                        fig_spatial = create_spatial_figure(
                            stats_df,
                            self.metadata,
                            parameters,
                            f"{dataset_dir.name} - {stats_type.title()} Statistics"
                        )
                        
                        spatial_file = dataset_plots_dir / f'{stats_type}_spatial.png'
                        fig_spatial.savefig(
                            spatial_file,
                            bbox_inches='tight',
                            dpi=300
                        )
                        plt.close(fig_spatial)
                        
                        created_files.append(str(spatial_file))
                        self._notify_visualization(f"Created spatial plot for {dataset_dir.name} - {stats_type}")
                    
                    # Create box plots if requested
                    if not vis_type or vis_type in ['all', 'boxplot']:
                        self._update_status(f"Creating box plots for {stats_type}...")
                        
                        fig_box = create_boxplots(
                            stats_df,
                            parameters,
                            'station',
                            f"{dataset_dir.name} - {stats_type.title()} Statistics Distribution"
                        )
                        
                        boxplot_file = dataset_plots_dir / f'{stats_type}_boxplot.png'
                        fig_box.savefig(
                            boxplot_file,
                            bbox_inches='tight',
                            dpi=300
                        )
                        plt.close(fig_box)
                        
                        created_files.append(str(boxplot_file))
                        self._notify_visualization(f"Created box plot for {dataset_dir.name} - {stats_type}")
                    
                except Exception as e:
                    logger.error(f"Error processing {stats_file}: {str(e)}", exc_info=True)
                    self._update_status(f"Error creating plots for {stats_type}: {str(e)}")
                    
        return created_files
    
    def process_seasonal_stats(self, dataset_dir: Path, dataset_plots_dir: Path) -> List[str]:
        """Process seasonal statistics"""
        created_files = []
        seasonal_file = dataset_dir / 'seasonal_stats.csv'
        
        if seasonal_file.exists():
            self._update_status("Creating seasonal plots...")
            
            try:
                # Load seasonal statistics
                stats_df = pd.read_csv(seasonal_file)
                parameters = get_plot_parameters('seasonal')
                
                # Create seasonal comparison plots
                fig_seasonal = create_seasonal_comparison(
                    stats_df,
                    parameters,
                    dataset_dir.name
                )
                
                seasonal_file = dataset_plots_dir / 'seasonal_comparison.png'
                fig_seasonal.savefig(
                    seasonal_file,
                    bbox_inches='tight',
                    dpi=300
                )
                plt.close(fig_seasonal)
                
                created_files.append(str(seasonal_file))
                self._notify_visualization(f"Created seasonal comparison plot for {dataset_dir.name}")
                
                # Create spatial plots for each season
                for season in ['Winter', 'Spring', 'Summer', 'Fall']:
                    season_stats = stats_df[stats_df['season'] == season]
                    if not season_stats.empty:
                        fig_spatial = create_spatial_figure(
                            season_stats,
                            self.metadata,
                            parameters,
                            f"{dataset_dir.name} - {season} Statistics"
                        )
                        
                        season_file = dataset_plots_dir / f'seasonal_{season.lower()}_spatial.png'
                        fig_spatial.savefig(
                            season_file,
                            bbox_inches='tight',
                            dpi=300
                        )
                        plt.close(fig_spatial)
                        
                        created_files.append(str(season_file))
                        self._notify_visualization(f"Created spatial plot for {dataset_dir.name} - {season}")
                
            except Exception as e:
                logger.error(f"Error processing seasonal stats: {str(e)}", exc_info=True)
                self._update_status(f"Error creating seasonal plots: {str(e)}")
                
        return created_files
    
    def _matches_vis_type(self, stats_type: str, vis_type: str) -> bool:
        """Check if stats type matches visualization type"""
        if vis_type == 'all':
            return True
            
        if vis_type == 'spatial':
            return True  # All stats types can create spatial plots
            
        if vis_type == 'boxplot':
            return True  # All stats types can create box plots
            
        if vis_type == 'seasonal':
            return 'seasonal' in stats_type
            
        return False
    
    def process_dataset(self, dataset_dir: Path, vis_type: Optional[str] = None) -> Dict[str, List[str]]:
        """Process all statistics files for a dataset"""
        dataset_name = dataset_dir.name
        self._update_status(f"Processing {dataset_name}...")
        
        result = {'regular': [], 'seasonal': []}
        
        # Create dataset plots directory
        dataset_plots_dir = self.plots_dir / dataset_name
        dataset_plots_dir.mkdir(exist_ok=True)
        
        # Process regular statistics if requested
        if not vis_type or vis_type in ['all', 'spatial', 'boxplot']:
            result['regular'] = self.process_regular_stats(dataset_dir, dataset_plots_dir, vis_type)
        
        # Process seasonal statistics if requested
        if not vis_type or vis_type in ['all', 'seasonal']:
            result['seasonal'] = self.process_seasonal_stats(dataset_dir, dataset_plots_dir)
            
        self._update_status(f"Created {len(result['regular']) + len(result['seasonal'])} plots for {dataset_name}")
        
        return result
    
    def run(self, dataset_filter: Optional[str] = None, vis_type: Optional[str] = None) -> Dict[str, Dict[str, List[str]]]:
        """
        Run plotting for all datasets
        
        Args:
            dataset_filter: Optional filter for specific dataset (ERA5, DAYMET, PRISM)
            vis_type: Optional filter for visualization type (spatial, boxplot, seasonal, all)
            
        Returns:
            Dictionary of created files by dataset
        """
        self._update_status("Starting plot generation...")
        self._update_progress(0)
        
        results = {}
        
        try:
            self.setup()
            
            # Get list of dataset directories to process
            dataset_dirs = []
            for dir_path in self.results_dir.glob('*'):
                if dir_path.is_dir():
                    if dataset_filter and dataset_filter.upper() != 'ALL' and dir_path.name.upper() != dataset_filter.upper():
                        continue
                    dataset_dirs.append(dir_path)
            
            # Process each dataset
            total_datasets = len(dataset_dirs)
            for i, dataset_dir in enumerate(dataset_dirs):
                # Calculate progress - 10% for setup, 90% for datasets
                progress = 10 + ((i / total_datasets) * 90)
                self._update_progress(int(progress))
                
                # Process dataset
                results[dataset_dir.name] = self.process_dataset(dataset_dir, vis_type)
                
                # Update progress after dataset
                progress = 10 + (((i + 1) / total_datasets) * 90)
                self._update_progress(int(progress))
            
            self._update_status("Plot generation complete!")
            self._update_progress(100)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during plot generation: {str(e)}", exc_info=True)
            self._update_status(f"Error during plot generation: {str(e)}")
            raise