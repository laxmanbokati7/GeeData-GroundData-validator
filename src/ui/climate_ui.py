import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import pandas as pd

from config import GroundDataConfig, GriddedDataConfig
from src.data.ground_fetcher import GroundDataFetcher
from src.data.gridded_fetcher import GriddedDataFetcher
from utils.utils import validate_states, print_summary, compare_datasets

class ClimateDataUI:
    """
    Class to handle the Climate Data Fetcher UI and interactions
    """
    def __init__(self):
        # Create all the widgets
        self._create_widgets()
        
        # Set up widget interactions
        self._setup_interactions()
        
    def _create_widgets(self):
        """Create all the UI widgets"""
        # Create data type selector
        self.data_type_widget = widgets.RadioButtons(
            options=[('Ground data only', 'ground'),
                    ('Gridded data only', 'gridded'),
                    ('Both', 'both')],
            description='Data Type:',
            style={'description_width': 'initial'}
        )

        # Create state selection widgets
        self.state_scope_widget = widgets.RadioButtons(
            options=[('All US States', 'all'),
                    ('Select specific states', 'specific')],
            description='States:',
            style={'description_width': 'initial'}
        )

        # List of US states
        self.us_states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming'
        }

        self.state_selector = widgets.SelectMultiple(
            options=[(f"{code} - {name}", code) for code, name in self.us_states.items()],
            rows=10,
            description='Select States:',
            disabled=True,
            style={'description_width': 'initial'}
        )

        # Create year range widgets
        self.start_year = widgets.IntSlider(
            value=1980,
            min=1980,
            max=2024,
            description='Start Year:',
            style={'description_width': 'initial'}
        )

        self.end_year = widgets.IntSlider(
            value=2024,
            min=1980,
            max=2024,
            description='End Year:',
            style={'description_width': 'initial'}
        )

        # Create gridded dataset selection
        self.gridded_datasets = widgets.SelectMultiple(
            options=[('ERA5', 'ERA5'),
                    ('DAYMET', 'DAYMET'),
                    ('PRISM', 'PRISM')],
            rows=3,
            description='Datasets:',
            disabled=True,
            style={'description_width': 'initial'}
        )

        # Create download button
        self.download_button = widgets.Button(
            description='Download Data',
            button_style='primary',
            style={'description_width': 'initial'}
        )

        # Create output area for results and messages
        self.output_area = widgets.Output()
        
    def _setup_interactions(self):
        """Set up the widget interactions"""
        # State scope change listener
        self.state_scope_widget.observe(self._on_state_scope_change, names='value')
        
        # Data type change listener
        self.data_type_widget.observe(self._on_data_type_change, names='value')
        
        # Download button click handler
        self.download_button.on_click(self._on_download_button_click)
    
    def _on_state_scope_change(self, change):
        """Handle state scope widget change"""
        if change['new'] == 'specific':
            self.state_selector.disabled = False
        else:
            self.state_selector.disabled = True
    
    def _on_data_type_change(self, change):
        """Handle data type widget change"""
        if change['new'] in ['gridded', 'both']:
            self.gridded_datasets.disabled = False
        else:
            self.gridded_datasets.disabled = True
    
    def _on_download_button_click(self, b):
        """Handle download button click"""
        with self.output_area:
            clear_output()
            
            # Validate inputs
            if self.end_year.value < self.start_year.value:
                print("Error: End year must be greater than or equal to start year")
                return
                
            # Get states
            states = None
            if self.state_scope_widget.value == 'specific':
                states = list(self.state_selector.value)
                if not states:
                    print("Error: Please select at least one state")
                    return
            
            # Process ground data if requested
            results = {}
            if self.data_type_widget.value in ['ground', 'both']:
                print("Processing ground data...")
                config = GroundDataConfig(
                    states=states,
                    start_year=self.start_year.value,
                    end_year=self.end_year.value
                )
                try:
                    fetcher = GroundDataFetcher(config)
                    ground_data = fetcher.process()
                    results['Ground'] = ground_data
                    print("Ground data processing complete")
                except Exception as e:
                    print(f"Error processing ground data: {e}")
            
            # Process gridded data if requested
            if self.data_type_widget.value in ['gridded', 'both']:
                print("\nProcessing gridded data...")
                config = GriddedDataConfig(
                    start_year=self.start_year.value,
                    end_year=self.end_year.value
                )
                
                # Enable selected datasets
                selected_datasets = list(self.gridded_datasets.value)
                for name, dataset in config.datasets.items():
                    dataset.enabled = name in selected_datasets
                
                if config.is_valid():
                    try:
                        fetcher = GriddedDataFetcher(config)
                        gridded_results = fetcher.process()
                        results.update(gridded_results)
                        print("Gridded data processing complete")
                    except Exception as e:
                        print(f"Error processing gridded data: {e}")
                else:
                    print("No gridded datasets selected")
            
            # Show results summary
            if results:
                print("\nResults Summary:")
                comparison = compare_datasets(results)
                display(comparison)
            else:
                print("\nNo data was processed successfully")
    
    def display(self):
        """Display the UI"""
        display(HTML("<h2>Climate Data Fetcher</h2>"))
        display(widgets.VBox([
            self.data_type_widget,
            widgets.HBox([self.start_year, self.end_year]),
            self.state_scope_widget,
            self.state_selector,
            self.gridded_datasets,
            self.download_button,
            self.output_area
        ]))