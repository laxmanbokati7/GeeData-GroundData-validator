@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo         Climate Data Fetcher GUI - Setup and Launch
echo ============================================================
echo.

:: Check if this is the correct repository
if not exist "config.py" (
    echo ERROR: Required files not found. Make sure you're running this script
    echo from the GeeData-GroundData-validator root directory.
    echo.
    pause
    exit /b 1
)

:: Check if Python is installed
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in your PATH.
    echo Please install Python 3.7 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%a in ('python --version 2^>^&1') do (
    set PYTHON_VERSION=%%a
)
echo Found Python version: %PYTHON_VERSION%
echo.

:: Create data directories if they don't exist
if not exist Data (
    echo Creating Data directory...
    mkdir Data
)
if not exist Results (
    echo Creating Results directory...
    mkdir Results
)
if not exist Plots (
    echo Creating Plots directory...
    mkdir Plots
)

:: Check if conda is available
conda --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Conda detected. Using conda for environment setup.
    
    :: Check if environment exists
    conda env list | findstr /C:"climate-data-fetcher" >nul
    if %errorlevel% equ 0 (
        echo Found existing conda environment. Activating...
        call conda activate climate-data-fetcher
    ) else (
        echo Creating new conda environment (this may take a few minutes)...
        call conda create -y -n climate-data-fetcher python=3.8
        if %errorlevel% neq 0 (
            echo ERROR: Failed to create conda environment.
            pause
            exit /b 1
        )
        call conda activate climate-data-fetcher
        
        :: Install conda-specific packages that might be difficult with pip
        echo Installing geospatial dependencies via conda...
        call conda install -y -c conda-forge geopandas contextily
    )
    
    :: Install requirements
    echo Installing required packages from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo WARNING: Some packages may not have installed correctly.
        echo The application may still work, but you might encounter issues.
        echo Press any key to continue anyway...
        pause >nul
    )
    
) else (
    echo Conda not found. Using venv for environment setup.
    
    :: Check if venv exists
    if exist venv (
        echo Found existing virtual environment. Activating...
    ) else (
        echo Creating new virtual environment...
        python -m venv venv
        if %errorlevel% neq 0 (
            echo ERROR: Failed to create virtual environment.
            pause
            exit /b 1
        )
    )
    
    :: Activate venv
    call venv\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo ERROR: Failed to activate virtual environment.
        pause
        exit /b 1
    )
    
    :: Upgrade pip
    echo Upgrading pip...
    python -m pip install --upgrade pip
    
    :: Install requirements
    echo Installing required packages from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo WARNING: Some packages may not have installed correctly.
        echo The application may still work, but you might encounter issues.
        echo.
        echo If you encounter problems with geospatial libraries (GDAL, Fiona, etc.),
        echo consider installing Anaconda and running this script again.
        echo.
        echo Press any key to continue anyway...
        pause >nul
    )
)

:: Check if Earth Engine is authenticated
echo Checking Earth Engine authentication...
python -c "import ee; ee.Initialize()" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Google Earth Engine authentication needed.
    echo If you don't have an Earth Engine account, sign up at:
    echo https://earthengine.google.com/signup/
    echo.
    echo Running Earth Engine authentication...
    earthengine authenticate
    if %errorlevel% neq 0 (
        echo WARNING: Earth Engine authentication failed.
        echo Some features of the application may not work.
        echo Press any key to continue anyway...
        pause >nul
    )
)

:: Run the application
echo.
echo ============================================================
echo Starting Climate Data Fetcher GUI...
echo ============================================================
echo.
echo If this is your first time running the application:
echo 1. Begin by selecting an area of interest in the Data Selection tab
echo 2. Choose a time period and datasets to download
echo 3. Click "Download Data" to fetch precipitation data
echo 4. Navigate to the Analysis tab to analyze the downloaded data
echo 5. Use the Visualization tab to create and view plots
echo.
echo Press Ctrl+C to exit the application at any time.
echo.

python main.py

:: Check if application exited successfully
if %errorlevel% neq 0 (
    echo.
    echo ERROR: The application encountered a problem and closed unexpectedly.
    echo Exit code: %errorlevel%
    echo.
    echo If you need assistance, please report this issue along with any
    echo error messages that appeared in the application window.
    echo.
)

:: Deactivate environment
if defined CONDA_PREFIX (
    call conda deactivate
) else (
    call venv\Scripts\deactivate.bat
)

echo.
echo ============================================================
echo Climate Data Fetcher GUI session ended.
echo ============================================================
echo.
pause

endlocal