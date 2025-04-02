#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QProgressBar, QTreeWidget, QTreeWidgetItem, QSplitter,
                            QGroupBox, QComboBox, QCheckBox, QFileDialog, QFrame,
                            QPlainTextEdit, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

logger = logging.getLogger(__name__)

class ImageViewer(QLabel):
    """Widget for displaying and zooming images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setFrameShape(QFrame.Box)
        self.setStyleSheet("border: 1px solid #CCCCCC;")
        self.setScaledContents(False)
        self.original_pixmap = None
    
    def set_image(self, image_path):
        """Set the image to display"""
        if not image_path or not os.path.exists(image_path):
            self.setText("No image available")
            self.original_pixmap = None
            return
            
        # Load image
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            self.setText("Failed to load image")
            self.original_pixmap = None
            return
            
        # Scale pixmap to fit label while maintaining aspect ratio
        self.update_pixmap()
        
    def update_pixmap(self):
        """Update the displayed pixmap with proper scaling"""
        if not self.original_pixmap:
            return
            
        scaled_pixmap = self.original_pixmap.scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """Handle resize event to maintain proper image scaling"""
        super().resizeEvent(event)
        self.update_pixmap()

class VisualizationPanel(QWidget):
    """
    Panel for visualizing analysis results.
    Replicates the functionality of the visualization part of main.ipynb.
    """
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        # Store current image path
        self.current_image_path = None
        
        # Initialize UI
        self.init_ui()
        
        # Connect controller signals
        self.controller.visualization_controller.progress_updated.connect(self.update_progress)
        self.controller.visualization_controller.visualization_created.connect(self.on_vis_created)
        
        logger.info("Visualization Panel initialized")
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title_label = QLabel("Data Visualization")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Tree view and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Visualization settings
        settings_group = QGroupBox("Visualization Settings")
        settings_layout = QVBoxLayout()
        
        # Dataset selection
        dataset_layout = QHBoxLayout()
        dataset_label = QLabel("Dataset:")
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems([
            "All", "ERA5", "DAYMET", "PRISM", "CHIRPS", 
        "FLDAS", "GSMAP", "GLDAS"
        ])
        dataset_layout.addWidget(dataset_label)
        dataset_layout.addWidget(self.dataset_combo)
        
        # Visualization type
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Spatial Distribution",
            "Box Plots",
            "Time Series",
            "Seasonal Comparison",
            "Error Distribution",
            "Dataset Comparison",
            "Radar Comparison"
        ])
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        
        # Options
        options_layout = QHBoxLayout()
        self.high_res_checkbox = QCheckBox("High Resolution")
        self.high_res_checkbox.setChecked(True)
        
        options_layout.addWidget(self.high_res_checkbox)
        options_layout.addStretch()
        
        # Generate button
        self.generate_button = QPushButton("Generate Visualizations")
        self.generate_button.setMinimumHeight(40)
        
        settings_layout.addLayout(dataset_layout)
        settings_layout.addLayout(type_layout)
        settings_layout.addLayout(options_layout)
        settings_layout.addWidget(self.generate_button)
        
        settings_group.setLayout(settings_layout)
        left_layout.addWidget(settings_group)
        
        # File browser
        browser_group = QGroupBox("Visualization Files")
        browser_layout = QVBoxLayout()
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Visualizations"])
        self.file_tree.setColumnCount(1)
        self.file_tree.setMinimumWidth(250)
        
        refresh_button = QPushButton("Refresh")
        export_button = QPushButton("Export Selected")
        
        # Add to layout
        browser_layout.addWidget(self.file_tree)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addWidget(export_button)
        
        browser_layout.addLayout(buttons_layout)
        
        browser_group.setLayout(browser_layout)
        left_layout.addWidget(browser_group)
        
        # Progress bar
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_text = QPlainTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_text)
        
        left_layout.addLayout(progress_layout)
        
        # Add left panel to splitter
        splitter.addWidget(left_panel)
        
        # Right panel - Image viewer
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for different views
        view_tabs = QTabWidget()
        
        # Image view
        self.image_viewer = ImageViewer()
        view_tabs.addTab(self.image_viewer, "Image View")
        
        # Data view (for future implementation)
        data_view = QWidget()
        data_layout = QVBoxLayout(data_view)
        data_label = QLabel("Data visualization will be implemented in a future update.")
        data_label.setAlignment(Qt.AlignCenter)
        data_layout.addWidget(data_label)
        
        view_tabs.addTab(data_view, "Data View")
        
        # Add tabs to right panel
        right_layout.addWidget(view_tabs)
        
        # Add right panel to splitter
        splitter.addWidget(right_panel)
        
        # Set initial sizes for splitter
        splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Connect signals
        self.generate_button.clicked.connect(self.on_generate_clicked)
        self.file_tree.itemClicked.connect(self.on_file_selected)
        refresh_button.clicked.connect(self.refresh_file_tree)
        export_button.clicked.connect(self.on_export_clicked)
        
        # Initialize file tree
        self.refresh_file_tree()
    
    @pyqtSlot()
    def on_generate_clicked(self):
        """Handle generate visualizations button click"""
        try:
            # Disable generate button
            self.generate_button.setEnabled(False)
            self.generate_button.setText("Generating...")
            
            # Reset progress bar and status text
            self.progress_bar.setValue(0)
            self.status_text.clear()
            self.status_text.appendPlainText("Starting visualization generation...")
            
            # Get visualization settings
            settings = {
                'dataset': self.dataset_combo.currentText(),
                'type': self.type_combo.currentText(),
                'high_res': self.high_res_checkbox.isChecked()
            }
            
            logger.info(f"Generating visualizations with settings: {settings}")
            
            # Generate visualizations
            self.controller.visualization_controller.settings = settings
            self.controller.generate_visualizations()
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}", exc_info=True)
            self.controller.error_occurred.emit("Visualization Error", str(e))
            
            # Re-enable generate button
            self.generate_button.setEnabled(True)
            self.generate_button.setText("Generate Visualizations")
    
    @pyqtSlot()
    def refresh_file_tree(self):
        """Refresh the file tree with available visualizations"""
        try:
            self.file_tree.clear()
            
            plots_dir = Path(self.controller.plots_dir)
            if not plots_dir.exists():
                return
                
            # Add dataset folders
            for dataset_dir in plots_dir.glob('*'):
                if dataset_dir.is_dir():
                    dataset_item = QTreeWidgetItem(self.file_tree, [dataset_dir.name])
                    
                    # Add plot files
                    for plot_file in dataset_dir.glob('*.png'):
                        plot_item = QTreeWidgetItem(dataset_item, [plot_file.name])
                        plot_item.setData(0, Qt.UserRole, str(plot_file))
                    
                    dataset_item.setExpanded(True)
                    
            self.status_text.appendPlainText("Refreshed visualization files")
            
        except Exception as e:
            logger.error(f"Error refreshing file tree: {str(e)}", exc_info=True)
            self.status_text.appendPlainText(f"Error refreshing files: {str(e)}")
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_file_selected(self, item, column):
        """Handle file selection in the tree view"""
        # Check if item has file path data
        file_path = item.data(0, Qt.UserRole)
        if file_path:
            try:
                # Load and display image
                self.current_image_path = file_path
                self.image_viewer.set_image(file_path)
                self.status_text.appendPlainText(f"Loaded image: {file_path}")
                
            except Exception as e:
                logger.error(f"Error loading image: {str(e)}", exc_info=True)
                self.status_text.appendPlainText(f"Error loading image: {str(e)}")
    
    @pyqtSlot()
    def on_export_clicked(self):
        """Handle export button click"""
        if not self.current_image_path:
            self.status_text.appendPlainText("No image selected for export")
            return
            
        try:
            # Get save location
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Image",
                os.path.basename(self.current_image_path),
                "Images (*.png *.jpg)"
            )
            
            if save_path:
                # Copy file
                import shutil
                shutil.copy2(self.current_image_path, save_path)
                self.status_text.appendPlainText(f"Exported image to: {save_path}")
                
        except Exception as e:
            logger.error(f"Error exporting image: {str(e)}", exc_info=True)
            self.status_text.appendPlainText(f"Error exporting image: {str(e)}")
    
    @pyqtSlot(int)
    def update_progress(self, value):
        """Update the progress bar value"""
        self.progress_bar.setValue(value)
        
        # Re-enable generate button when complete
        if value >= 100:
            self.generate_button.setEnabled(True)
            self.generate_button.setText("Generate Visualizations")
    
    @pyqtSlot(str)
    def append_status(self, text):
        """Append text to the status text area"""
        self.status_text.appendPlainText(text)
        # Auto-scroll to bottom
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    @pyqtSlot(str)
    def on_vis_created(self, message):
        """Handle visualization creation event"""
        self.append_status(message)
        self.refresh_file_tree()
    
    def reset_ui(self):
        """Reset UI to default state"""
        # Reset combo boxes
        self.dataset_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        
        # Reset checkbox
        self.high_res_checkbox.setChecked(True)
        
        # Reset progress and status
        self.progress_bar.setValue(0)
        self.status_text.clear()
        
        # Reset image viewer
        self.image_viewer.setText("No image selected")
        self.image_viewer.original_pixmap = None
        self.current_image_path = None
        
        # Reset button
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Visualizations")
        
        # Refresh file tree
        self.refresh_file_tree()
        
        logger.info("Visualization panel UI reset")
    
    def on_dataset_selection_changed(self, index):
        """Handle dataset selection change in combo box"""
        dataset = self.dataset_combo.currentText()
        
        # Show temporal resolution note for FLDAS
        if dataset == "FLDAS":
            # Show warning in status text
            self.status_text.appendPlainText(
                "NOTE: FLDAS data is at monthly resolution. Visualizations represent "
                "monthly values, not daily values like other datasets."
            )
            
            # Also change the visualization options
            self.type_combo.clear()
            self.type_combo.addItems([
                "Monthly Comparison",
                "Seasonal Comparison",
                "Spatial Distribution",
                "Error Distribution"
            ])
        else:
            # Reset visualization options for daily datasets
            if self.type_combo.count() != 5:  # If we previously changed the options
                self.type_combo.clear()
                self.type_combo.addItems([
                    "Spatial Distribution",
                    "Box Plots",
                    "Time Series",
                    "Seasonal Comparison",
                    "Error Distribution"
                ])