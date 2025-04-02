from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx
import geopandas as gpd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def load_metadata(data_dir: str) -> pd.DataFrame:
    """Load station metadata with coordinates"""
    metadata = pd.read_csv(Path(data_dir) / 'stations_metadata.csv')
    return metadata.set_index('id')

def load_stats_file(file_path: Path) -> pd.DataFrame:
    """Load statistics file and ensure consistent format"""
    df = pd.read_csv(file_path)
    if 'station' in df.columns:
        df.set_index('station', inplace=True)
    return df

def create_spatial_figure(stats_df: pd.DataFrame, metadata_df: pd.DataFrame, 
                        parameters: List[str], title: str) -> plt.Figure:
    """Create spatial distribution plots for multiple parameters"""
    # Number of rows needed (2 parameters per row)
    n_rows = (len(parameters) + 1) // 2
    
    # Create figure
    fig, axes = plt.subplots(n_rows, 2, figsize=(10, 3*n_rows))
    fig.suptitle(title, fontsize=16, y=1.02)
    
    # Flatten axes if needed
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    # Create GeoDataFrame
    gdf = metadata_df.copy()
    gdf = gpd.GeoDataFrame(
        gdf, 
        geometry=gpd.points_from_xy(gdf.longitude, gdf.latitude),
        crs="EPSG:4326"
    )
    
    # Convert to Web Mercator for contextily
    gdf = gdf.to_crs(epsg=3857)
    
    # Plot each parameter
    for idx, param in enumerate(parameters):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        if param in stats_df.columns:
            # Merge statistics with locations
            gdf[param] = stats_df[param]
            
            # Create scatter plot
            scatter = gdf.plot(
                column=param,
                ax=ax,
                legend=True,
                legend_kwds={'label': param},
                cmap='viridis',
                markersize=50
            )
            
            # Add contextily basemap
            ctx.add_basemap(
                ax, 
                source=ctx.providers.CartoDB.Positron,
                zoom=4
            )
            
            ax.set_title(param)
            ax.axis('off')
        else:
            ax.remove()
    
    # Remove any empty subplots
    for idx in range(len(parameters), n_rows*2):
        row = idx // 2
        col = idx % 2
        axes[row, col].remove()
    
    plt.tight_layout()
    return fig

def create_latitude_correlation(stats_df: pd.DataFrame, metadata_df: pd.DataFrame,
                              parameters: List[str], title: str) -> plt.Figure:
    """Create correlation plots with latitude"""
    # Number of rows needed (2 parameters per row)
    n_rows = (len(parameters) + 1) // 2
    
    # Create figure
    fig, axes = plt.subplots(n_rows, 2, figsize=(15, 5*n_rows))
    fig.suptitle(f"{title} - Latitude Correlation", fontsize=16, y=1.02)
    
    # Flatten axes if needed
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    # Plot each parameter
    for idx, param in enumerate(parameters):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        if param in stats_df.columns:
            # Merge data
            merged = pd.DataFrame({
                'latitude': metadata_df.latitude,
                param: stats_df[param]
            }).dropna()
            
            # Create scatter plot
            sns.regplot(
                data=merged,
                x='latitude',
                y=param,
                ax=ax,
                scatter_kws={'alpha': 0.5}
            )
            
            # Calculate correlation
            corr = merged.corr().iloc[0, 1]
            ax.set_title(f"{param} (r = {corr:.3f})")
            
        else:
            ax.remove()
    
    # Remove any empty subplots
    for idx in range(len(parameters), n_rows*2):
        row = idx // 2
        col = idx % 2
        axes[row, col].remove()
    
    plt.tight_layout()
    return fig

def get_plot_parameters(stats_type: str) -> List[str]:
    """Get list of parameters to plot based on statistics type"""
    common_params = ['r2', 'rmse', 'bias', 'mae', 'nse', 'pbias']
    
    if stats_type == 'daily':
        return common_params
    elif stats_type in ['monthly', 'yearly']:
        return common_params
    elif stats_type in ['low_extreme', 'high_extreme']:
        return common_params
    else:
        return common_params
    
def create_boxplots(stats_df: pd.DataFrame, parameters: List[str], 
                   group_by: Optional[str] = None, title: str = "") -> plt.Figure:
    """
    Create box plots for statistics parameters
    
    Args:
        stats_df: DataFrame with statistics
        parameters: List of parameter names to plot
        group_by: Optional column to group by. If None, creates a single boxplot per parameter
        title: Plot title
        
    Returns:
        Figure object
    """
    n_params = len(parameters)
    
    if group_by is None:
        # Create a grid of boxplots (2x3 or similar)
        n_rows = (n_params + 2) // 3  # Use 3 columns, calculate rows needed
        n_cols = min(3, n_params)  # Use up to 3 columns
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4*n_cols, 4*n_rows))
        fig.suptitle(title, fontsize=16, y=1.02)
        
        # Handle single parameter case
        if n_params == 1:
            axes = np.array([axes])
        
        # Flatten axes for easier indexing if we have a grid
        axes_flat = axes.flatten() if n_rows > 1 or n_cols > 1 else [axes]
        
        # Create a boxplot for each parameter
        for i, param in enumerate(parameters):
            if i < len(axes_flat) and param in stats_df.columns:
                ax = axes_flat[i]
                
                # Create box plot - no grouping, just the parameter values
                sns.boxplot(
                    y=stats_df[param].values,  # Get just the values as a 1D array
                    ax=ax
                )
                ax.set_title(param)
                ax.set_ylabel(param)
                ax.set_xlabel("")  # No x label needed
                
        # Remove any unused subplots
        if n_rows > 1 or n_cols > 1:
            for i in range(n_params, n_rows * n_cols):
                if i < len(axes_flat):
                    fig.delaxes(axes_flat[i])
    else:
        # Original implementation - a vertical stack of boxplots grouped by group_by
        fig, axes = plt.subplots(n_params, 1, figsize=(12, 4*n_params))
        fig.suptitle(title, fontsize=16, y=1.02)
        
        if n_params == 1:
            axes = [axes]
        
        for ax, param in zip(axes, parameters):
            if param in stats_df.columns:
                # Create box plot
                sns.boxplot(
                    data=stats_df,
                    x=group_by,
                    y=param,
                    ax=ax
                )
                ax.set_title(param)
                ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def create_seasonal_comparison(seasonal_stats: Dict[str, pd.DataFrame], 
                             parameters: List[str], title: str) -> plt.Figure:
    """Create seasonal comparison plots"""
    # Combine all seasonal data
    all_data = pd.concat(seasonal_stats.values(), keys=seasonal_stats.keys())
    all_data.index.names = ['season', 'station']
    all_data = all_data.reset_index()
    
    # Create box plots
    return create_boxplots(
        all_data,
        parameters,
        'season',
        f"{title} - Seasonal Comparison"
    )

def create_time_series_plots(ground_data: pd.DataFrame, gridded_data: pd.DataFrame, 
                           station_ids: List[str] = None, 
                           aggregate: str = 'monthly',
                           max_stations: int = 4,
                           title: str = "") -> plt.Figure:
    """
    Create time series plots comparing ground data with gridded data
    
    Args:
        ground_data: DataFrame with ground station data (datetime index)
        gridded_data: DataFrame with gridded data (datetime index)
        station_ids: List of station IDs to plot (if None, selects top stations by data availability)
        aggregate: Aggregation level ('daily', 'monthly', 'yearly')
        max_stations: Maximum number of stations to plot
        title: Plot title
        
    Returns:
        Figure object
    """
    # Ensure the data is aligned
    ground_data, gridded_data = ground_data.align(gridded_data, join='inner')
    
    if ground_data.empty or gridded_data.empty:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No matching data available for time series comparison", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Get common stations
    common_stations = list(set(ground_data.columns) & set(gridded_data.columns))
    
    if not common_stations:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No common stations found between ground and gridded data", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # If no specific stations provided, select based on data availability
    if station_ids is None or not all(s in common_stations for s in station_ids):
        # Find stations with most data
        data_counts = {}
        for station in common_stations:
            valid_count = (~ground_data[station].isna() & ~gridded_data[station].isna()).sum()
            data_counts[station] = valid_count
            
        # Sort by data availability and take top N
        station_ids = [s for s, _ in sorted(data_counts.items(), 
                                         key=lambda x: x[1], reverse=True)[:max_stations]]
    else:
        # Ensure only valid stations are used and limit to max_stations
        station_ids = [s for s in station_ids if s in common_stations][:max_stations]
    
    if not station_ids:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No valid stations found for plotting", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Aggregate data if requested
    if aggregate == 'monthly':
        # Monthly aggregation
        ground_monthly = ground_data[station_ids].resample('MS').sum()
        gridded_monthly = gridded_data[station_ids].resample('MS').sum()
        ground_data = ground_monthly
        gridded_data = gridded_monthly
    elif aggregate == 'yearly':
        # Yearly aggregation
        ground_yearly = ground_data[station_ids].resample('YS').sum()
        gridded_yearly = gridded_data[station_ids].resample('YS').sum()
        ground_data = ground_yearly
        gridded_data = gridded_yearly
    
    # Create subplots for each station
    n_stations = len(station_ids)
    n_cols = 2  # Always use 2 columns
    n_rows = (n_stations + 1) // 2  # Calculate rows needed
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4*n_rows), sharex=True)
    fig.suptitle(title, fontsize=16, y=1.02)
    
    # Handle single row/column cases
    if n_stations == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes.reshape(1, -1)
    
    # Create time series plots for each station
    for i, station_id in enumerate(station_ids):
        row = i // 2
        col = i % 2
        ax = axes[row, col]
        
        # Plot ground data
        ground = ground_data[station_id].dropna()
        if not ground.empty:
            ax.plot(ground.index, ground.values, 'b-', label='Ground', linewidth=1.5)
        
        # Plot gridded data
        gridded = gridded_data[station_id].dropna()
        if not gridded.empty:
            ax.plot(gridded.index, gridded.values, 'r-', label='Gridded', linewidth=1.5)
        
        # Calculate statistics
        if not ground.empty and not gridded.empty:
            # Align the data
            g, p = ground.align(gridded, join='inner')
            if len(g) > 10:  # Need enough points for meaningful statistics
                from sklearn.metrics import r2_score, mean_squared_error
                r2 = r2_score(g, p)
                rmse = np.sqrt(mean_squared_error(g, p))
                
                # Add statistics to plot
                ax.text(0.05, 0.95, f"R² = {r2:.3f}\nRMSE = {rmse:.3f}", 
                        transform=ax.transAxes, fontsize=9, 
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
        
        # Set title and labels
        ax.set_title(f"Station {station_id}")
        ax.set_ylabel("Precipitation (mm)")
        
        # Add legend
        ax.legend(loc='upper right')
        
        # Format x-axis based on aggregation
        if aggregate == 'yearly':
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y'))
        elif aggregate == 'monthly':
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %Y'))
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
            ax.tick_params(axis='x', rotation=45)
    
    # Remove any unused subplots
    for i in range(n_stations, n_rows * n_cols):
        row = i // 2
        col = i % 2
        fig.delaxes(axes[row, col])
    
    plt.tight_layout()
    return fig

def create_multi_dataset_comparison(results_dir: Path, plots_dir: Path, 
                                  metric: str = 'rmse', 
                                  stats_type: str = 'daily',
                                  title: str = "Gridded Dataset Comparison") -> plt.Figure:
    """
    Create boxplot comparing statistical metrics across multiple datasets
    
    Args:
        results_dir: Path to results directory containing dataset subdirectories
        plots_dir: Path to save visualization 
        metric: Statistical metric to compare ('rmse', 'r2', 'bias', 'mae', etc.)
        stats_type: Type of statistics to use ('daily', 'monthly', 'yearly')
        title: Plot title
        
    Returns:
        Figure object with the comparison plot
    """
    # Prepare to collect data from all datasets
    dataset_data = {}
    metric_upper = metric.upper()  # For plot labels
    
    # Scan through results directory for all datasets
    for dataset_dir in results_dir.glob('*'):
        if dataset_dir.is_dir():
            dataset_name = dataset_dir.name
            stats_file = dataset_dir / f'{stats_type}_stats.csv'
            
            if stats_file.exists():
                try:
                    # Load statistics
                    stats_df = pd.read_csv(stats_file)
                    if 'station' in stats_df.columns:
                        stats_df.set_index('station', inplace=True)
                    
                    # Check if the metric exists in this dataset
                    if metric in stats_df.columns:
                        # Store the data for this dataset
                        dataset_data[dataset_name] = stats_df[metric].dropna().values
                except Exception as e:
                    print(f"Error loading {dataset_name}: {str(e)}")
    
    # Create the plot if we have data
    if dataset_data:
        # Sort datasets by median metric value (for better visualization)
        sorted_datasets = sorted(dataset_data.items(), 
                               key=lambda x: np.median(x[1]) if len(x[1]) > 0 else np.nan)
        sorted_names = [item[0] for item in sorted_datasets]
        sorted_data = [item[1] for item in sorted_datasets]
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create the boxplot
        box = ax.boxplot(sorted_data, patch_artist=True, labels=sorted_names)
        
        # Add a different color for each dataset
        colors = plt.cm.tab10.colors[:len(sorted_data)]
        for patch, color in zip(box['boxes'], colors):
            patch.set_facecolor(color)
        
        # Add grid, title and labels
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_title(f"{title} - {metric_upper} Comparison ({stats_type.title()})", fontsize=16)
        ax.set_ylabel(metric_upper, fontsize=14)
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return fig
    else:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"No {metric} data found for {stats_type} statistics", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
def create_radar_chart_comparison(data_dir: Path, plots_dir: Path, 
                                station_id: str = None,
                                value_type: str = 'sum',
                                title: str = "Annual Precipitation Comparison") -> plt.Figure:
    """
    Create radar/polar chart comparing annual data across multiple datasets
    
    Args:
        data_dir: Path to data directory containing precipitation files
        plots_dir: Path to save visualization 
        station_id: Station ID to use for comparison (if None, will use first common station)
        value_type: Type of aggregation ('sum', 'mean', 'max')
        title: Plot title
        
    Returns:
        Figure object with the radar chart
    """
    # Load ground data first
    data_dir = Path(data_dir)
    ground_file = data_dir / 'ground_daily_precipitation.csv'
    if not ground_file.exists():
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, "Ground data file not found", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    ground_data = pd.read_csv(ground_file, index_col=0)
    ground_data.index = pd.to_datetime(ground_data.index)
    
    # Collect all gridded dataset files
    dataset_files = list(data_dir.glob('*_precipitation.csv'))
    if not dataset_files:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, "No gridded dataset files found", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Load all gridded datasets
    gridded_datasets = {}
    for file in dataset_files:
        try:
            dataset_name = file.stem.split('_')[0].upper()
            data = pd.read_csv(file, index_col=0)
            data.index = pd.to_datetime(data.index)
            gridded_datasets[dataset_name] = data
        except Exception as e:
            print(f"Error loading {file.name}: {str(e)}")
    
    # Find common stations across all datasets
    stations = set(ground_data.columns)
    for dataset in gridded_datasets.values():
        stations = stations.intersection(set(dataset.columns))
    
    if not stations:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, "No common stations found across datasets", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # If no station_id provided, use the first common station
    if station_id is None or station_id not in stations:
        station_id = list(stations)[0]
    
    # Extract yearly data for the selected station
    yearly_data = {}
    
    # Add ground data
    ground_station = ground_data[station_id].dropna()
    if value_type == 'sum':
        ground_yearly = ground_station.resample('Y').sum()
    elif value_type == 'mean':
        ground_yearly = ground_station.resample('Y').mean()
    else:  # max
        ground_yearly = ground_station.resample('Y').max()
    
    yearly_data['Ground'] = ground_yearly
    
    # Add gridded datasets
    for name, data in gridded_datasets.items():
        if station_id in data.columns:
            station_data = data[station_id].dropna()
            if value_type == 'sum':
                dataset_yearly = station_data.resample('Y').sum()
            elif value_type == 'mean':
                dataset_yearly = station_data.resample('Y').mean()
            else:  # max
                dataset_yearly = station_data.resample('Y').max()
            
            yearly_data[name] = dataset_yearly
    
    # Find common years across all datasets
    all_years = set()
    for df in yearly_data.values():
        all_years.update(df.index.year)
    
    # Sort years
    all_years = sorted(all_years)
    
    # If no years available, return empty figure
    if not all_years:
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, "No yearly data available", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Prepare data for radar plot
    angles = np.linspace(0, 2*np.pi, len(all_years), endpoint=False).tolist()
    angles += angles[:1]  # Close the loop
    
    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(polar=True))
    
    # Plot each dataset
    colors = plt.cm.tab10.colors
    for i, (name, data) in enumerate(yearly_data.items()):
        values = []
        for year in all_years:
            if pd.Timestamp(year=year, month=1, day=1) in data.index:
                values.append(data.loc[pd.Timestamp(year=year, month=1, day=1)])
            else:
                values.append(np.nan)
        
        # Close the loop
        values += values[:1]
        
        # Plot
        ax.plot(angles, values, 'o-', linewidth=2, label=name, color=colors[i % len(colors)])
    
    # Set ticks and labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([str(year) for year in all_years])
    
    # Add title and legend
    plt.title(f"{title}\nStation {station_id} - {value_type.title()} Precipitation", 
              fontsize=16, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
    
    return fig

def create_multi_metric_radar_chart(results_dir: Path, plots_dir: Path, 
                               metrics: List[str] = None,
                               stats_type: str = 'daily',
                               normalize: bool = True,
                               title: str = "Dataset Performance Comparison") -> plt.Figure:
    """
    Create a radar chart comparing multiple datasets across multiple statistical metrics
    
    Args:
        results_dir: Path to results directory containing dataset subdirectories
        plots_dir: Path to save visualization 
        metrics: List of metrics to compare (if None, uses ['r2', 'rmse', 'bias', 'mae', 'nse'])
        stats_type: Type of statistics to use ('daily', 'monthly', 'yearly')
        normalize: Whether to normalize metrics to 0-1 scale
        title: Plot title
        
    Returns:
        Figure object with the radar chart
    """
    # Default metrics
    if metrics is None:
        metrics = ['r2', 'rmse', 'bias', 'mae', 'nse']
    
    # Set up normalization directions (1 is better or -1 is better)
    metric_directions = {
        'r2': 1,    # Higher is better
        'rmse': -1, # Lower is better
        'bias': -1, # Lower absolute value is better
        'mae': -1,  # Lower is better
        'nse': 1,   # Higher is better
        'pbias': -1 # Lower absolute value is better
    }
    
    # Prepare to collect data from all datasets
    dataset_metrics = {}
    
    # Scan through results directory for all datasets
    for dataset_dir in results_dir.glob('*'):
        if dataset_dir.is_dir():
            dataset_name = dataset_dir.name
            stats_file = dataset_dir / f'{stats_type}_stats.csv'
            
            if stats_file.exists():
                try:
                    # Load statistics
                    stats_df = pd.read_csv(stats_file)
                    if 'station' in stats_df.columns:
                        stats_df.set_index('station', inplace=True)
                    
                    # Calculate average metrics across all stations
                    dataset_values = {}
                    for metric in metrics:
                        if metric in stats_df.columns:
                            # For bias and pbias, use absolute values for better comparison
                            if metric in ['bias', 'pbias']:
                                dataset_values[metric] = stats_df[metric].abs().mean()
                            else:
                                dataset_values[metric] = stats_df[metric].mean()
                        else:
                            # Use NaN if metric not available
                            dataset_values[metric] = np.nan
                    
                    dataset_metrics[dataset_name] = dataset_values
                except Exception as e:
                    print(f"Error loading {dataset_name}: {str(e)}")
    
    # Check if we have data
    if not dataset_metrics:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, f"No data found for {stats_type} statistics", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Normalize metrics if requested
    if normalize:
        # Find min and max for each metric across all datasets
        metric_min = {metric: float('inf') for metric in metrics}
        metric_max = {metric: float('-inf') for metric in metrics}
        
        for dataset_values in dataset_metrics.values():
            for metric, value in dataset_values.items():
                if not np.isnan(value):
                    metric_min[metric] = min(metric_min[metric], value)
                    metric_max[metric] = max(metric_max[metric], value)
        
        # Apply normalization
        for dataset_name, dataset_values in dataset_metrics.items():
            for metric, value in dataset_values.items():
                if not np.isnan(value) and metric_max[metric] > metric_min[metric]:
                    # Normalize to 0-1 range
                    norm_value = (value - metric_min[metric]) / (metric_max[metric] - metric_min[metric])
                    
                    # Adjust direction (1 is always better after normalization)
                    if metric_directions.get(metric, 1) < 0:
                        norm_value = 1 - norm_value
                    
                    dataset_metrics[dataset_name][metric] = norm_value
    
    # Create the radar chart
    # Number of variables
    N = len(metrics)
    
    # Create figure
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, polar=True)
    
    # Set ticks and labels
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([metric.upper() for metric in metrics])
    
    # Add grid
    ax.grid(True)
    
    # Add title
    plt.title(title, fontsize=16, y=1.1)
    
    # Plot each dataset
    colors = plt.cm.tab10.colors
    for i, (dataset_name, dataset_values) in enumerate(dataset_metrics.items()):
        values = [dataset_values.get(metric, 0) for metric in metrics]
        values += values[:1]  # Close the loop
        
        # Plot
        ax.plot(angles, values, 'o-', linewidth=2, label=dataset_name, color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.1, color=colors[i % len(colors)])
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
    
    return fig


def create_seasonal_radar_chart(results_dir: Path, plots_dir: Path, 
                              metric: str = 'r2',
                              normalize: bool = True,
                              title: str = "Seasonal Performance Comparison") -> plt.Figure:
    """
    Create radar chart comparing multiple datasets across different seasons
    
    Args:
        results_dir: Path to results directory containing dataset subdirectories
        plots_dir: Path to save visualization 
        metric: Metric to compare (default 'r2')
        normalize: Whether to normalize metrics to 0-1 scale
        title: Plot title
        
    Returns:
        Figure object with the radar chart
    """
    # Define seasons
    seasons = ['Winter', 'Spring', 'Summer', 'Fall']
    
    # Prepare to collect data from all datasets
    dataset_metrics = {}
    
    # Scan through results directory for all datasets
    for dataset_dir in results_dir.glob('*'):
        if dataset_dir.is_dir():
            dataset_name = dataset_dir.name
            stats_file = dataset_dir / 'seasonal_stats.csv'
            
            if stats_file.exists():
                try:
                    # Load statistics
                    stats_df = pd.read_csv(stats_file)
                    
                    # Calculate average metric by season
                    dataset_values = {}
                    for season in seasons:
                        season_data = stats_df[stats_df['season'] == season]
                        if not season_data.empty and metric in season_data.columns:
                            # For bias and pbias, use absolute value
                            if metric in ['bias', 'pbias']:
                                dataset_values[season] = season_data[metric].abs().mean()
                            else:
                                dataset_values[season] = season_data[metric].mean()
                        else:
                            dataset_values[season] = np.nan
                    
                    # Add to dataset metrics if we have at least one valid value
                    if any(not np.isnan(v) for v in dataset_values.values()):
                        dataset_metrics[dataset_name] = dataset_values
                except Exception as e:
                    print(f"Error loading seasonal data for {dataset_name}: {str(e)}")
    
    # Check if we have data
    if not dataset_metrics:
        # Create an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, f"No seasonal data found for {metric}", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # Determine if metric is "higher is better" or "lower is better"
    higher_is_better = metric in ['r2', 'nse']
    
    # Normalize if requested
    if normalize:
        # Find min and max for each season across all datasets
        season_min = {season: float('inf') for season in seasons}
        season_max = {season: float('-inf') for season in seasons}
        
        for dataset_values in dataset_metrics.values():
            for season, value in dataset_values.items():
                if not np.isnan(value):
                    season_min[season] = min(season_min[season], value)
                    season_max[season] = max(season_max[season], value)
        
        # Apply normalization
        for dataset_name, dataset_values in dataset_metrics.items():
            for season, value in dataset_values.items():
                if not np.isnan(value) and season_max[season] > season_min[season]:
                    # Normalize to 0-1 range
                    norm_value = (value - season_min[season]) / (season_max[season] - season_min[season])
                    
                    # Adjust direction (1 is always better after normalization)
                    if not higher_is_better:
                        norm_value = 1 - norm_value
                    
                    dataset_metrics[dataset_name][season] = norm_value
    
    # Create the radar chart
    # Number of variables
    N = len(seasons)
    
    # Create figure
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, polar=True)
    
    # Set ticks and labels
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(seasons)
    
    # Add grid
    ax.grid(True)
    
    # Add title
    plt.title(f"{title} - {metric.upper()}", fontsize=16, y=1.1)
    
    # Plot each dataset
    colors = plt.cm.tab10.colors
    for i, (dataset_name, dataset_values) in enumerate(dataset_metrics.items()):
        values = [dataset_values.get(season, 0) for season in seasons]
        values += values[:1]  # Close the loop
        
        # Plot
        ax.plot(angles, values, 'o-', linewidth=2, label=dataset_name, color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.1, color=colors[i % len(colors)])
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
    
    return fig