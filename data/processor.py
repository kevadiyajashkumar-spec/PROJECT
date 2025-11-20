# ==============================================================================
# FILE: data/processor.py
# ==============================================================================
"""
Data processing and filtering utilities.
"""

import polars as pl
from config import DISTINCTION_GRADE


# ------------------------------------------------------------------------------
# PERFORMANCE CLASSIFICATION
# ------------------------------------------------------------------------------

def classify_performance_expr():
    """Return Polars expression for performance classification.
    
    Priority:
    1) Fail: pass_fail == 'fail' or theory_result shows fail
    2) Distinction: total_percentage >= 80 (theory + practical combined)
    3) Pass: otherwise if pass_fail == 'pass'
    """
    pass_fail_norm = (
        pl.col("pass_fail")
        .cast(pl.Utf8, strict=False)
        .fill_null("")
        .str.to_lowercase()
    )
    
    # Calculate total percentage: theory_percentage + practical_percentage
    theory_pct = pl.col("theory_percentage").cast(pl.Float64, strict=False).fill_null(0)
    practical_pct = pl.col("practical_percentage").cast(pl.Float64, strict=False).fill_null(0)
    total_pct = theory_pct + practical_pct

    return (
        pl.when(pass_fail_norm.eq("fail"))
        .then(pl.lit("Fail"))
        .when(total_pct.ge(80))
        .then(pl.lit("Distinction"))
        .when(pass_fail_norm.eq("pass"))
        .then(pl.lit("Pass"))
        .otherwise(pl.lit(None))
    )


def add_performance_column(df: pl.DataFrame) -> pl.DataFrame:
    """Add performance classification column to DataFrame.
    
    Optimized single-pass expression to classify performance.
    """
    # Use percentage-based distinction criteria
    theory_pct = pl.col("theory_percentage").cast(pl.Float64, strict=False).fill_null(0)
    practical_pct = pl.col("practical_percentage").cast(pl.Float64, strict=False).fill_null(0)
    total_pct = theory_pct + practical_pct
    
    # Base logic: Fail → Distinction (if >=80%) → Pass
    base_expr = (
        pl.when(
            pl.col("pass_fail").cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase().eq("fail")
        )
        .then(pl.lit("Fail"))
        .when(total_pct.ge(80))
        .then(pl.lit("Distinction"))
        .when(
            pl.col("pass_fail").cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase().eq("pass")
        )
        .then(pl.lit("Pass"))
        .otherwise(pl.lit(None))
    )
    
    # Check for explicit Fail in result columns and override base classification
    # Build the final expression by chaining when-then for each result column
    result_columns = [
        "theory_result",
        "theory_internal_result",
        "practical_result",
        "practical_internal_result",
    ]
    
    # Start with base expression
    final_expr = base_expr
    
    # For each result column, if it contains "fail" or "sus" (and not "not applicable"),
    # force performance to "Fail"
    for col in result_columns:
        if col in df.columns:
            na_check = (
                pl.col(col)
                .cast(pl.Utf8, strict=False)
                .fill_null("")
                .str.contains("(?i)not\\s*applicable|^na$")
            )
            fail_check = (
                pl.col(col)
                .fill_null("")
                .str.contains("(?i)(fail|sus)")
            )
            # If column has fail and is not NA, override to Fail
            final_expr = pl.when(~na_check & fail_check).then(pl.lit("Fail")).otherwise(final_expr)
    
    df = df.with_columns(final_expr.alias("performance"))
    
    return df


# ------------------------------------------------------------------------------
# FILTERING UTILITIES
# ------------------------------------------------------------------------------

def filter_data(
    df: pl.DataFrame,
    year_range=None,
    department: str = "All",
    semester: str | int = "All",
    subject: str = "All",
) -> pl.DataFrame:
    """
    Safely filter DataFrame based on user selections.
    Handles all edge cases (type mismatches, empty filters, etc.)
    """
    filtered = df.clone()

    # ---- Year Range ----
    if (
        isinstance(year_range, (list, tuple))
        and len(year_range) >= 2
        and all(isinstance(y, (int, float)) for y in year_range)
    ):
        filtered = filtered.filter(
            (pl.col("exam_year") >= year_range[0])
            & (pl.col("exam_year") <= year_range[1])
        )
    elif year_range not in (None, [], "All"):
        # Fallback for a single year value
        try:
            yr = int(year_range[0]) if isinstance(year_range, (list, tuple)) else int(year_range)
            filtered = filtered.filter(pl.col("exam_year") == yr)
        except Exception:
            print(f"[WARN] Invalid year_range '{year_range}' — skipping year filter.")

    # ---- Department ----
    if department and department != "All":
        filtered = filtered.filter(pl.col("department") == department)

    # ---- Semester ----
    if semester not in ("All", None, ""):
        try:
            semester_num = int(semester)
            filtered = filtered.filter(pl.col("semester") == semester_num)
        except Exception:
            print(f"[WARN] Semester value '{semester}' not numeric — skipping semester filter.")

    # ---- Subject ----
    if subject and subject != "All":
        filtered = filtered.filter(pl.col("subject") == subject)

    return filtered


# ------------------------------------------------------------------------------
# DROPDOWN OPTIONS
# ------------------------------------------------------------------------------

def get_filter_options(df: pl.DataFrame) -> dict:
    """Get unique values for all filter dropdowns."""
    try:
        subjects = sorted(
            [subj for subj in df["subject"].unique().to_list() if subj not in (None, "")]
        )
    except Exception:
        subjects = []

    years = [year for year in df["exam_year"].unique().to_list() if year is not None]
    departments = [
        dept for dept in df["department"].unique().to_list() if dept not in (None, "")
    ]
    semesters = [
        sem for sem in df["semester"].unique().to_list() if sem is not None
    ]

    return {
        "years": ["All"]
        + sorted(years, reverse=True),
        "departments": ["All"]
        + sorted(departments),
        "semesters": ["All"]
        + sorted(semesters),
        "subjects": ["All"] + subjects,
    }
