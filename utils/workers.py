# Add to utils/workers.py

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import logging
import pandas as pd
from typing import Dict, Any, Optional
from utils.huc_utils import HUCDataProvider

logger = logging.getLogger(__name__)

class HUCLoadWorker(QThread):
    """Worker thread for loading HUC metadata"""
    
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(dict)  # Emits region-grouped HUC data
    failed = pyqtSignal(Exception)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_id = None
        
    def set_project_id(self, project_id):
        """Set the project ID for the worker"""
        self.project_id = project_id
    
    def run(self):
        """Run the worker"""
        try:
            # Update progress
            self.progress_updated.emit(10)
            
            # Create HUC provider
            provider = HUCDataProvider(project_id=self.project_id)
            
            # Fetch metadata
            self.progress_updated.emit(30)
            
            try:
                # When loading existing metadata, ensure HUC IDs are strings
                metadata = provider.fetch_huc_metadata(force_refresh=False)
                # Convert huc_id column to string if it exists and isn't already
                if 'huc_id' in metadata.columns and metadata['huc_id'].dtype != 'object':
                    metadata['huc_id'] = metadata['huc_id'].astype(str)
            except Exception as e:
                logger.error(f"Error loading metadata: {str(e)}", exc_info=True)
                self.failed.emit(e)
                return
            
            # Group by region (first 2 digits of HUC code)
            self.progress_updated.emit(60)
            regions = {}
            
            for _, row in metadata.iterrows():
                # Ensure huc_id is a string before slicing
                huc_id = str(row['huc_id'])
                region_id = huc_id[:2]
                
                # Create region name based on ID ranges
                if region_id not in regions:
                    region_name = f"Region {region_id} ({huc_id[:2]}XX)"
                    regions[region_id] = {}
                
                # Add HUC to region
                regions[region_id][huc_id] = {
                    'name': row['name'],
                    'states': row['states'],
                    'area_sqkm': float(row['area_sqkm']) if isinstance(row['area_sqkm'], (int, float, str)) else row['area_sqkm']
                }
            
            # Sort regions by ID
            sorted_regions = {}
            for region_id in sorted(regions.keys()):
                region_name = f"Region {region_id} ({region_id}XX)"
                sorted_regions[region_name] = regions[region_id]
            
            # Complete
            self.progress_updated.emit(100)
            self.finished.emit(sorted_regions)
            
        except Exception as e:
            logger.error(f"Error in HUC data loading: {str(e)}", exc_info=True)
            self.failed.emit(e)

class HUCBoundaryWorker(QThread):
    """Worker thread for loading a HUC boundary"""
    
    finished = pyqtSignal()
    failed = pyqtSignal(Exception)
    
    def __init__(self, huc_id, project_id=None):
        super().__init__()
        self.huc_id = huc_id
        self.project_id = project_id
    
    def set_project_id(self, project_id):
        """Set the project ID for the worker"""
        self.project_id = project_id
    
    def run(self):
        """Run the worker"""
        try:
            # Create HUC provider with project ID
            provider = HUCDataProvider(project_id=self.project_id)
            
            # Fetch boundary with simplification
            boundary = provider.get_huc_boundary(self.huc_id, simplify_tolerance=0.01)
            
            if boundary is None:
                raise ValueError(f"Failed to fetch boundary for HUC {self.huc_id}")
                
            # Complete
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"Error loading HUC boundary: {str(e)}", exc_info=True)
            self.failed.emit(e)