#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Try to import Earth Engine
try:
    import ee
    EARTH_ENGINE_AVAILABLE = True
except ImportError:
    EARTH_ENGINE_AVAILABLE = False

class EarthEngineUtils:
    """Utility functions for Earth Engine operations"""
    
    @staticmethod
    def check_ee_initialized(project_id: Optional[str] = None) -> bool:
        """
        Check if Earth Engine is initialized or can be initialized
        
        Args:
            project_id: Optional project ID to use for initialization
            
        Returns:
            bool: True if Earth Engine is or can be initialized, False otherwise
        """
        if not EARTH_ENGINE_AVAILABLE:
            logger.error("Earth Engine API not available. Install with: pip install earthengine-api")
            return False
            
        try:
            # Try to use Earth Engine - will fail if not initialized
            ee.Number(1).getInfo()
            logger.info("Earth Engine already initialized")
            return True
        except Exception:
            # Not initialized, try to initialize
            try:
                if project_id:
                    logger.info(f"Initializing Earth Engine with project ID: {project_id}")
                    ee.Initialize(project=project_id)
                else:
                    logger.info("Initializing Earth Engine with default credentials")
                    ee.Initialize()
                
                # Test if initialization worked
                ee.Number(1).getInfo()
                logger.info("Earth Engine initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Earth Engine: {str(e)}")
                return False
                
    @staticmethod
    def check_auth_status() -> Dict[str, Any]:
        """
        Check Earth Engine authentication status
        
        Returns:
            Dict with authentication status information
        """
        result = {
            'available': EARTH_ENGINE_AVAILABLE,
            'authenticated': False,
            'error': None,
            'project_id': None
        }
        
        if not EARTH_ENGINE_AVAILABLE:
            result['error'] = "Earth Engine API not available"
            return result
            
        try:
            # Try to get the initialized status
            initialized = ee.data._initialized
            result['authenticated'] = initialized
            
            if initialized:
                # Try to get project info
                try:
                    # This might not always work depending on EE version
                    # and authentication method
                    info = ee.data.getProjectsInfo()
                    if info:
                        result['project_id'] = info[0]['name']
                except:
                    # Fall back to simple test
                    test = ee.Number(1).getInfo()
                    result['authenticated'] = test == 1
            
            return result
        except Exception as e:
            result['error'] = str(e)
            return result
            
    @staticmethod
    def authenticate(project_id: Optional[str] = None) -> bool:
        """
        Trigger Earth Engine authentication
        
        Args:
            project_id: Optional project ID to use
            
        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        if not EARTH_ENGINE_AVAILABLE:
            logger.error("Earth Engine API not available. Install with: pip install earthengine-api")
            return False
            
        try:
            # Try to authenticate
            if project_id:
                ee.Authenticate(project=project_id)
            else:
                ee.Authenticate()
                
            return EarthEngineUtils.check_ee_initialized(project_id)
        except Exception as e:
            logger.error(f"Earth Engine authentication failed: {str(e)}")
            return False
            
    @staticmethod
    def get_available_collections() -> List[str]:
        """
        Get list of available Earth Engine collections
        
        Returns:
            List of collection names
        """
        if not EarthEngineUtils.check_ee_initialized():
            return []
            
        try:
            # This isn't directly available in the EE API
            # We'll return some common ones used in the application
            return [
                "ECMWF/ERA5_LAND/DAILY_AGGR",
                "NASA/ORNL/DAYMET_V4",
                "OREGONSTATE/PRISM/AN81d",
            ]
        except Exception as e:
            logger.error(f"Error getting collections: {str(e)}")
            return []