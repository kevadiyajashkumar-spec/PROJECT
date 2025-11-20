"""
Student Endpoints
Get individual student performance and results.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Query
import polars as pl

from api.dependencies import get_dataframe
from api.models.response_models import BaseResponse
from api.models.request_models import BatchStudentRequest

router = APIRouter(prefix="/api/v1/students", tags=["Students"])


@router.get("/search", response_model=BaseResponse)
async def search_students(
    query: str = Query(..., description="Student ID, name, or department"),
    limit: int = Query(50, description="Number of results"),
    search_type: str = Query("all", description="all, id, name, or department")
):
    """
    Search students by ID, name, or department.
    
    Args:
        query: Search query
        limit: Number of results
        search_type: Type of search
        
    Returns:
        BaseResponse with student list
    """
    try:
        df = get_dataframe()
        
        # Filter by search type
        if search_type == "id":
            try:
                student_id = int(query)
                results = df.filter(pl.col('student_id') == student_id)
            except:
                results = df.filter(pl.lit(False))
        elif search_type == "name":
            results = df.filter(
                pl.col('student_name').str.to_lowercase().str.contains(query.lower())
            )
        elif search_type == "department":
            results = df.filter(
                pl.col('department').str.to_lowercase().str.contains(query.lower())
            )
        else:  # all
            results = df.filter(
                (pl.col('student_id').cast(pl.Utf8).str.contains(query)) |
                (pl.col('student_name').str.to_lowercase().str.contains(query.lower())) |
                (pl.col('department').str.to_lowercase().str.contains(query.lower()))
            )
        
        # Get unique students
        unique_students = results.select(['student_id', 'student_name', 'department']).unique()
        unique_students = unique_students.head(limit)
        
        student_list = []
        for row in unique_students.iter_rows(named=True):
            student_list.append({
                "student_id": int(row['student_id']),
                "name": row['student_name'],
                "department": row['department']
            })
        
        return BaseResponse(
            status="success",
            message=f"Found {len(student_list)} students",
            data=student_list,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error searching students: {str(e)}",
            error_code="ERR_STU_001",
            timestamp=datetime.utcnow()
        )


@router.get("/{student_id}", response_model=BaseResponse)
async def get_student_details(student_id: int):
    """
    Get individual student details.
    
    Args:
        student_id: Student ID
        
    Returns:
        BaseResponse with student details
    """
    try:
        df = get_dataframe()
        student_df = df.filter(pl.col('student_id') == student_id)
        
        if student_df.height == 0:
            return BaseResponse(
                status="error",
                message=f"Student {student_id} not found",
                error_code="ERR_STU_404",
                timestamp=datetime.utcnow()
            )
        
        first_row = student_df.row(0, named=True)
        
        return BaseResponse(
            status="success",
            message=f"Student {student_id} details retrieved",
            data={
                "student_id": student_id,
                "name": first_row['student_name'],
                "gender": first_row['gender'],
                "nationality": first_row['nationality'],
                "department": first_row['department'],
                "campus": first_row['campus'],
                "total_exams": student_df.height,
                "years_active": sorted(student_df['exam_year'].unique().to_list())
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving student details: {str(e)}",
            error_code="ERR_STU_002",
            timestamp=datetime.utcnow()
        )


@router.get("/{student_id}/performance", response_model=BaseResponse)
async def get_student_performance(student_id: int):
    """
    Get student performance metrics.
    
    Args:
        student_id: Student ID
        
    Returns:
        BaseResponse with performance metrics
    """
    try:
        df = get_dataframe()
        student_df = df.filter(pl.col('student_id') == student_id)
        
        if student_df.height == 0:
            return BaseResponse(
                status="error",
                message=f"Student {student_id} not found",
                error_code="ERR_STU_404",
                timestamp=datetime.utcnow()
            )
        
        total_exams = student_df.height
        
        # Pass/fail counts
        pass_fail_norm = student_df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        pass_count = (pass_fail_norm == 'pass').sum()
        fail_count = (pass_fail_norm == 'fail').sum()
        distinction_count = (student_df['performance'] == 'Distinction').sum()
        
        pass_rate = (pass_count / total_exams * 100) if total_exams > 0 else 0
        
        # Averages
        avg_cia_theory = student_df['cia_theory_avg'].mean()
        avg_ese_theory = student_df['ese_theory_internal'].mean()
        
        return BaseResponse(
            status="success",
            message=f"Performance metrics for student {student_id}",
            data={
                "student_id": student_id,
                "total_exams": total_exams,
                "pass_exams": int(pass_count),
                "fail_exams": int(fail_count),
                "distinctions": int(distinction_count),
                "pass_rate": round(pass_rate, 2),
                "avg_cia_theory": round(avg_cia_theory, 2) if avg_cia_theory else None,
                "avg_ese_theory": round(avg_ese_theory, 2) if avg_ese_theory else None
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving performance: {str(e)}",
            error_code="ERR_STU_003",
            timestamp=datetime.utcnow()
        )


@router.get("/{student_id}/results", response_model=BaseResponse)
async def get_student_results(
    student_id: int,
    limit: int = Query(100, description="Number of results"),
    year: int = Query(None, description="Filter by year")
):
    """
    Get all exam results for a student.
    
    Args:
        student_id: Student ID
        limit: Number of results
        year: Optional year filter
        
    Returns:
        BaseResponse with exam results
    """
    try:
        df = get_dataframe()
        student_df = df.filter(pl.col('student_id') == student_id)
        
        if student_df.height == 0:
            return BaseResponse(
                status="error",
                message=f"Student {student_id} not found",
                error_code="ERR_STU_404",
                timestamp=datetime.utcnow()
            )
        
        if year:
            student_df = student_df.filter(pl.col('exam_year') == year)
        
        results = []
        for row in student_df.head(limit).iter_rows(named=True):
            results.append({
                "subject": row['subject'],
                "year": int(row['exam_year']),
                "pass_fail": row['pass_fail'],
                "performance": row['performance'],
                "grade": row['grade'],
                "grade_point": row['grade_point'],
                "cia_theory": row['cia_theory_avg'],
                "ese_theory": row['ese_theory_internal'],
                "total_theory": row['total_theory_marks']
            })
        
        return BaseResponse(
            status="success",
            message=f"Exam results for student {student_id}",
            data={
                "student_id": student_id,
                "results": results,
                "total": len(results)
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving results: {str(e)}",
            error_code="ERR_STU_004",
            timestamp=datetime.utcnow()
        )


@router.post("/batch", response_model=BaseResponse)
async def get_batch_students(request: BatchStudentRequest):
    """
    Get details for multiple students in one request.
    
    Args:
        request: BatchStudentRequest with student IDs
        
    Returns:
        BaseResponse with batch student data
    """
    try:
        df = get_dataframe()
        
        students = []
        for student_id in request.student_ids:
            student_df = df.filter(pl.col('student_id') == student_id)
            
            if student_df.height == 0:
                continue
            
            first_row = student_df.row(0, named=True)
            total_exams = student_df.height
            
            pass_fail_norm = student_df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
            pass_count = (pass_fail_norm == 'pass').sum()
            pass_rate = (pass_count / total_exams * 100) if total_exams > 0 else 0
            
            student_data = {
                "student_id": student_id,
                "name": first_row['student_name'],
                "department": first_row['department'],
                "total_exams": total_exams,
                "pass_rate": round(pass_rate, 2)
            }
            
            if request.include_results:
                results = []
                for row in student_df.head(20).iter_rows(named=True):
                    results.append({
                        "subject": row['subject'],
                        "year": int(row['exam_year']),
                        "pass_fail": row['pass_fail']
                    })
                student_data["recent_results"] = results
            
            students.append(student_data)
        
        return BaseResponse(
            status="success",
            message=f"Batch data for {len(students)} students",
            data=students,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving batch data: {str(e)}",
            error_code="ERR_STU_005",
            timestamp=datetime.utcnow()
        )
