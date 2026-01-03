"""
Configuration Module

This module centralizes all application configuration including:
- Database connection settings (loaded from environment variables)
- LLM API settings for AI chat functionality
- Metric mappings between API names and database column names
- Project groupings for combining related projects
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Test Mode Configuration
# When TEST_MODE=true, the app uses XLSX dummy data instead of SQL Server
# =============================================================================
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# =============================================================================
# Database Configuration
# These settings connect to the SQL Server database
# =============================================================================
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

# =============================================================================
# LLM API Configuration
# Used for AI-powered chat about project data
# =============================================================================
URL = os.getenv("LLM_API_URL", "")
api_key = os.getenv("LLM_API_KEY", "")
TEMPERATURE = 0.4
MAX_TOKENS = 5000
FREQUENCY_PENALTY = 0.5

# =============================================================================
# Metric Mapping
# Maps API metric names to database column names
# =============================================================================
metric_map = {
    "forecast_costs_at_completion": "rForecast",  # Forecast costs column
    "ytd_actual": "rYearAct"                       # Year-to-date actual column
}

# Default columns used for project identification
PROJECT_KEYS_DEFAULT = ["iProjNo", "iProjYear", "cProjDesc", "cClientDesc"]

# =============================================================================
# Project Groupings
# Defines which projects should be combined in reports
# Format: {"key": single_id} or {"key": [id1, id2]} for grouped projects
# =============================================================================
projects_list = {
    "2035": 2035,
    "2121": 2121,
    "2171": [2171, 2172],
    "2172": [2171, 2172],
    "2222": 2222,
    "2300": [2300, 2301],
    "2301": [2300, 2301],
    "2302": [2302, 2303],
    "2303": [2302, 2303],
    "2369": 2369,
    "2377": [2377, 8353],
    "8353": [2377, 8353],
    "2412": [2412, 2413],
    "2413": [2412, 2413],
    "2462": 2462,
    "2523": 2523,
    "2543": 2543,
    "2631": 2631,
    "2642": [2642, 2883],
    "2883": [2642, 2883],
    "2682": 2682,
    "2683": 2683,
    "2705": 2705,
    "2706": 2706,
    "2722": 2722,
    "2734": [2734, 2735],
    "2735": [2734, 2735],
    "2745": 2745,
    "2790": [2790, 2791],
    "2791": [2790, 2791],
    "2792": [2792, 2793],
    "2793": [2792, 2793],
    "2800": 2800,
    "2820": 2820,
    "2824": 2824,
    "2859": 2859,
    "2891": 2891,
    "2913": 2913,
    "2993": 2993,
    "7279": 7279,
    "8288": 8288,
    "8405": 8405
}
