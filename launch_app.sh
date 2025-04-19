#!/bin/bash

echo "============================================================"
echo "         Climate Data Fetcher GUI - Setup and Launch        "
echo "============================================================"
echo ""

# Check if Python is installed
echo "Checking for Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.7 or higher:"
    echo "  - macOS: brew install python3"
    echo "  - Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  - Fedora: sudo dnf install python3 python3-pip"
    echo ""
    read -p "Press Enter to exit..." key
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d " " -f 2)
echo "Found Python version: $PYTHON_VERSION"
echo ""

# Create data directories if they don't exist
if [ ! -d "Data" ]; then
    echo "Creating Data directory..."
    mkdir -p Data
fi
if [ ! -d "Results" ]; then
    echo "Creating Results directory..."
    mkdir -p Results
fi
if [ ! -d "Plots" ]; then
    echo "Creating Plots directory..."
    mkdir -p Plots
fi

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "Conda detected. Using conda for environment setup."
    
    # Check if environment exists
    if conda env list | grep -q "climate-data-fetcher"; then
        echo "Found existing conda environment. Activating..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate climate-data-fetcher
    else
        echo "Creating new conda environment (this may take a few minutes)..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda create -y -n climate-data-fetcher python=3.8
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to create conda environment."
            read -p "Press Enter to exit..." key
            exit 1
        fi
        conda activate climate-data-fetcher
        
        # Install conda-specific packages that might be difficult with pip
        echo "Installing geospatial dependencies via conda..."
        conda install -y -c conda-forge geopandas contextily
    fi
    
    # Install requirements
    echo "Installing required packages from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "WARNING: Some packages may not have installed correctly."
        echo "The application may still work, but you might encounter issues."
        read -p "Press Enter to continue anyway..." key
    fi
    
else
    echo "Conda not found. Using venv for environment setup."
    
    # Check if venv exists
    if [ -d "venv" ]; then
        echo "Found existing virtual environment. Activating..."
    else
        echo "Creating new virtual environment..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to create virtual environment."
            read -p "Press Enter to exit..." key
            exit 1
        fi
    fi
    
    # Activate venv
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to activate virtual environment."
        read -p "Press Enter to exit..." key
        exit 1
    fi
    
    # Upgrade pip
    echo "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    # Install requirements
    echo "Installing required packages from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "WARNING: Some packages may not have installed correctly."
        echo "The application may still work, but you might encounter issues."
        echo ""
        echo "If you encounter problems with geospatial libraries (GDAL, Fiona, etc.),"
        echo "consider installing Anaconda and running this script again."
        echo ""
        read -p "Press Enter to continue anyway..." key
    fi
fi

# Check if Earth Engine is authenticated
echo "Checking Earth Engine authentication..."
python3 -c "import ee; ee.Initialize()" &> /dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Google Earth Engine authentication needed."
    echo "If you don't have an Earth Engine account, sign up at:"
    echo "https://earthengine.google.com/signup/"
    echo ""
    echo "Running Earth Engine authentication..."
    earthengine authenticate
    if [ $? -ne 0 ]; then
        echo "WARNING: Earth Engine authentication failed."
        echo "Some features of the application may not work."
        read -p "Press Enter to continue anyway..." key
    fi
fi

# Check for required system libraries on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Checking for required system libraries..."
    
    # Check for Qt dependencies
    if ! ldconfig -p | grep -q libQt5Core.so; then
        echo "WARNING: Qt5 libraries may be missing. If the application fails to start, install them:"
        echo "  - Ubuntu/Debian: sudo apt-get install python3-pyqt5 libqt5gui5"
        echo "  - Fedora: sudo dnf install python3-qt5"
        echo ""
    fi
    
    # Check for GDAL
    if ! ldconfig -p | grep -q libgdal.so; then
        echo "WARNING: GDAL libraries may be missing. If you encounter GeoPandas errors, install them:"
        echo "  - Ubuntu/Debian: sudo apt-get install libgdal-dev"
        echo "  - Fedora: sudo dnf install gdal-devel"
        echo ""
    fi
fi

# Run the application
echo ""
echo "============================================================"
echo "Starting Climate Data Fetcher GUI..."
echo "============================================================"
echo ""
echo "If this is your first time running the application:"
echo "1. Begin by selecting an area of interest in the Data Selection tab"
echo "2. Choose a time period and datasets to download"
echo "3. Click \"Download Data\" to fetch precipitation data"
echo "4. Navigate to the Analysis tab to analyze the downloaded data"
echo "5. Use the Visualization tab to create and view plots"
echo ""
echo "Press Ctrl+C to exit the application at any time."
echo ""

python3 main.py

# Check if application exited successfully
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: The application encountered a problem and closed unexpectedly."
    echo "Exit code: $?"
    echo ""
    echo "If you need assistance, please report this issue along with any"
    echo "error messages that appeared in the application window."
    echo ""
fi

# Deactivate environment
if [ -n "$CONDA_PREFIX" ]; then
    conda deactivate
else
    deactivate
fi

echo ""
echo "============================================================"
echo "Climate Data Fetcher GUI session ended."
echo "============================================================"
echo ""
read -p "Press Enter to exit..." key