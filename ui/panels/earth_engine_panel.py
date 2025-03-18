#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QLineEdit, QGroupBox, QMessageBox, QRadioButton,
                            QCheckBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

from utils.earth_engine_utils import EarthEngineUtils, EARTH_ENGINE_AVAILABLE

logger = logging.getLogger(__name__)

class EarthEnginePanel(QWidget):
    """
    Panel for configuring Earth Engine settings.
    """
    
    # Define signals
    config_updated = pyqtSignal(dict)
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        self.ee_available = EARTH_ENGINE_AVAILABLE
        
        # Load configuration
        self.load_config()
        
        # Initialize UI
        self.init_ui()
        
        # Check Earth Engine status
        self.check_ee_status()
        
        logger.info("Earth Engine Panel initialized")
    
    def load_config(self):
        """Load Earth Engine configuration"""
        try:
            from utils.config_manager import ConfigManager
            
            # Load configuration
            config = ConfigManager.get_earth_engine_config()
            
            # Store configuration
            self.project_id = config.get('project_id', "ee-sauravbhattarai1999")
            
        except ImportError:
            logger.warning("ConfigManager not available, using default configuration")
            self.project_id = "ee-sauravbhattarai1999"

    def save_config(self):
        """Save Earth Engine configuration"""
        try:
            from utils.config_manager import ConfigManager
            
            # Create configuration
            config = {
                'project_id': self.project_id_input.text().strip()
            }
            
            # Save configuration
            ConfigManager.save_earth_engine_config(config)
            
            logger.info("Earth Engine configuration saved")
            
        except ImportError:
            logger.warning("ConfigManager not available, configuration not saved")
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title_label = QLabel("Earth Engine Configuration")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Add status group
        status_group = QGroupBox("Earth Engine Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Checking Earth Engine status...")
        self.status_details = QLabel("")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.status_details)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Add configuration group
        config_group = QGroupBox("Earth Engine Configuration")
        config_layout = QFormLayout()
        
        # Project ID
        self.project_id_input = QLineEdit(self.project_id)
        self.project_id_input.setPlaceholderText("Earth Engine Project ID")
        config_layout.addRow("Project ID:", self.project_id_input)
        
        # Save button
        self.save_button = QPushButton("Save Configuration")
        
        config_layout.addRow("", self.save_button)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Add authentication group
        auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout()
        
        self.auth_button = QPushButton("Authenticate Earth Engine")
        auth_layout.addWidget(self.auth_button)
        
        auth_group.setLayout(auth_layout)
        main_layout.addWidget(auth_group)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Connect signals
        self.save_button.clicked.connect(self.on_save_clicked)
        self.auth_button.clicked.connect(self.on_auth_clicked)
        
        # Disable if Earth Engine not available
        if not self.ee_available:
            self.project_id_input.setEnabled(False)
            self.save_button.setEnabled(False)
            self.auth_button.setEnabled(False)
    
    def check_ee_status(self):
        """Check Earth Engine status and update UI"""
        if not self.ee_available:
            self.status_label.setText("⚠️ Earth Engine API not available")
            self.status_details.setText("Install with: pip install earthengine-api")
            return
            
        status = EarthEngineUtils.check_auth_status()
        
        if status['authenticated']:
            self.status_label.setText("✅ Earth Engine authenticated")
            if status['project_id']:
                self.status_details.setText(f"Project ID: {status['project_id']}")
            else:
                self.status_details.setText("Project ID not available")
        else:
            self.status_label.setText("❌ Earth Engine not authenticated")
            if status['error']:
                self.status_details.setText(f"Error: {status['error']}")
            else:
                self.status_details.setText("Use the Authenticate button to authenticate")
    
    @pyqtSlot()
    def on_save_clicked(self):
        """Handle save button click"""
        project_id = self.project_id_input.text().strip()
        
        if not project_id:
            QMessageBox.warning(self, "Invalid Input", "Project ID cannot be empty")
            return
            
        # Update configuration
        self.project_id = project_id
        
        # Save configuration
        self.save_config()
        
        # Update controller configuration
        config = {
            'ee_project_id': project_id
        }
        
        # Emit signal
        self.config_updated.emit(config)
        
        QMessageBox.information(self, "Configuration Saved", 
                            "Earth Engine configuration has been saved.\nThe new configuration will apply to future data fetching operations.")
    
    @pyqtSlot()
    def on_auth_clicked(self):
        """Handle authentication button click"""
        if not self.ee_available:
            QMessageBox.warning(self, "Earth Engine Not Available",
                               "Earth Engine API is not available.\nInstall with: pip install earthengine-api")
            return
            
        try:
            project_id = self.project_id_input.text().strip()
            
            # Start authentication
            QMessageBox.information(self, "Authentication",
                                   "A browser window will open to authenticate with Earth Engine.\nFollow the instructions and then return to this application.")
            
            success = EarthEngineUtils.authenticate(project_id if project_id else None)
            
            if success:
                QMessageBox.information(self, "Authentication Successful",
                                       "Earth Engine authentication successful!")
            else:
                QMessageBox.warning(self, "Authentication Failed",
                                   "Earth Engine authentication failed. Check the logs for details.")
                
            # Update status
            self.check_ee_status()
            
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Authentication Error",
                                f"An error occurred during authentication: {str(e)}")