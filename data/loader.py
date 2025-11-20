# ==============================================================================
# FILE: data/loader.py (FIXED FOR NEW SCHEMA)
# ==============================================================================
"""
Data loading utilities for new exam schema.
Handles CIA marks, ESE marks, practical/theory separation, and null values.
"""

import polars as pl
import os
from pathlib import Path
from utils.subject_normalizer import normalize_subjects

import gdown

GOOGLE_DRIVE_FILES = {
    "data2.csv": "1avHt6EG0VfMBMsHz6E__62irtiY62may",
    "data.csv": "10N8A91tsj5r7O4XKMt_8rIKAKVloS9N4"  
}


def download_from_google_drive(file_id: str, dest_path: Path):
    """Download file from Google Drive only if not already present."""
    if not dest_path.exists():
        print(f"⬇️ Downloading {dest_path.name} from Google Drive...")
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, str(dest_path), quiet=False)
        print(f"📁 Saved to: {dest_path}")
    else:
        print(f"✔️ Using cached file: {dest_path}")



def load_data(verbose: bool = True):
    """
    Load and preprocess exam data with new schema.
    
    Supports both old schema (data.csv) and new schema (data2.csv):
    - Old: cia_obtained, cia_max, ese_obtainded, ese_max, grade_point
    - New: theory_internal_percentage, practical_internal_percentage, 
           theory_ese_percentage, practical_ese_percentage (with "Not Applicable" for theory-only subjects)
    
    Returns:
        pl.DataFrame: Processed dataframe
    """
    
    # Try data2.csv first, then data.csv
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)

    # Define possible files
    files_to_check = ["data2.csv", "data.csv"]

    # First try existing local files
    for filename in files_to_check:
        local_path = data_dir / filename
        if local_path.exists():
            data_path = local_path
            break
    else:
        # If no local file, try downloading from Google Drive
        for filename in files_to_check:
            if filename in GOOGLE_DRIVE_FILES:
                file_id = GOOGLE_DRIVE_FILES[filename]
                download_from_google_drive(file_id, data_dir / filename)
                data_path = data_dir / filename
                break
        else:
            print("[WARN] No data file found locally or from Google Drive.")
            return _create_sample_data()

    
    
    
    if not os.path.exists(data_path):
        if verbose:
            print(f"[WARN] Data file not found at {data_path}")
            print("Creating sample data for demonstration...")
        return _create_sample_data()
    
    if verbose:
        print(f"Loading data from {data_path}...")
    
    try:
        # Load CSV
        df = pl.read_csv(data_path)
        
        # Normalize column names (remove whitespace, lowercase)
        df = df.rename({col: col.strip().lower().replace(' ', '_') for col in df.columns})
        
        if verbose:
            print(f"Loaded {len(df):,} records")
            print(f"Columns: {df.columns}")
        
        # Validate and process
        df = _validate_and_process(df)
        
        # Add derived columns
        df = _add_derived_columns(df)
        
        if verbose:
            print(f"\nData Summary:")
            print(f"   Unique Students: {df['student_id'].n_unique():,}")
            print(f"   Departments: {df['department'].n_unique()}")
            print(f"   Subjects: {df['subject'].n_unique()}")
            print(f"   Exam Years: {df['exam_year'].min()} - {df['exam_year'].max()}")
        
        return df
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] Error loading data: {e}")
            print("Creating sample data instead...")
        return _create_sample_data()



def _validate_and_process(df: pl.DataFrame) -> pl.DataFrame:
    """Validate and process required columns."""
    
    # Required columns mapping (flexible naming)
    column_map = {
        'student_id': ['student_id', 'studentid'],
        'subject': ['subject', 'subject_name', 'name'],
        'department': ['department', 'dept', 'offering_department'],
        'exam_name': ['exam_name', 'exam'],
        'student_name': ['student_name', 'name'],
        'course_name': ['course_name', 'course'],
    }
    
    # Find and standardize column names
    for std_col, variants in column_map.items():
        found = False
        for variant in variants:
            if variant in df.columns:
                if variant != std_col:
                    df = df.rename({variant: std_col})
                found = True
                break
        
        if not found and std_col in ['student_id', 'subject', 'department']:
            print(f"⚠️  Required column '{std_col}' not found!")
    
    # Derive exam_year robustly
    def _ensure_exam_year(frame: pl.DataFrame) -> pl.DataFrame:
        # 1) If exam_year already present and looks numeric, keep as Int32
        if 'exam_year' in frame.columns:
            return frame.with_columns(
                pl.col('exam_year').cast(pl.Int32, strict=False)
            )

        # 2) Try from exam_name like "202310-ENDSEM-UG-PG" or starting with 4-digit year
        if 'exam_name' in frame.columns:
            candidate = (
                frame.select(
                    pl.col('exam_name')
                    .cast(pl.Utf8, strict=False)
                    .str.extract(r'(\d{4})', 1)
                    .cast(pl.Int32, strict=False)
                    .alias('exam_year')
                )['exam_year']
            )
            frame = frame.with_columns(candidate)

        # 3) Try from exam_month like "202310" -> 2023 or 2023? Typically first 4 digits
        if 'exam_year' not in frame.columns or frame['exam_year'].fill_null(0).is_null().all():
            if 'exam_month' in frame.columns:
                frame = frame.with_columns(
                    pl.col('exam_month')
                    .cast(pl.Utf8, strict=False)
                    .str.extract(r'(\d{4})', 1)
                    .cast(pl.Int32, strict=False)
                    .alias('exam_year')
                )

        # 4) Try any column that contains 'year' in its name
        if 'exam_year' not in frame.columns or frame['exam_year'].fill_null(0).is_null().all():
            year_like = [c for c in frame.columns if 'year' in c]
            for c in year_like:
                series = frame[c].cast(pl.Int32, strict=False)
                if series.drop_nulls().len() > 0:
                    frame = frame.with_columns(series.alias('exam_year'))
                    break

        # 5) As a last resort, attempt to extract a 4-digit year from any text column
        if 'exam_year' not in frame.columns or frame['exam_year'].fill_null(0).is_null().all():
            text_cols = [c for c in frame.columns if frame.schema.get(c) == pl.Utf8]
            if text_cols:
                # Concatenate text cols and search
                combined = pl.concat_str([pl.col(c).fill_null('') for c in text_cols], separator=' ')
                frame = frame.with_columns(
                    combined.str.extract(r'(\d{4})', 1).cast(pl.Int32, strict=False).alias('exam_year')
                )

        # 6) If still missing, set to null (no hardcoded 2024), will be filtered/handled later
        if 'exam_year' not in frame.columns:
            frame = frame.with_columns(pl.lit(None).cast(pl.Int32).alias('exam_year'))

        return frame

    df = _ensure_exam_year(df)
    
    # Derive semester robustly
    if 'semester' not in df.columns:
        if 'exam_name' in df.columns:
            df = df.with_columns(
                pl.col('exam_name')
                .cast(pl.Utf8, strict=False)
                .str.extract(r'^\d{4}(\d{2})', 1)
                .cast(pl.Int32, strict=False)
                .alias('semester')
            )
        else:
            df = df.with_columns(pl.lit(None).cast(pl.Int32).alias('semester'))
    
    # Handle null values in theory/practical columns
    theory_cols = [col for col in df.columns if 'theory' in col and 'internal' in col]
    practical_cols = [col for col in df.columns if 'practical' in col and 'internal' in col]
    
    for col in theory_cols + practical_cols:
        if col in df.columns:
            df = df.with_columns(
                pl.col(col).cast(pl.Float64, strict=False).fill_null(0.0)
            )
    
    # Ensure string columns
    str_cols = ['student_id', 'subject', 'department', 'student_name', 'course_name']
    for col in str_cols:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Utf8))

    # Normalize subject names to collapse duplicates (e.g., ". NET" vs ".NET")
    if 'subject' in df.columns:
        df = df.with_columns(
            pl.col('subject')
            .cast(pl.Utf8, strict=False)
            .fill_null('')
            .str.replace_all(r'\s+', ' ')
            .str.strip()
            .alias('subject_raw')
        ).with_columns(
            pl.when(pl.col('subject_raw') == '')
            .then(pl.lit(None))
            .otherwise(
                pl.col('subject_raw')
                .str.to_uppercase()
                .str.replace_all(r'[^A-Z0-9]+', ' ')
                .str.strip()
            )
            .alias('subject_key')
        ).with_columns(
            pl.when(pl.col('subject_key').is_null())
            .then(pl.lit(None))
            .otherwise(pl.col('subject_key').str.to_titlecase())
            .alias('subject')
        )

        df = df.drop('subject_raw')
    
    return df


def _add_derived_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add calculated columns for CIA, ESE, and overall performance.
    
    Handles two data formats:
    1. Old format: cia_obtained, cia_max, ese_obtainded, ese_max
    2. New format (data2.csv): theory_internal_percentage, practical_internal_percentage, etc.
       - Treats "Not Applicable" as NULL (theory-only or practical-only subjects)
    """
    
    # Helper function: safely convert percentage strings to float, treating "Not Applicable" as None
    def safe_percentage(col_name: str) -> pl.Expr:
        return pl.col(col_name).\
            cast(pl.Utf8, strict=False).\
            str.replace_all(r'(?i)not applicable', '').\
            cast(pl.Float64, strict=False)
    
    # ==================== CIA THEORY ====================
    # Try: existing CIA theory columns (old format)
    cia_theory_cols = ['cia1_theory_internal', 'cia2_theory_internal', 'cia3_theory_internal']
    existing_cia_theory = [col for col in cia_theory_cols if col in df.columns]

    if existing_cia_theory:
        df = df.with_columns(
            pl.concat_list([pl.col(c) for c in existing_cia_theory])
            .list.mean()
            .alias('cia_theory_avg')
        )
    # Try: theory_internal_percentage (new format - data2.csv)
    # Only use it if theory_credit > 0 (practical-only subjects have 0 theory credit)
    elif 'theory_internal_percentage' in df.columns and 'theory_credit' in df.columns:
        df = df.with_columns(
            pl.when(pl.col('theory_credit').cast(pl.Float64, strict=False) > 0)
            .then(safe_percentage('theory_internal_percentage'))
            .otherwise(None)
            .alias('cia_theory_avg')
        )
    elif 'theory_internal_percentage' in df.columns:
        df = df.with_columns(
            safe_percentage('theory_internal_percentage').alias('cia_theory_avg')
        )
    elif 'cia_theory_avg' in df.columns:
        df = df.with_columns(pl.col('cia_theory_avg').cast(pl.Float64, strict=False))
    elif 'cia_obtained' in df.columns and 'cia_max' in df.columns:
        df = df.with_columns(
            pl.when(pl.col('cia_max').cast(pl.Float64, strict=False) > 0)
            .then(pl.col('cia_obtained').cast(pl.Float64, strict=False) / pl.col('cia_max').cast(pl.Float64, strict=False) * 100.0)
            .otherwise(None)
            .alias('cia_theory_avg')
        )
    else:
        df = df.with_columns(pl.lit(None).cast(pl.Float64).alias('cia_theory_avg'))
    
    # ==================== CIA PRACTICAL ====================
    # Try: existing CIA practical columns (old format)
    cia_prac_cols = ['cia1_practical_internal', 'cia2_practical_internal', 'cia3_practical_internal']
    existing_cia_prac = [col for col in cia_prac_cols if col in df.columns]
    
    if existing_cia_prac:
        df = df.with_columns(
            pl.concat_list([pl.col(c) for c in existing_cia_prac])
            .list.mean()
            .alias('cia_practical_avg')
        )
    # Try: practical_internal_percentage (new format - data2.csv)
    # Only use it if practical_credit > 0 (theory-only subjects have 0 practical credit)
    elif 'practical_internal_percentage' in df.columns and 'practical_credit' in df.columns:
        df = df.with_columns(
            pl.when(pl.col('practical_credit').cast(pl.Float64, strict=False) > 0)
            .then(safe_percentage('practical_internal_percentage'))
            .otherwise(None)
            .alias('cia_practical_avg')
        )
    elif 'practical_internal_percentage' in df.columns:
        df = df.with_columns(
            safe_percentage('practical_internal_percentage').alias('cia_practical_avg')
        )
    elif 'cia_practical_avg' in df.columns:
        df = df.with_columns(pl.col('cia_practical_avg').cast(pl.Float64, strict=False))
    else:
        df = df.with_columns(pl.lit(None).cast(pl.Float64).alias('cia_practical_avg'))
    
    # ==================== ESE THEORY ====================
    if 'ese_theory_internal' in df.columns:
        df = df.with_columns(pl.col('ese_theory_internal').cast(pl.Float64, strict=False))
    # Only use theory_ese_percentage if theory_credit > 0 (practical-only subjects have 0 theory credit)
    elif 'theory_ese_percentage' in df.columns and 'theory_credit' in df.columns:
        df = df.with_columns(
            pl.when(pl.col('theory_credit').cast(pl.Float64, strict=False) > 0)
            .then(safe_percentage('theory_ese_percentage'))
            .otherwise(None)
            .alias('ese_theory_internal')
        )
    elif 'theory_ese_percentage' in df.columns:
        df = df.with_columns(
            safe_percentage('theory_ese_percentage').alias('ese_theory_internal')
        )
    elif 'ese_obtainded' in df.columns and 'ese_max' in df.columns:
        df = df.with_columns(
            pl.when(pl.col('ese_max').cast(pl.Float64, strict=False) > 0)
            .then(pl.col('ese_obtainded').cast(pl.Float64, strict=False) / pl.col('ese_max').cast(pl.Float64, strict=False) * 100.0)
            .otherwise(None)
            .alias('ese_theory_internal')
        )
    else:
        df = df.with_columns(pl.lit(None).cast(pl.Float64).alias('ese_theory_internal'))
    
    # ==================== ESE PRACTICAL ====================
    if 'ese_practical_internal' in df.columns:
        df = df.with_columns(pl.col('ese_practical_internal').cast(pl.Float64, strict=False))
    # Only use practical_ese_percentage if practical_credit > 0
    elif 'practical_ese_percentage' in df.columns and 'practical_credit' in df.columns:
        df = df.with_columns(
            pl.when(pl.col('practical_credit').cast(pl.Float64, strict=False) > 0)
            .then(safe_percentage('practical_ese_percentage'))
            .otherwise(None)
            .alias('ese_practical_internal')
        )
    elif 'practical_ese_percentage' in df.columns:
        df = df.with_columns(
            safe_percentage('practical_ese_percentage').alias('ese_practical_internal')
        )
    else:
        df = df.with_columns(pl.lit(None).cast(pl.Float64).alias('ese_practical_internal'))
    
    # Calculate Total Marks (Theory + Practical)
    if 'total_theory_marks' in df.columns:
        df = df.with_columns(pl.col('total_theory_marks').cast(pl.Float64, strict=False))
    else:
        df = df.with_columns(
            (pl.col('cia_theory_avg') + pl.col('ese_theory_internal')).alias('total_theory_marks')
        )

    if 'total_practical_marks' in df.columns:
        df = df.with_columns(pl.col('total_practical_marks').cast(pl.Float64, strict=False))
    else:
        df = df.with_columns(
            (pl.col('cia_practical_avg') + pl.col('ese_practical_internal')).alias('total_practical_marks')
        )

    # Replace NaN with nulls for percentage columns
    df = df.with_columns([
        pl.when(pl.col(col).is_nan()).then(None).otherwise(pl.col(col)).alias(col)
        for col in [
            'cia_theory_avg',
            'cia_practical_avg',
            'ese_theory_internal',
            'ese_practical_internal',
            'total_theory_marks',
            'total_practical_marks',
        ]
        if col in df.columns
    ])
    
    # Overall Total (considering credits when present)
    if 'total_theory_marks' in df.columns and 'total_practical_marks' in df.columns:
        theory_credit = pl.col('theory_credit').cast(pl.Float64, strict=False).fill_null(1.0) if 'theory_credit' in df.columns else pl.lit(1.0)
        practical_credit = pl.col('practical_credit').cast(pl.Float64, strict=False).fill_null(1.0) if 'practical_credit' in df.columns else pl.lit(1.0)
        
        df = df.with_columns(
            (
                (pl.col('total_theory_marks').cast(pl.Float64, strict=False).fill_null(0.0) * theory_credit) +
                (pl.col('total_practical_marks').cast(pl.Float64, strict=False).fill_null(0.0) * practical_credit)
            ).alias('weighted_total')
        )
    else:
        df = df.with_columns(pl.lit(None).cast(pl.Float64).alias('weighted_total'))
    
    # Performance classification is handled in `data.processor.add_performance_column`
    # to ensure a single, consistent business-rule for Distinction/Pass/Fail.
    # Do not assign performance here.
    
    return df


def _create_sample_data() -> pl.DataFrame:
    """Create sample data for testing."""
    import numpy as np
    
    print("Generating sample dataset...")
    
    departments = ['LIFE SCIENCES', 'BUSINESS AND MANAGEMENT', 'COMMERCE', 'COMPUTER SCIENCE']
    subjects = ['Mathematics', 'Physics', 'Chemistry', 'Business Studies', 'Economics']
    
    n_records = 1000
    
    df = pl.DataFrame({
        'student_id': [f'ST{i:05d}' for i in range(n_records)],
        'subject': np.random.choice(subjects, n_records),
        'department': np.random.choice(departments, n_records),
        'exam_year': np.random.choice([2019, 2020, 2021, 2022, 2023], n_records),
        'semester': np.random.choice([1, 2, 3, 4, 5, 6, 7, 8], n_records),
        'cia_theory_avg': np.random.uniform(10, 30, n_records),
        'ese_theory_internal': np.random.uniform(20, 70, n_records),
        'total_theory_marks': np.random.uniform(30, 100, n_records),
        'student_name': [f'Student {i}' for i in range(n_records)],
        'course_name': np.random.choice(['BSc', 'BCom', 'BBA', 'BTech'], n_records),
    })
    
    df = df.with_columns(
        pl.when(pl.col('total_theory_marks') >= 85)
        .then(pl.lit('Distinction'))
        .when(pl.col('total_theory_marks') >= 50)
        .then(pl.lit('Pass'))
        .otherwise(pl.lit('Fail'))
        .alias('performance')
    )
    
    return df


if __name__ == '__main__':
    df = load_data()
    print("\n✅ Data loaded successfully!")
    print(df.head())    