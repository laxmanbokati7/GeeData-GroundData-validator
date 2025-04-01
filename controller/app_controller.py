#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
import pickle
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from config import GroundDataConfig, GriddedDataConfig
from controller.data_fetching_controller import DataFetchingController
from controller.analysis_controller import AnalysisController
from controller.visualization_controller import VisualizationController

logger = logging.getLogger(__name__)

class AppController(QObject):
    """
    Main application controller that coordinates the workflow and 
    connects UI components with the business logic.
    """
    
    # Define signals
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)
    data_downloaded = pyqtSignal()
    analysis_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Initialize child controllers
        self.data_controller = DataFetchingController()
        self.analysis_controller = AnalysisController()
        self.visualization_controller = VisualizationController()
        
        # Connect child controller signals
        self._connect_controller_signals()
        
        # Application state
        self.data_available = False
        self.analysis_complete = False
        
        # Initialize base directory for data storage
        self.base_dir = Path(os.getcwd())
        self.data_dir = self.base_dir / "Data"
        self.results_dir = self.base_dir / "Results"
        self.plots_dir = self.base_dir / "Plots"
        
        # Create directories if they don't exist
        self._create_directories()

        # Check if data already exists
        ground_path = self.data_dir / 'ground_daily_precipitation.csv'
        if ground_path.exists():
            self.data_available = True
            logger.info("Found existing data files")
        
        logger.info("AppController initialized")
    
    def _connect_controller_signals(self):
        """Connect signals from child controllers"""
        # Data controller signals
        self.data_controller.status_updated.connect(self.status_updated)
        self.data_controller.error_occurred.connect(self.error_occurred)
        self.data_controller.data_fetched.connect(self._on_data_fetched)
        
        # Analysis controller signals
        self.analysis_controller.status_updated.connect(self.status_updated)
        self.analysis_controller.error_occurred.connect(self.error_occurred)
        self.analysis_controller.analysis_completed.connect(self._on_analysis_completed)
        
        # Visualization controller signals
        self.visualization_controller.status_updated.connect(self.status_updated)
        self.visualization_controller.error_occurred.connect(self.error_occurred)
    
    def _create_directories(self):
        """Create necessary directories for data storage"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created directories: {self.data_dir}, {self.results_dir}, {self.plots_dir}")
    
    @pyqtSlot()
    def _on_data_fetched(self):
        """Handle data fetching completion"""
        self.data_available = True
        self.data_downloaded.emit()
        logger.info("Data fetching completed")
    
    @pyqtSlot()
    def _on_analysis_completed(self):
        """Handle analysis completion"""
        self.analysis_complete = True
        self.analysis_completed.emit()
        logger.info("Analysis completed")
    
    def fetch_data(self, data_config):
        """
        Start the data fetching process
        
        Args:
            data_config (dict): Configuration for data fetching
        """
        try:
            logger.info("Starting data fetching process")
            self.status_updated.emit("Starting data download...")
            
            # Create configurations
            selection_type = data_config.get('selection_type', 'states')
            
            ground_config = GroundDataConfig(
                states=data_config.get('states'),
                huc_id=data_config.get('huc_id') if selection_type == 'huc' else None,
                start_year=data_config.get('start_year', 1980),
                end_year=data_config.get('end_year', 2024),
                data_dir=str(self.data_dir)
            )
            
            gridded_config = GriddedDataConfig(
                start_year=data_config.get('start_year', 1980),
                end_year=data_config.get('end_year', 2024),
                data_dir=str(self.data_dir),
                ee_project_id=data_config.get('ee_project_id', "ee-sauravbhattarai1999")
            )
            
            # Configure gridded datasets
            for name, dataset in gridded_config.datasets.items():
                dataset.enabled = name in data_config.get('gridded_datasets', [])
            
            # Start data fetching
            self.data_controller.fetch_data(
                data_config.get('data_type', 'both'),
                ground_config,
                gridded_config
            )
            
        except Exception as e:
            logger.error(f"Error in fetch_data: {str(e)}", exc_info=True)
            self.error_occurred.emit("Data Fetching Error", str(e))
    
    def run_analysis(self):
        """Start the data analysis process"""
        try:
            if not self.data_available:
                raise ValueError("No data available for analysis")
            
            logger.info("Starting data analysis process")
            self.status_updated.emit("Starting data analysis...")
            
            self.analysis_controller.run_analysis(
                str(self.data_dir),
                str(self.results_dir)
            )
            
        except Exception as e:
            logger.error(f"Error in run_analysis: {str(e)}", exc_info=True)
            self.error_occurred.emit("Analysis Error", str(e))
    
    def generate_visualizations(self):
        """Start the visualization generation process"""
        try:
            if not self.analysis_complete:
                raise ValueError("No analysis results available for visualization")
            
            logger.info("Starting visualization generation process")
            self.status_updated.emit("Generating visualizations...")
            
            self.visualization_controller.generate_visualizations(
                str(self.data_dir),
                str(self.results_dir),
                str(self.plots_dir)
            )
            
        except Exception as e:
            logger.error(f"Error in generate_visualizations: {str(e)}", exc_info=True)
            self.error_occurred.emit("Visualization Error", str(e))
    
    def reset(self):
        """Reset the application state"""
        self.data_available = False
        self.analysis_complete = False
        
        # Reset controllers
        self.data_controller.reset()
        self.analysis_controller.reset()
        self.visualization_controller.reset()
        
        logger.info("Application state reset")
        self.status_updated.emit("Application reset")
    
    def save_project(self, file_path):
        """
        Save the current project state to a file
        
        Args:
            file_path (str): Path to the project file
        """
        try:
            project_data = {
                'data_available': self.data_available,
                'analysis_complete': self.analysis_complete,
                # Add more state information as needed
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(project_data, f)
                
            logger.info(f"Project saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving project: {str(e)}", exc_info=True)
            raise
    
    def load_project(self, file_path):
        """
        Load a project from a file
        
        Args:
            file_path (str): Path to the project file
        """
        try:
            with open(file_path, 'rb') as f:
                project_data = pickle.load(f)
            
            self.data_available = project_data.get('data_available', False)
            self.analysis_complete = project_data.get('analysis_complete', False)
            # Load more state information as needed
            
            logger.info(f"Project loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading project: {str(e)}", exc_info=True)
            raise
    
    def is_data_available(self):
        """Check if data is available for analysis"""
        return self.data_available
    
    def is_analysis_complete(self):
        """Check if analysis is complete"""
        return self.analysis_complete