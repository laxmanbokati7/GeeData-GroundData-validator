# Climate Data Fetcher GUI

A comprehensive PyQt-based desktop application for fetching, analyzing, and visualizing climate data from multiple sources including ground stations (Meteostat), ERA5 reanalysis, DAYMET, and PRISM datasets across the United States.

## Overview

Climate Data Fetcher GUI provides researchers and climate analysts with an intuitive graphical interface to download, compare, and analyze precipitation data from various sources. The tool supports temporal analysis (daily, monthly, yearly, seasonal) and generates publication-quality visualizations to help identify discrepancies and patterns across different climate datasets.

![Application Screenshot](docs/screenshots/main_screen.png)

## Features

- **User-friendly GUI** for data selection and visualization
- **Support for multiple data sources**:
  - Ground station data (via Meteostat)
  - ERA5 reanalysis data
  - DAYMET data
  - PRISM data
- **Comprehensive statistical analysis**:
  - Daily, monthly, and yearly comparisons
  - Seasonal analysis
  - Extreme value analysis
- **Powerful visualization tools**:
  - Spatial distribution maps
  - Box plots
  - Seasonal comparisons
  - Time series analysis
- **Extensible architecture** for adding new data sources and analysis methods

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

Quick start:

```bash
# Clone the repository
git clone https://github.com/your-username/climate-data-fetcher-gui.git
cd climate-data-fetcher-gui

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

See [USER_GUIDE.md](USER_GUIDE.md) for detailed usage instructions.

## Project Structure

The project follows a modular architecture with clear separation of concerns:

- **UI Layer**: PyQt-based user interface components
- **Controller Layer**: Application logic and workflow management
- **Business Logic Layer**: Core functionality for data fetching, analysis, and visualization
- **Data Layer**: Configuration and data storage

```
climate_data_fetcher_gui/
├── controller/        # Application controllers
├── ui/                # User interface components
├── src/               # Core functionality
│   ├── data/          # Data fetching modules
│   ├── analysis/      # Analysis modules
│   └── visualization/ # Visualization modules
└── utils/             # Utility functions
```

See the [architecture documentation](docs/architecture.md) for more details.

## Development

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/climate-data-fetcher-gui.git
cd climate-data-fetcher-gui

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Coding Guidelines

- Follow PEP 8 for Python code style
- Use type hints for function signatures
- Document all classes and functions using docstrings
- Use logging instead of print statements
- Write unit tests for new functionality

### Running Tests

```bash
pytest
```

### Building Standalone Executable

```bash
pyinstaller --name=ClimateDataFetcher --windowed --icon=ui/resources/icons/app_icon.ico main.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this code in your research, please cite:

**APA Style**
Bhattarai, S., & Talchabhadel, R. (2024). Comparative Analysis of Satellite-Based Precipitation Data across the CONUS and Hawaii: Identifying Optimal Satellite Performance. *Remote Sensing*, *16*(16), 3058. https://doi.org/10.3390/rs16163058