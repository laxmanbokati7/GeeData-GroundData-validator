# Climate Data Fetcher GUI - User Guide

This guide provides instructions for using the Climate Data Fetcher GUI application.

## Overview

Climate Data Fetcher GUI is a desktop application for fetching, analyzing, and visualizing climate data from multiple sources including ground stations, ERA5 reanalysis, DAYMET, and PRISM datasets across the United States.

## Getting Started

After installing the application following the instructions in INSTALL.md, launch the application by running:

```bash
python main.py
```

Or if you're using a standalone executable, simply run the application.

## Main Interface

The application interface is divided into three main tabs:

1. **Data Selection**: Select and download climate data
2. **Analysis**: Analyze the downloaded data
3. **Visualization**: Visualize analysis results

## Data Selection Tab

### Step 1: Select Data Type

Choose one of the following options:
- **Ground data only**: Fetch only ground station data
- **Gridded data only**: Fetch only gridded datasets
- **Both**: Fetch both ground and gridded data

### Step 2: Set Year Range

Use the sliders to select the start and end years for the data. The available range is from 1980 to 2024.

### Step 3: Select States

Choose one of the following options:
- **All US States**: Fetch data for all available US states
- **Select specific states**: Choose one or more states from the list

### Step 4: Select Gridded Datasets

If you selected "Gridded data only" or "Both" in Step 1, choose one or more of the following gridded datasets:
- **ERA5**: ECMWF Reanalysis v5 data
- **DAYMET**: Daily Surface Weather Data on a 1-km Grid for North America
- **PRISM**: Parameter-elevation Regressions on Independent Slopes Model

### Step 5: Download Data

Click the "Download Data" button to start the data download process. The progress bar will show the download progress.

Once the download is complete, you'll see a confirmation message and a data summary.

## Analysis Tab

### Step 1: Configure Analysis Settings

Choose the analysis type and options:
- **Analysis Type**: Standard or Custom analysis
- **Include Seasonal Analysis**: Check to include seasonal analysis
- **Include Extreme Value Analysis**: Check to include extreme value analysis

### Step 2: Run Analysis

Click the "Run Analysis" button to start the analysis process. The progress bar will show the analysis progress, and the status text area will display messages about the analysis process.

### Step 3: View Results

Once the analysis is complete, the results will be displayed in the tabs:
- **Summary**: Shows an overview of the analysis results
- **ERA5**, **DAYMET**, **PRISM**: Shows detailed statistics for each dataset

## Visualization Tab

### Step 1: Configure Visualization Settings

Choose the visualization settings:
- **Dataset**: Select the dataset to visualize (ERA5, DAYMET, PRISM)
- **Type**: Select the type of visualization (Spatial Distribution, Box Plots, Time Series, etc.)
- **High Resolution**: Check to generate high-resolution images

### Step 2: Generate Visualizations

Click the "Generate Visualizations" button to create the visualizations. The progress bar will show the generation progress.

### Step 3: View and Export Visualizations

The generated visualizations will appear in the file tree on the left. Click on a file to view it in the image viewer.

To export a visualization:
1. Select the visualization in the file tree
2. Click the "Export Selected" button
3. Choose a location to save the image

## Project Management

You can manage your projects using the menu options:

- **File > New Project**: Start a new project and clear all current data
- **File > Open Project**: Open an existing project file
- **File > Save Project**: Save the current project to a file

## Tips and Best Practices

1. **Start with a smaller dataset**: For initial testing, select a specific state and a shorter time period.

2. **Data directory structure**: All downloaded data is stored in the "Data" directory, results in the "Results" directory, and visualizations in the "Plots" directory.

3. **Memory considerations**: Fetching large amounts of data (many states or long time periods) may require significant system memory.

4. **Visualization customization**: The visualization tab allows you to create different types of visualizations. Experiment with different settings to find the best representation for your data.

5. **Progress indicators**: During long-running operations, watch the progress bar and status text for updates.

## Troubleshooting

### Common Issues

1. **No data available for analysis**: Ensure you've completed the data download step in the Data Selection tab.

2. **No analysis results for visualization**: Ensure you've completed the analysis step in the Analysis tab.

3. **Empty visualizations**: Check that the selected dataset has enough data points for meaningful visualization.

4. **Application becomes unresponsive**: For large datasets, operations may take some time. The progress bar and status text will update to show that the application is still working.

If you encounter any other issues, please refer to the troubleshooting section in the INSTALL.md file or contact the developers.