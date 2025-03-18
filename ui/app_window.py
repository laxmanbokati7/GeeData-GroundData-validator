#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QAction, QMessageBox,
                            QFileDialog, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon

from ui.panels.data_selection_panel import DataSelectionPanel
from ui.panels.analysis_panel import AnalysisPanel
from ui.panels.visualization_panel import VisualizationPanel
from controller.app_controller import AppController

logger = logging.getLogger(__name__)

class ClimateDataApp(QMainWindow):
    """
    Main window for the Climate Data Fetcher application.
    Contains the main UI components and manages the overall application flow.
    """
    
    def __init__(self):
        super().__init__()
        
        self.controller = AppController()
        
        # Initialize UI
        self.init_ui()
        
        logger.info("Application window initialized")
        
    def init_ui(self):
        """Initialize the UI components"""
        # Set window properties
        self.setWindowTitle("Climate Data Fetcher")
        self.setMinimumSize(1000, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create panels
        self.data_selection_panel = DataSelectionPanel(self.controller)
        self.analysis_panel = AnalysisPanel(self.controller)
        self.visualization_panel = VisualizationPanel(self.controller)
        
        # Create Earth Engine panel if available
        try:
            from ui.panels.earth_engine_panel import EarthEnginePanel
            self.earth_engine_panel = EarthEnginePanel(self.controller)
            has_earth_engine_panel = True
        except ImportError:
            has_earth_engine_panel = False
        
        # Add panels to tabs
        self.tabs.addTab(self.data_selection_panel, "Data Selection")
        self.tabs.addTab(self.analysis_panel, "Analysis")
        self.tabs.addTab(self.visualization_panel, "Visualization")
        
        # Add Earth Engine panel if available
        if has_earth_engine_panel:
            self.tabs.addTab(self.earth_engine_panel, "Earth Engine")
            
            # Connect Earth Engine configuration updates
            self.earth_engine_panel.config_updated.connect(self.on_ee_config_updated)
        
        # Connect tab signals
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Add tabs to layout
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Connect controller signals
        self.controller.status_updated.connect(self.update_status)
        self.controller.error_occurred.connect(self.show_error)
        self.controller.data_downloaded.connect(self.on_data_downloaded)
        self.controller.analysis_completed.connect(self.on_analysis_completed)

    @pyqtSlot(dict)
    def on_ee_config_updated(self, config):
        """Handle Earth Engine configuration updates"""
        # Store the configuration in the controller
        self.controller.ee_config = config
        
        # Update status
        self.status_bar.showMessage("Earth Engine configuration updated")
        
    def create_menu_bar(self):
        """Create the application menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("File")
        
        # New project action
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.on_new_project)
        file_menu.addAction(new_action)
        
        # Open project action
        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.on_open_project)
        file_menu.addAction(open_action)
        
        # Save project action
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.on_save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = self.menuBar().addMenu("Tools")
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.on_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
    @pyqtSlot(int)
    def on_tab_changed(self, index):
        """Handle tab change events"""
        tab_name = self.tabs.tabText(index)
        logger.info(f"Switched to {tab_name} tab")
        
        # Enable/disable tabs based on application state
        if tab_name == "Analysis":
            if not self.controller.is_data_available():
                QMessageBox.warning(
                    self, "No Data Available", 
                    "Please download data in the Data Selection tab first."
                )
                self.tabs.setCurrentIndex(0)  # Switch back to data selection
        
        elif tab_name == "Visualization":
            if not self.controller.is_analysis_complete():
                QMessageBox.warning(
                    self, "No Analysis Results", 
                    "Please run the analysis in the Analysis tab first."
                )
                self.tabs.setCurrentIndex(1)  # Switch to analysis tab
    
    @pyqtSlot()
    def on_new_project(self):
        """Handle new project action"""
        reply = QMessageBox.question(
            self, "New Project", 
            "This will clear all current data. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.reset()
            self.data_selection_panel.reset_ui()
            self.analysis_panel.reset_ui()
            self.visualization_panel.reset_ui()
            self.tabs.setCurrentIndex(0)  # Switch to data selection
            self.status_bar.showMessage("New project created")
            
    @pyqtSlot()
    def on_open_project(self):
        """Handle open project action"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Climate Data Project (*.cdp)"
        )
        
        if file_path:
            try:
                self.controller.load_project(file_path)
                self.status_bar.showMessage(f"Project loaded: {file_path}")
            except Exception as e:
                logger.error(f"Error loading project: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self, "Error", f"Failed to load project: {str(e)}"
                )
    
    @pyqtSlot()
    def on_save_project(self):
        """Handle save project action"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "Climate Data Project (*.cdp)"
        )
        
        if file_path:
            try:
                self.controller.save_project(file_path)
                self.status_bar.showMessage(f"Project saved: {file_path}")
            except Exception as e:
                logger.error(f"Error saving project: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self, "Error", f"Failed to save project: {str(e)}"
                )
    
    @pyqtSlot()
    def on_settings(self):
        """Handle settings action"""
        # TODO: Implement settings dialog
        QMessageBox.information(
            self, "Settings", "Settings dialog will be implemented in a future update."
        )
    
    @pyqtSlot()
    def on_about(self):
        """Handle about action"""
        QMessageBox.about(
            self, "About Climate Data Fetcher",
            "<h2>Climate Data Fetcher</h2>"
            "<p>Version 1.0.0</p>"
            "<p>A comprehensive tool for fetching, analyzing, and visualizing "
            "climate data from multiple sources including ground stations (Meteostat), "
            "ERA5 reanalysis, DAYMET, and PRISM datasets.</p>"
            "<p>© 2024 - Climate Data Fetcher Team</p>"
        )
    
    @pyqtSlot(str)
    def update_status(self, message):
        """Update the status bar with a message"""
        self.status_bar.showMessage(message)
    
    @pyqtSlot(str, str)
    def show_error(self, title, message):
        """Show an error message dialog"""
        QMessageBox.critical(self, title, message)
    
    @pyqtSlot()
    def on_data_downloaded(self):
        """Handle data download completion"""
        QMessageBox.information(
            self, "Download Complete", 
            "Data download has completed successfully. You can now proceed to analysis."
        )
        # Enable the Analysis tab
        self.tabs.setTabEnabled(1, True)
    
    @pyqtSlot()
    def on_analysis_completed(self):
        """Handle analysis completion"""
        QMessageBox.information(
            self, "Analysis Complete", 
            "Data analysis has completed successfully. You can now view the results."
        )
        # Enable the Visualization tab
        self.tabs.setTabEnabled(2, True)