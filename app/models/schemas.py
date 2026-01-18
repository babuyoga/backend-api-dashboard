"""
Pydantic Schemas Module

This module defines the data models (schemas) used for:
- API request validation
- API response serialization
- OpenAPI documentation generation

All models use Pydantic for automatic validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ProjectMetadata(BaseModel):
    """Basic project information - description and client name."""
    description: str
    client: str


class MetricTotal(BaseModel):
    """Total metric values for two periods with their difference."""
    period1: str      # Label for first period (e.g., "january-2023")
    period2: str      # Label for second period
    file1: float      # Value in first period
    file2: float      # Value in second period
    difference: float # Difference (file2 - file1)


class CostlineChild(BaseModel):
    """Deepest level cost item (sub-subcategory)."""
    category: str
    file1_metric: float
    file2_metric: float
    difference: float


class CostlineSubcategory(BaseModel):
    """Mid-level cost category containing child items."""
    category: str
    file1_metric: float
    file2_metric: float
    difference: float
    children: List[CostlineChild]


class CostlineTrajectory(BaseModel):
    """Top-level cost type (e.g., '10 - Direct', '70 - Variations')."""
    category: str
    file1_metric: float
    file2_metric: float
    difference: float
    subcategories: List[CostlineSubcategory]


class ProjectAnalysis(BaseModel):
    """Complete analysis result for a single project."""
    project_meta: ProjectMetadata
    total_forecast_costs_at_completion: Optional[MetricTotal] = None
    total_ytd_actual: Optional[MetricTotal] = None
    costline_increases_trajectory: List[CostlineTrajectory]


class ForecastComparisonRequest(BaseModel):
    """
    Request body for the forecast comparison endpoint.
    
    Attributes:
        from_period: Start period in YYYYMM format (e.g., "202301")
        to_period: End period in YYYYMM format
        project_no: Project ID to analyze
        metric: Which metric to compare
    """
    from_period: str = Field(..., pattern=r"^\d{6}$", description="Format: YYYYMM")
    to_period: str = Field(..., pattern=r"^\d{6}$", description="Format: YYYYMM")
    project_no: int
    metric: str = Field(..., pattern="^(forecast_costs_at_completion|ytd_actual)$")



class ForecastComparisonResponse(BaseModel):
    """Response containing analysis for all matching projects."""
    projects: Dict[str, ProjectAnalysis]


class ProjectSummaryRequest(BaseModel):
    """
    Request body for the overall project summary endpoint.
    
    Attributes:
        period: Period to analyze in YYYYMM format
        metric: Metric to summarize (e.g., 'forecast_costs_at_completion')
    """
    period: str = Field(..., pattern=r"^\d{6}$", description="Format: YYYYMM")
    metric: str = Field(..., pattern="^(forecast_costs_at_completion|ytd_actual)$")