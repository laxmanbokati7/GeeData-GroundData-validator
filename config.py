from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
@dataclass
class AnalysisConfig:
    """
    Configuration for data analysis and filtering
    
    The filtering is 'direction-aware' - it only filters in the 'bad' direction:
    - For metrics where higher is better (R², NSE), only filters low values
    - For metrics where lower is better (RMSE, MAE), only filters high values
    
    This preserves stations with good performance metrics (high R², low RMSE)
    while removing only problematic outliers.
    """
    # Filtering settings
    filter_extremes: bool = True  # Whether to filter extreme values
    lower_percentile: float = 1.0  # Lower percentile threshold 
    upper_percentile: float = 99.0  # Upper percentile threshold
    # Which metrics to filter (None means all numeric columns)
    metrics_to_filter: Optional[List[str]] = None
    
    def __post_init__(self):
        # Validate percentile values
        if not 0 <= self.lower_percentile < self.upper_percentile <= 100:
            raise ValueError("Invalid percentile range: must have 0 <= lower < upper <= 100")
        
        # Default metrics to filter if not specified
        if self.metrics_to_filter is None:
            self.metrics_to_filter = [
                'r2', 'rmse', 'bias', 'mae', 'nse', 'pbias', 
                'rel_bias', 'rel_rmse', 'corr'
            ]

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
    huc_id: Optional[str] = None  # None means all HUCs
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
    time_scale: str = "daily"  # Added: daily, hourly, 3hourly, monthly
    date_range: Optional[Tuple[int, Optional[int]]] = None

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
                ),
                'CHIRPS': GriddedDatasetConfig(
                    name='CHIRPS',
                    collection_name="UCSB-CHG/CHIRPS/DAILY",
                    variable_name="precipitation",
                    time_scale="daily",
                    # Already in mm/day, no conversion needed
                ),
                'FLDAS': GriddedDatasetConfig(
                    name='FLDAS',
                    collection_name="NASA/FLDAS/NOAH01/C/GL/M/V001",
                    variable_name="Rainf_f_tavg",
                    conversion_factor=86400,  # Convert kg/m²/s to mm/day
                    time_scale="monthly"
                ),
                'GSMAP': GriddedDatasetConfig(
                    name='GSMAP',
                    collection_name="JAXA/GPM_L3/GSMaP/v8/operational",
                    variable_name="hourlyPrecipRateGC",
                    conversion_factor=1.0,  
                    time_scale="hourly"
                ),
                'GLDAS-Historical': GriddedDatasetConfig(
                    name='GLDAS-Historical',
                    collection_name="NASA/GLDAS/V20/NOAH/G025/T3H",
                    variable_name="Rainf_f_tavg",
                    conversion_factor=86400,  # Convert kg/m²/s to mm/day
                    time_scale="3-hourly",
                    date_range=(1948, 2014)
                ),
                'GLDAS-Current': GriddedDatasetConfig(
                    name='GLDAS-Current',
                    collection_name="NASA/GLDAS/V021/NOAH/G025/T3H",
                    variable_name="Rainf_f_tavg",
                    conversion_factor=86400,  # Convert kg/m²/s to mm/day
                    time_scale="3-hourly",
                    date_range=(2000, None)
                )
            }

    def get_enabled_datasets(self) -> List[GriddedDatasetConfig]:
        return [ds for ds in self.datasets.values() if ds.enabled]

    def is_valid(self) -> bool:
        return any(ds.enabled for ds in self.datasets.values())