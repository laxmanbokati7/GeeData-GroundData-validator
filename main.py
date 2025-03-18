#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui.app_window import ClimateDataApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("climate_data_fetcher.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Climate Data Fetcher application.
    Initializes and runs the PyQt application.
    """
    try:
        logger.info("Starting Climate Data Fetcher Application")
        
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("Climate Data Fetcher")
        app.setApplicationVersion("1.0.0")
        
        # Create and show the main window
        main_window = ClimateDataApp()
        main_window.show()
        
        # Start the event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()