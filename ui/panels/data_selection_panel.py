#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                            QGroupBox, QRadioButton, QSlider, QListWidget, 
                            QListWidgetItem, QPushButton, QProgressBar, QCheckBox,
                            QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from utils.huc_utils import HUCDataProvider
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import QTimer
from utils.workers import HUCLoadWorker, HUCBoundaryWorker
from PyQt5.QtWebEngineWidgets import QWebEngineView
from utils.drawing_utils import filter_stations_by_polygon
from utils.geemap_integration import DrawMapWidget

logger = logging.getLogger(__name__)

class DataSelectionPanel(QWidget):
    """
    Panel for selecting and downloading climate data.
    Replicates the functionality of the data selection part of main.ipynb.
    """
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        self.active_threads = []
        self.drawn_feature = None
        
        # Get Earth Engine project ID from configuration
        self.ee_project_id = getattr(self.controller, 'ee_config', {}).get('ee_project_id')
        if not self.ee_project_id:
            logger.warning("No Earth Engine project ID configured, using default")
            self.ee_project_id = "ee-sauravbhattarai1999"
        
        # US states dictionary
        self.us_states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        
        # Initialize UI
        self.init_ui()
        
        logger.info("Data Selection Panel initialized")
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title_label = QLabel("Climate Data Selection")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Data Type Selection
        data_type_group = QGroupBox("Data Type")
        data_type_layout = QVBoxLayout()
        
        self.rb_ground_only = QRadioButton("Ground data only")
        self.rb_gridded_only = QRadioButton("Gridded data only")
        self.rb_both = QRadioButton("Both")
        self.rb_both.setChecked(True)  # Default selection
        
        data_type_layout.addWidget(self.rb_ground_only)
        data_type_layout.addWidget(self.rb_gridded_only)
        data_type_layout.addWidget(self.rb_both)
        
        data_type_group.setLayout(data_type_layout)
        scroll_layout.addWidget(data_type_group)
        
        # Connect signals
        self.rb_ground_only.toggled.connect(self.on_data_type_changed)
        self.rb_gridded_only.toggled.connect(self.on_data_type_changed)
        self.rb_both.toggled.connect(self.on_data_type_changed)
        
        # 2. Year Range Selection
        year_range_group = QGroupBox("Year Range")
        year_range_layout = QVBoxLayout()
        
        # Start Year
        start_year_layout = QHBoxLayout()
        start_year_label = QLabel("Start Year:")
        self.start_year_slider = QSlider(Qt.Horizontal)
        self.start_year_slider.setMinimum(1980)
        self.start_year_slider.setMaximum(2024)
        self.start_year_slider.setValue(1980)
        self.start_year_value = QLabel("1980")
        
        start_year_layout.addWidget(start_year_label)
        start_year_layout.addWidget(self.start_year_slider)
        start_year_layout.addWidget(self.start_year_value)
        
        # End Year
        end_year_layout = QHBoxLayout()
        end_year_label = QLabel("End Year:")
        self.end_year_slider = QSlider(Qt.Horizontal)
        self.end_year_slider.setMinimum(1980)
        self.end_year_slider.setMaximum(2024)
        self.end_year_slider.setValue(2024)
        self.end_year_value = QLabel("2024")
        
        end_year_layout.addWidget(end_year_label)
        end_year_layout.addWidget(self.end_year_slider)
        end_year_layout.addWidget(self.end_year_value)
        
        year_range_layout.addLayout(start_year_layout)
        year_range_layout.addLayout(end_year_layout)
        
        year_range_group.setLayout(year_range_layout)
        scroll_layout.addWidget(year_range_group)
        
        # Connect signals
        self.start_year_slider.valueChanged.connect(self.on_start_year_changed)
        self.end_year_slider.valueChanged.connect(self.on_end_year_changed)
        
        # 3. State Selection
        area_group = QGroupBox("Area Selection")
        area_layout = QVBoxLayout()
        
        # Selection method
        selection_method_layout = QHBoxLayout()
        selection_method_label = QLabel("Selection Method:")
        self.rb_states = QRadioButton("States")
        self.rb_huc = QRadioButton("HUC Watershed")
        self.rb_draw = QRadioButton("Draw Area")
        self.rb_states.setChecked(True)  # Default selection
        
        selection_method_layout.addWidget(selection_method_label)
        selection_method_layout.addWidget(self.rb_states)
        selection_method_layout.addWidget(self.rb_huc)
        selection_method_layout.addWidget(self.rb_draw)
        
        area_layout.addLayout(selection_method_layout)
        
        # Create State selection widgets (same as before)
        self.state_selection_widget = QWidget()
        state_selection_layout = QVBoxLayout(self.state_selection_widget)
        
        self.rb_all_states = QRadioButton("All US States")
        self.rb_specific_states = QRadioButton("Select specific states")
        self.rb_all_states.setChecked(True)
        
        self.state_list = QListWidget()
        self.state_list.setEnabled(False)
        self.state_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Add states to list
        for code, name in self.us_states.items():
            item = QListWidgetItem(f"{code} - {name}")
            self.state_list.addItem(item)
        
        state_selection_layout.addWidget(self.rb_all_states)
        state_selection_layout.addWidget(self.rb_specific_states)
        state_selection_layout.addWidget(self.state_list)
        
        # Create HUC selection widgets
        self.huc_selection_widget = QWidget()
        self.huc_selection_widget.setVisible(False)  # Initially hidden
        huc_selection_layout = QVBoxLayout(self.huc_selection_widget)
        
        # HUC selection components
        huc_info_label = QLabel("Select a HUC08 watershed:")
        huc_info_label.setWordWrap(True)
        
        # Region filter
        huc_region_layout = QHBoxLayout()
        huc_region_label = QLabel("Region:")
        self.huc_region_combo = QComboBox()
        self.huc_region_combo.addItem("Loading regions...", None)
        
        huc_region_layout.addWidget(huc_region_label)
        huc_region_layout.addWidget(self.huc_region_combo)
        
        # HUC selector
        huc_selection_layout2 = QHBoxLayout()
        huc_selection_label = QLabel("HUC:")
        self.huc_selection_combo = QComboBox()
        self.huc_selection_combo.addItem("Select region first", None)
        self.huc_selection_combo.setEnabled(False)
        
        huc_selection_layout2.addWidget(huc_selection_label)
        huc_selection_layout2.addWidget(self.huc_selection_combo)
        
        # Load HUC button
        self.load_huc_button = QPushButton("Load HUC Data")
        self.load_huc_button.setEnabled(False)
        
        # HUC info
        self.huc_info_text = QLabel("No HUC selected")
        self.huc_info_text.setWordWrap(True)
        self.huc_info_text.setStyleSheet("font-size: 10px; color: #666;")
        
        # Add components to layout
        huc_selection_layout.addWidget(huc_info_label)
        huc_selection_layout.addLayout(huc_region_layout)
        huc_selection_layout.addLayout(huc_selection_layout2)
        huc_selection_layout.addWidget(self.load_huc_button)
        huc_selection_layout.addWidget(self.huc_info_text)
        
        # Create drawing selection widget with project ID - Add after HUC selection widget code
        project_id = getattr(self.controller, 'ee_config', {}).get('ee_project_id', "ee-sauravbhattarai1999")
        self.draw_selection_widget = DrawMapWidget()
        self.draw_selection_widget.set_project_id(project_id)  # Pass project ID
        self.draw_selection_widget.setVisible(False)  # Initially hidden
        self.draw_selection_widget.polygon_drawn.connect(self.on_polygon_drawn)
        
        # Add all selection widgets to the area group
        area_layout.addWidget(self.state_selection_widget)
        area_layout.addWidget(self.huc_selection_widget)
        area_layout.addWidget(self.draw_selection_widget)  # <=== ADD THIS LINE
        
        area_group.setLayout(area_layout)
        scroll_layout.addWidget(area_group)
        
        # Connect signals for area selection
        self.rb_states.toggled.connect(self.on_selection_method_changed)
        self.rb_huc.toggled.connect(self.on_selection_method_changed)
        self.rb_draw.toggled.connect(self.on_selection_method_changed)  # <=== ADD THIS LINE
        self.rb_all_states.toggled.connect(self.on_state_scope_changed)
        self.rb_specific_states.toggled.connect(self.on_state_scope_changed)
        self.huc_region_combo.currentIndexChanged.connect(self.on_huc_region_changed)
        self.huc_selection_combo.currentIndexChanged.connect(self.on_huc_selected)
        self.load_huc_button.clicked.connect(self.on_load_huc_clicked)
        
        # 4. Gridded Dataset Selection
        gridded_group = QGroupBox("Gridded Datasets")
        gridded_layout = QVBoxLayout()
        
        # Existing checkboxes
        self.cb_era5 = QCheckBox("ERA5")
        self.cb_daymet = QCheckBox("DAYMET")
        self.cb_prism = QCheckBox("PRISM")
        
        # New checkboxes
        self.cb_chirps = QCheckBox("CHIRPS (1981-present, Daily)")
        self.cb_fldas = QCheckBox("FLDAS (1982-present, Monthly)")
        self.cb_fldas.setToolTip(
        "FLDAS provides monthly precipitation data. During analysis, ground station data "
        "will be aggregated to monthly for valid comparisons. Daily statistics will not "
        "be available for this dataset."
        )
        self.cb_gsmap = QCheckBox("GSMAP-v8 (1998-present, Hourly→Daily)")
        self.cb_gldas_hist = QCheckBox("GLDAS Historical (1948-2014, 3-hourly→Daily)")
        self.cb_gldas_curr = QCheckBox("GLDAS Current (2000-present, 3-hourly→Daily)")
        
        # Set default state
        self.cb_era5.setChecked(True)
        self.cb_daymet.setChecked(True)
        self.cb_prism.setChecked(True)
        self.cb_chirps.setChecked(False)
        self.cb_fldas.setChecked(False)
        self.cb_gsmap.setChecked(False)
        self.cb_gldas_hist.setChecked(False)
        self.cb_gldas_curr.setChecked(False)
        
        # Add tooltips with information about datasets
        self.cb_chirps.setToolTip("Climate Hazards Group InfraRed Precipitation with Station data - 5.5km resolution")
        self.cb_fldas.setToolTip("Famine Early Warning Systems Network Land Data Assimilation System - 11km resolution")
        self.cb_gsmap.setToolTip("Global Satellite Mapping of Precipitation - 11km resolution")
        self.cb_gldas_hist.setToolTip("Global Land Data Assimilation System (Historical) - 28km resolution")
        self.cb_gldas_curr.setToolTip("Global Land Data Assimilation System (Current) - 28km resolution")
        
        # Add to layout
        gridded_layout.addWidget(self.cb_era5)
        gridded_layout.addWidget(self.cb_daymet)
        gridded_layout.addWidget(self.cb_prism)
        gridded_layout.addWidget(self.cb_chirps)
        gridded_layout.addWidget(self.cb_fldas)
        gridded_layout.addWidget(self.cb_gsmap)
        gridded_layout.addWidget(self.cb_gldas_hist)
        gridded_layout.addWidget(self.cb_gldas_curr)
        
        gridded_group.setLayout(gridded_layout)
        scroll_layout.addWidget(gridded_group)
        
        # Add the scroll area to the main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Add progress bar
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progress:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
        
        # Add download button
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download Data")
        self.download_button.setMinimumHeight(40)
        
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        
        main_layout.addLayout(button_layout)
        
        # Connect signals
        self.download_button.clicked.connect(self.on_download_clicked)
        
        # Connect controller signals
        self.controller.data_controller.progress_updated.connect(self.update_progress)

        QTimer.singleShot(1000, self.load_huc_metadata)  # Reset UI on startup
    
    @pyqtSlot(bool)
    def on_data_type_changed(self, checked):
        """Handle data type selection change"""
        if not checked:
            return
            
        if self.rb_gridded_only.isChecked():
            # Disable ground data options
            self.rb_all_states.setEnabled(False)
            self.rb_specific_states.setEnabled(False)
            self.state_list.setEnabled(False)
            
            # Enable gridded options
            self.cb_era5.setEnabled(True)
            self.cb_daymet.setEnabled(True)
            self.cb_prism.setEnabled(True)
            
        elif self.rb_ground_only.isChecked():
            # Enable ground data options
            self.rb_all_states.setEnabled(True)
            self.rb_specific_states.setEnabled(True)
            if self.rb_specific_states.isChecked():
                self.state_list.setEnabled(True)
                
            # Disable gridded options
            self.cb_era5.setEnabled(False)
            self.cb_daymet.setEnabled(False)
            self.cb_prism.setEnabled(False)
            
        else:  # Both
            # Enable all options
            self.rb_all_states.setEnabled(True)
            self.rb_specific_states.setEnabled(True)
            if self.rb_specific_states.isChecked():
                self.state_list.setEnabled(True)
                
            self.cb_era5.setEnabled(True)
            self.cb_daymet.setEnabled(True)
            self.cb_prism.setEnabled(True)
            
        logger.debug(f"Data type changed: {self.get_data_type()}")
    
    @pyqtSlot(bool)
    def on_state_scope_changed(self, checked):
        """Handle state scope selection change"""
        if not checked:
            return
            
        if self.rb_specific_states.isChecked():
            self.state_list.setEnabled(True)
        else:
            self.state_list.setEnabled(False)
            
        logger.debug("State scope changed")
    
    @pyqtSlot(int)
    def on_start_year_changed(self, value):
        """Handle start year slider change"""
        self.start_year_value.setText(str(value))
        
        # Ensure end year is not less than start year
        if value > self.end_year_slider.value():
            self.end_year_slider.setValue(value)
            
        logger.debug(f"Start year changed: {value}")
    
    @pyqtSlot(int)
    def on_end_year_changed(self, value):
        """Handle end year slider change"""
        self.end_year_value.setText(str(value))
        
        # Ensure start year is not greater than end year
        if value < self.start_year_slider.value():
            self.start_year_slider.setValue(value)
            
        logger.debug(f"End year changed: {value}")
    
    @pyqtSlot()
    def on_download_clicked(self):
        """Handle download button click"""
        try:
            # Disable download button
            self.download_button.setEnabled(False)
            self.download_button.setText("Downloading...")
            
            # Reset progress bar
            self.progress_bar.setValue(0)
            
            # Get selection type
            selection_type = self.get_selection_type()
            
            # Get data configuration
            data_config = {
                'data_type': self.get_data_type(),
                'start_year': self.start_year_slider.value(),
                'end_year': self.end_year_slider.value(),
                'selection_type': selection_type,
                'states': self.get_selected_states() if selection_type == 'states' else None,
                'drawn_feature': self.drawn_feature if selection_type == 'draw' else None,
                'huc_id': self.get_selected_huc() if selection_type == 'huc' else None,
                'gridded_datasets': self.get_selected_datasets(),
                'ee_project_id': getattr(self.controller, 'ee_config', {}).get('ee_project_id', "ee-sauravbhattarai1999")
            }
            
            logger.info(f"Starting data download with config: {data_config}")
            
            # Start data fetching, passing the drawn_feature for station filtering
            self.controller.fetch_data(data_config, drawn_feature=self.drawn_feature)
            
        except Exception as e:
            logger.error(f"Error starting download: {str(e)}", exc_info=True)
            self.controller.error_occurred.emit("Download Error", str(e))
            
            # Re-enable download button
            self.download_button.setEnabled(True)
            self.download_button.setText("Download Data")
    
    @pyqtSlot(int)
    def update_progress(self, value):
        """Update the progress bar value"""
        self.progress_bar.setValue(value)
        
        # Re-enable download button when complete
        if value >= 100:
            self.download_button.setEnabled(True)
            self.download_button.setText("Download Data")
    
    def get_data_type(self):
        """Get the selected data type"""
        if self.rb_ground_only.isChecked():
            return "ground"
        elif self.rb_gridded_only.isChecked():
            return "gridded"
        else:
            return "both"
    
    def get_selected_states(self):
        """Get the selected states"""
        if self.rb_all_states.isChecked():
            return None
            
        selected_states = []
        for item in self.state_list.selectedItems():
            text = item.text()
            state_code = text.split(' - ')[0]
            selected_states.append(state_code)
            
        return selected_states if selected_states else None
    
    def get_selected_datasets(self):
        """Get the selected gridded datasets"""
        datasets = []
        
        if self.cb_era5.isChecked():
            datasets.append("ERA5")
        if self.cb_daymet.isChecked():
            datasets.append("DAYMET")
        if self.cb_prism.isChecked():
            datasets.append("PRISM")
        if self.cb_chirps.isChecked():
            datasets.append("CHIRPS")
        if self.cb_fldas.isChecked():
            datasets.append("FLDAS")
        if self.cb_gsmap.isChecked():
            datasets.append("GSMAP")
        if self.cb_gldas_hist.isChecked():
            datasets.append("GLDAS-Historical")
        if self.cb_gldas_curr.isChecked():
            datasets.append("GLDAS-Current")
            
        return datasets
    
    def reset_ui(self):
        """Reset UI to default state"""
        # Reset data type
        self.rb_both.setChecked(True)
        
        # Reset year range
        self.start_year_slider.setValue(1980)
        self.end_year_slider.setValue(2024)
        
        # Reset state selection
        self.rb_all_states.setChecked(True)
        self.state_list.clearSelection()
        
        # Reset gridded datasets
        self.cb_era5.setChecked(True)
        self.cb_daymet.setChecked(True)
        self.cb_prism.setChecked(True)
        self.cb_chirps.setChecked(False)
        self.cb_fldas.setChecked(False)
        self.cb_gsmap.setChecked(False)
        self.cb_gldas_hist.setChecked(False)
        self.cb_gldas_curr.setChecked(False)
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Reset download button
        self.download_button.setEnabled(True)
        self.download_button.setText("Download Data")
        
        logger.info("UI reset to default state")

    # Add new methods to handle HUC selection
    def on_selection_method_changed(self, checked):
        """Handle selection method change between States and HUC"""
        if not checked:
            return
            
        if self.rb_states.isChecked():
            self.state_selection_widget.setVisible(True)
            self.huc_selection_widget.setVisible(False)
            self.draw_selection_widget.setVisible(False)
        elif self.rb_huc.isChecked():  # HUC selected
            self.state_selection_widget.setVisible(False)
            self.huc_selection_widget.setVisible(True)
            self.draw_selection_widget.setVisible(False)
        else:
            self.state_selection_widget.setVisible(False)
            self.huc_selection_widget.setVisible(False)
            self.draw_selection_widget.setVisible(True)
            
            # If HUC metadata not loaded yet, load it
            if self.huc_region_combo.count() <= 1:
                self.load_huc_metadata()

    def load_huc_metadata(self):
        """Load HUC metadata in the background"""
        try:
            # Create progress dialog
            progress = QProgressDialog("Loading HUC data...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Create worker thread - passing self as parent and project_id as parameter
            project_id = getattr(self.controller, 'ee_config', {}).get('ee_project_id', "ee-sauravbhattarai1999")
            worker = HUCLoadWorker(parent=self)  # Pass parent first
            worker.set_project_id(project_id)  # Set project_id through a method
            
            worker.progress_updated.connect(progress.setValue)
            worker.finished.connect(self.on_huc_metadata_loaded)
            worker.failed.connect(self.on_huc_metadata_failed)
            
            # Add cleanup handler
            worker.finished.connect(lambda: self.cleanup_thread(worker))
            worker.failed.connect(lambda e: self.cleanup_thread(worker))
            
            # Keep reference to prevent garbage collection
            self.active_threads.append(worker)
            
            # Start worker
            worker.start()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load HUC metadata: {str(e)}")
            logger.error(f"Error loading HUC metadata: {str(e)}", exc_info=True)

    def on_huc_metadata_loaded(self, regions):
        """Handle loaded HUC metadata"""
        # Clear and populate region combo
        self.huc_region_combo.clear()
        self.huc_region_combo.addItem("Select a region", None)
        
        for region_name, region_data in regions.items():
            self.huc_region_combo.addItem(region_name, region_data)
            
        self.huc_region_combo.setEnabled(True)

    def on_huc_metadata_failed(self, error):
        """Handle HUC metadata loading failure"""
        # Update UI with error message
        self.huc_info_text.setText(f"Error loading HUC metadata: {str(error)}")
        QMessageBox.warning(
            self, 
            "HUC Data Error", 
            f"Failed to load HUC watershed data: {str(error)}\n\nPlease try again later."
        )
        
        # Reset the HUC combo boxes
        self.huc_region_combo.clear()
        self.huc_region_combo.addItem("Error loading data", None)
        self.huc_selection_combo.clear()
        self.huc_selection_combo.addItem("Error loading data", None)
        self.huc_selection_combo.setEnabled(False)

    def on_huc_region_changed(self, index):
        """Handle HUC region selection change"""
        # Get selected region data
        region_data = self.huc_region_combo.currentData()
        
        # Clear and populate HUC combo
        self.huc_selection_combo.clear()
        self.huc_selection_combo.addItem("Select a HUC", None)
        
        if region_data:
            # Add HUCs in this region
            for huc_id, huc_info in region_data.items():
                display_text = f"{huc_id} - {huc_info['name']}"
                self.huc_selection_combo.addItem(display_text, huc_id)
                
            self.huc_selection_combo.setEnabled(True)
        else:
            self.huc_selection_combo.setEnabled(False)

    def on_huc_selected(self, index):
        """Handle HUC selection change"""
        # Get selected HUC
        huc_id = self.huc_selection_combo.currentData()
        
        if huc_id:
            # Get region data
            region_data = self.huc_region_combo.currentData()
            
            if region_data and huc_id in region_data:
                huc_info = region_data[huc_id]
                
                # Handle area_sqkm whether it's a string or float
                try:
                    # Try to format it as a float
                    area_sqkm = float(huc_info['area_sqkm'])
                    area_display = f"{area_sqkm:.2f} km²"
                except (ValueError, TypeError):
                    # If conversion fails, just use it as is
                    area_display = f"{huc_info['area_sqkm']} km²"
                
                # Update info display
                info_text = (
                    f"HUC ID: {huc_id}\n"
                    f"Name: {huc_info['name']}\n"
                    f"States: {huc_info['states']}\n"
                    f"Area: {area_display}"
                )
                self.huc_info_text.setText(info_text)
                
                # Enable load button
                self.load_huc_button.setEnabled(True)
            else:
                self.huc_info_text.setText("No HUC selected")
                self.load_huc_button.setEnabled(False)
        else:
            self.huc_info_text.setText("No HUC selected")
            self.load_huc_button.setEnabled(False)

    def on_load_huc_clicked(self):
        """Handle load HUC button click"""
        huc_id = self.huc_selection_combo.currentData()
        
        if not huc_id:
            return
            
        # Show loading message
        self.huc_info_text.setText(f"Loading HUC {huc_id} boundary...")
        
        # Get project ID from controller
        project_id = getattr(self.controller, 'ee_config', {}).get('ee_project_id', "ee-sauravbhattarai1999")
        
        # Create worker to load boundary
        worker = HUCBoundaryWorker(huc_id)
        worker.set_project_id(project_id)  # Set project ID
        worker.finished.connect(lambda: self.on_huc_boundary_loaded(huc_id))
        worker.failed.connect(lambda e: self.on_huc_boundary_failed(huc_id, e))
        
        # Add cleanup handlers
        worker.finished.connect(lambda: self.cleanup_thread(worker))
        worker.failed.connect(lambda e: self.cleanup_thread(worker))
        
        # Keep reference to prevent garbage collection
        self.active_threads.append(worker)
        
        # Start worker
        worker.start()

    def on_huc_boundary_loaded(self, huc_id):
        """Handle loaded HUC boundary"""
        # Update info with success message
        region_data = self.huc_region_combo.currentData()
        if region_data and huc_id in region_data:
            huc_info = region_data[huc_id]
            
            # Handle area_sqkm whether it's a string or float
            try:
                # Try to format it as a float
                area_sqkm = float(huc_info['area_sqkm'])
                area_display = f"{area_sqkm:.2f} km²"
            except (ValueError, TypeError):
                # If conversion fails, just use it as is
                area_display = f"{huc_info['area_sqkm']} km²"
            
            # Update info display with success
            info_text = (
                f"HUC ID: {huc_id}\n"
                f"Name: {huc_info['name']}\n"
                f"States: {huc_info['states']}\n"
                f"Area: {area_display}\n"
                f"Status: Boundary loaded successfully"
            )
            self.huc_info_text.setText(info_text)

    def on_huc_boundary_failed(self, huc_id, error):
        """Handle HUC boundary loading failure"""
        # Update info with error message
        self.huc_info_text.setText(f"Error loading HUC {huc_id} boundary: {str(error)}")

    # Update the get_selection_type method
    def get_selection_type(self):
        """Get the current selection type"""
        if self.rb_draw.isChecked():
            return "draw"
        elif self.rb_huc.isChecked():
            return "huc"
        else:
            return "states"

    # Update the get_selected_huc method
    def get_selected_huc(self):
        """Get the selected HUC ID or None if no HUC selected"""
        if not self.rb_huc.isChecked():
            return None
            
        return self.huc_selection_combo.currentData()
    
    def on_polygon_drawn(self, feature):
        """Handle polygon drawn on the map"""
        # Store the drawn feature
        self.drawn_feature = feature
        
        # Show a confirmation to the user
        QMessageBox.information(
            self,
            "Area Selected",
            "Study area selection has been confirmed. You can now proceed with data download."
        )
    
    def cleanup_thread(self, worker):
        """Remove completed thread from active threads list"""
        if worker in self.active_threads:
            self.active_threads.remove(worker)