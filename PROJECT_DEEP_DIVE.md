# Project Deep Dive: Architecture & API Reference

This document provides a comprehensive technical breakdown of the Finance Dashboard Backend. It explains the purpose of every folder and file, details the API endpoints, and illustrates how data flows through the system.

## 1. System Architecture

The project follows a standard **FastAPI** layered architecture, separating concerns into Routers (API handling), Services (Business Logic), and Database interactions.

### High-Level Data Flow

```mermaid
graph TD
    Client[Frontend / Client] -->|HTTP Request| API[API Routers (app/routers)]
    API -->|Calls| ServiceLogic[Data Processor (app/services/data_processor.py)]
    ServiceLogic -->|Requests Data| DataLayer[SQL Queries (app/services/sql_queries.py)]

    subgraph Data Sources
        DataLayer -->|TEST_MODE=True| Excel[Excel Dummy Files (.xlsx)]
        DataLayer -->|TEST_MODE=False| SQL[SQL Server Database]
    end

    DataLayer -->|Returns DataFrame| ServiceLogic
    ServiceLogic -->|Returns Analyzed JSON| API
    API -->|JSON Response| Client
```

## 2. Folder & File Structure

Here is the complete breakdown of the project structure (`app/` directory):

### Root Level

- **`main.py`**: The entry point of the application. It initializes the `FastAPI` app, configures CORS (to allow the frontend to talk to it), and registers the routers.
- **`config.py`**: Central configuration. Loads environment variables (DB credentials, Test Mode flag) and defines static configurations like `metric_map` and `projects_list` (project groupings).
- **`database.py`**: Handles the database connection logic using SQLAlchemy. It creates the engine and session factory.

### `routers/` (API Layer)

This directory contains the "Controllers" of the application.

- **`projects.py`**: Handles endpoints for fetching metadata (lists of projects and periods) to populate dropdown filters.
- **`analysis.py`**: The core business endpoints. Handles the logic for comparing forecasts between two periods and generating summaries.

### `services/` (Business Logic)

This directory contains the heavy lifting.

- **`sql_queries.py`**: The data access layer. It contains the raw SQL queries and the switch logic to load from Excel if `TEST_MODE` is on.
- **`data_processor.py`**: The "brains" of the operation. It takes the raw data (pandas DataFrame) and transforms it into the complex nested JSON structure required by the frontend. It also computes the differences between periods.

### `models/` (Data Structures)

- **`schemas.py`**: Pydantic models that define the expected request bodies and response structures. Ensures type safety for API inputs.

### `utils/` (Helpers)

- **`helpers.py`**: Generic utility functions used by services (e.g., string formatting, safe number conversion).

## 3. detailed API Reference

### A. Projects & Metadata (`/api/projects`)

#### 1. Get Available Periods

- **Endpoint**: `GET /api/projects/periods`
- **Function**: `get_available_periods` in `routers/projects.py`
- **Description**: Scans availability to return a list of valid reporting periods (YYYYMM).
- **Usage**: Frontend uses this to populate the "From Period" and "To Period" dropdowns.

#### 2. Get Available Projects

- **Endpoint**: `GET /api/projects/list`
- **Function**: `get_available_projects` in `routers/projects.py`
- **Description**: Returns a sorted list of all Project IDs available in the dataset.
- **Usage**: Frontend uses this to populate the "Project" dropdown.

### B. Core Analysis (`/api/analysis`)

#### 1. Compare Forecasts

- **Endpoint**: `POST /api/analysis/forecast-comparison`
- **Function**: `compare_forecasts` in `routers/analysis.py`
- **Input**:
  ```json
  {
    "from_period": "202305",
    "to_period": "202312",
    "project_no": 2171,
    "metric": "forecast_costs_at_completion"
  }
  ```
- **Process**:
  1.  Calls `query_batch_to_df` for both periods to get raw data.
  2.  Calls `combine_projects_rows` to merge related projects (defined in `config.py`) if applicable.
  3.  Calls `table_to_nested_json` to convert the flat table into a hierarchical tree (Project -> Section -> Cost Type -> Category).
  4.  Calls `compute_forecast_diff` to calculate the monetary difference for every node in that tree between the two periods.
- **Output**: A complex JSON object detailing the "trajectory" of cost increases/decreases.

#### 2. Get Project Summary

- **Endpoint**: `GET /api/analysis/summary/{project_no}`
- **Function**: `get_project_summary` in `routers/analysis.py`
- **Description**: Runs the comparison (same as above) but then passes the result to `hand_crafted_summary`.
- **Process**:
  - Executes the comparison logic.
  - Feeds the result into a text generator that interprets the numbers into English sentences (e.g., "Main Cost Type X increased by 5 million...").
- **Output**:
  ```json
  {
    "summary": "Job No: 2171... There is an increase in the total forecast..."
  }
  ```

## 4. Key Functions Explained

### `app/services/sql_queries.py`

- **`query_batch_to_df(db, period)`**: The gatekeeper. Checks `TEST_MODE`. Only calls the database if false.
- **`base_sql`**: A massive SQL query string used to join 9+ tables (`Ac_JcPackageDt`, `Ac_Client`, etc.) to get every detail of a project's financials.

### `app/services/data_processor.py`

- **`table_to_nested_json(df)`**: Converts a flat SQL result set (rows and columns) into a nested JSON structure that represents the project hierarchy.
- **`compute_forecast_diff(json_paths)`**: Takes two JSON files (representing two periods), walks through their trees, and subtracts the values to find exactly where costs changed.
- **`hand_crafted_summary(result)`**: A specialized string builder that iterates through the diff results to create a human-readable text report.
