#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                            QGroupBox, QRadioButton, QSlider, QListWidget, 
                            QListWidgetItem, QPushButton, QProgressBar, QCheckBox,
                            QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)

class DataSelectionPanel(QWidget):
    """
    Panel for selecting and downloading climate data.
    Replicates the functionality of the data selection part of main.ipynb.
    """
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
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
        state_group = QGroupBox("State Selection")
        state_layout = QVBoxLayout()
        
        self.rb_all_states = QRadioButton("All US States")
        self.rb_specific_states = QRadioButton("Select specific states")
        self.rb_all_states.setChecked(True)  # Default selection
        
        self.state_list = QListWidget()
        self.state_list.setEnabled(False)
        self.state_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Add states to list
        for code, name in self.us_states.items():
            item = QListWidgetItem(f"{code} - {name}")
            self.state_list.addItem(item)
        
        state_layout.addWidget(self.rb_all_states)
        state_layout.addWidget(self.rb_specific_states)
        state_layout.addWidget(self.state_list)
        
        state_group.setLayout(state_layout)
        scroll_layout.addWidget(state_group)
        
        # Connect signals
        self.rb_all_states.toggled.connect(self.on_state_scope_changed)
        self.rb_specific_states.toggled.connect(self.on_state_scope_changed)
        
        # 4. Gridded Dataset Selection
        gridded_group = QGroupBox("Gridded Datasets")
        gridded_layout = QVBoxLayout()
        
        self.cb_era5 = QCheckBox("ERA5")
        self.cb_daymet = QCheckBox("DAYMET")
        self.cb_prism = QCheckBox("PRISM")
        
        # Select all by default
        self.cb_era5.setChecked(True)
        self.cb_daymet.setChecked(True)
        self.cb_prism.setChecked(True)
        
        gridded_layout.addWidget(self.cb_era5)
        gridded_layout.addWidget(self.cb_daymet)
        gridded_layout.addWidget(self.cb_prism)
        
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
            
            # Get data configuration
            data_config = {
                'data_type': self.get_data_type(),
                'start_year': self.start_year_slider.value(),
                'end_year': self.end_year_slider.value(),
                'states': self.get_selected_states(),
                'gridded_datasets': self.get_selected_datasets(),
                'ee_project_id': getattr(self.controller, 'ee_config', {}).get('ee_project_id', "ee-sauravbhattarai1999")
            }
            
            logger.info(f"Starting data download with config: {data_config}")
            
            # Start data fetching
            self.controller.fetch_data(data_config)
            
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
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Reset download button
        self.download_button.setEnabled(True)
        self.download_button.setText("Download Data")
        
        logger.info("UI reset to default state")