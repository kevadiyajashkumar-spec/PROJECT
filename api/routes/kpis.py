"""
KPI Endpoints
Get key performance indicators and statistics.
"""

from datetime import datetime
from fastapi import APIRouter, Query
import polars as pl

from api.dependencies import get_dataframe
from api.models.response_models import (
    BaseResponse, KPIResponse, YearlyKPIResponse, 
    DepartmentStatsResponse, FilterOptionsResponse
)
from utils.calculations import calculate_rates, get_yearly_data, get_department_stats

router = APIRouter(prefix="/api/v1/kpis", tags=["KPIs"])


@router.get("/overall", response_model=BaseResponse)
async def get_overall_kpis(
    year: int = Query(None, description="Filter by year"),
    department: str = Query(None, description="Filter by department")
):
    """
    Get overall pass rate, fail rate, and distinction rate.
    
    Returns:
        BaseResponse with KPI data
    """
    try:
        df = get_dataframe()
        
        # Apply filters
        if year:
            df = df.filter(pl.col('exam_year') == year)
        if department:
            df = df.filter(pl.col('department') == department)
        
        pass_rate, dist_rate, fail_rate, unique_students, total_exams = calculate_rates(df)
        
        kpi_data = KPIResponse(
            pass_rate=round(pass_rate, 2),
            fail_rate=round(fail_rate, 2),
            distinction_rate=round(dist_rate, 2),
            unique_students=unique_students,
            total_exams=total_exams,
            last_updated=datetime.utcnow()
        )
        
        return BaseResponse(
            status="success",
            message="KPI data retrieved successfully",
            data=kpi_data.dict(),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving KPI data: {str(e)}",
            error_code="ERR_KPI_001",
            timestamp=datetime.utcnow()
        )


@router.get("/yearly", response_model=BaseResponse)
async def get_yearly_kpis(
    department: str = Query(None, description="Filter by department")
):
    """
    Get year-over-year performance metrics.
    
    Returns:
        BaseResponse with yearly KPI data
    """
    try:
        df = get_dataframe()
        
        if department:
            df = df.filter(pl.col('department') == department)
        
        yearly = get_yearly_data(df)
        
        yearly_list = []
        for row in yearly.iter_rows(named=True):
            yearly_list.append(YearlyKPIResponse(
                exam_year=int(row['exam_year']),
                unique_students=int(row['unique_students']),
                total_exams=int(row['total_exams']),
                pass_count=int(row['pass_count']),
                fail_count=int(row['fail_count']),
                dist_count=int(row['dist_count']),
                pass_rate=round(row['pass_rate'], 2),
                fail_rate=round(row['fail_rate'], 2),
                dist_rate=round(row['dist_rate'], 2)
            ).dict())
        
        return BaseResponse(
            status="success",
            message="Yearly KPI data retrieved successfully",
            data=yearly_list,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving yearly KPI data: {str(e)}",
            error_code="ERR_KPI_002",
            timestamp=datetime.utcnow()
        )


@router.get("/department-stats", response_model=BaseResponse)
async def get_department_kpis(
    limit: int = Query(70, description="Number of departments to return"),
    sort_by: str = Query("pass_rate", description="Sort by: pass_rate, exam_count, students")
):
    """
    Get department-wise statistics.
    
    Returns:
        BaseResponse with department statistics
    """
    try:
        df = get_dataframe()
        dept_stats = get_department_stats(df)
        
        # Sort
        if sort_by == "exam_count":
            dept_stats = dept_stats.sort("exams", descending=True)
        elif sort_by == "students":
            dept_stats = dept_stats.sort("students", descending=True)
        else:
            dept_stats = dept_stats.sort("pass_rate", descending=True)
        
        dept_list = []
        for i, row in enumerate(dept_stats.head(limit).iter_rows(named=True), 1):
            dept_list.append({
                "rank": i,
                "department": row['department'],
                "students": int(row['students']),
                "exams": int(row['exams']),
                "pass_count": int(row['pass_count']),
                "pass_rate": round(row['pass_rate'], 2)
            })
        
        return BaseResponse(
            status="success",
            message=f"Department statistics retrieved (showing {len(dept_list)} of {dept_stats.height})",
            data=dept_list,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving department statistics: {str(e)}",
            error_code="ERR_KPI_003",
            timestamp=datetime.utcnow()
        )


@router.get("/filters", response_model=BaseResponse)
async def get_filter_options():
    """
    Get available filter options for all endpoints.
    
    Returns:
        BaseResponse with filter options
    """
    try:
        df = get_dataframe()
        
        departments = sorted(df['department'].unique().to_list())
        subjects = sorted(df['subject'].unique().to_list())
        years = sorted(df['exam_year'].unique().to_list())
        
        filter_opts = FilterOptionsResponse(
            departments=departments,
            subjects=subjects,
            years=years
        )
        
        return BaseResponse(
            status="success",
            message="Filter options retrieved successfully",
            data=filter_opts.dict(),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving filter options: {str(e)}",
            error_code="ERR_KPI_004",
            timestamp=datetime.utcnow()
        )
