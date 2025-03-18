# Climate Data Fetcher GUI - Installation and Setup Guide

This guide provides instructions for installing and running the Climate Data Fetcher GUI application.

## Prerequisites

Before installing the application, ensure you have the following prerequisites:

- Python 3.10 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)
- Earth Engine account (for accessing gridded datasets)

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/your-username/climate-data-fetcher-gui.git
cd climate-data-fetcher-gui
```

### 2. Create and Activate a Virtual Environment

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Earth Engine Authentication (if needed)

If you plan to use the Earth Engine features, you'll need to authenticate:

```bash
earthengine authenticate
```

Follow the instructions to complete the authentication process.

## Running the Application

### Starting the GUI Application

```bash
python main.py
```

## Development Setup

If you're planning to contribute to the development of the Climate Data Fetcher GUI, here are some additional setup steps:

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Code Formatting

Use Black to format your code:

```bash
black .
```

### Running Tests

```bash
pytest
```

## Building a Standalone Executable

You can build a standalone executable using PyInstaller:

```bash
pyinstaller --name=ClimateDataFetcher --windowed --icon=ui/resources/icons/app_icon.ico main.py
```

The executable will be created in the `dist/ClimateDataFetcher` directory.

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: If you encounter errors about missing modules, ensure you've installed all dependencies with `pip install -r requirements.txt`.

2. **Earth Engine Authentication Issues**: If you have problems with Earth Engine, try running `earthengine authenticate` again and ensure you have proper permissions.

3. **PyQt Display Issues**: On some Linux systems, you might need to install additional packages:
   ```bash
   sudo apt-get install libxcb-xinerama0
   ```

4. **Data Directory Access**: Ensure the application has write permissions to the directories it needs to create (Data, Results, and Plots).

### Getting Help

If you encounter any issues not covered in this guide, please open an issue on the GitHub repository or contact the maintainers directly.

## License

This project is licensed under the MIT License - see the LICENSE file for details.