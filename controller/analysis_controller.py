#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading
from pathlib import Path
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from config import AnalysisConfig

from src.analysis.statistical_analyzer import GriddedDataAnalyzer

logger = logging.getLogger(__name__)

class AnalysisController(QObject):
    """
    Controller for handling analysis operations.
    Manages the interaction between the UI and the analysis components.
    """
    
    # Define signals
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal()
    dataset_analyzed = pyqtSignal(str, dict)
    
    def __init__(self, analysis_config: AnalysisConfig = None):
        super().__init__()
        
        # Use default config if none provided
        self.config = analysis_config or AnalysisConfig()
        
        # Thread for background processing
        self.analysis_thread = None
        
        # Analysis settings
        self.settings = {
            'type': 'Standard Analysis',
            'include_seasonal': True,
            'include_extreme': True
        }
        
        logger.info("AnalysisController initialized")
    
    def run_analysis(self, data_dir, results_dir, analysis_config: AnalysisConfig = None):
        """
        Start the analysis process in a background thread
        
        Args:
            data_dir (str): Directory containing the data
            results_dir (str): Directory to store results
            analysis_config (AnalysisConfig, optional): Analysis configuration
        """
        if self.analysis_thread and self.analysis_thread.is_alive():
            logger.warning("Analysis already in progress")
            self.status_updated.emit("Analysis already in progress")
            return
            
        # Use default config if none provided
        if analysis_config is None:
            analysis_config = self.config
            
        # Start a new thread for analysis
        self.analysis_thread = threading.Thread(
            target=self._analysis_thread,
            args=(data_dir, results_dir, analysis_config),
            daemon=True
        )
        self.analysis_thread.start()
        
        logger.info(f"Started analysis thread with settings: {self.settings}")
    
    def _analysis_thread(self, data_dir, results_dir, analysis_config: AnalysisConfig = None):
        """
        Thread function for running analysis
        
        Args:
            data_dir (str): Directory containing the data
            results_dir (str): Directory to store results
            analysis_config (AnalysisConfig, optional): Analysis configuration
        """
        try:
            self.status_updated.emit("Initializing analysis...")
            
            # Create analyzer
            analyzer = GriddedDataAnalyzer(data_dir=data_dir, results_dir=results_dir)
            
            # Pass the analysis config to analyzer
            analyzer.set_analysis_config(analysis_config)
            
            # Set up progress tracking
            original_analyze_dataset = analyzer.analyze_dataset
            
            def analyze_dataset_wrapper(dataset_name, gridded_data):
                """Wrapper for analyze_dataset to track progress"""
                self.status_updated.emit(f"Analyzing {dataset_name} dataset...")
                result = original_analyze_dataset(dataset_name, gridded_data)
                
                # Read summary file for the dataset
                output_dir = Path(results_dir) / dataset_name
                summary_file = output_dir / 'analysis_summary.csv'
                
                summary = {}
                if summary_file.exists():
                    try:
                        summary = pd.read_csv(summary_file).iloc[0].to_dict()
                    except Exception as e:
                        logger.error(f"Error reading summary file: {str(e)}", exc_info=True)
                
                # Emit progress update
                self.dataset_analyzed.emit(dataset_name, summary)
                
                return result
                
            # Replace method with our wrapper
            analyzer.analyze_dataset = analyze_dataset_wrapper
            
            # Set up progress tracking for run_analysis
            original_run_analysis = analyzer.run_analysis
            
            def run_analysis_wrapper():
                """Wrapper for run_analysis to track progress"""
                self.status_updated.emit("Loading data...")
                
                # Run original load_data to assess number of datasets
                analyzer.load_data()
                
                # Get total number of datasets
                num_datasets = len(analyzer.gridded_datasets)
                if num_datasets == 0:
                    self.error_occurred.emit("Analysis Error", "No gridded datasets found")
                    return
                
                # Initialize progress
                self.progress_updated.emit(10)  # 10% for loading
                
                # Track dataset progress
                processed_datasets = 0
                
                # Replace analyze_dataset again to track progress
                original_analyze_dataset_wrapped = analyzer.analyze_dataset
                
                def analyze_dataset_progress_wrapper(dataset_name, gridded_data):
                    """Wrapper to track dataset progress"""
                    nonlocal processed_datasets
                    
                    # Call the existing wrapper
                    result = original_analyze_dataset_wrapped(dataset_name, gridded_data)
                    
                    # Update progress
                    processed_datasets += 1
                    progress = 10 + (processed_datasets / num_datasets * 90)
                    self.progress_updated.emit(int(progress))
                    
                    return result
                
                # Replace method again
                analyzer.analyze_dataset = analyze_dataset_progress_wrapper
                
                # Now call the original method to run the analysis
                original_run_analysis()
                
                # Signal completion
                self.progress_updated.emit(100)
                self.status_updated.emit("Analysis completed!")
                self.analysis_completed.emit()
            
            # Replace method with our wrapper
            analyzer.run_analysis = run_analysis_wrapper
            
            # Run the analysis
            analyzer.run_analysis()

            print(f"AnalysisController values: lower={analysis_config.lower_percentile}, upper={analysis_config.upper_percentile}")
            
        except Exception as e:
            logger.error(f"Error running analysis: {str(e)}", exc_info=True)
            self.error_occurred.emit("Analysis Error", str(e))
            self.progress_updated.emit(0)
    
    def reset(self):
        """Reset the controller state"""
        # Cancel any running threads
        self.analysis_thread = None
        
        # Reset settings to defaults
        self.settings = {
            'type': 'Standard Analysis',
            'include_seasonal': True,
            'include_extreme': True
        }
        
        logger.info("AnalysisController reset")