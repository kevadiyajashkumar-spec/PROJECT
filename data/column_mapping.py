# ==============================================================================
# FILE: data/column_mapping.py
# ==============================================================================
"""
Column mapping configuration for handling different CSV structures.
Update this file when you receive new CSV with different column names.
"""

# ==============================================================================
# COLUMN MAPPING CONFIGURATION
# ==============================================================================
# Map your CSV columns to standardized names
# Format: 'standard_name': ['possible_name_1', 'possible_name_2', ...]

COLUMN_MAPPINGS = {
    'student_id': [
        'student_id', 'studentid', 'student_code', 'roll_no', 
        'rollno', 'roll_number', 'enrollment_no', 'id'
    ],
    
    'exam_year': [
        'exam_year', 'year', 'academic_year', 'year_of_exam',
        'examination_year', 'exam_session'
    ],
    
    'semester': [
        'semester', 'sem', 'term', 'session', 'period'
    ],
    
    'offering_department': [
        'offering_department', 'department', 'dept', 'branch',
        'program', 'faculty', 'school'
    ],
    
    'subject_name': [
        'name', 'subject_name', 'course_name', 'subject',
        'course', 'subject_code', 'course_code', 'paper_name'
    ],
    
    'grade_point': [
        'grade_point', 'gpa', 'cgpa', 'marks', 'score',
        'grade', 'percentage', 'total_marks'
    ],
    
    'course_result': [
        'course_result', 'result', 'status', 'outcome',
        'pass_fail', 'grade_status'
    ]
}

# ==============================================================================
# DATA TYPE SPECIFICATIONS
# ==============================================================================
# Specify the expected data type for each standard column

COLUMN_DTYPES = {
    'student_id': 'string',
    'exam_year': 'int',
    'semester': 'int',
    'offering_department': 'string',
    'subject_name': 'string',
    'grade_point': 'float',
    'course_result': 'string'
}

# ==============================================================================
# DEFAULT VALUES
# ==============================================================================
# Default values to use when data is missing

DEFAULT_VALUES = {
    'student_id': 'UNKNOWN',
    'exam_year': 2024,
    'semester': 1,
    'offering_department': 'Unknown Department',
    'subject_name': 'Unknown Subject',
    'grade_point': 0.0,
    'course_result': 'Fail'
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def find_column_match(df_columns, standard_name):
    """
    Find matching column name from CSV.
    
    Args:
        df_columns (list): List of column names in the CSV
        standard_name (str): Standard column name to find
        
    Returns:
        str or None: Matched column name or None
    """
    possible_names = COLUMN_MAPPINGS.get(standard_name, [])
    
    # Normalize column names for comparison
    normalized_df_cols = {col.lower().strip().replace(' ', '_'): col 
                          for col in df_columns}
    
    for possible_name in possible_names:
        normalized = possible_name.lower().strip().replace(' ', '_')
        if normalized in normalized_df_cols:
            return normalized_df_cols[normalized]
    
    return None


def get_column_mapping(df_columns):
    """
    Generate complete column mapping for a DataFrame.
    
    Args:
        df_columns (list): List of column names in the CSV
        
    Returns:
        dict: Mapping of standard names to actual CSV column names
    """
    mapping = {}
    missing = []
    
    for standard_name in COLUMN_MAPPINGS.keys():
        matched_col = find_column_match(df_columns, standard_name)
        if matched_col:
            mapping[standard_name] = matched_col
        else:
            missing.append(standard_name)
    
    return mapping, missing


def print_mapping_report(mapping, missing):
    """
    Print a report of column mapping results.
    
    Args:
        mapping (dict): Successful mappings
        missing (list): Missing columns
    """
    print("\n" + "="*60)
    print("COLUMN MAPPING REPORT")
    print("="*60)
    
    if mapping:
        print("\n✅ Successfully Mapped Columns:")
        for std_name, csv_col in mapping.items():
            print(f"   {std_name:20s} → {csv_col}")
    
    if missing:
        print("\n⚠️  Missing Columns (will use defaults):")
        for col in missing:
            print(f"   {col:20s} → Default: {DEFAULT_VALUES[col]}")
    
    print("\n" + "="*60 + "\n")


# ==============================================================================
# MANUAL MAPPING OVERRIDE
# ==============================================================================
# If automatic mapping fails, you can manually specify mappings here
# Format: 'standard_name': 'your_csv_column_name'

MANUAL_OVERRIDE = {
    # Example:
    # 'student_id': 'StudentRollNumber',
    # 'exam_year': 'YearOfExamination',
}