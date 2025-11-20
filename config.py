# ==============================================================================
# FILE: config.py (ENHANCED VERSION)
# ==============================================================================
"""
Configuration file for the Student Analytics Dashboard.
Contains all constants, thresholds, and application settings.
"""

import os
from pathlib import Path

# ==============================================================================
# API KEYS (Use environment variables in production)
# ==============================================================================



# ==============================================================================
# LLM SETTINGS
# ==============================================================================

LLM_MODEL = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo" for faster/cheaper
LLM_TEMPERATURE = 0.3  # Lower = more deterministic
LLM_MAX_TOKENS = 1000

# Follow-up question generation
FOLLOWUP_QUESTIONS_COUNT = 4
FOLLOWUP_TEMPERATURE = 0.8  # Higher for more creative suggestions

# ==============================================================================
# PERFORMANCE THRESHOLDS
# ==============================================================================

PASS_GRADE = 3.0
DISTINCTION_GRADE = 3.7
IMPROVEMENT_THRESHOLD = 5  # Percentage change threshold for alerts

# ==============================================================================
# ALERT THRESHOLDS
# ==============================================================================

HIGH_FAILURE_THRESHOLD = 20  # Alert if failure rate > 20%
LOW_DISTINCTION_THRESHOLD = 15  # Alert if distinction rate < 15%
EXCELLENT_PERFORMANCE_THRESHOLD = 90  # Alert if pass rate > 90%

# Critical Performance Thresholds
CRITICAL_PASS_RATE = 60  # Departments below this need intervention
HIGH_PERFORMANCE_PASS_RATE = 85  # Departments above this are exemplary

# ==============================================================================
# DISPLAY SETTINGS
# ==============================================================================

TOP_DEPARTMENTS_DISPLAY = 10
TOP_SUBJECTS_DISPLAY = 100
CRITICAL_DEPARTMENTS_DISPLAY = 5
HIGH_PERFORMERS_DISPLAY = 5

# ==============================================================================
# CHART COLORS
# ==============================================================================

# ==============================================================================
# CHART COLORS - Modern Professional Palette
# ==============================================================================

COLORS = {
    # Performance colors
    'pass': '#06b6d4',  # Cyans
    'distinction': '#8b5cf6',  # Purple
    'fail': '#f43f5e',  # Rose
    
    # Assessment colors
    'cia': '#14b8a6',  # Teal
    'ese': '#f59e0b',  # Amber
    'practical': '#ec4899',  # Pink
    
    # Neutral and utility
    'neutral': '#64748b',  # Slate
    'primary': '#6366f1',  # Indigo
    'secondary': '#8b5cf6',  # Purple
    'success': '#10b981',  # Emerald
    'warning': '#f59e0b',  # Amber
    'danger': '#ef4444',  # Red
    
    # Difficulty levels
    'very_easy': '#10b981',  # Emerald
    'easy': '#84cc16',  # Lime
    'moderate': '#f59e0b',  # Amber
    'difficult': '#f97316',  # Orange
    'very_difficult': '#dc2626',  # Red
    
    # Chart palette for multiple series
    'chart_palette': [
        '#6366f1',  # Indigo
        '#8b5cf6',  # Purple
        '#06b6d4',  # Cyan
        '#10b981',  # Emerald
        '#f59e0b',  # Amber
        '#f43f5e',  # Rose
        '#14b8a6',  # Teal
        '#ec4899',  # Pink
    ],

    # Surfaces
    'card': '#ffffff',
    'background': '#f1f5f9'
}
# ==============================================================================
# SERVER SETTINGS
# ==============================================================================

HOST = "127.0.0.1"
PORT = 8052  # Chat app port
API_PORT = 8000  # API port
DEBUG = False

# ==============================================================================
# API SETTINGS
# ==============================================================================

API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 1  # Number of Uvicorn workers
API_RELOAD = False  # Auto-reload on code changes
API_LOG_LEVEL = "info"  # debug, info, warning, error
API_TIMEOUT = 30  # Request timeout in seconds
API_CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)
API_MAX_QUERY_SIZE = 100000  # Max records in single query

# ==============================================================================
# DATA SETTINGS
# ==============================================================================

DATA_PATH = 'data/data2.csv'

# Column Names
COLUMNS = {
    'student_id': 'student_id',
    'exam_year': 'exam_year',
    'semester': 'semester',
    'offering_department': 'offering_department',
    'subject_name': 'name',
    'grade_point': 'grade_point',
    'course_result': 'course_result'
}

# ==============================================================================
# PDF EXPORT SETTINGS
# ==============================================================================

PDF_ORIENTATION = 'landscape'  # 'portrait' or 'landscape'
PDF_PAGESIZE = 'letter'  # 'letter' or 'A4'
PDF_TITLE = "Student Analytics Dashboard Report"
PDF_AUTHOR = "Student Analytics System"

# Chart dimensions for PDF (inches)
PDF_CHART_WIDTH = 9
PDF_CHART_HEIGHT = 4.5

# ==============================================================================
# SEMESTER GROUPS
# ==============================================================================

SEMESTER_GROUPS = {
    'odd': [1, 3, 5, 7],
    'even': [2, 4, 6, 8],
    'early': [1, 2, 3, 4],
    'late': [5, 6, 7, 8]
}

# ==============================================================================
# COMPARISON KEYWORDS
# ==============================================================================

COMPARISON_KEYWORDS = [
    'compare', 'comparison', 'versus', 'vs', 'against',
    'difference', 'between', 'both', 'and'
]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_data_path():
    """Get absolute path to data file."""
    return Path(__file__).parent / DATA_PATH

def validate_config():
    """Validate configuration settings."""
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your-api-key-here':
        print("⚠️  WARNING: OpenAI API key not set!")
        print("   Set OPENAI_API_KEY environment variable or update config.py")
        return False
    
    if not get_data_path().exists():
        print(f"⚠️  WARNING: Data file not found at {get_data_path()}")
        return False
    
    return True

# ==============================================================================
# ENVIRONMENT-SPECIFIC SETTINGS
# ==============================================================================

ENV = os.getenv('ENV', 'production')

if ENV == 'production':
    DEBUG = False
    HOST = "0.0.0.0"
elif ENV == 'development':
    HOST = "127.0.0.1"
