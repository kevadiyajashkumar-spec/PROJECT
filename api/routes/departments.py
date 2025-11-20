"""
Department Endpoints
Get department-level statistics and analysis.
"""

from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
import polars as pl

from api.dependencies import get_dataframe
from api.models.response_models import BaseResponse
from utils.calculations import get_department_stats

router = APIRouter(prefix="/api/v1/departments", tags=["Departments"])


@router.get("", response_model=BaseResponse)
async def list_departments(
    limit: int = Query(70, description="Number of departments"),
    offset: int = Query(0, description="Offset for pagination"),
    sort_by: str = Query("pass_rate", description="Sort by: pass_rate, exams, students")
):
    """
    List all departments with statistics.
    
    Returns:
        BaseResponse with department list
    """
    try:
        df = get_dataframe()
        dept_stats = get_department_stats(df)
        
        # Sort
        if sort_by == "exams":
            dept_stats = dept_stats.sort("exams", descending=True)
        elif sort_by == "students":
            dept_stats = dept_stats.sort("students", descending=True)
        else:
            dept_stats = dept_stats.sort("pass_rate", descending=True)
        
        total = dept_stats.height
        dept_stats = dept_stats.slice(offset, limit)
        
        dept_list = []
        for row in dept_stats.iter_rows(named=True):
            dept_list.append({
                "department": row['department'],
                "students": int(row['students']),
                "exams": int(row['exams']),
                "pass_count": int(row['pass_count']),
                "pass_rate": round(row['pass_rate'], 2)
            })
        
        return BaseResponse(
            status="success",
            message="Departments retrieved successfully",
            data={
                "departments": dept_list,
                "total": total,
                "limit": limit,
                "offset": offset
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving departments: {str(e)}",
            error_code="ERR_DEPT_001",
            timestamp=datetime.utcnow()
        )


@router.get("/{department_name}", response_model=BaseResponse)
async def get_department_details(department_name: str):
    """
    Get detailed statistics for a specific department.
    
    Args:
        department_name: Name of the department
        
    Returns:
        BaseResponse with department details
    """
    try:
        df = get_dataframe()
        dept_df = df.filter(pl.col('department') == department_name)
        
        if dept_df.height == 0:
            return BaseResponse(
                status="error",
                message=f"Department '{department_name}' not found",
                error_code="ERR_DEPT_404",
                timestamp=datetime.utcnow()
            )
        
        total_exams = dept_df.height
        unique_students = dept_df['student_id'].n_unique()
        
        # Pass/fail stats
        pass_fail_norm = dept_df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        pass_count = (pass_fail_norm == 'pass').sum()
        fail_count = (pass_fail_norm == 'fail').sum()
        dist_count = (dept_df['performance'] == 'Distinction').sum()
        
        pass_rate = (pass_count / total_exams * 100) if total_exams > 0 else 0
        fail_rate = (fail_count / total_exams * 100) if total_exams > 0 else 0
        dist_rate = (dist_count / total_exams * 100) if total_exams > 0 else 0
        
        # CIA/ESE averages
        cia_theory_avg = dept_df['cia_theory_avg'].mean()
        cia_practical_avg = dept_df['cia_practical_avg'].mean()
        ese_theory_avg = dept_df['ese_theory_internal'].mean()
        ese_practical_avg = dept_df['ese_practical_internal'].mean()
        
        return BaseResponse(
            status="success",
            message=f"Department '{department_name}' details retrieved successfully",
            data={
                "department": department_name,
                "unique_students": unique_students,
                "total_exams": total_exams,
                "pass_count": int(pass_count),
                "fail_count": int(fail_count),
                "distinction_count": int(dist_count),
                "pass_rate": round(pass_rate, 2),
                "fail_rate": round(fail_rate, 2),
                "distinction_rate": round(dist_rate, 2),
                "avg_cia_theory": round(cia_theory_avg, 2) if cia_theory_avg else None,
                "avg_cia_practical": round(cia_practical_avg, 2) if cia_practical_avg else None,
                "avg_ese_theory": round(ese_theory_avg, 2) if ese_theory_avg else None,
                "avg_ese_practical": round(ese_practical_avg, 2) if ese_practical_avg else None
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving department details: {str(e)}",
            error_code="ERR_DEPT_002",
            timestamp=datetime.utcnow()
        )


@router.get("/{department_name}/subjects", response_model=BaseResponse)
async def get_department_subjects(
    department_name: str,
    limit: int = Query(100, description="Number of subjects")
):
    """
    Get subjects taught in a department with pass rates.
    
    Args:
        department_name: Name of the department
        
    Returns:
        BaseResponse with subject list
    """
    try:
        df = get_dataframe()
        dept_df = df.filter(pl.col('department') == department_name)
        
        if dept_df.height == 0:
            return BaseResponse(
                status="error",
                message=f"Department '{department_name}' not found",
                error_code="ERR_DEPT_404",
                timestamp=datetime.utcnow()
            )
        
        # Get subjects with pass rates
        pass_fail_norm = dept_df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        
        subject_stats = (
            dept_df.with_columns(pass_fail_norm.alias('_pass_fail_norm'))
            .group_by('subject')
            .agg([
                pl.count().alias('exam_count'),
                (pl.col('_pass_fail_norm') == 'pass').sum().alias('pass_count'),
            ])
            .with_columns(
                (pl.col('pass_count') / pl.col('exam_count') * 100).alias('pass_rate')
            )
            .sort('pass_rate', descending=True)
            .head(limit)
        )
        
        subject_list = []
        for row in subject_stats.iter_rows(named=True):
            subject_list.append({
                "subject": row['subject'],
                "exam_count": int(row['exam_count']),
                "pass_count": int(row['pass_count']),
                "pass_rate": round(row['pass_rate'], 2)
            })
        
        return BaseResponse(
            status="success",
            message=f"Subjects for '{department_name}' retrieved successfully",
            data={
                "department": department_name,
                "subjects": subject_list,
                "total": subject_stats.height
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving department subjects: {str(e)}",
            error_code="ERR_DEPT_003",
            timestamp=datetime.utcnow()
        )


@router.get("/leaderboard", response_model=BaseResponse)
async def get_department_leaderboard(
    top_n: int = Query(10, description="Number of top/bottom departments")
):
    """
    Get top and bottom performing departments.
    
    Returns:
        BaseResponse with leaderboard data
    """
    try:
        df = get_dataframe()
        dept_stats = get_department_stats(df).sort('pass_rate')
        
        bottom = dept_stats.head(top_n)
        top = dept_stats.sort('pass_rate', descending=True).head(top_n)
        
        top_list = []
        for i, row in enumerate(top.iter_rows(named=True), 1):
            top_list.append({
                "rank": i,
                "department": row['department'],
                "pass_rate": round(row['pass_rate'], 2),
                "exams": int(row['exams']),
                "students": int(row['students'])
            })
        
        bottom_list = []
        for i, row in enumerate(bottom.iter_rows(named=True), 1):
            bottom_list.append({
                "rank": i,
                "department": row['department'],
                "pass_rate": round(row['pass_rate'], 2),
                "exams": int(row['exams']),
                "students": int(row['students'])
            })
        
        return BaseResponse(
            status="success",
            message="Department leaderboard retrieved successfully",
            data={
                "top": top_list,
                "bottom": bottom_list
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving leaderboard: {str(e)}",
            error_code="ERR_DEPT_004",
            timestamp=datetime.utcnow()
        )
