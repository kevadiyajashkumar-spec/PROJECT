"""
Pydantic models for API responses.
Standard response structure for all endpoints.
"""

from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response wrapper for all API endpoints."""
    status: str = Field(..., description="success or error")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    data: Optional[Any] = Field(None, description="Response data")
    error_code: Optional[str] = Field(None, description="Error code if error")


class KPIResponse(BaseModel):
    """Global KPI metrics response."""
    pass_rate: float = Field(..., description="Pass rate percentage")
    fail_rate: float = Field(..., description="Fail rate percentage")
    distinction_rate: float = Field(..., description="Distinction rate percentage")
    unique_students: int = Field(..., description="Total unique students")
    total_exams: int = Field(..., description="Total exam records")
    last_updated: datetime = Field(..., description="When data was last updated")


class YearlyKPIResponse(BaseModel):
    """Yearly KPI metrics."""
    exam_year: int = Field(..., description="Academic year")
    unique_students: int = Field(..., description="Unique students in year")
    total_exams: int = Field(..., description="Total exams in year")
    pass_count: int = Field(..., description="Number of passes")
    fail_count: int = Field(..., description="Number of fails")
    dist_count: int = Field(..., description="Number of distinctions")
    pass_rate: float = Field(..., description="Pass rate percentage")
    fail_rate: float = Field(..., description="Fail rate percentage")
    dist_rate: float = Field(..., description="Distinction rate percentage")


class DepartmentStatsResponse(BaseModel):
    """Department statistics."""
    department: str = Field(..., description="Department name")
    students: int = Field(..., description="Number of students")
    exams: int = Field(..., description="Number of exams")
    pass_count: int = Field(..., description="Number of passes")
    pass_rate: float = Field(..., description="Pass rate percentage")


class SubjectDifficultyResponse(BaseModel):
    """Subject difficulty metrics."""
    subject: str = Field(..., description="Subject name")
    avg_total_marks: float = Field(..., description="Average total marks")
    exam_count: int = Field(..., description="Number of exams")
    pass_rate: float = Field(..., description="Pass rate percentage")


class StudentPerformanceResponse(BaseModel):
    """Student performance metrics."""
    student_id: int = Field(..., description="Student ID")
    name: Optional[str] = Field(None, description="Student name")
    department: str = Field(..., description="Department")
    total_exams: int = Field(..., description="Total exams taken")
    pass_exams: int = Field(..., description="Exams passed")
    pass_rate: float = Field(..., description="Pass rate percentage")
    distinction_count: int = Field(..., description="Number of distinctions")


class FilterOptionsResponse(BaseModel):
    """Available filter options."""
    departments: List[str] = Field(..., description="List of departments")
    subjects: List[str] = Field(..., description="List of subjects")
    years: List[int] = Field(..., description="List of available years")
    pass_fail_options: List[str] = Field(default=["Pass", "Fail"], description="Pass/fail options")
    performance_options: List[str] = Field(default=["Pass", "Fail", "Distinction"], description="Performance options")


class PaginatedResponse(BaseModel):
    """Response with pagination."""
    data: List[Any] = Field(..., description="Response data array")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset from start")


class ExportResponse(BaseModel):
    """Export response."""
    format: str = Field(..., description="Export format (csv/json)")
    download_url: str = Field(..., description="URL to download file")
    file_name: str = Field(..., description="Name of the file")
    record_count: int = Field(..., description="Number of records exported")
