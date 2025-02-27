import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from utils.plotting_utils import (
    load_metadata,
    load_stats_file,
    create_spatial_figure,
    create_boxplots,
    create_seasonal_comparison,
    get_plot_parameters
)

class ResultPlotter:
    """Class to generate plots for all results"""
    
    def __init__(self, data_dir: str = 'Data', results_dir: str = 'Results'):
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.plots_dir = Path('Plots')
        self.metadata = None
        
    def setup(self):
        """Setup necessary directories and load metadata"""
        self.plots_dir.mkdir(exist_ok=True)
        self.metadata = load_metadata(self.data_dir)
        print("Metadata loaded successfully")
        
    def process_regular_stats(self, dataset_dir: Path, dataset_plots_dir: Path):
        """Process regular statistics files (daily, monthly, yearly)"""
        for stats_file in dataset_dir.glob('*_stats.csv'):
            if 'seasonal' not in stats_file.name:
                stats_type = stats_file.stem.replace('_stats', '')
                print(f"Creating plots for {stats_type} statistics...")
                
                try:
                    # Load statistics
                    stats_df = load_stats_file(stats_file)
                    parameters = get_plot_parameters(stats_type)
                    
                    # Create spatial plots
                    fig_spatial = create_spatial_figure(
                        stats_df,
                        self.metadata,
                        parameters,
                        f"{dataset_dir.name} - {stats_type.title()} Statistics"
                    )
                    fig_spatial.savefig(
                        dataset_plots_dir / f'{stats_type}_spatial.png',
                        bbox_inches='tight',
                        dpi=300
                    )
                    plt.close(fig_spatial)
                    
                    # Create box plots
                    fig_box = create_boxplots(
                        stats_df,
                        parameters,
                        'station',
                        f"{dataset_dir.name} - {stats_type.title()} Statistics Distribution"
                    )
                    fig_box.savefig(
                        dataset_plots_dir / f'{stats_type}_boxplot.png',
                        bbox_inches='tight',
                        dpi=300
                    )
                    plt.close(fig_box)
                    
                except Exception as e:
                    print(f"Error processing {stats_file}: {str(e)}")
    
    def process_seasonal_stats(self, dataset_dir: Path, dataset_plots_dir: Path):
        """Process seasonal statistics"""
        seasonal_file = dataset_dir / 'seasonal_stats.csv'
        if seasonal_file.exists():
            print("Creating seasonal plots...")
            try:
                # Load seasonal statistics
                stats_df = pd.read_csv(seasonal_file)
                parameters = get_plot_parameters('seasonal')
                
                # Create seasonal comparison plots
                fig_seasonal = create_seasonal_comparison(
                    stats_df,
                    parameters,
                    dataset_dir.name
                )
                fig_seasonal.savefig(
                    dataset_plots_dir / 'seasonal_comparison.png',
                    bbox_inches='tight',
                    dpi=300
                )
                plt.close(fig_seasonal)
                
                # Create spatial plots for each season
                for season in ['Winter', 'Spring', 'Summer', 'Fall']:
                    season_stats = stats_df[stats_df['season'] == season]
                    if not season_stats.empty:
                        fig_spatial = create_spatial_figure(
                            season_stats,
                            self.metadata,
                            parameters,
                            f"{dataset_dir.name} - {season} Statistics"
                        )
                        fig_spatial.savefig(
                            dataset_plots_dir / f'seasonal_{season.lower()}_spatial.png',
                            bbox_inches='tight',
                            dpi=300
                        )
                        plt.close(fig_spatial)
                
            except Exception as e:
                print(f"Error processing seasonal stats: {str(e)}")
    
    def process_dataset(self, dataset_dir: Path):
        """Process all statistics files for a dataset"""
        dataset_name = dataset_dir.name
        print(f"\nProcessing {dataset_name}...")
        
        # Create dataset plots directory
        dataset_plots_dir = self.plots_dir / dataset_name
        dataset_plots_dir.mkdir(exist_ok=True)
        
        # Process regular statistics
        self.process_regular_stats(dataset_dir, dataset_plots_dir)
        
        # Process seasonal statistics
        self.process_seasonal_stats(dataset_dir, dataset_plots_dir)
    
    def run(self):
        """Run plotting for all datasets"""
        print("Starting plot generation...")
        
        try:
            self.setup()
            
            for dataset_dir in self.results_dir.glob('*'):
                if dataset_dir.is_dir():
                    self.process_dataset(dataset_dir)
            
            print("\nPlot generation complete!")
            
        except Exception as e:
            print(f"Error during plot generation: {str(e)}")
            raise