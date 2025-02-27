from typing import Tuple, Dict, Optional
import click
from pathlib import Path
import pandas as pd

from config import GroundDataConfig, GriddedDataConfig
from src.ground_fetcher import GroundDataFetcher
from src.gridded_fetcher import GriddedDataFetcher
from utils import validate_states, check_data_exists, print_summary, compare_datasets

def get_data_type() -> str:
    """Get data type selection from user"""
    options = {
        '1': 'ground',
        '2': 'gridded',
        '3': 'both'
    }
    
    while True:
        choice = input("""
What type of data would you like to fetch?
1. Ground data only
2. Gridded data only
3. Both ground and gridded data
Enter choice (1-3): """).strip()
        
        if choice in options:
            return options[choice]
        print("Invalid choice. Please enter 1, 2, or 3.")

def get_states() -> Optional[list]:
    """Get state selection from user"""
    while True:
        choice = input("""
Would you like to fetch data for:
1. All US states
2. Specific states
Enter choice (1-2): """).strip()
        
        if choice == '1':
            return None
        elif choice == '2':
            states = input("\nEnter state codes separated by commas (e.g., NY,CA,TX): ").strip()
            states = [s.strip().upper() for s in states.split(',')]
            if validate_states(states):
                return states
            print("Invalid state codes. Please try again.")
        else:
            print("Invalid choice. Please enter 1 or 2.")

def get_gridded_datasets(config: GriddedDataConfig) -> None:
    """Get gridded dataset selection from user"""
    print("\nWhich gridded datasets would you like to use?")
    for name, dataset in config.datasets.items():
        choice = input(f"Include {name}? (y/n): ").lower().strip()
        dataset.enabled = choice.startswith('y')

def get_year_range() -> Tuple[int, int]:
    """Get year range from user"""
    while True:
        try:
            start_year = int(input("\nEnter start year (1980-2024): "))
            end_year = int(input("Enter end year (1980-2024): "))
            if 1980 <= start_year <= end_year <= 2024:
                return start_year, end_year
            print("Invalid year range. Please ensure start_year <= end_year and both are between 1980-2024.")
        except ValueError:
            print("Please enter valid years as numbers.")

def process_ground_data(config: GroundDataConfig) -> Optional[pd.DataFrame]:
    """Process ground data"""
    fetcher = GroundDataFetcher(config)
    try:
        data = fetcher.process()
        summary = get_summary(data)
        print_summary("Ground", summary)
        return data
    except Exception as e:
        print(f"Error processing ground data: {e}")
        return None

def process_gridded_data(config: GriddedDataConfig) -> Dict[str, pd.DataFrame]:
    """Process gridded data"""
    fetcher = GriddedDataFetcher(config)
    try:
        return fetcher.process()
    except Exception as e:
        print(f"Error processing gridded data: {e}")
        return {}

@click.command()
@click.option('--data-dir', default='Data', help='Directory for data storage')
def main(data_dir: str):
    """Main function to run the data fetcher"""
    print("Welcome to Climate Data Fetcher!")
    
    # Get user input
    data_type = get_data_type()
    states = get_states()
    start_year, end_year = get_year_range()
    
    # Initialize results dictionary
    results = {}
    
    # Process ground data if requested
    if data_type in ['ground', 'both']:
        config = GroundDataConfig(
            states=states,
            start_year=start_year,
            end_year=end_year,
            data_dir=data_dir
        )
        ground_data = process_ground_data(config)
        if ground_data is not None:
            results['Ground'] = ground_data
    
    # Process gridded data if requested
    if data_type in ['gridded', 'both']:
        config = GriddedDataConfig(
            start_year=start_year,
            end_year=end_year,
            data_dir=data_dir
        )
        get_gridded_datasets(config)
        
        if config.is_valid():
            gridded_results = process_gridded_data(config)
            results.update(gridded_results)
        else:
            print("No gridded datasets selected.")
    
    # Compare results if multiple datasets
    if len(results) > 1:
        print("\nDataset Comparison:")
        comparison = compare_datasets(results)
        print(comparison.to_string(index=False))

if __name__ == '__main__':
    main()