"""
Finance Dashboard API - Main Application Entry Point

This module initializes the FastAPI application and configures:
- CORS middleware for Next.js frontend communication
- API routers for projects and analysis endpoints
- Health check and root endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import projects, analysis

# Initialize FastAPI application with metadata for OpenAPI docs
app = FastAPI(
    title="Finance Dashboard API",
    version="1.0.0",
    description="API for financial forecast analysis - compares project costs across periods"
)

# Configure CORS to allow requests from the Next.js frontend
# In production, replace with your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with their URL prefixes
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


@app.get("/")
def root():
    """
    Root endpoint - returns API information.
    Useful for verifying the API is running.
    """
    return {"message": "Finance Dashboard API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns a simple status indicating the API is operational.
    """
    return {"status": "healthy"}