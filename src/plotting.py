import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

class Plotter:
    def __init__(self):
        self.metrics = ['r2', 'rmse', 'mae', 'pbias']
        self.seasons = ['winter', 'spring', 'summer', 'fall']
        # Load and ensure shapefile is in WGS84 (EPSG:4326)
        self.ca_shape = gpd.read_file('ShapeFile/CA_State.shp')
        if self.ca_shape.crs is None:
            self.ca_shape.set_crs(epsg=4326, inplace=True)
        elif self.ca_shape.crs != 'EPSG:4326':
            self.ca_shape = self.ca_shape.to_crs(epsg=4326)

    def _create_gdf(self, df):
        """Convert DataFrame to GeoDataFrame with correct CRS"""
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
        return gdf

    def create_spatial_plot(self, stats_df, title, output_path):
        """Create spatial distribution plot with CRS-aligned data"""
        fig, axes = plt.subplots(2, 2, figsize=(6, 6))
        fig.suptitle(title, fontsize=16, y=1.02)
        
        # Convert stats to GeoDataFrame
        stats_gdf = self._create_gdf(stats_df)
        
        for ax, metric in zip(axes.flat, self.metrics):
            # Plot CA shape
            self.ca_shape.boundary.plot(ax=ax, color='black', linewidth=1)
            
            # Plot stations
            scatter = ax.scatter(
                stats_gdf.geometry.x,
                stats_gdf.geometry.y,
                c=stats_gdf[metric],
                cmap='RdYlBu',
                s=50
            )
            
            # Set plot bounds based on California shape
            bounds = self.ca_shape.total_bounds
            ax.set_xlim([bounds[0], bounds[2]])
            ax.set_ylim([bounds[1], bounds[3]])
            
            # Customize plot
            plt.colorbar(scatter, ax=ax)
            ax.set_title(f'{metric.upper()}')
            #ax.set_xlabel('Longitude')
            #ax.set_ylabel('Latitude')
            
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.3, hspace=0.3)  # Adjust the space between plots
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()
        
    def create_all_spatial_plots(self, stats_df, seasonal_df, metadata_df):
        """Create all spatial distribution plots"""
        # Merge statistics with station metadata
        stats_with_loc = pd.merge(
            stats_df,
            metadata_df[['id', 'latitude', 'longitude']],
            left_on='station_id',
            right_on='id'
        )
        
        # Create plots
        self.create_spatial_plot(
            stats_with_loc,
            'Overall Statistics Distribution',
            'Results/overall_spatial_stats.png'
        )
        
        for season in self.seasons:
            season_stats = seasonal_df[seasonal_df['season'] == season]
            season_with_loc = pd.merge(
                season_stats,
                metadata_df[['id', 'latitude', 'longitude']],
                left_on='station_id',
                right_on='id'
            )
            
            self.create_spatial_plot(
                season_with_loc,
                f'{season.capitalize()} Statistics Distribution',
                f'Results/{season}_spatial_stats.png'
            )

    def create_seasonal_boxplot(self, seasonal_df):
        """Create seasonal boxplot without outliers"""
        fig, axes = plt.subplots(2, 2, figsize=(10, 6))
        fig.suptitle('Seasonal Statistics Distribution', fontsize=16)
        
        for ax, metric in zip(axes.flat, self.metrics):
            sns.boxplot(
                data=seasonal_df,
                x='season',
                y=metric,
                hue='season',
                ax=ax,
                showfliers=False,  # Remove outliers
                legend=False
            )
            ax.set_title(f'{metric.upper()} by Season')
            
        plt.tight_layout()
        plt.savefig('Results/seasonal_boxplots.png', bbox_inches='tight', dpi=300)
        plt.close()