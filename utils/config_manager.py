#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages application configuration storage and retrieval.
    """
    
    DEFAULT_CONFIG_DIR = Path.home() / ".climate_data_fetcher"
    DEFAULT_CONFIG_FILE = "config.json"
    
    @classmethod
    def get_config_path(cls, filename: Optional[str] = None) -> Path:
        """Get the path to the configuration file"""
        config_dir = cls.DEFAULT_CONFIG_DIR
        config_dir.mkdir(exist_ok=True, parents=True)
        
        if filename:
            return config_dir / filename
        else:
            return config_dir / cls.DEFAULT_CONFIG_FILE
    
    @classmethod
    def save_config(cls, config: Dict[str, Any], section: Optional[str] = None, 
                 filename: Optional[str] = None) -> bool:
        """
        Save configuration to a file
        
        Args:
            config: Configuration dictionary to save
            section: Optional section name to save under
            filename: Optional filename to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = cls.get_config_path(filename)
            
            # Load existing config if it exists
            if config_path.exists():
                with open(config_path, 'r') as f:
                    try:
                        existing_config = json.load(f)
                    except json.JSONDecodeError:
                        existing_config = {}
            else:
                existing_config = {}
            
            # Update config
            if section:
                if section not in existing_config:
                    existing_config[section] = {}
                existing_config[section].update(config)
            else:
                existing_config.update(config)
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
                
            logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    @classmethod
    def load_config(cls, section: Optional[str] = None, 
                 filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from a file
        
        Args:
            section: Optional section name to load
            filename: Optional filename to load from
            
        Returns:
            Configuration dictionary
        """
        try:
            config_path = cls.get_config_path(filename)
            
            if not config_path.exists():
                logger.info(f"Configuration file {config_path} does not exist")
                return {}
            
            with open(config_path, 'r') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in configuration file {config_path}")
                    return {}
            
            if section:
                return config.get(section, {})
            else:
                return config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}
    
    @classmethod
    def get_earth_engine_config(cls) -> Dict[str, Any]:
        """Get Earth Engine configuration"""
        return cls.load_config(section="earth_engine")
    
    @classmethod
    def save_earth_engine_config(cls, config: Dict[str, Any]) -> bool:
        """Save Earth Engine configuration"""
        return cls.save_config(config, section="earth_engine")
    
    @classmethod
    def get_app_config(cls) -> Dict[str, Any]:
        """Get application configuration"""
        return cls.load_config(section="app")
    
    @classmethod
    def save_app_config(cls, config: Dict[str, Any]) -> bool:
        """Save application configuration"""
        return cls.save_config(config, section="app")