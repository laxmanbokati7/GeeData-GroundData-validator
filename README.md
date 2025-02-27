# Climate Data Fetcher

A comprehensive tool for fetching, analyzing, and visualizing climate data from multiple sources including ground stations (Meteostat), ERA5 reanalysis, DAYMET, and PRISM datasets across the United States.

## Description

Climate Data Fetcher provides researchers and climate analysts with an intuitive interface to download, compare, and analyze precipitation data from various sources. The tool supports temporal analysis (daily, monthly, yearly, seasonal) and generates publication-quality visualizations to help identify discrepancies and patterns across different climate datasets.

## Features

- Interactive UI for data selection
- Support for multiple data sources (ground stations, ERA5, DAYMET, PRISM)
- Comprehensive statistical analysis
- Spatial and temporal visualization
- Comparison between ground observations and gridded datasets
- Seasonal, monthly, and yearly aggregation

## Prerequisites

- Python 3.10+
- Jupyter Notebook
- Required Python packages (see `requirements.txt`)
- Earth Engine account for accessing gridded datasets

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/climate-data-fetcher.git
cd climate-data-fetcher
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Launch Jupyter Notebook:
```bash
jupyter notebook
```

2. Open `main.ipynb`

3. Run the cells in sequence:
   - First cell: Set up the environment
   - Second cell: Display the data selection UI
   - Use the UI to select data sources, time periods, and geographic areas
   - Click the "Download Data" button and wait for the process to complete
   - Confirm data download is complete using the confirmation button
   - Run the analysis cell
   - Run the visualization cell

## Project Structure

```
climate_data_fetcher/
  ├── config.py                # Configuration classes
  ├── main.ipynb               # Main notebook interface
  ├── src/
  │   ├── base_fetcher.py      # Abstract base classes
  │   ├── cli.py               # Command-line interface
  │   ├── data/                # Data fetching modules
  │   ├── ui/                  # UI components
  │   ├── analysis/            # Statistical analysis
  │   └── visualization/       # Plotting and visualization
  └── utils/                   # Utility functions
```

## Data Sources

- **Ground Stations**: NOAA ground weather stations via Meteostat
- **ERA5**: ECMWF Reanalysis v5 data
- **DAYMET**: Daily Surface Weather Data on a 1-km Grid for North America
- **PRISM**: Parameter-elevation Regressions on Independent Slopes Model

## Output

- **Data/**: Raw data files
- **Results/**: Statistical analysis results
- **Plots/**: Generated visualizations

## Citation

If you use this code in your research, please cite:

**APA Style**
Bhattarai, S., & Talchabhadel, R. (2024). Comparative Analysis of Satellite-Based Precipitation Data across the CONUS and Hawaii: Identifying Optimal Satellite Performance. *Remote Sensing*, *16*(16), 3058. https://doi.org/10.3390/rs16163058