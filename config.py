from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DataConfig:
    """Base configuration for data fetching"""
    start_year: int = 1980
    end_year: int = 2024
    data_dir: str = "Data"
    
    def __post_init__(self):
        if self.end_year < self.start_year:
            raise ValueError("end_year must be greater than or equal to start_year")
        if self.start_year < 1980 or self.end_year > 2024:
            raise ValueError("Years must be between 1980 and 2024")
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)

@dataclass
class GroundDataConfig(DataConfig):
    """Configuration for ground data fetching"""
    states: Optional[List[str]] = None  # None means entire US
    metadata_filename: str = "stations_metadata.csv"
    data_filename: str = "ground_daily_precipitation.csv"

    def get_metadata_path(self) -> str:
        return str(Path(self.data_dir) / self.metadata_filename)

    def get_data_path(self) -> str:
        return str(Path(self.data_dir) / self.data_filename)

@dataclass
class GriddedDatasetConfig:
    """Configuration for a single gridded dataset"""
    name: str
    collection_name: str
    variable_name: str
    conversion_factor: float = 1.0
    enabled: bool = False

    def get_filename(self) -> str:
        return f"{self.name.lower()}_precipitation.csv"

@dataclass
class GriddedDataConfig(DataConfig):
    """Configuration for gridded data fetching"""
    datasets: Dict[str, GriddedDatasetConfig] = None
    ee_project_id: str = "ee-sauravbhattarai1999"  # Default project ID
    
    def __post_init__(self):
        super().__post_init__()
        if self.datasets is None:
            self.datasets = {
                'ERA5': GriddedDatasetConfig(
                    name='ERA5',
                    collection_name="ECMWF/ERA5_LAND/DAILY_AGGR",
                    variable_name="total_precipitation_sum",
                    conversion_factor=1000  # Convert to mm
                ),
                'DAYMET': GriddedDatasetConfig(
                    name='DAYMET',
                    collection_name="NASA/ORNL/DAYMET_V4",
                    variable_name="prcp"
                ),
                'PRISM': GriddedDatasetConfig(
                    name='PRISM',
                    collection_name="OREGONSTATE/PRISM/AN81d",
                    variable_name="ppt"
                )
            }

    def get_enabled_datasets(self) -> List[GriddedDatasetConfig]:
        return [ds for ds in self.datasets.values() if ds.enabled]

    def is_valid(self) -> bool:
        return any(ds.enabled for ds in self.datasets.values())