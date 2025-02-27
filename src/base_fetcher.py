from abc import ABC, abstractmethod
from typing import Dict, Optional, Union
import pandas as pd

class DataFetcher(ABC):
    """Abstract base class for all data fetchers"""
    
    @abstractmethod
    def fetch_data(self) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Fetch data according to configuration"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> bool:
        """Validate fetched data"""
        pass
    
    @abstractmethod
    def save_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], path: str) -> None:
        """Save data to specified path"""
        pass

class MetadataProvider(ABC):
    """Abstract base class for metadata providers"""
    
    @abstractmethod
    def get_metadata(self) -> pd.DataFrame:
        """Get metadata for stations/points"""
        pass
    
    @abstractmethod
    def save_metadata(self, metadata: pd.DataFrame, path: str) -> None:
        """Save metadata to specified path"""
        pass

    @abstractmethod
    def load_metadata(self, path: str) -> pd.DataFrame:
        """Load metadata from specified path
        
        Note: When implementing this method, do not use parse_dates in pd.read_csv.
        Instead, load the CSV first, then convert date columns using pd.to_datetime.
        """
        pass