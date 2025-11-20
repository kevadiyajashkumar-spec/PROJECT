"""
Pydantic models for API requests.
Request body validation for POST/PUT endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FilterRequest(BaseModel):
    """Advanced filter request."""
    year: Optional[int] = Field(None, description="Exam year")
    department: Optional[str] = Field(None, description="Department name")
    subject: Optional[str] = Field(None, description="Subject name")
    pass_fail: Optional[str] = Field(None, description="Pass or Fail")
    performance: Optional[str] = Field(None, description="Performance category")
    limit: int = Field(default=100, description="Number of records to return")
    offset: int = Field(default=0, description="Offset for pagination")

    class Config:
        schema_extra = {
            "example": {
                "year": 2024,
                "department": "MBA",
                "subject": "Management",
                "pass_fail": "Pass",
                "performance": "Distinction",
                "limit": 50,
                "offset": 0
            }
        }


class BatchStudentRequest(BaseModel):
    """Batch request for multiple students."""
    student_ids: List[int] = Field(..., description="List of student IDs")
    include_results: bool = Field(default=False, description="Include exam results")

    class Config:
        schema_extra = {
            "example": {
                "student_ids": [1001, 1002, 1003],
                "include_results": True
            }
        }


class ExportRequest(BaseModel):
    """Export request."""
    format: str = Field(..., description="Export format: csv or json")
    filters: Optional[FilterRequest] = Field(None, description="Filters to apply")

    class Config:
        schema_extra = {
            "example": {
                "format": "csv",
                "filters": {
                    "year": 2024,
                    "department": "MBA"
                }
            }
        }
