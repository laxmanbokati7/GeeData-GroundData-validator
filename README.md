# ERA5 vs Ground Station Precipitation Analysis

## Overview
A Python-based analytical tool comparing ERA5 reanalysis precipitation data with ground station measurements across California. This tool fetches data from ERA5 and ground stations, performs statistical comparisons, and generates visualizations for analysis.

## Features
- Data Collection
  - ERA5 reanalysis data via Google Earth Engine API
  - Ground station measurements via Meteostat
  - Automated data synchronization and cleaning
- Statistical Analysis
  - R-squared (R²)
  - Root Mean Square Error (RMSE)
  - Mean Absolute Error (MAE)
  - Percent Bias (PBIAS)
- Temporal Analysis
  - Seasonal comparisons
  - Multi-year trends
  - Data completeness checks
- Spatial Analysis
  - California-wide distribution maps
  - Station-specific comparisons
  - Regional patterns

## Project Structure
```
ERA5compare/ ├── Data/ # Data storage │ ├── ca_daily_precipitation.csv │ ├── era5_daily_precipitation.csv │ └── ca_stations_metadata.csv ├── Results/ # Analysis outputs │ ├── station_statistics.csv │ ├── seasonal_statistics.csv │ └── plots/ ├── ShapeFile/ # Geographic data │ └── CA_State.shp ├── src/ # Source code │ ├── data_fetcher.py │ ├── data_loader.py │ ├── get_statistics.py │ └── plotting.py ├── tests/ # Unit tests ├── notebooks/ # Jupyter notebooks ├── requirements.txt # Dependencies └── main.py # Entry point
```

## Quick Start

### Prerequisites
- Python 3.8+
- Google Earth Engine account
- Git


## Quick Start

### Prerequisites
- Python 3.8+
- Google Earth Engine account
- Git

### Installation
```sh
# Clone repository
git clone https://github.com/Saurav-JSU/GeeData-GroundData-validator.git
cd ERA5compare

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Authenticate Earth Engine
earthengine authenticate

###Basic Usage
```
# Fetch new data
python src/data_fetcher.py --start-year 1980 --end-year 2024

# Run analysis
python main.py
```

## File Structure & Dependencies

### Data Files
| File                        | Description                                                   |
|-----------------------------|---------------------------------------------------------------|
| `ca_daily_precipitation.csv`| Daily precipitation measurements from California ground stations |
| `era5_daily_precipitation.csv` | ERA5 reanalysis precipitation data for corresponding locations |
| `ca_stations_metadata.csv`  | Station metadata including ID, lat/lon, elevation             |

### Source Files
### Source Files
| File               | Purpose                                                   |
|--------------------|-----------------------------------------------------------|
| `data_fetcher.py`  | Fetches data from ERA5 and ground stations via APIs       |
| `data_loader.py`   | Loads, validates and preprocesses input data              |
| `get_statistics.py`| Calculates comparison statistics (R², RMSE, MAE, PBIAS)   |
| `plotting.py`      | Generates spatial and temporal visualizations             |
| `main.py`          | Main execution script orchestrating the analysis          |

### Core Dependencies
```
| Package          | Version  | Purpose                        |
|------------------|----------|--------------------------------|
| numpy            | >=1.21.0 | Numerical computations         |
| pandas           | >=1.3.0  | Data manipulation and analysis |
| geopandas        | >=0.9.0  | Spatial data handling          |
| scikit-learn     | >=0.24.2 | Statistical metrics            |
| matplotlib       | >=3.4.0  | Basic plotting                 |
| seaborn          | >=0.11.0 | Statistical visualizations     |
| earthengine-api  | >=0.1.323| ERA5 data access               |
| meteostat        | >=1.6.5  | Ground station data access     |
```

All dependencies can be installed via:
```bash
pip install -r requirements.txt


### License
```markdown
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
