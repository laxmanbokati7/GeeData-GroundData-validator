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
                   group_by: str, title: str) -> plt.Figure:
    """Create box plots for statistics parameters"""
    n_params = len(parameters)
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