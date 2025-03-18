@echo off
REM Climate Data Fetcher GUI - Windows Launcher Script

echo Starting Climate Data Fetcher GUI...

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo Using existing virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the application
python main.py

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo Climate Data Fetcher GUI has been closed.
pause