"""
Analytics Endpoints
Advanced filtering, comparison, and reporting.
"""

from datetime import datetime
from fastapi import APIRouter, Query
import polars as pl
import json

from api.dependencies import get_dataframe
from api.models.response_models import BaseResponse
from api.models.request_models import FilterRequest

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.post("/filter", response_model=BaseResponse)
async def advanced_filter(request: FilterRequest):
    """
    Apply advanced filters with multiple criteria.
    
    Args:
        request: FilterRequest with filter criteria
        
    Returns:
        BaseResponse with filtered data
    """
    try:
        df = get_dataframe()
        
        # Apply filters
        if request.year:
            df = df.filter(pl.col('exam_year') == request.year)
        if request.department:
            df = df.filter(pl.col('department') == request.department)
        if request.subject:
            df = df.filter(pl.col('subject') == request.subject)
        if request.pass_fail:
            df = df.filter(pl.col('pass_fail') == request.pass_fail)
        if request.performance:
            df = df.filter(pl.col('performance') == request.performance)
        
        total_records = df.height
        
        # Get statistics
        pass_fail_norm = df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        pass_count = (pass_fail_norm == 'pass').sum()
        fail_count = (pass_fail_norm == 'fail').sum()
        dist_count = (df['performance'] == 'Distinction').sum()
        
        pass_rate = (pass_count / total_records * 100) if total_records > 0 else 0
        
        # Get paginated records
        results = df.select([
            'student_id', 'subject', 'pass_fail', 'performance', 'grade', 'exam_year'
        ]).slice(request.offset, request.limit)
        
        result_list = []
        for row in results.iter_rows(named=True):
            result_list.append({
                "student_id": int(row['student_id']),
                "subject": row['subject'],
                "pass_fail": row['pass_fail'],
                "performance": row['performance'],
                "grade": row['grade'],
                "year": int(row['exam_year'])
            })
        
        return BaseResponse(
            status="success",
            message="Advanced filter applied successfully",
            data={
                "filters_applied": request.dict(exclude_none=True),
                "total_records": total_records,
                "pass_count": int(pass_count),
                "fail_count": int(fail_count),
                "distinction_count": int(dist_count),
                "pass_rate": round(pass_rate, 2),
                "records": result_list,
                "limit": request.limit,
                "offset": request.offset
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error applying filters: {str(e)}",
            error_code="ERR_ANA_001",
            timestamp=datetime.utcnow()
        )


@router.get("/comparison", response_model=BaseResponse)
async def compare_entities(
    entity_type: str = Query("department", description="department or subject"),
    entity_name_1: str = Query(..., description="First entity name"),
    entity_name_2: str = Query(..., description="Second entity name")
):
    """
    Compare performance between two departments or subjects.
    
    Args:
        entity_type: Type of entity to compare
        entity_name_1: First entity name
        entity_name_2: Second entity name
        
    Returns:
        BaseResponse with comparison data
    """
    try:
        df = get_dataframe()
        
        col_name = 'department' if entity_type == 'department' else 'subject'
        
        # Get data for both entities
        df1 = df.filter(pl.col(col_name) == entity_name_1)
        df2 = df.filter(pl.col(col_name) == entity_name_2)
        
        if df1.height == 0 or df2.height == 0:
            return BaseResponse(
                status="error",
                message=f"One or both {entity_type}s not found",
                error_code="ERR_ANA_002",
                timestamp=datetime.utcnow()
            )
        
        def get_stats(data):
            total = data.height
            pass_fail_norm = data['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
            pass_count = (pass_fail_norm == 'pass').sum()
            dist_count = (data['performance'] == 'Distinction').sum()
            
            return {
                "total_exams": total,
                "pass_count": int(pass_count),
                "distinction_count": int(dist_count),
                "pass_rate": round((pass_count / total * 100) if total > 0 else 0, 2),
                "distinction_rate": round((dist_count / total * 100) if total > 0 else 0, 2),
                "unique_students": data['student_id'].n_unique(),
                "avg_cia_theory": round(data['cia_theory_avg'].mean(), 2) if data['cia_theory_avg'].mean() else None,
                "avg_ese_theory": round(data['ese_theory_internal'].mean(), 2) if data['ese_theory_internal'].mean() else None
            }
        
        stats1 = get_stats(df1)
        stats2 = get_stats(df2)
        
        return BaseResponse(
            status="success",
            message=f"Comparison between {entity_name_1} and {entity_name_2}",
            data={
                "comparison_type": entity_type,
                entity_name_1: stats1,
                entity_name_2: stats2,
                "better_performer": entity_name_1 if stats1['pass_rate'] > stats2['pass_rate'] else entity_name_2,
                "difference": {
                    "pass_rate_diff": round(stats1['pass_rate'] - stats2['pass_rate'], 2),
                    "distinction_rate_diff": round(stats1['distinction_rate'] - stats2['distinction_rate'], 2)
                }
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error comparing entities: {str(e)}",
            error_code="ERR_ANA_003",
            timestamp=datetime.utcnow()
        )


@router.get("/trends", response_model=BaseResponse)
async def get_trends(
    entity_type: str = Query("department", description="department or subject"),
    entity_name: str = Query(..., description="Entity name"),
    metric: str = Query("pass_rate", description="pass_rate, distinction_rate, or exam_count")
):
    """
    Get trend analysis over time for an entity.
    
    Args:
        entity_type: Type of entity
        entity_name: Entity name
        metric: Metric to analyze
        
    Returns:
        BaseResponse with trend data
    """
    try:
        df = get_dataframe()
        
        col_name = 'department' if entity_type == 'department' else 'subject'
        entity_df = df.filter(pl.col(col_name) == entity_name)
        
        if entity_df.height == 0:
            return BaseResponse(
                status="error",
                message=f"{entity_type} '{entity_name}' not found",
                error_code="ERR_ANA_404",
                timestamp=datetime.utcnow()
            )
        
        # Group by year and calculate metrics
        pass_fail_norm = entity_df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        
        yearly_trends = (
            entity_df.with_columns(pass_fail_norm.alias('_pass_fail_norm'))
            .group_by('exam_year')
            .agg([
                pl.count().alias('exam_count'),
                (pl.col('_pass_fail_norm') == 'pass').sum().alias('pass_count'),
                (pl.col('performance') == 'Distinction').sum().alias('dist_count')
            ])
            .with_columns([
                (pl.col('pass_count') / pl.col('exam_count') * 100).alias('pass_rate'),
                (pl.col('dist_count') / pl.col('exam_count') * 100).alias('distinction_rate')
            ])
            .sort('exam_year')
        )
        
        trends = []
        for row in yearly_trends.iter_rows(named=True):
            trends.append({
                "year": int(row['exam_year']),
                "exam_count": int(row['exam_count']),
                "pass_rate": round(row['pass_rate'], 2),
                "distinction_rate": round(row['distinction_rate'], 2),
                "value": round(row[metric], 2) if metric != 'exam_count' else int(row[metric])
            })
        
        # Calculate trend direction
        if len(trends) > 1:
            first_val = trends[0]['value']
            last_val = trends[-1]['value']
            trend_direction = "upward" if last_val > first_val else ("downward" if last_val < first_val else "stable")
            trend_change = round(last_val - first_val, 2)
        else:
            trend_direction = "stable"
            trend_change = 0
        
        return BaseResponse(
            status="success",
            message=f"Trends for {entity_type} '{entity_name}'",
            data={
                "entity": entity_name,
                "metric": metric,
                "trends": trends,
                "trend_direction": trend_direction,
                "trend_change": trend_change,
                "latest_value": trends[-1]['value'] if trends else None,
                "earliest_value": trends[0]['value'] if trends else None
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error retrieving trends: {str(e)}",
            error_code="ERR_ANA_004",
            timestamp=datetime.utcnow()
        )


@router.get("/report", response_model=BaseResponse)
async def generate_report(
    report_type: str = Query("summary", description="summary, detailed, or executive"),
    department: str = Query(None, description="Optional department filter")
):
    """
    Generate a performance report.
    
    Args:
        report_type: Type of report
        department: Optional department filter
        
    Returns:
        BaseResponse with report data
    """
    try:
        df = get_dataframe()
        
        if department:
            df = df.filter(pl.col('department') == department)
        
        total_records = df.height
        unique_students = df['student_id'].n_unique()
        unique_subjects = df['subject'].n_unique()
        unique_depts = df['department'].n_unique()
        
        pass_fail_norm = df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
        pass_count = (pass_fail_norm == 'pass').sum()
        fail_count = (pass_fail_norm == 'fail').sum()
        dist_count = (df['performance'] == 'Distinction').sum()
        
        pass_rate = (pass_count / total_records * 100) if total_records > 0 else 0
        fail_rate = (fail_count / total_records * 100) if total_records > 0 else 0
        dist_rate = (dist_count / total_records * 100) if total_records > 0 else 0
        
        report = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "data_scope": "department" if department else "entire dataset",
            "summary": {
                "total_exam_records": total_records,
                "unique_students": unique_students,
                "unique_subjects": unique_subjects,
                "departments_included": unique_depts if not department else 1,
                "pass_rate": round(pass_rate, 2),
                "fail_rate": round(fail_rate, 2),
                "distinction_rate": round(dist_rate, 2)
            }
        }
        
        if report_type in ["detailed", "executive"]:
            # Top performing departments
            if not department:
                top_depts = (
                    df.group_by('department')
                    .agg([(pass_fail_norm == 'pass').sum().alias('pass_count'), pl.count().alias('total')])
                    .with_columns((pl.col('pass_count') / pl.col('total') * 100).alias('pass_rate'))
                    .sort('pass_rate', descending=True)
                    .head(5)
                )
                
                report["top_departments"] = []
                for row in top_depts.iter_rows(named=True):
                    report["top_departments"].append({
                        "department": row['department'],
                        "pass_rate": round(row['pass_rate'], 2)
                    })
        
        if report_type == "executive":
            # Key insights
            report["key_insights"] = []
            if pass_rate >= 95:
                report["key_insights"].append("High overall pass rate indicates strong academic performance")
            if dist_rate >= 10:
                report["key_insights"].append("Distinction rate above 10% shows excellent student achievement")
            if fail_rate >= 5:
                report["key_insights"].append("Fail rate above 5% suggests need for academic support programs")
        
        return BaseResponse(
            status="success",
            message=f"Performance report generated ({report_type})",
            data=report,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Error generating report: {str(e)}",
            error_code="ERR_ANA_005",
            timestamp=datetime.utcnow()
        )
