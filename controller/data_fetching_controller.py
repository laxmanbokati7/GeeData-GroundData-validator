#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.data.ground_fetcher import GroundDataFetcher
from src.data.gridded_fetcher import GriddedDataFetcher
from utils.utils import compare_datasets

logger = logging.getLogger(__name__)

class DataFetchingController(QObject):
    """
    Controller for handling data fetching operations.
    Manages the interaction between the UI and the data fetchers.
    """
    
    # Define signals
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)
    progress_updated = pyqtSignal(int)
    data_fetched = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Thread for background processing
        self.fetch_thread = None
        
        # Data storage
        self.ground_data = None
        self.gridded_data = {}
        
        logger.info("DataFetchingController initialized")
    
    def fetch_data(self, data_type, ground_config, gridded_config):
        """
        Start the data fetching process in a background thread
        
        Args:
            data_type (str): Type of data to fetch ('ground', 'gridded', or 'both')
            ground_config (GroundDataConfig): Configuration for ground data
            gridded_config (GriddedDataConfig): Configuration for gridded data
        """
        if self.fetch_thread and self.fetch_thread.is_alive():
            logger.warning("Data fetching already in progress")
            self.status_updated.emit("Data fetching already in progress")
            return
            
        # Start a new thread for fetching
        self.fetch_thread = threading.Thread(
            target=self._fetch_data_thread,
            args=(data_type, ground_config, gridded_config),
            daemon=True
        )
        self.fetch_thread.start()
        
        logger.info(f"Started data fetching thread for {data_type} data")
    
    def _fetch_data_thread(self, data_type, ground_config, gridded_config):
        """
        Thread function for fetching data
        
        Args:
            data_type (str): Type of data to fetch ('ground', 'gridded', or 'both')
            ground_config (GroundDataConfig): Configuration for ground data
            gridded_config (GriddedDataConfig): Configuration for gridded data
        """
        try:
            results = {}
            total_steps = self._get_total_steps(data_type, gridded_config)
            current_step = 0
            
            # Fetch ground data if requested
            if data_type in ['ground', 'both']:
                self.status_updated.emit("Fetching ground data...")
                logger.info("Fetching ground data")
                
                fetcher = GroundDataFetcher(ground_config)
                self.ground_data = fetcher.process()
                results['Ground'] = self.ground_data
                
                current_step += 1
                self.progress_updated.emit(int(current_step / total_steps * 100))
                
                logger.info("Ground data fetching completed")
                self.status_updated.emit("Ground data fetching completed")
            
            # Fetch gridded data if requested
            if data_type in ['gridded', 'both']:
                if gridded_config.is_valid():
                    self.status_updated.emit("Fetching gridded data...")
                    logger.info("Fetching gridded data")
                    
                    fetcher = GriddedDataFetcher(gridded_config)
                    
                    # Set up progress tracking
                    def progress_callback(dataset, progress):
                        nonlocal current_step
                        # Increment step for completed datasets
                        if progress == 100:
                            current_step += 1
                        # Calculate overall progress
                        dataset_progress = progress / 100
                        overall_progress = (current_step + dataset_progress) / total_steps
                        self.progress_updated.emit(int(overall_progress * 100))
                        
                        # Update status
                        self.status_updated.emit(f"Fetching {dataset} data: {progress}%")
                    
                    # Register callback
                    fetcher.set_progress_callback(progress_callback)
                    
                    # Process data
                    gridded_results = fetcher.process()
                    self.gridded_data = gridded_results
                    results.update(gridded_results)
                    
                    logger.info("Gridded data fetching completed")
                    self.status_updated.emit("Gridded data fetching completed")
                else:
                    logger.warning("No gridded datasets selected")
                    self.status_updated.emit("No gridded datasets selected")
            
            # Show results summary
            if results:
                self.status_updated.emit("Generating data summary...")
                comparison = compare_datasets(results)
                summary_text = f"Data Summary:\n{comparison.to_string(index=False)}"
                logger.info(f"Data fetching completed: {summary_text}")
                self.status_updated.emit(summary_text)
                
                # Signal completion
                self.progress_updated.emit(100)
                self.data_fetched.emit()
            else:
                logger.warning("No data was fetched")
                self.status_updated.emit("No data was fetched")
                self.progress_updated.emit(0)
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}", exc_info=True)
            self.error_occurred.emit("Data Fetching Error", str(e))
            self.progress_updated.emit(0)
    
    def _get_total_steps(self, data_type, gridded_config):
        """
        Calculate the total number of steps for progress tracking
        
        Args:
            data_type (str): Type of data to fetch
            gridded_config (GriddedDataConfig): Configuration for gridded data
            
        Returns:
            int: Total number of steps
        """
        total_steps = 0
        
        if data_type in ['ground', 'both']:
            total_steps += 1
            
        if data_type in ['gridded', 'both']:
            total_steps += len(gridded_config.get_enabled_datasets())
            
        return max(1, total_steps)  # Ensure at least 1 step
    
    def reset(self):
        """Reset the controller state"""
        # Cancel any running threads
        self.fetch_thread = None
        
        # Clear data
        self.ground_data = None
        self.gridded_data = {}
        
        logger.info("DataFetchingController reset")