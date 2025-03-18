import sys
import os
from PyQt5.QtWidgets import (QApplication, QPushButton, QVBoxLayout, QWidget, 
                            QLabel, QProgressBar, QTextEdit, QMainWindow)
from PyQt5.QtCore import Qt, QTimer

# Add the current directory to system path to find modules
sys.path.append(os.getcwd())

# Try importing the controller
try:
    from controller.app_controller import AppController
    from controller.analysis_controller import AnalysisController
except ImportError as e:
    print(f"Error importing controllers: {e}")
    sys.exit(1)

class AnalysisRunnerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Climate Data Fetcher - Analysis Runner")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Climate Data Analysis Runner")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Add description
        desc = QLabel("This tool will run the analysis on your downloaded climate data.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Add status
        self.status_label = QLabel("Ready to run analysis...")
        layout.addWidget(self.status_label)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Add log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Add run button
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)
        
        # Initialize controller
        self.controller = AppController()
        
        # Connect signals
        self.controller.status_updated.connect(self.update_status)
        self.controller.analysis_controller.progress_updated.connect(self.update_progress)
        self.controller.analysis_completed.connect(self.on_analysis_completed)
        
        self.log("Application initialized")
        
    def log(self, message):
        """Add message to log area"""
        self.log_area.append(message)
        
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
        self.log(message)
        
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        
    def on_analysis_completed(self):
        """Handle analysis completion"""
        self.log("Analysis completed successfully!")
        self.run_button.setEnabled(True)
        self.run_button.setText("Run Analysis Again")
        
    def run_analysis(self):
        """Run the analysis"""
        try:
            # Check if data is available
            if not self.controller.is_data_available():
                self.log("Error: No data available for analysis")
                self.status_label.setText("Error: No data available for analysis")
                return
                
            self.log("Starting analysis...")
            self.status_label.setText("Running analysis...")
            self.progress_bar.setValue(0)
            self.run_button.setEnabled(False)
            self.run_button.setText("Analysis in progress...")
            
            # Run analysis
            QTimer.singleShot(100, self.controller.run_analysis)
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.run_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnalysisRunnerWindow()
    window.show()
    sys.exit(app.exec_())