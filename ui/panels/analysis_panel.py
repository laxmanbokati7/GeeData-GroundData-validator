#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QProgressBar, QTableWidget, QTableWidgetItem, QTabWidget,
                            QGroupBox, QComboBox, QSplitter, QPlainTextEdit,
                            QHeaderView, QCheckBox, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor

logger = logging.getLogger(__name__)

class AnalysisPanel(QWidget):
    """
    Panel for analyzing climate data.
    Replicates the functionality of the analysis part of main.ipynb.
    """
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        # Initialize UI
        self.init_ui()
        
        # Connect controller signals
        self.controller.analysis_controller.progress_updated.connect(self.update_progress)
        self.controller.analysis_controller.dataset_analyzed.connect(self.on_dataset_analyzed)
        self.controller.status_updated.connect(self.append_status)
        self.controller.data_downloaded.connect(self.check_data_availability)
        
        # Check data availability
        self.check_data_availability()
        
        logger.info("Analysis Panel initialized")
    
    def init_ui(self):
        """Initialize the UI components - FIXED VERSION"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title_label = QLabel("Data Analysis")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Add instructions
        self.instruction_label = QLabel(
            "This panel allows you to analyze the downloaded climate data. "
            "Select your analysis options and click 'Run Analysis' to start the process."
        )
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
        main_layout.addWidget(self.instruction_label)
        
        # Data availability message
        self.data_status_label = QLabel("")
        self.data_status_label.setWordWrap(True)
        self.data_status_label.setStyleSheet("font-size: 12px; color: #FF5733; margin-bottom: 10px;")
        main_layout.addWidget(self.data_status_label)
        
        # FIXED: Instead of using a splitter, use separate widgets with fixed layouts
        
        # Analysis settings section (TOP PANEL)
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Analysis type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Analysis Type:")
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            "Standard Analysis",
            "Custom Analysis"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.analysis_type_combo)
        type_layout.addStretch()
        settings_layout.addLayout(type_layout)
        
        # Optional settings
        options_layout = QHBoxLayout()
        self.include_seasonal = QCheckBox("Include Seasonal Analysis")
        self.include_seasonal.setChecked(True)
        self.include_extreme = QCheckBox("Include Extreme Value Analysis")
        self.include_extreme.setChecked(True)
        options_layout.addWidget(self.include_seasonal)
        options_layout.addWidget(self.include_extreme)
        options_layout.addStretch()
        settings_layout.addLayout(options_layout)
        
        # Run button
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setMinimumHeight(40)
        settings_layout.addWidget(self.run_button)
        
        # Progress section
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_text = QPlainTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Status updates will appear here during analysis...")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_text)
        
        # FIXED: Add settings and progress groups to main layout directly
        main_layout.addWidget(settings_group)
        main_layout.addWidget(progress_group)
        
        # Results section (BOTTOM PANEL)
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        
        # Summary tab
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        summary_label = QLabel("Summary of analysis results across all datasets:")
        summary_layout.addWidget(summary_label)
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels([
            "Dataset", "Stations", "Start Date", "End Date", "Analysis Date"
        ])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        summary_layout.addWidget(self.summary_table)
        
        self.results_tabs.addTab(summary_widget, "Summary")
        
        # ERA5 tab
        era5_widget = QWidget()
        era5_layout = QVBoxLayout(era5_widget)
        
        era5_label = QLabel("Statistical comparison between ground stations and ERA5 dataset:")
        era5_layout.addWidget(era5_label)
        
        self.era5_table = QTableWidget()
        self.setup_stats_table(self.era5_table)
        
        era5_layout.addWidget(self.era5_table)
        
        self.results_tabs.addTab(era5_widget, "ERA5")
        
        # DAYMET tab
        daymet_widget = QWidget()
        daymet_layout = QVBoxLayout(daymet_widget)
        
        daymet_label = QLabel("Statistical comparison between ground stations and DAYMET dataset:")
        daymet_layout.addWidget(daymet_label)
        
        self.daymet_table = QTableWidget()
        self.setup_stats_table(self.daymet_table)
        
        daymet_layout.addWidget(self.daymet_table)
        
        self.results_tabs.addTab(daymet_widget, "DAYMET")
        
        # PRISM tab
        prism_widget = QWidget()
        prism_layout = QVBoxLayout(prism_widget)
        
        prism_label = QLabel("Statistical comparison between ground stations and PRISM dataset:")
        prism_layout.addWidget(prism_label)
        
        self.prism_table = QTableWidget()
        self.setup_stats_table(self.prism_table)
        
        prism_layout.addWidget(self.prism_table)
        
        self.results_tabs.addTab(prism_widget, "PRISM")

        # Add tabs for new datasets
        chirps_widget = QWidget()
        chirps_layout = QVBoxLayout(chirps_widget)
        chirps_label = QLabel("Statistical comparison between ground stations and CHIRPS dataset:")
        chirps_layout.addWidget(chirps_label)
        self.chirps_table = QTableWidget()
        self.setup_stats_table(self.chirps_table)
        chirps_layout.addWidget(self.chirps_table)
        self.results_tabs.addTab(chirps_widget, "CHIRPS")
        
        fldas_widget = QWidget()
        fldas_layout = QVBoxLayout(fldas_widget)
        fldas_label = QLabel("Statistical comparison between ground stations and FLDAS dataset:")
        fldas_layout.addWidget(fldas_label)
        self.fldas_table = QTableWidget()
        self.setup_stats_table(self.fldas_table)
        fldas_layout.addWidget(self.fldas_table)
        self.results_tabs.addTab(fldas_widget, "FLDAS")
        
        gsmap_widget = QWidget()
        gsmap_layout = QVBoxLayout(gsmap_widget)
        gsmap_label = QLabel("Statistical comparison between ground stations and GSMAP dataset:")
        gsmap_layout.addWidget(gsmap_label)
        self.gsmap_table = QTableWidget()
        self.setup_stats_table(self.gsmap_table)
        gsmap_layout.addWidget(self.gsmap_table)
        self.results_tabs.addTab(gsmap_widget, "GSMAP")
        
        gldas_widget = QWidget()
        gldas_layout = QVBoxLayout(gldas_widget)
        gldas_label = QLabel("Statistical comparison between ground stations and GLDAS dataset:")
        gldas_layout.addWidget(gldas_label)
        self.gldas_table = QTableWidget()
        self.setup_stats_table(self.gldas_table)
        gldas_layout.addWidget(self.gldas_table)
        self.results_tabs.addTab(gldas_widget, "GLDAS")

        
        # Add results tabs to layout
        results_layout.addWidget(self.results_tabs)
        
        # FIXED: Add results group to main layout directly
        main_layout.addWidget(results_group)
        
        # Set stretch factors to ensure proper sizing
        main_layout.setStretch(2, 1)  # Give results section more space
        
        # Connect signals
        self.run_button.clicked.connect(self.on_run_analysis)
        
        # Add help button at the bottom
        help_button = QPushButton("Help & Guidance")
        help_button.clicked.connect(self.show_help)
        main_layout.addWidget(help_button)
        
    def setup_stats_table(self, table):
        """Set up a statistics table with common columns"""
        table.setColumnCount(8)  # Increased to 8 columns
        table.setHorizontalHeaderLabels([
            "Metric", "Daily", "Monthly", "Yearly", "Winter", "Spring", "Summer", "Fall"
        ])
        table.setRowCount(6)
        
        # Add row headers
        metrics = ["R²", "RMSE", "Bias", "MAE", "NSE", "PBIAS"]
        for i, metric in enumerate(metrics):
            item = QTableWidgetItem(metric)
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            item.setFlags(Qt.ItemIsEnabled)  # Make non-editable
            table.setItem(i, 0, item)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def check_data_availability(self):
        """Check if data is available for analysis and update UI accordingly"""
        data_available = self.controller.is_data_available()
        
        if not data_available:
            self.data_status_label.setText(
                "⚠️ No data is currently available for analysis. Please download data in the Data Selection tab first."
            )
            self.run_button.setEnabled(False)
        else:
            self.data_status_label.setText(
                "✅ Data is available for analysis. Configure your settings and click 'Run Analysis'."
            )
            # Ensure button is definitely enabled
            self.run_button.setEnabled(True)
    
    def load_existing_results(self):
        """Load existing analysis results if available"""
        self.append_status("Loading existing analysis results...")
        
        try:
            # Check if results directory exists and has dataset folders
            results_dir = Path(self.controller.results_dir)
            if not results_dir.exists():
                return
                
            # Check for each dataset results
            for dataset_name in ['ERA5', 'DAYMET', 'PRISM']:
                dataset_dir = results_dir / dataset_name
                if dataset_dir.exists() and dataset_dir.is_dir():
                    # Check for summary file
                    summary_file = dataset_dir / 'analysis_summary.csv'
                    if summary_file.exists():
                        # Load summary
                        summary_df = pd.read_csv(summary_file)
                        if not summary_df.empty:
                            summary = summary_df.iloc[0].to_dict()
                            
                            # Add to summary table
                            self.on_dataset_analyzed(dataset_name, summary)
                            
                            # Update dataset-specific table
                            self.update_stats_table(
                                getattr(self, f"{dataset_name.lower()}_table"), 
                                dataset_name
                            )
                            
                            self.append_status(f"Loaded results for {dataset_name}")
            
            self.append_status("Existing analysis results loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading existing results: {str(e)}", exc_info=True)
            self.append_status(f"Error loading existing results: {str(e)}")
            
    @pyqtSlot()
    def on_run_analysis(self):
        """Handle run analysis button click"""
        try:
            # Check data availability
            if not self.controller.is_data_available():
                QMessageBox.warning(
                    self, 
                    "No Data Available", 
                    "No data is available for analysis. Please download data in the Data Selection tab first."
                )
                return
                
            # Confirm analysis
            reply = QMessageBox.question(
                self,
                "Run Analysis",
                "This will analyze the downloaded data and may take some time. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.No:
                return
                
            # Disable run button
            self.run_button.setEnabled(False)
            self.run_button.setText("Running Analysis...")
            
            # Reset progress bar and status text
            self.progress_bar.setValue(0)
            self.status_text.clear()
            self.status_text.appendPlainText("Starting analysis...")
            
            # Get analysis settings
            settings = {
                'type': self.analysis_type_combo.currentText(),
                'include_seasonal': self.include_seasonal.isChecked(),
                'include_extreme': self.include_extreme.isChecked()
            }
            
            logger.info(f"Starting analysis with settings: {settings}")
            
            # Run analysis
            self.controller.analysis_controller.settings = settings
            self.controller.run_analysis()
            
        except Exception as e:
            logger.error(f"Error running analysis: {str(e)}", exc_info=True)
            self.controller.error_occurred.emit("Analysis Error", str(e))
            
            # Re-enable run button
            self.run_button.setEnabled(True)
            self.run_button.setText("Run Analysis")
    
    @pyqtSlot(int)
    def update_progress(self, value):
        """Update the progress bar value"""
        self.progress_bar.setValue(value)
        
        # Re-enable run button when complete
        if value >= 100:
            self.run_button.setEnabled(True)
            self.run_button.setText("Run Analysis")
    
    @pyqtSlot(str)
    def append_status(self, text):
        """Append text to the status text area"""
        self.status_text.appendPlainText(text)
        # Auto-scroll to bottom
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    @pyqtSlot(str, dict)
    def on_dataset_analyzed(self, dataset_name, summary):
        """Update UI with dataset analysis results"""
        # Update summary table
        row_position = self.summary_table.rowCount()
        
        # Check if dataset already exists in summary table
        existing_row = -1
        for row in range(self.summary_table.rowCount()):
            if self.summary_table.item(row, 0) and self.summary_table.item(row, 0).text() == dataset_name:
                existing_row = row
                break
                
        if existing_row >= 0:
            # Update existing row
            row_position = existing_row
        else:
            # Add new row
            self.summary_table.insertRow(row_position)
        
        # Update or insert data
        self.summary_table.setItem(row_position, 0, QTableWidgetItem(dataset_name))
        self.summary_table.setItem(row_position, 1, QTableWidgetItem(str(summary.get('n_stations', 'N/A'))))
        
        # Format dates if needed
        start_date = summary.get('start_date', 'N/A')
        if isinstance(start_date, pd.Timestamp):
            start_date = start_date.strftime('%Y-%m-%d')
            
        end_date = summary.get('end_date', 'N/A')
        if isinstance(end_date, pd.Timestamp):
            end_date = end_date.strftime('%Y-%m-%d')
            
        self.summary_table.setItem(row_position, 2, QTableWidgetItem(str(start_date)))
        self.summary_table.setItem(row_position, 3, QTableWidgetItem(str(end_date)))
        self.summary_table.setItem(row_position, 4, QTableWidgetItem(pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')))
        
        # Update dataset-specific table
        self.append_status(f"Processed {dataset_name} dataset.")
        
        # Load dataset stats
        try:
            if dataset_name == "ERA5":
                self.update_stats_table(self.era5_table, dataset_name)
            elif dataset_name == "DAYMET":
                self.update_stats_table(self.daymet_table, dataset_name)
            elif dataset_name == "PRISM":
                self.update_stats_table(self.prism_table, dataset_name)
            elif dataset_name == "CHIRPS":
                self.update_stats_table(self.chirps_table, dataset_name)
            elif dataset_name == "FLDAS":
                # Create a warning label if it doesn't exist
                if not hasattr(self, 'fldas_warning_label'):
                    self.fldas_warning_label = QLabel()
                    self.fldas_warning_label.setStyleSheet(
                        "background-color: #FFF3CD; color: #856404; padding: 10px; border-radius: 4px;"
                    )
                    self.fldas_warning_label.setWordWrap(True)
                    
                    # Add to layout in the FLDAS tab
                    fldas_tab_idx = self.results_tabs.indexOf(self.results_tabs.findChild(QWidget, "FLDAS"))
                    if fldas_tab_idx >= 0:
                        fldas_widget = self.results_tabs.widget(fldas_tab_idx)
                        fldas_layout = fldas_widget.layout()
                        fldas_layout.insertWidget(0, self.fldas_warning_label)
                
                # Update the warning text
                self.fldas_warning_label.setText(
                    "⚠️ TEMPORAL RESOLUTION NOTICE: FLDAS provides data at a monthly resolution. "
                    "For this analysis, daily ground station data has been aggregated to monthly "
                    "values. Daily and sub-monthly statistics are not available for FLDAS."
                )
                self.update_stats_table(self.fldas_table, dataset_name)
            elif dataset_name == "GSMAP":
                self.update_stats_table(self.gsmap_table, dataset_name)
            elif dataset_name in ["GLDAS-Historical", "GLDAS-Current", "GLDAS-Combined"]:
                self.update_stats_table(self.gldas_table, dataset_name)
        except Exception as e:
            logger.error(f"Error updating stats table: {str(e)}", exc_info=True)
            self.append_status(f"Error updating {dataset_name} statistics: {str(e)}")
    
    def update_stats_table(self, table, dataset_name):
        """Update a statistics table with data from results directory"""
        results_dir = Path(self.controller.results_dir) / dataset_name
        
        # For FLDAS, disable daily stats columns
        if dataset_name == "FLDAS":
            # Gray out daily column
            for row_idx in range(table.rowCount()):
                if table.item(row_idx, 1):  # Daily column
                    daily_item = table.item(row_idx, 1)
                    daily_item.setText("N/A (Monthly)")
                    daily_item.setBackground(QColor("#f0f0f0"))
                    daily_item.setFlags(Qt.ItemIsEnabled)  # Make non-editable

        # Define files to load stats from
        stats_files = {
            'daily': results_dir / 'daily_stats.csv',
            'monthly': results_dir / 'monthly_stats.csv',
            'yearly': results_dir / 'yearly_stats.csv'
        }
        
        # Seasonal summary
        seasonal_file = results_dir / 'seasonal_summary.csv'
        
        # Load and calculate mean stats
        for col_idx, (period, file_path) in enumerate(stats_files.items(), start=1):
            if file_path.exists():
                try:
                    stats_df = pd.read_csv(file_path)
                    
                    # Calculate means
                    means = {
                        'r2': stats_df['r2'].mean(),
                        'rmse': stats_df['rmse'].mean(),
                        'bias': stats_df['bias'].mean(),
                        'mae': stats_df['mae'].mean(),
                        'nse': stats_df['nse'].mean() if 'nse' in stats_df.columns else float('nan'),
                        'pbias': stats_df['pbias'].mean() if 'pbias' in stats_df.columns else float('nan')
                    }
                    
                    # Update table
                    metrics = ['r2', 'rmse', 'bias', 'mae', 'nse', 'pbias']
                    for row_idx, metric in enumerate(metrics):
                        value = means.get(metric, float('nan'))
                        # Format based on metric type
                        if metric == 'r2' or metric == 'nse':
                            formatted_value = f"{value:.3f}"
                        elif metric == 'pbias':
                            formatted_value = f"{value:.2f}%"
                        else:
                            formatted_value = f"{value:.3f}"
                            
                        table.setItem(row_idx, col_idx, QTableWidgetItem(formatted_value))
                        
                except Exception as e:
                    logger.error(f"Error loading {period} stats: {str(e)}", exc_info=True)
        
        # Load seasonal stats
        if seasonal_file.exists():
            try:
                seasonal_df = pd.read_csv(seasonal_file)
                
                # Map seasons to columns
                season_map = {
                    'Winter': 4,
                    'Spring': 5,
                    'Summer': 6,
                    'Fall': 7
                }
                
                for _, row in seasonal_df.iterrows():
                    season = row['season']
                    col_idx = season_map.get(season)
                    
                    if col_idx:
                        # Update table with seasonal stats
                        metrics = {
                            'r2': 'mean_r2',
                            'rmse': 'mean_rmse',
                            'bias': 'mean_bias',
                            'mae': 'mean_mae',
                            'nse': 'N/A',
                            'pbias': 'N/A'
                        }
                        
                        for row_idx, (metric, col_name) in enumerate(metrics.items()):
                            if col_name in row and col_name != 'N/A':
                                value = row[col_name]
                                # Format based on metric type
                                if metric == 'r2' or metric == 'nse':
                                    formatted_value = f"{value:.3f}"
                                elif metric == 'pbias':
                                    formatted_value = f"{value:.2f}%"
                                else:
                                    formatted_value = f"{value:.3f}"
                                    
                                table.setItem(row_idx, col_idx, QTableWidgetItem(formatted_value))
                            else:
                                table.setItem(row_idx, col_idx, QTableWidgetItem("N/A"))
                
            except Exception as e:
                logger.error(f"Error loading seasonal stats: {str(e)}", exc_info=True)
    
    def reset_ui(self):
        """Reset UI to default state"""
        # Reset analysis type
        self.analysis_type_combo.setCurrentIndex(0)
        
        # Reset checkboxes
        self.include_seasonal.setChecked(True)
        self.include_extreme.setChecked(True)
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.status_text.clear()
        
        # Reset tables
        self.summary_table.setRowCount(0)
        self.reset_stats_table(self.era5_table)
        self.reset_stats_table(self.daymet_table)
        self.reset_stats_table(self.prism_table)
        
        # Reset button
        self.run_button.setEnabled(True)
        self.run_button.setText("Run Analysis")
        
        # Check data availability
        self.check_data_availability()
        
        logger.info("Analysis panel UI reset")
    
    def reset_stats_table(self, table):
        """Clear the statistics table while keeping headers"""
        for row in range(table.rowCount()):
            for col in range(1, table.columnCount()):
                table.setItem(row, col, QTableWidgetItem(""))
    
    def show_help(self):
        """Show help and guidance for the Analysis tab"""
        QMessageBox.information(
            self,
            "Analysis Tab Help",
            "<h3>Climate Data Analysis Guide</h3>"
            "<p><b>Purpose:</b> This tab allows you to analyze the climate data you've downloaded and compare ground station data with gridded datasets.</p>"
            "<p><b>Steps to follow:</b></p>"
            "<ol>"
            "<li>Ensure you've downloaded data in the Data Selection tab first</li>"
            "<li>Select Analysis Type (Standard or Custom)</li>"
            "<li>Choose optional settings (Seasonal Analysis, Extreme Value Analysis)</li>"
            "<li>Click 'Run Analysis' to start the process</li>"
            "<li>Monitor progress in the status window</li>"
            "<li>View results in the tabs below after analysis completes</li>"
            "</ol>"
            "<p><b>Results:</b> The analysis calculates statistical metrics like R² (correlation), RMSE (error), bias, and more to measure how well the gridded datasets match ground station measurements.</p>"
            "<p><b>Tabs:</b> Results are organized by dataset (ERA5, DAYMET, PRISM) with seasonal breakdowns.</p>"
            "<p><b>Note:</b> Analysis results are saved to the Results directory and can be visualized in the Visualization tab.</p>",
            QMessageBox.Ok
        )