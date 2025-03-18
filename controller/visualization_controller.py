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
                                
                                fig_box = create_boxplots(
                                    stats_df,
                                    parameters,
                                    'station',
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