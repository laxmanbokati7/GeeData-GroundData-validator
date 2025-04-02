#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading
from pathlib import Path
import matplotlib.pyplot as plt
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.visualization.plot_results import ResultPlotter

logger = logging.getLogger(__name__)

class VisualizationController(QObject):
    """
    Controller for handling visualization operations.
    Manages the interaction between the UI and the visualization components.
    """
    
    # Define signals
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)
    progress_updated = pyqtSignal(int)
    visualization_created = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Thread for background processing
        self.vis_thread = None
        
        # Visualization settings
        self.settings = {
            'dataset': 'ERA5',
            'type': 'Spatial Distribution',
            'high_res': True
        }
        
        logger.info("VisualizationController initialized")
    
    def generate_visualizations(self, data_dir, results_dir, plots_dir):
        """
        Start the visualization generation process in a background thread
        
        Args:
            data_dir (str): Directory containing the data
            results_dir (str): Directory containing analysis results
            plots_dir (str): Directory to store visualizations
        """
        if self.vis_thread and self.vis_thread.is_alive():
            logger.warning("Visualization generation already in progress")
            self.status_updated.emit("Visualization generation already in progress")
            return
            
        # Start a new thread for visualization
        self.vis_thread = threading.Thread(
            target=self._visualization_thread,
            args=(data_dir, results_dir, plots_dir),
            daemon=True
        )
        self.vis_thread.start()
        
        logger.info(f"Started visualization thread with settings: {self.settings}")
    
    def _visualization_thread(self, data_dir, results_dir, plots_dir):
        """
        Thread function for generating visualizations
        
        Args:
            data_dir (str): Directory containing the data
            results_dir (str): Directory containing analysis results
            plots_dir (str): Directory to store visualizations
        """
        try:
            self.status_updated.emit("Initializing visualization generation...")
            
            # Set higher DPI for high resolution plots
            if self.settings.get('high_res', True):
                plt.rcParams['figure.dpi'] = 300
            else:
                plt.rcParams['figure.dpi'] = 100
            
            # Create plotter
            plotter = ResultPlotter(data_dir=data_dir, results_dir=results_dir)
            plotter.plots_dir = Path(plots_dir)
            
            # Set up progress tracking and customization
            selected_dataset = self.settings.get('dataset')
            vis_type = self.settings.get('type')
            
            # Initialize progress
            self.progress_updated.emit(10)
            
            # Set up and load metadata
            self.status_updated.emit("Loading metadata...")
            plotter.setup()
            self.progress_updated.emit(20)
            
            # Process only the selected dataset if specified
            dataset_dirs = []
            results_path = Path(results_dir)
            
            if selected_dataset and selected_dataset != "All":
                # Check if the dataset exists
                dataset_dir = results_path / selected_dataset
                if dataset_dir.exists() and dataset_dir.is_dir():
                    dataset_dirs.append(dataset_dir)
                    self.status_updated.emit(f"Processing {selected_dataset} dataset...")
                else:
                    self.status_updated.emit(f"Dataset {selected_dataset} not found")
                    self.error_occurred.emit("Visualization Error", f"Dataset {selected_dataset} not found")
                    self.progress_updated.emit(0)
                    return
            else:
                # Process all datasets
                for dataset_dir in results_path.glob('*'):
                    if dataset_dir.is_dir():
                        dataset_dirs.append(dataset_dir)
                self.status_updated.emit(f"Processing all datasets...")
            
            # Custom methods to override default behavior based on settings
            original_process_dataset = plotter.process_dataset
            
            def custom_process_dataset(dataset_dir):
                """Custom dataset processing to focus on selected visualization type"""
                dataset_name = dataset_dir.name
                self.status_updated.emit(f"Generating visualizations for {dataset_name}...")
                
                # Create dataset plots directory
                dataset_plots_dir = plotter.plots_dir / dataset_name
                dataset_plots_dir.mkdir(exist_ok=True)
                
                # Process based on visualization type
                if vis_type == "Spatial Distribution":
                    # Only create spatial plots
                    for stats_file in dataset_dir.glob('*_stats.csv'):
                        if 'seasonal' not in stats_file.name:
                            stats_type = stats_file.stem.replace('_stats', '')
                            self.status_updated.emit(f"Creating spatial plots for {stats_type}...")
                            
                            try:
                                from utils.plotting_utils import (
                                    load_stats_file,
                                    create_spatial_figure,
                                    get_plot_parameters
                                )
                                
                                stats_df = load_stats_file(stats_file)
                                parameters = get_plot_parameters(stats_type)
                                
                                fig_spatial = create_spatial_figure(
                                    stats_df,
                                    plotter.metadata,
                                    parameters,
                                    f"{dataset_name} - {stats_type.title()} Statistics"
                                )
                                fig_spatial.savefig(
                                    dataset_plots_dir / f'{stats_type}_spatial.png',
                                    bbox_inches='tight',
                                    dpi=plt.rcParams['figure.dpi']
                                )
                                plt.close(fig_spatial)
                                
                                self.visualization_created.emit(
                                    f"Created spatial plot for {dataset_name} - {stats_type}"
                                )
                                
                            except Exception as e:
                                logger.error(f"Error creating spatial plot: {str(e)}", exc_info=True)
                                self.status_updated.emit(f"Error creating spatial plot: {str(e)}")
                
                elif vis_type == "Box Plots":
                    # Only create box plots
                    for stats_file in dataset_dir.glob('*_stats.csv'):
                        if 'seasonal' not in stats_file.name:
                            stats_type = stats_file.stem.replace('_stats', '')
                            self.status_updated.emit(f"Creating box plots for {stats_type}...")
                            
                            try:
                                from utils.plotting_utils import (
                                    load_stats_file,
                                    create_boxplots,
                                    get_plot_parameters
                                )
                                
                                stats_df = load_stats_file(stats_file)
                                parameters = get_plot_parameters(stats_type)
                                
                                # Call create_boxplots with group_by=None for the grid layout of single boxplots
                                fig_box = create_boxplots(
                                    stats_df,
                                    parameters,
                                    None,  # No grouping by station
                                    f"{dataset_name} - {stats_type.title()} Statistics Distribution"
                                )
                                fig_box.savefig(
                                    dataset_plots_dir / f'{stats_type}_boxplot.png',
                                    bbox_inches='tight',
                                    dpi=plt.rcParams['figure.dpi']
                                )
                                plt.close(fig_box)
                                
                                self.visualization_created.emit(
                                    f"Created box plot for {dataset_name} - {stats_type}"
                                )
                                
                            except Exception as e:
                                logger.error(f"Error creating box plot: {str(e)}", exc_info=True)
                                self.status_updated.emit(f"Error creating box plot: {str(e)}")
                
                elif vis_type == "Time Series":
                    import pandas as pd
                    # Create time series plots
                    self.status_updated.emit(f"Creating time series plots...")
                    
                    try:
                        from utils.plotting_utils import create_time_series_plots
                        
                        # First, we need the original data, not just statistics
                        # Load ground data
                        ground_data_path = Path(data_dir) / 'ground_daily_precipitation.csv'
                        if ground_data_path.exists():
                            ground_data = pd.read_csv(ground_data_path, index_col=0)
                            ground_data.index = pd.to_datetime(ground_data.index)
                            
                            # Load gridded data for this dataset
                            gridded_data_path = Path(data_dir) / f"{dataset_name.lower()}_precipitation.csv"
                            if gridded_data_path.exists():
                                gridded_data = pd.read_csv(gridded_data_path, index_col=0)
                                gridded_data.index = pd.to_datetime(gridded_data.index)
                                
                                # Create plots for different time aggregations
                                for agg_level in ['daily', 'monthly', 'yearly']:
                                    # Skip daily for FLDAS which is monthly data
                                    if dataset_name == "FLDAS" and agg_level == "daily":
                                        continue
                                        
                                    # Create time series plot
                                    fig_ts = create_time_series_plots(
                                        ground_data,
                                        gridded_data,
                                        aggregate=agg_level,
                                        title=f"{dataset_name} - {agg_level.title()} Time Series Comparison"
                                    )
                                    
                                    ts_file = dataset_plots_dir / f'timeseries_{agg_level}.png'
                                    fig_ts.savefig(
                                        ts_file,
                                        bbox_inches='tight',
                                        dpi=plt.rcParams['figure.dpi']
                                    )
                                    plt.close(fig_ts)
                                    
                                    self.visualization_created.emit(
                                        f"Created {agg_level} time series plot for {dataset_name}"
                                    )
                            else:
                                self.status_updated.emit(f"Gridded data file not found for {dataset_name}")
                        else:
                            self.status_updated.emit("Ground data file not found")
                            
                    except Exception as e:
                        logger.error(f"Error creating time series plots: {str(e)}", exc_info=True)
                        self.status_updated.emit(f"Error creating time series plots: {str(e)}")
                
                elif vis_type == "Dataset Comparison":
                    # Create dataset comparison visualizations
                    self.status_updated.emit(f"Creating dataset comparison visualizations...")
                    
                    # Create comparison plots directory
                    comparison_plots_dir = plotter.plots_dir / "Comparisons"
                    comparison_plots_dir.mkdir(exist_ok=True)
                    
                    try:
                        # Import the function
                        from utils.plotting_utils import create_multi_dataset_comparison
                        
                        # Get results directory (parent of the current dataset directory)
                        results_path = dataset_dir.parent
                        
                        # Create comparison boxplots for different metrics and time periods
                        metrics = ['rmse', 'r2', 'bias', 'mae']
                        periods = ['daily', 'monthly', 'yearly']
                        
                        for metric in metrics:
                            for period in periods:
                                # Skip daily for FLDAS which is monthly data
                                if dataset_name == "FLDAS" and period == "daily":
                                    continue
                                    
                                self.status_updated.emit(f"Creating {period} {metric} comparison...")
                                
                                fig = create_multi_dataset_comparison(
                                    results_path,
                                    comparison_plots_dir,
                                    metric=metric,
                                    stats_type=period,
                                    title="Gridded Dataset Comparison"
                                )
                                
                                # Save the plot
                                output_file = comparison_plots_dir / f'comparison_{period}_{metric}.png'
                                fig.savefig(
                                    output_file,
                                    bbox_inches='tight',
                                    dpi=plt.rcParams['figure.dpi']
                                )
                                plt.close(fig)
                                
                                self.visualization_created.emit(
                                    f"Created {period} {metric} dataset comparison"
                                )
                                
                    except Exception as e:
                        logger.error(f"Error creating dataset comparison: {str(e)}", exc_info=True)
                        self.status_updated.emit(f"Error creating dataset comparison: {str(e)}")

                elif vis_type == "Radar Comparison":
                    # Create radar chart comparison visualizations
                    self.status_updated.emit(f"Creating radar comparison visualizations...")
                    
                    # Create comparison plots directory
                    comparison_plots_dir = plotter.plots_dir / "Comparisons"
                    comparison_plots_dir.mkdir(exist_ok=True)
                    
                    try:
                        # Import the function
                        from utils.plotting_utils import create_radar_chart_comparison
                        
                        # Create radar charts for sum, mean, and max
                        value_types = ['sum', 'mean', 'max']
                        
                        for value_type in value_types:
                            self.status_updated.emit(f"Creating {value_type} radar comparison...")
                            
                            fig = create_radar_chart_comparison(
                                data_dir,
                                comparison_plots_dir,
                                value_type=value_type,
                                title="Multi-Dataset Time Series Comparison"
                            )
                            
                            # Save the plot
                            output_file = comparison_plots_dir / f'radar_{value_type}.png'
                            fig.savefig(
                                output_file,
                                bbox_inches='tight',
                                dpi=plt.rcParams['figure.dpi']
                            )
                            plt.close(fig)
                            
                            self.visualization_created.emit(
                                f"Created radar chart for {value_type} precipitation"
                            )
                            
                    except Exception as e:
                        logger.error(f"Error creating radar comparison: {str(e)}", exc_info=True)
                        self.status_updated.emit(f"Error creating radar comparison: {str(e)}")
                elif vis_type == "Seasonal Comparison":
                    # Only create seasonal plots
                    self.status_updated.emit(f"Creating seasonal plots...")
                    plotter.process_seasonal_stats(dataset_dir, dataset_plots_dir)
                    self.visualization_created.emit(f"Created seasonal plots for {dataset_name}")
                
                elif vis_type == "All Types":
                    # Use the original method
                    original_process_dataset(dataset_dir)
                    self.visualization_created.emit(f"Created all plots for {dataset_name}")
                
                else:
                    # Default to original method
                    original_process_dataset(dataset_dir)
                    self.visualization_created.emit(f"Created plots for {dataset_name}")
            
            # Override the method
            plotter.process_dataset = custom_process_dataset
            
            # Process datasets
            for i, dataset_dir in enumerate(dataset_dirs):
                plotter.process_dataset(dataset_dir)
                
                # Update progress (20-90%)
                progress = 20 + ((i + 1) / len(dataset_dirs) * 70)
                self.progress_updated.emit(int(progress))
            
            # Final steps
            self.progress_updated.emit(100)
            self.status_updated.emit("Visualization generation completed!")
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}", exc_info=True)
            self.error_occurred.emit("Visualization Error", str(e))
            self.progress_updated.emit(0)
    
    def reset(self):
        """Reset the controller state"""
        # Cancel any running threads
        self.vis_thread = None
        
        # Reset settings to defaults
        self.settings = {
            'dataset': 'ERA5',
            'type': 'Spatial Distribution',
            'high_res': True
        }
        
        logger.info("VisualizationController reset")