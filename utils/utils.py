from typing import List, Dict, Any
from pathlib import Path
import pandas as pd

def validate_states(states: List[str]) -> bool:
    """Validate state codes"""
    valid_states = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    return all(state in valid_states for state in states)

def check_data_exists(data_dir: str, filenames: List[str]) -> bool:
    """Check if all specified files exist in the data directory"""
    data_path = Path(data_dir)
    return all((data_path / filename).exists() for filename in filenames)

def load_data(data_dir: str, filename: str) -> pd.DataFrame:
    """Load data from CSV file with proper datetime handling"""
    file_path = Path(data_dir) / filename
    
    # First load without parsing dates
    df = pd.read_csv(file_path)
    
    # Then convert date column to datetime after loading
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    return df

def get_data_summary(data: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for a dataset"""
    return {
        'shape': data.shape,
        'time_range': (data.index.min(), data.index.max()),
        'missing_values': data.isna().sum().sum(),
        'stations': data.columns.tolist(),
        'total_stations': len(data.columns)
    }

def print_summary(name: str, summary: Dict[str, Any]) -> None:
    """Print summary statistics in a formatted way"""
    print(f"\n{name} Dataset Summary:")
    print(f"Shape: {summary['shape']}")
    print(f"Time Range: {summary['time_range'][0]} to {summary['time_range'][1]}")
    print(f"Number of Stations: {summary['total_stations']}")
    print(f"Total Missing Values: {summary['missing_values']}")

def compare_datasets(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compare multiple datasets"""
    comparisons = []
    for name, data in datasets.items():
        stats = {
            'Dataset': name,
            'Rows': data.shape[0],
            'Stations': data.shape[1],
            'Start Date': data.index.min(),
            'End Date': data.index.max(),
            'Missing (%)': (data.isna().sum().sum() / (data.shape[0] * data.shape[1])) * 100
        }
        comparisons.append(stats)
    
    return pd.DataFrame(comparisons)