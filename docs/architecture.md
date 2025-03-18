# Climate Data Fetcher GUI - Architecture Documentation

This document outlines the architecture of the Climate Data Fetcher GUI application, describing the key components, their responsibilities, and their interactions.

## 1. Architectural Overview

The application follows a layered architecture with clear separation of concerns:

![Architecture Diagram](../ui/resources/architecture_diagram.png)

### 1.1 Layers

1. **UI Layer**: Contains all user interface components built with PyQt5.
2. **Controller Layer**: Manages application flow and coordinates between UI and business logic.
3. **Business Logic Layer**: Implements core functionality for data fetching, analysis, and visualization.
4. **Data Layer**: Handles data storage, loading, and configuration management.

## 2. Key Components

### 2.1 UI Layer

The UI Layer is built using PyQt5 and organized into modular panels:

- **ClimateDataApp** (`ui/app_window.py`): Main application window that contains the tab widget and menu bar.
- **DataSelectionPanel** (`ui/panels/data_selection_panel.py`): Panel for selecting and downloading climate data.
- **AnalysisPanel** (`ui/panels/analysis_panel.py`): Panel for analyzing downloaded data.
- **VisualizationPanel** (`ui/panels/visualization_panel.py`): Panel for generating and viewing visualizations.

### 2.2 Controller Layer

The Controller Layer orchestrates the application workflow:

- **AppController** (`controller/app_controller.py`): Main controller that coordinates all aspects of the application.
- **DataFetchingController** (`controller/data_fetching_controller.py`): Manages data fetching operations.
- **AnalysisController** (`controller/analysis_controller.py`): Manages analysis operations.
- **VisualizationController** (`controller/visualization_controller.py`): Manages visualization generation.

### 2.3 Business Logic Layer

The Business Logic Layer implements the core functionality:

- **GroundDataFetcher** (`src/data/ground_fetcher.py`): Fetches data from ground stations.
- **GriddedDataFetcher** (`src/data/gridded_fetcher.py`): Fetches data from gridded datasets.
- **GriddedDataAnalyzer** (`src/analysis/statistical_analyzer.py`): Analyzes and compares datasets.
- **ResultPlotter** (`src/visualization/plot_results.py`): Generates visualizations.

### 2.4 Data Layer

The Data Layer manages data and configuration:

- **DataConfig** (`config.py`): Base configuration for data fetching.
- **GroundDataConfig** (`config.py`): Configuration for ground data fetching.
- **GriddedDataConfig** (`config.py`): Configuration for gridded data fetching.

## 3. Communication Flow

### 3.1 UI to Controller

The UI communicates with the controllers through:
- Direct method calls for user actions (e.g., button clicks)
- Properties and attributes for state information

### 3.2 Controller to Business Logic

Controllers coordinate with the business logic through:
- Method calls to initiate operations
- Callback functions for progress reporting
- Background threads for long-running operations

### 3.3 Controller to UI

Controllers update the UI through:
- Signal-slot connections for asynchronous communication
- Callback functions for progress reporting

## 4. Threading Model

To ensure a responsive UI, the application uses a threading model:

1. **Main Thread**: Handles UI rendering and user interactions.
2. **Worker Threads**: Handle long-running operations such as data fetching, analysis, and visualization generation.

Thread communication is managed through PyQt's signals and slots mechanism.

## 5. Error Handling

The application implements a comprehensive error handling strategy:

1. **Exception Propagation**: Exceptions in the business logic are caught by controllers.
2. **User Feedback**: Controllers report errors to the UI for user notification.
3. **Logging**: All errors are logged for debugging purposes.

## 6. Extensibility Points

The architecture is designed for extensibility:

### 6.1 Adding New Data Sources

To add a new data source:
1. Create a new data fetcher class implementing the `DataFetcher` interface
2. Update the `GriddedDataConfig` class to include the new dataset
3. Update the UI to include the new dataset in the selection options

### 6.2 Adding New Analysis Methods

To add a new analysis method:
1. Extend the `GriddedDataAnalyzer` class with the new analysis functionality
2. Update the `AnalysisController` to support the new analysis method
3. Update the UI to provide options for the new analysis method

### 6.3 Adding New Visualization Types

To add a new visualization type:
1. Extend the `ResultPlotter` class with the new visualization functionality
2. Update the `VisualizationController` to support the new visualization type
3. Update the UI to allow selection of the new visualization type

## 7. File Storage

The application uses a simple file-based storage system:

- **Data/**: Raw data files downloaded from sources
- **Results/**: Statistical analysis results
- **Plots/**: Generated visualizations

## 8. Application Configuration

The application configuration is managed through:

- **config.py**: Contains configuration classes for various aspects of the application
- **settings.json**: Runtime settings saved between application sessions (future implementation)

## 9. Logging

The application uses Python's built-in logging module:

- Log messages are categorized by severity (INFO, WARNING, ERROR, etc.)
- Logs are written to a file and displayed in the console during development
- In production, logs are written to a file only