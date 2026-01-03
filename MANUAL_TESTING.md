# Manual Testing Guide

This guide explains how to manually test the Finance Dashboard API endpoints.

---

## Prerequisites

1. **Start the Server**

   ```bash
   # Activate virtual environment
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # Start the development server
   uvicorn app.main:app --reload
   ```

2. **Verify Server is Running**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy"}
   ```

---

## Testing Methods

### Method 1: Swagger UI (Recommended)

The easiest way to test is via the interactive Swagger documentation:

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click **"Try it out"**
4. Fill in the parameters
5. Click **"Execute"**
6. View the response below

### Method 2: ReDoc

For a cleaner documentation view: http://localhost:8000/redoc

### Method 3: cURL Commands

Use the terminal commands below.

### Method 4: API Clients

Import the OpenAPI spec into:

- **Postman**: Import from `http://localhost:8000/openapi.json`
- **Insomnia**: Same URL
- **Thunder Client** (VS Code extension)

---

## Endpoint Reference

### Health & Info Endpoints

#### `GET /` — API Info

```bash
curl http://localhost:8000/
```

**Expected Response:**

```json
{ "message": "Finance Dashboard API", "version": "1.0.0" }
```

---

#### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**

```json
{ "status": "healthy" }
```

---

### Project Endpoints

#### `GET /api/projects/periods` — List Available Periods

Returns all periods (YYYYMM format) that have data in the database.

```bash
curl http://localhost:8000/api/projects/periods
```

**Expected Response:**

```json
{
  "periods": ["202301", "202302", "202303", ...]
}
```

**What to verify:**

- [ ] Returns a sorted list of period strings
- [ ] All periods are in YYYYMM format (6 digits)
- [ ] Response status is 200

---

#### `GET /api/projects/list` — List Available Projects

Returns all project numbers with data in the system.

```bash
curl http://localhost:8000/api/projects/list
```

**Expected Response:**

```json
{
  "projects": [2035, 2121, 2171, 2172, 2208, ...]
}
```

**What to verify:**

- [ ] Returns a sorted list of project numbers (integers)
- [ ] Response status is 200

---

### Analysis Endpoints

#### `POST /api/analysis/forecast-comparison` — Compare Costs Between Periods

This is the main analysis endpoint. Compares project costs between two time periods.

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

**Request Body Parameters:**

| Parameter   | Type   | Required | Description                                    |
| ----------- | ------ | -------- | ---------------------------------------------- |
| from_period | string | Yes      | Start period (YYYYMM format)                   |
| to_period   | string | Yes      | End period (YYYYMM format)                     |
| project_no  | int    | Yes      | Project ID to analyze                          |
| metric      | string | Yes      | `forecast_costs_at_completion` or `ytd_actual` |

**Expected Response Structure:**

```json
{
  "projects": {
    "2208": {
      "project_meta": {
        "description": "Project Description",
        "client": "Client Name"
      },
      "total_forecast_costs_at_completion": {
        "period1": "january-2023",
        "period2": "january-2024",
        "file1": 1000000.00,
        "file2": 1200000.00,
        "difference": 200000.00
      },
      "costline_increases_trajectory": [
        {
          "category": "10 - Direct",
          "file1_metric": 500000,
          "file2_metric": 600000,
          "difference": 100000,
          "subcategories": [...]
        }
      ]
    }
  }
}
```

**Test Cases:**

| Test Case                            | Expected Result        |
| ------------------------------------ | ---------------------- |
| Valid periods & project              | 200 with analysis data |
| Invalid period format (e.g., "2023") | 422 Validation Error   |
| Non-existent period                  | 404 Not Found          |
| Invalid metric name                  | 422 Validation Error   |

**Example: Test with ytd_actual metric**

```bash
curl -X POST "http://localhost:8000/api/analysis/forecast-comparison" \
  -H "Content-Type: application/json" \
  -d '{
    "from_period": "202301",
    "to_period": "202312",
    "project_no": 2171,
    "metric": "ytd_actual"
  }'
```

---

#### `GET /api/analysis/summary/{project_no}` — Get Project Summary

Generates a human-readable text summary for AI chat integration.

```bash
curl "http://localhost:8000/api/analysis/summary/2208?from_period=202301&to_period=202401&metric=forecast_costs_at_completion"
```

**Path Parameter:**

- `project_no` (int): Project ID

**Query Parameters:**

| Parameter   | Type   | Required | Description                                    |
| ----------- | ------ | -------- | ---------------------------------------------- |
| from_period | string | Yes      | Start period (YYYYMM format)                   |
| to_period   | string | Yes      | End period (YYYYMM format)                     |
| metric      | string | Yes      | `forecast_costs_at_completion` or `ytd_actual` |

**Expected Response:**

```json
{
  "summary": "Project 2208 shows a forecast cost increase of $200,000 between January 2023 and January 2024. The main drivers are..."
}
```

---

## Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**

| Code | Meaning          | When It Occurs                          |
| ---- | ---------------- | --------------------------------------- |
| 200  | Success          | Request completed successfully          |
| 404  | Not Found        | No data for specified period/project    |
| 422  | Validation Error | Invalid request parameters              |
| 500  | Server Error     | Database connection or analysis failure |

---

## Testing Checklist

Use this checklist to verify all endpoints are working:

### Basic Connectivity

- [ ] Server starts without errors
- [ ] `GET /` returns API info
- [ ] `GET /health` returns healthy status

### Projects API

- [ ] `GET /api/projects/periods` returns period list
- [ ] `GET /api/projects/list` returns project list

### Analysis API

- [ ] `POST /api/analysis/forecast-comparison` with valid data returns analysis
- [ ] `POST /api/analysis/forecast-comparison` with invalid period returns 422
- [ ] `GET /api/analysis/summary/{project_no}` returns text summary

### Error Handling

- [ ] Invalid JSON body returns 422
- [ ] Non-existent project returns appropriate error
- [ ] Database connection failure returns 500

---

## Tips

1. **Use Pretty Print**: Add `| python -m json.tool` after curl commands for formatted output:

   ```bash
   curl http://localhost:8000/api/projects/periods | python -m json.tool
   ```

2. **Save Responses**: Redirect output to files for comparison:

   ```bash
   curl http://localhost:8000/api/projects/periods > periods.json
   ```

3. **Check Database**: If endpoints return empty data, verify your `.env` database configuration is correct.
