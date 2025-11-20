"""
Subject Endpoints
Get subject difficulty, pass rates, and related analytics.
"""

from datetime import datetime
from fastapi import APIRouter, Query
import polars as pl

from api.dependencies import get_dataframe
from api.models.response_models import BaseResponse
from utils.calculations import get_subject_difficulty

router = APIRouter(prefix="/api/v1/subjects", tags=["Subjects"])


@router.get("", response_model=BaseResponse)
async def list_subjects(
    limit: int = Query(100, description="Number of subjects"),
    offset: int = Query(0, description="Offset for pagination"),
    sort_by: str = Query("difficulty", description="Sort by: difficulty, pass_rate, exam_count")
):
    """
    List subjects with difficulty and pass rate metrics.
    
    Returns:
        BaseResponse with subject list
    """
    try:
        df = get_dataframe()
        subject_diff = get_subject_difficulty(df)
        
        # Sort
        if sort_by == "pass_rate":
            subject_diff = subject_diff.sort("pass_rate", descending=True)
        elif sort_by == "exam_count":
            subject_diff = subject_diff.sort("exam_count", descending=True)
        else:  # difficulty
            subject_diff = subject_diff.sort("avg_total_marks", descending=False)
        
        total = subject_diff.height
        subject_diff = subject_diff.slice(offset, limit)
        
        subject_list = []
        for i, row in enumerate(subject_diff.iter_rows(named=True), offset + 1):
            subject_list.append({
                "rank": i,
                "subject": row['subject'],
                "avg_marks": round(row['avg_total_marks'], 2),
                "exam_count": int(row['exam_count']),
                "pass_rate": round(row['pass_rate'], 2)
            })
        
        return BaseResponse(
            status="success",
            message="Subjects retrieved successfully",
            data={
                "subjects": subject_list,
                "total": total,
                "limit": limit,
                "offset": offset
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving subjects: {str(e)}",
            error_code="ERR_SUBJ_001",
            timestamp=datetime.utcnow()
        )


@router.get("/search", response_model=BaseResponse)
async def search_subjects(
    query: str = Query(..., description="Search query for subject name"),
    limit: int = Query(50, description="Number of results")
):
    """
    Search subjects by name.
    
    Args:
        query: Search string
        
    Returns:
        BaseResponse with matching subjects
    """
    try:
        df = get_dataframe()
        subject_diff = get_subject_difficulty(df)
        
        # Filter by query (case-insensitive)
        query_lower = query.lower()
        filtered = subject_diff.filter(
            pl.col('subject').str.to_lowercase().str.contains(query_lower)
        ).head(limit)
        
        subject_list = []
        for row in filtered.iter_rows(named=True):
            subject_list.append({
                "subject": row['subject'],
                "avg_marks": round(row['avg_total_marks'], 2),
                "exam_count": int(row['exam_count']),
                "pass_rate": round(row['pass_rate'], 2)
            })
        
        return BaseResponse(
            status="success",
            message=f"Found {len(subject_list)} subjects matching '{query}'",
            data=subject_list,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error searching subjects: {str(e)}",
            error_code="ERR_SUBJ_002",
            timestamp=datetime.utcnow()
        )


@router.get("/difficulty-rank", response_model=BaseResponse)
async def get_difficulty_ranking(
    limit: int = Query(50, description="Number of subjects"),
    category: str = Query("hardest", description="hardest or easiest")
):
    """
    Get subjects ranked by difficulty.
    
    Args:
        limit: Number of subjects to return
        category: hardest or easiest
        
    Returns:
        BaseResponse with difficulty ranking
    """
    try:
        df = get_dataframe()
        subject_diff = get_subject_difficulty(df)
        
        if category == "easiest":
            subject_diff = subject_diff.sort("avg_total_marks", descending=True)
        else:  # hardest
            subject_diff = subject_diff.sort("avg_total_marks", descending=False)
        
        subject_diff = subject_diff.head(limit)
        
        subject_list = []
        for i, row in enumerate(subject_diff.iter_rows(named=True), 1):
            subject_list.append({
                "rank": i,
                "subject": row['subject'],
                "avg_marks": round(row['avg_total_marks'], 2),
                "difficulty": "Hard" if category == "hardest" else "Easy",
                "exam_count": int(row['exam_count']),
                "pass_rate": round(row['pass_rate'], 2)
            })
        
        return BaseResponse(
            status="success",
            message=f"Top {limit} {category} subjects retrieved",
            data=subject_list,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving difficulty ranking: {str(e)}",
            error_code="ERR_SUBJ_003",
            timestamp=datetime.utcnow()
        )


@router.get("/pass-rates", response_model=BaseResponse)
async def get_pass_rate_ranking(
    limit: int = Query(50, description="Number of subjects"),
    order: str = Query("highest", description="highest or lowest")
):
    """
    Get subjects ranked by pass rate.
    
    Args:
        limit: Number of subjects to return
        order: highest or lowest
        
    Returns:
        BaseResponse with pass rate ranking
    """
    try:
        df = get_dataframe()
        subject_diff = get_subject_difficulty(df)
        
        if order == "lowest":
            subject_diff = subject_diff.sort("pass_rate", descending=False)
        else:  # highest
            subject_diff = subject_diff.sort("pass_rate", descending=True)
        
        subject_diff = subject_diff.head(limit)
        
        subject_list = []
        for i, row in enumerate(subject_diff.iter_rows(named=True), 1):
            subject_list.append({
                "rank": i,
                "subject": row['subject'],
                "pass_rate": round(row['pass_rate'], 2),
                "rank_type": "Highest" if order == "highest" else "Lowest",
                "exam_count": int(row['exam_count']),
                "avg_marks": round(row['avg_total_marks'], 2)
            })
        
        return BaseResponse(
            status="success",
            message=f"Subjects ranked by {order} pass rate",
            data=subject_list,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving pass rate ranking: {str(e)}",
            error_code="ERR_SUBJ_004",
            timestamp=datetime.utcnow()
        )
