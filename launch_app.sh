#!/bin/bash
# Climate Data Fetcher GUI - macOS/Linux Launcher Script

echo "Starting Climate Data Fetcher GUI..."

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo "Using existing virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
python main.py

# Deactivate virtual environment
deactivate

echo "Climate Data Fetcher GUI has been closed."
read -p "Press Enter to continue..."