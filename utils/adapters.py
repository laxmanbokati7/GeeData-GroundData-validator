#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Callable, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import os
import threading
import time

logger = logging.getLogger(__name__)

class ProgressAdapter:
    """
    Adapter class to convert various progress reporting mechanisms
    to a standardized callback approach for the GUI.
    """
    
    def __init__(self, callback: Callable[[str, int], None], dataset_name: str):
        """
        Initialize the progress adapter
        
        Args:
            callback: Function that takes dataset_name and progress percentage
            dataset_name: Name of the dataset being processed
        """
        self.callback = callback
        self.dataset_name = dataset_name
        self.last_progress = 0
        self.last_update_time = time.time()
        self.update_interval = 0.1  # seconds
        
    def update(self, progress: int):
        """Update progress"""
        if progress != self.last_progress:
            current_time = time.time()
            if (current_time - self.last_update_time) >= self.update_interval:
                self.callback(self.dataset_name, progress)
                self.last_progress = progress
                self.last_update_time = current_time

class TqdmToQtAdapter:
    """
    Adapter to convert tqdm progress to Qt progress signals.
    
    This allows existing code using tqdm to report progress to the GUI.
    """
    
    def __init__(self, callback: Callable[[str, int], None], dataset_name: str, total: int):
        """
        Initialize the adapter
        
        Args:
            callback: Function that takes dataset_name and progress percentage
            dataset_name: Name of the dataset being processed
            total: Total number of items for 100% progress
        """
        self.callback = callback
        self.dataset_name = dataset_name
        self.total = total
        self.progress_adapter = ProgressAdapter(callback, dataset_name)
        self.n = 0
        
    def update(self, n: int = 1):
        """Update progress by n items"""
        self.n += n
        progress = min(100, int(self.n / self.total * 100))
        self.progress_adapter.update(progress)
        
    def close(self):
        """Close the progress bar"""
        self.progress_adapter.update(100)
        
class AsyncTask:
    """
    Helper class to run tasks asynchronously with progress reporting.
    """
    
    def __init__(self, 
                task_func: Callable, 
                callback: Callable[[Dict[str, Any]], None] = None,
                error_callback: Callable[[Exception], None] = None,
                progress_callback: Callable[[str, int], None] = None):
        """
        Initialize the async task
        
        Args:
            task_func: Function to run asynchronously
            callback: Function to call when task completes successfully
            error_callback: Function to call when task fails
            progress_callback: Function to call to report progress
        """
        self.task_func = task_func
        self.callback = callback
        self.error_callback = error_callback
        self.progress_callback = progress_callback
        self.thread = None
        
    def start(self, *args, **kwargs):
        """Start the async task"""
        if self.thread and self.thread.is_alive():
            logger.warning("Task already running")
            return
            
        self.thread = threading.Thread(
            target=self._run_task,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        self.thread.start()
        
    def _run_task(self, *args, **kwargs):
        """Run the task and handle callbacks"""
        try:
            result = self.task_func(*args, **kwargs)
            
            # Call completion callback if provided
            if self.callback:
                self.callback(result)
                
        except Exception as e:
            logger.error(f"Error in async task: {str(e)}", exc_info=True)
            
            # Call error callback if provided
            if self.error_callback:
                self.error_callback(e)
                
class FileSystemAdapter:
    """
    Adapter to ensure consistent file system access across the application.
    """
    
    @staticmethod
    def ensure_directory(directory: str) -> Path:
        """Ensure a directory exists and return the Path object"""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
        
    @staticmethod
    def get_data_path(base_dir: str, filename: str) -> Path:
        """Get path for a data file"""
        return Path(base_dir) / "Data" / filename
        
    @staticmethod
    def get_results_path(base_dir: str, dataset: str, filename: str) -> Path:
        """Get path for a results file"""
        return Path(base_dir) / "Results" / dataset / filename
        
    @staticmethod
    def get_plots_path(base_dir: str, dataset: str, filename: str) -> Path:
        """Get path for a plot file"""
        return Path(base_dir) / "Plots" / dataset / filename
        
    @staticmethod
    def list_datasets(directory: str) -> list:
        """List all dataset directories in the given directory"""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return []
            
        return [d.name for d in dir_path.glob('*') if d.is_dir()]
        
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> list:
        """List all files matching the pattern in the directory"""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return []
            
        return [f.name for f in dir_path.glob(pattern) if f.is_file()]