#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QPushButton, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

logger = logging.getLogger(__name__)

try:
    import geemap
    import ee
    GEEMAP_AVAILABLE = True
except ImportError:
    GEEMAP_AVAILABLE = False
    logger.warning("geemap is not available. Install with: pip install geemap")

# Define CONUS (Continental US) bounding box
CONUS_BOUNDS = {
    'west': -125.0,
    'south': 24.0,
    'east': -66.0,
    'north': 49.5
}

class DrawMapWidget(QWidget):
    """Widget for drawing study area boundaries on a map using geemap"""
    
    # Signal emitted when a valid polygon is drawn
    polygon_drawn = pyqtSignal(object)  # Emits the GeoJSON of the drawn polygon
    
    def __init__(self, parent=None, project_id=None):
        super().__init__(parent)
        
        # Store the Earth Engine project ID
        self.project_id = project_id
        self.ee_initialized = False
        
        if not GEEMAP_AVAILABLE:
            self.init_placeholder_ui()
            return
            
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_html = os.path.join(self.temp_dir.name, "map.html")
        self.drawn_features = None
        
        self.init_ui()
        
    def set_project_id(self, project_id):
        """Set the Earth Engine project ID"""
        self.project_id = project_id
        # If the map is already created, recreate it with the new project ID
        if hasattr(self, 'web_view'):
            self.create_map()
    
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
        
    def init_placeholder_ui(self):
        """Initialize a placeholder UI when geemap is not available"""
        layout = QVBoxLayout(self)
        
        message = QLabel(
            "The map drawing feature requires the geemap package, which is not installed. "
            "Please install it with: pip install geemap"
        )
        message.setWordWrap(True)
        message.setStyleSheet("color: red;")
        
        layout.addWidget(message)
        
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions_label = QLabel(
            "Draw a polygon on the map to select your study area. "
            "The selection must be within the Continental United States."
        )
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)
        
        # Map container
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)
        layout.addWidget(self.web_view)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.draw_button = QPushButton("Draw New Polygon")
        self.clear_button = QPushButton("Clear")
        self.confirm_button = QPushButton("Confirm Selection")
        self.confirm_button.setEnabled(False)  # Disabled until a valid polygon is drawn
        
        button_layout.addWidget(self.draw_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.confirm_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready. Click 'Draw New Polygon' to start.")
        layout.addWidget(self.status_label)
        
        # Connect signals
        self.draw_button.clicked.connect(self.start_drawing)
        self.clear_button.clicked.connect(self.clear_map)
        self.confirm_button.clicked.connect(self.confirm_selection)
        
        # Create and display the map
        self.create_map()
        
    def create_map(self):
        """Create geemap and display it in the web view"""
        try:
            # Initialize Earth Engine - this will use the project ID if set
            if not self.initialize_earth_engine():
                self.status_label.setText("Failed to initialize Earth Engine. Check your project ID.")
                return
            
            # Create a map centered on the US
            self.map = geemap.Map(center=[39.8283, -98.5795], zoom=4)
            
            # Add CONUS boundary
            conus_coords = [
                [CONUS_BOUNDS['west'], CONUS_BOUNDS['south']],
                [CONUS_BOUNDS['west'], CONUS_BOUNDS['north']],
                [CONUS_BOUNDS['east'], CONUS_BOUNDS['north']],
                [CONUS_BOUNDS['east'], CONUS_BOUNDS['south']],
                [CONUS_BOUNDS['west'], CONUS_BOUNDS['south']]
            ]
            conus_poly = Polygon(conus_coords)
            conus_gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[conus_poly])
            
            # Add CONUS outline to the map
            self.map.add_gdf(
                conus_gdf, 
                layer_name="CONUS Boundary",
                fill_colors=None,  # CHANGED fill_color to fill_colors
                border_color="red",
                info_mode=None
            )
            
            # Add a basemap
            self.map.add_basemap("ROADMAP")
            
            # Save the map to a temporary HTML file
            self.map.to_html(self.temp_html)
            
            # Load the HTML into the web view
            self.web_view.load(QUrl.fromLocalFile(self.temp_html))
        except Exception as e:
            logger.error(f"Error creating map: {str(e)}", exc_info=True)
            self.status_label.setText(f"Error creating map: {str(e)}")
        
    def start_drawing(self):
        """Start the drawing tool in geemap"""
        try:
            # Enable drawing tools
            self.map.draw_control = True
            self.map.draw_control_options = {
                'polyline': False,
                'circlemarker': False,
                'marker': False,
                'circle': False,
                'rectangle': True,
                'polygon': True
            }
            
            # Add callback for drawing completion
            self.map.on_draw(self.handle_draw)
            
            # Update map
            self.map.to_html(self.temp_html)
            self.web_view.load(QUrl.fromLocalFile(self.temp_html))
            
            self.status_label.setText("Drawing mode active. Draw a polygon or rectangle on the map.")
        except Exception as e:
            logger.error(f"Error starting drawing: {str(e)}", exc_info=True)
            self.status_label.setText(f"Error starting drawing: {str(e)}")
        
    def handle_draw(self, feature, feature_type):
        """Handle the draw event from geemap"""
        try:
            self.drawn_features = feature
            
            # Convert feature to GeoJSON
            if feature_type in ['polygon', 'rectangle']:
                # Validate if the drawn polygon is within CONUS
                if self.validate_is_within_conus(feature):
                    self.status_label.setText("Valid selection within CONUS. Click 'Confirm Selection' to proceed.")
                    self.confirm_button.setEnabled(True)
                else:
                    self.status_label.setText("Selection must be entirely within the Continental US. Please try again.")
                    self.confirm_button.setEnabled(False)
                    
                    # Clear the invalid drawing
                    self.clear_map()
            else:
                self.status_label.setText("Please draw a polygon or rectangle.")
                self.confirm_button.setEnabled(False)
        except Exception as e:
            logger.error(f"Error handling draw event: {str(e)}", exc_info=True)
            self.status_label.setText(f"Error handling draw event: {str(e)}")
    
    def validate_is_within_conus(self, feature):
        """Check if the drawn polygon is within the CONUS boundaries"""
        try:
            # Extract coordinates from feature
            coordinates = feature['geometry']['coordinates']
            
            # Create a shapely polygon
            if feature['geometry']['type'] == 'Polygon':
                polygon = Polygon(coordinates[0])
            else:
                # Handle multipolygon or other geometry types
                return False
            
            # Create CONUS polygon
            conus_coords = [
                [CONUS_BOUNDS['west'], CONUS_BOUNDS['south']],
                [CONUS_BOUNDS['west'], CONUS_BOUNDS['north']],
                [CONUS_BOUNDS['east'], CONUS_BOUNDS['north']],
                [CONUS_BOUNDS['east'], CONUS_BOUNDS['south']],
                [CONUS_BOUNDS['west'], CONUS_BOUNDS['south']]
            ]
            conus_poly = Polygon(conus_coords)
            
            # Check if polygon is within CONUS
            return conus_poly.contains(polygon)
        except Exception as e:
            logger.error(f"Error validating polygon: {str(e)}", exc_info=True)
            return False
    
    def clear_map(self):
        """Clear drawn features from the map"""
        try:
            # Reset the map
            self.create_map()
            self.drawn_features = None
            self.confirm_button.setEnabled(False)
            self.status_label.setText("Map cleared. Click 'Draw New Polygon' to start again.")
        except Exception as e:
            logger.error(f"Error clearing map: {str(e)}", exc_info=True)
            self.status_label.setText(f"Error clearing map: {str(e)}")
    
    def confirm_selection(self):
        """Confirm the selected polygon and emit signal"""
        if self.drawn_features:
            self.polygon_drawn.emit(self.drawn_features)
            self.status_label.setText("Selection confirmed!")
        else:
            self.status_label.setText("No valid selection to confirm.")
    
    def get_drawn_feature(self):
        """Get the current drawn feature"""
        return self.drawn_features