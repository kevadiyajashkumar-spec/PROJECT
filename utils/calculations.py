# ==============================================================================
# FILE: utils/calculations.py
# ==============================================================================
"""
Performance calculation utilities.
Statistical computations and rate calculations.
"""

import polars as pl


def calculate_rates(data):
    """
    Calculate pass, distinction, and fail rates.
    
    Args:
        data (pl.DataFrame): Input DataFrame with performance column and pass_fail column
        
    Returns:
        tuple: (pass_rate, dist_rate, fail_rate, unique_students, total_exams)
    """
    if len(data) == 0:
        return 0, 0, 0, 0, 0
    
    unique_students = data['student_id'].n_unique()
    total_exams = len(data)
    
    # Pass/Fail rates use pass_fail column directly
    pass_fail_norm = data['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
    pass_count = (pass_fail_norm == 'pass').sum()
    fail_count = (pass_fail_norm == 'fail').sum()
    
    # Distinction rate uses performance column (based on combined percentage >= 80%)
    dist_count = (data['performance'] == 'Distinction').sum()
    
    pass_rate = (pass_count / total_exams * 100) if total_exams > 0 else 0
    dist_rate = (dist_count / total_exams * 100) if total_exams > 0 else 0
    fail_rate = (fail_count / total_exams * 100) if total_exams > 0 else 0
    
    return pass_rate, dist_rate, fail_rate, unique_students, total_exams


def get_yearly_data(df):
    """
    Calculate year-over-year performance metrics.
    
    Args:
        df (pl.DataFrame): Input DataFrame
        
    Returns:
        pl.DataFrame: Aggregated yearly statistics
    """
    # Normalize pass_fail column for pass/fail counts
    pass_fail_norm = df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
    
    yearly_data = (df
        .with_columns(pass_fail_norm.alias('_pass_fail_norm'))
        .group_by('exam_year')
        .agg([
            pl.col('student_id').n_unique().alias('unique_students'),
            pl.count().alias('total_exams'),
            (pl.col('_pass_fail_norm') == 'pass').sum().alias('pass_count'),
            (pl.col('performance') == 'Distinction').sum().alias('dist_count'),
            (pl.col('_pass_fail_norm') == 'fail').sum().alias('fail_count')
        ])
        .with_columns([
            pl.col('exam_year').cast(pl.Int32, strict=False),
            (pl.col('pass_count') / pl.col('total_exams') * 100).alias('pass_rate'),
            (pl.col('dist_count') / pl.col('total_exams') * 100).alias('dist_rate'),
            (pl.col('fail_count') / pl.col('total_exams') * 100).alias('fail_rate')
        ])
        .sort('exam_year')
    )
    
    return yearly_data


def get_department_stats(df, top_n=10):
    """
    Calculate department-wise performance statistics.
    
    Args:
        df (pl.DataFrame): Input DataFrame
        top_n (int): Number of top departments to return
        
    Returns:
        pl.DataFrame: Department statistics
    """
    # Normalize pass_fail for accurate pass count
    pass_fail_norm = df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
    
    dept_stats = (df.with_columns(pass_fail_norm.alias('_pass_fail_norm'))
        .group_by('department')
        .agg([
            pl.col('student_id').n_unique().alias('students'),
            pl.count().alias('exams'),
            (pl.col('_pass_fail_norm') == 'pass').sum().alias('pass_count')
        ])
        .with_columns(
            (pl.col('pass_count') / pl.col('exams') * 100).alias('pass_rate')
        )
        .sort('pass_rate')
    )
    return dept_stats


def get_subject_difficulty(df: pl.DataFrame, top_n: int = 15) -> pl.DataFrame:
    """
    Calculate subject difficulty metrics. Lower average marks imply higher difficulty.
    Uses theory marks as the basis for difficulty ranking (higher marks = easier subject).
    """
    # Priority: use total marks (theory + practical combined), fall back to theory only
    score_col = None
    for col in ["total_theory_marks", "cia_theory_avg", "theory_percentage", "ese_theory_internal"]:
        if col in df.columns:
            score_col = col
            break
    if score_col is None:
        return pl.DataFrame([])

    subject_col = "subject"

    # Normalize pass_fail for accurate pass rate
    pass_fail_norm = df['pass_fail'].cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase()
    
    difficulty = (
        df.with_columns(pass_fail_norm.alias('_pass_fail_norm'))
        .filter(pl.col(subject_col).is_not_null())
        .filter(pl.col(score_col).is_not_null())  # Only include subjects with marks data
        .group_by(subject_col)
        .agg([
            pl.col(score_col).mean().alias("avg_total_marks"),
            pl.count().alias("exam_count"),
            (pl.col('_pass_fail_norm') == 'pass')
            .cast(pl.Float64, strict=False)
            .mean()
            .alias("pass_rate_raw"),
        ])
        .with_columns((pl.col("pass_rate_raw") * 100).alias("pass_rate"))
        .drop("pass_rate_raw")
        .sort("avg_total_marks", descending=False)
    )
    return difficulty


def get_department_leaderboard(df: pl.DataFrame, top_n: int = 5) -> dict:
    stats = get_department_stats(df)
    if stats.height == 0:
        return {}

    top = stats.sort("pass_rate", descending=True).head(top_n).with_columns(
        pl.lit("Top").alias("category")
    )
    bottom = stats.sort("pass_rate").head(top_n).with_columns(
        pl.lit("Bottom").alias("category")
    )
    combined = pl.concat([bottom, top]).sort("pass_rate")
    return {
        "top": top,
        "bottom": bottom,
        "combined": combined
    }

def get_assessment_yearly_summary(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate CIA and ESE metrics by academic year.
    
    For practical metrics, only includes records where practical_credit > 0
    (theory-only subjects are excluded from practical averages).

    Args:
        df (pl.DataFrame): Input DataFrame with percentage columns.

    Returns:
        pl.DataFrame: Yearly averages for CIA and ESE scores.
    """
    if "exam_year" not in df.columns:
        raise ValueError("Missing required column: 'exam_year'")

    column_variants = {
        "cia_theory": [
            "cia_theory_avg",  # Prefer processed column first
            "theory_internal_percentage",
            "cia_theory_percentage",
        ],
        "cia_practical": [
            "cia_practical_avg",  # Prefer processed column first
            "practical_internal_percentage",
            "cia_practical_percentage",
        ],
        "ese_theory": [
            "ese_theory_internal",  # Prefer processed column first
            "theory_ese_percentage",
            "ese_theory_percentage",
        ],
        "ese_practical": [
            "ese_practical_internal",  # Prefer processed column first
            "practical_ese_percentage",
            "ese_practical_percentage",
        ],
    }

    def pick(col_list: list[str]) -> str | None:
        for name in col_list:
            if name in df.columns:
                return name
        return None

    cia_theory_col = pick(column_variants["cia_theory"])
    cia_practical_col = pick(column_variants["cia_practical"])
    ese_theory_col = pick(column_variants["ese_theory"])
    ese_practical_col = pick(column_variants["ese_practical"])

    # For practical metrics, filter to only records with practical_credit > 0
    df_with_prac = df
    if 'practical_credit' in df.columns:
        df_with_prac = df.filter(pl.col('practical_credit').cast(pl.Float64, strict=False) > 0)

    agg_exprs = []
    if cia_theory_col:
        agg_exprs.append(
            pl.col(cia_theory_col)
            .cast(pl.Utf8, strict=False)
            .str.replace_all(r'(?i)not applicable', '')
            .cast(pl.Float64, strict=False)
            .mean()
            .alias("cia_theory_avg")
        )
    else:
        agg_exprs.append(pl.lit(None).alias("cia_theory_avg"))

    # For practical, use filtered dataframe to exclude theory-only courses
    if cia_practical_col:
        cia_prac_expr = (
            pl.col(cia_practical_col)
            .cast(pl.Utf8, strict=False)
            .str.replace_all(r'(?i)not applicable', '')
            .cast(pl.Float64, strict=False)
            .mean()
            .alias("cia_practical_avg")
        )
    else:
        cia_prac_expr = pl.lit(None).alias("cia_practical_avg")

    if ese_theory_col:
        agg_exprs.append(pl.col(ese_theory_col).cast(pl.Float64, strict=False).mean().alias("ese_theory_avg"))
    else:
        agg_exprs.append(pl.lit(None).alias("ese_theory_avg"))

    if ese_practical_col:
        ese_prac_expr = pl.col(ese_practical_col).cast(pl.Float64, strict=False).mean().alias("ese_practical_avg")
    else:
        ese_prac_expr = pl.lit(None).alias("ese_practical_avg")

    # Aggregate theory metrics using full dataframe
    summary_theory = (
        df.group_by("exam_year")
        .agg(agg_exprs)
        .with_columns(pl.col("exam_year").cast(pl.Int32, strict=False))
        .sort("exam_year")
    )
    
    # Aggregate practical metrics using filtered dataframe (practical_credit > 0)
    summary_practical = (
        df_with_prac.group_by("exam_year")
        .agg([cia_prac_expr, ese_prac_expr])
        .with_columns(pl.col("exam_year").cast(pl.Int32, strict=False))
        .sort("exam_year")
    )
    
    # Join the two summaries
    summary = summary_theory.join(summary_practical, on="exam_year", how="left")
    
    # Add gap calculations (fill nulls with 0 to prevent null subtraction errors)
    summary = summary.with_columns(
        [
            ((pl.col("cia_theory_avg").fill_null(0) + pl.col("cia_practical_avg").fill_null(0)) / 2).alias("cia_overall_avg"),
            ((pl.col("ese_theory_avg").fill_null(0) + pl.col("ese_practical_avg").fill_null(0)) / 2).alias("ese_overall_avg"),
            (pl.col("ese_theory_avg").fill_null(0) - pl.col("cia_theory_avg").fill_null(0)).alias("theory_gap"),
            (pl.col("ese_practical_avg").fill_null(0) - pl.col("cia_practical_avg").fill_null(0)).alias("practical_gap"),
        ]
    )
    return summary


def get_assessment_department_summary(df: pl.DataFrame, top_n: int = 12) -> pl.DataFrame:
    """
    Aggregate CIA vs ESE metrics by department.

    Args:
        df (pl.DataFrame): Input DataFrame with percentage columns.
        top_n (int): Number of departments to return.

    Returns:
        pl.DataFrame: Department-level assessment summary.
    """
    if "department" not in df.columns:
        raise ValueError("Missing required column: 'department'")

    column_variants = {
        "cia_theory": [
            "theory_internal_percentage",
            "cia_theory_percentage",
            "cia_theory_avg",
        ],
        "cia_practical": [
            "practical_internal_percentage",
            "cia_practical_percentage",
            "cia_practical_avg",
        ],
        "ese_theory": [
            "theory_ese_percentage",
            "ese_theory_percentage",
            "ese_theory_internal",
        ],
        "ese_practical": [
            "practical_ese_percentage",
            "practical_ese_avg",
            "ese_practical_internal",
        ],
    }

    def pick(col_list: list[str]) -> str | None:
        for name in col_list:
            if name in df.columns:
                return name
        return None

    cia_theory_col = pick(column_variants["cia_theory"])
    cia_practical_col = pick(column_variants["cia_practical"])
    ese_theory_col = pick(column_variants["ese_theory"])
    ese_practical_col = pick(column_variants["ese_practical"])

    agg_exprs = [pl.count().alias("exam_count")]
    
    # Helper to handle "Not Applicable" strings
    def safe_float(col_name):
        if col_name:
            return (
                pl.col(col_name)
                .cast(pl.Utf8, strict=False)
                .str.replace_all(r'(?i)not applicable', '')
                .cast(pl.Float64, strict=False)
                .mean()
            )
        return pl.lit(None)
    
    agg_exprs.append(safe_float(cia_theory_col).alias("cia_theory_avg"))
    agg_exprs.append(safe_float(ese_theory_col).alias("ese_theory_avg"))
    agg_exprs.append(safe_float(cia_practical_col).alias("cia_practical_avg"))
    agg_exprs.append(safe_float(ese_practical_col).alias("ese_practical_avg"))

    summary = (
        df.group_by("department")
        .agg(agg_exprs)
        .with_columns(
            [
                (pl.col("ese_theory_avg").fill_null(0) - pl.col("cia_theory_avg").fill_null(0)).alias("theory_gap"),
                (pl.col("ese_practical_avg").fill_null(0) - pl.col("cia_practical_avg").fill_null(0)).alias("practical_gap"),
            ]
        )
        .sort("exam_count", descending=True)
        .head(top_n)
    )
    return summary