# Finance Dashboard API

A FastAPI backend for financial forecast analysis. This API replaces the original Streamlit dashboard, providing RESTful endpoints that can be consumed by a Next.js frontend or any other client.

## Features

- **Period Comparison**: Compare project costs between any two time periods
- **Deep Cost Analysis**: Drill down from main cost types → subcategories → sub-subcategories
- **Project Grouping**: Automatically combines related projects (e.g., 2171 & 2172)
- **Text Summaries**: Generate human-readable summaries for AI chat integration
- **Interactive Docs**: Auto-generated Swagger UI at `/docs`

## Quick Start

### 1. Prerequisites

- Python 3.10+
- SQL Server with ODBC Driver 17
- Access to the finance database

### 2. Installation

```bash
# Clone and navigate to the backend
cd fastapi-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your database connection details:

```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_server_hostname
DB_NAME=your_database_name
DB_DRIVER=ODBC Driver 17 for SQL Server
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- **API Root**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Info

| Method | Endpoint  | Description                     |
| ------ | --------- | ------------------------------- |
| GET    | `/`       | API information                 |
| GET    | `/health` | Health check for load balancers |

### Projects

| Method | Endpoint                | Description                            |
| ------ | ----------------------- | -------------------------------------- |
| GET    | `/api/projects/periods` | List available periods (YYYYMM format) |
| GET    | `/api/projects/list`    | List available project numbers         |

### Analysis

| Method | Endpoint                             | Description                       |
| ------ | ------------------------------------ | --------------------------------- |
| POST   | `/api/analysis/forecast-comparison`  | Compare costs between two periods |
| GET    | `/api/analysis/summary/{project_no}` | Get text summary for AI chat      |

## Example Usage

### Compare Forecasts

```bash
curl -X POST "http://localhost:8000/api/analysis/forecast-comparison" \
  -H "Content-Type: application/json" \
  -d '{
    "from_period": "202301",
    "to_period": "202401",
    "project_no": 2208,
    "metric": "forecast_costs_at_completion"
  }'
```

### Get Available Periods

```bash
curl "http://localhost:8000/api/projects/periods"
```

## Project Structure

```
fastapi-backend/
├── app/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration & environment variables
│   ├── database.py          # SQLAlchemy database connection
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic request/response models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py      # /api/analysis/* endpoints
│   │   └── projects.py      # /api/projects/* endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_processor.py  # Data transformation logic
│   │   └── sql_queries.py     # SQL queries & DB functions
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Utility functions
├── .env.example             # Environment template
├── Dockerfile               # Container build instructions
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Key Concepts

### Metrics

The API supports two metrics:

- `forecast_costs_at_completion` (rForecast): Projected total cost
- `ytd_actual` (rYearAct): Year-to-date actual costs

### Project Grouping

Some projects are related and should be analyzed together. The `projects_list` in `config.py` defines these groupings:

```python
"2171": [2171, 2172],  # These two projects are combined
"2172": [2171, 2172],
```

### Cost Hierarchy

Data is structured in three levels:

1. **Main Cost Type** (e.g., "10 - Direct", "70 - Variations")
2. **Subcategory** (e.g., "Labor", "Materials")
3. **Sub-subcategory** (individual cost items)

## Docker Deployment

Build and run with Docker:

```bash
docker build -t finance-api .
docker run -p 8000:8000 --env-file .env finance-api
```

## Development

### Adding New Endpoints

1. Create a new router in `app/routers/`
2. Add Pydantic models in `app/models/schemas.py`
3. Register the router in `app/main.py`

### Running Tests

```bash
pytest tests/
```

## Mapping from Streamlit

| Original Streamlit Function    | FastAPI Equivalent                       |
| ------------------------------ | ---------------------------------------- |
| `run_forecast_pipeline_json()` | `POST /api/analysis/forecast-comparison` |
| `get_filter_options()`         | `GET /api/projects/periods` + `/list`    |
| `hand_crafted_summary()`       | `GET /api/analysis/summary/{project_no}` |
| `st.session_state`             | React Query cache (frontend)             |
| `@st.cache_data`               | Response caching (future)                |

## License

Internal use only.
