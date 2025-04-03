#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QPushButton, QMessageBox, 
                             QTabWidget, QFormLayout, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)

try:
    import ee
    GEEMAP_AVAILABLE = True
except ImportError:
    GEEMAP_AVAILABLE = False
    logger.warning("ee is not available. Install with: pip install earthengine-api")

# Define CONUS (Continental US) bounding box
CONUS_BOUNDS = {
    'west': -125.0,
    'south': 24.0,
    'east': -66.0,
    'north': 49.5
}

class DrawMapWidget(QWidget):
    """Widget for defining study area boundaries using a form interface"""
    
    # Signal emitted when a valid polygon is defined
    polygon_drawn = pyqtSignal(object)  # Emits the GeoJSON of the defined polygon
    
    def __init__(self, parent=None, project_id=None):
        super().__init__(parent)
        
        # Store the Earth Engine project ID
        self.project_id = project_id
        self.ee_initialized = False
        self.drawn_features = None
        
        self.init_ui()
        
    def set_project_id(self, project_id):
        """Set the Earth Engine project ID"""
        self.project_id = project_id
    
    def initialize_earth_engine(self):
        """Initialize Earth Engine with the project ID"""
        if not GEEMAP_AVAILABLE:
            return False
            
        if self.ee_initialized:
            return True
            
        try:
            # Initialize Earth Engine with the project ID
            if self.project_id:
                logger.info(f"Initializing Earth Engine with project ID: {self.project_id}")
                ee.Initialize(project=self.project_id)
            else:
                logger.info("Initializing Earth Engine with default credentials")
                ee.Initialize()
                
            self.ee_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Earth Engine: {str(e)}")
            self.status_label.setText(f"Error initializing Earth Engine: {str(e)}")
            return False
        
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions_label = QLabel(
            "Define your study area by entering coordinates or selecting a predefined region."
        )
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)
        
        # Create tabs for different input methods
        tab_widget = QTabWidget()
        
        # Tab 1: Bounding Box
        bbox_tab = QWidget()
        bbox_layout = QFormLayout(bbox_tab)
        
        # Create form fields
        self.min_lon = QLineEdit("-95.0")  # Default to center of US
        self.min_lat = QLineEdit("35.0")
        self.max_lon = QLineEdit("-85.0")
        self.max_lat = QLineEdit("45.0")
        
        # Add fields to form
        bbox_layout.addRow("Min Longitude:", self.min_lon)
        bbox_layout.addRow("Min Latitude:", self.min_lat)
        bbox_layout.addRow("Max Longitude:", self.max_lon)
        bbox_layout.addRow("Max Latitude:", self.max_lat)
        
        # Tab 2: Predefined Areas
        predef_tab = QWidget()
        predef_layout = QVBoxLayout(predef_tab)
        
        # Create buttons for common US regions
        northeast_btn = QPushButton("Northeast US")
        southeast_btn = QPushButton("Southeast US")
        midwest_btn = QPushButton("Midwest US")
        southwest_btn = QPushButton("Southwest US")
        northwest_btn = QPushButton("Northwest US")
        
        # Connect buttons
        northeast_btn.clicked.connect(lambda: self.set_predefined_region("northeast"))
        southeast_btn.clicked.connect(lambda: self.set_predefined_region("southeast"))
        midwest_btn.clicked.connect(lambda: self.set_predefined_region("midwest"))
        southwest_btn.clicked.connect(lambda: self.set_predefined_region("southwest"))
        northwest_btn.clicked.connect(lambda: self.set_predefined_region("northwest"))
        
        # Add buttons to layout
        predef_layout.addWidget(northeast_btn)
        predef_layout.addWidget(southeast_btn)
        predef_layout.addWidget(midwest_btn)
        predef_layout.addWidget(southwest_btn)
        predef_layout.addWidget(northwest_btn)
        predef_layout.addStretch()
        
        # Add tabs to tab widget
        tab_widget.addTab(bbox_tab, "Bounding Box")
        tab_widget.addTab(predef_tab, "Predefined Regions")
        
        # Add tab widget to main layout
        layout.addWidget(tab_widget)
        
        # Preview area
        preview_group = QGroupBox("Area Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel("Coordinates: Not yet defined")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_group)
        
        # Buttons at bottom
        button_layout = QHBoxLayout()
        self.draw_button = QPushButton("Draw New Polygon")
        self.clear_button = QPushButton("Clear")
        self.confirm_button = QPushButton("Confirm Selection")
        self.confirm_button.setEnabled(False)
        
        button_layout.addWidget(self.draw_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.confirm_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Enter coordinates and click 'Draw New Polygon'")
        layout.addWidget(self.status_label)
        
        # Connect signals
        self.draw_button.clicked.connect(self.calculate_area)
        self.clear_button.clicked.connect(self.clear_form)
        self.confirm_button.clicked.connect(self.confirm_selection)
        
    def set_predefined_region(self, region):
        """Set coordinates for predefined regions"""
        regions = {
            "northeast": {"min_lon": -80.0, "min_lat": 37.0, "max_lon": -70.0, "max_lat": 45.0},
            "southeast": {"min_lon": -90.0, "min_lat": 30.0, "max_lon": -75.0, "max_lat": 37.0},
            "midwest": {"min_lon": -97.0, "min_lat": 36.0, "max_lon": -80.0, "max_lat": 49.0},
            "southwest": {"min_lon": -115.0, "min_lat": 31.0, "max_lon": -102.0, "max_lat": 42.0},
            "northwest": {"min_lon": -125.0, "min_lat": 42.0, "max_lon": -110.0, "max_lat": 49.0}
        }
        
        if region in regions:
            coords = regions[region]
            self.min_lon.setText(str(coords["min_lon"]))
            self.min_lat.setText(str(coords["min_lat"]))
            self.max_lon.setText(str(coords["max_lon"]))
            self.max_lat.setText(str(coords["max_lat"]))
            
            self.calculate_area()
    
    def calculate_area(self):
        """Calculate area from coordinates and create polygon"""
        try:
            # Get coordinates
            min_lon = float(self.min_lon.text())
            min_lat = float(self.min_lat.text())
            max_lon = float(self.max_lon.text())
            max_lat = float(self.max_lat.text())
            
            # Validate coordinates
            if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if min_lon >= max_lon or min_lat >= max_lat:
                raise ValueError("Min values must be less than max values")
            
            # Calculate area (approximate)
            # 1 degree of latitude ≈ 111.32 km
            # 1 degree of longitude at the equator ≈ 111.32 km, decreases with latitude
            lat_distance = (max_lat - min_lat) * 111.32
            # Average latitude for longitude calculation
            avg_lat = (min_lat + max_lat) / 2
            # Correction factor for longitude
            lon_correction = abs(np.cos(np.radians(avg_lat)))
            lon_distance = (max_lon - min_lon) * 111.32 * lon_correction
            
            area_sqkm = lat_distance * lon_distance
            
            # Create GeoJSON for the bounding box
            self.drawn_features = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat],
                        [min_lon, max_lat],
                        [max_lon, max_lat],
                        [max_lon, min_lat],
                        [min_lon, min_lat]  # Close the polygon
                    ]]
                },
                "properties": {
                    "area_sqkm": area_sqkm
                }
            }
            
            # Update preview
            self.preview_label.setText(
                f"Coordinates: [{min_lon}, {min_lat}, {max_lon}, {max_lat}]\n"
                f"Area: {area_sqkm:.2f} km²"
            )
            
            # Enable confirm button
            self.confirm_button.setEnabled(True)
            
            # Update status
            self.status_label.setText("Area defined. Click 'Confirm Selection' to proceed.")
            
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            self.status_label.setText(f"Error: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Unexpected error: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def clear_form(self):
        """Clear the form fields"""
        self.min_lon.setText("")
        self.min_lat.setText("")
        self.max_lon.setText("")
        self.max_lat.setText("")
        self.preview_label.setText("Coordinates: Not yet defined")
        self.drawn_features = None
        self.confirm_button.setEnabled(False)
        self.status_label.setText("Form cleared.")
    
    def confirm_selection(self):
        """Confirm the selection and emit the signal"""
        if self.drawn_features:
            self.polygon_drawn.emit(self.drawn_features)
            self.status_label.setText("Selection confirmed!")
        else:
            self.status_label.setText("No area defined yet. Please calculate an area first.")
    
    def start_drawing(self):
        """
        Compatibility method with the original DrawMapWidget interface
        Just calculates the area from current values
        """
        self.calculate_area()
    
    def clear_map(self):
        """Compatibility method - just clears the form"""
        self.clear_form()
    
    def get_drawn_feature(self):
        """Get the current drawn feature"""
        return self.drawn_features