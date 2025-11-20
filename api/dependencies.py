"""
Shared dependencies for API routes.
Includes data loading and caching logic.
"""

from functools import lru_cache
from data.loader import load_data
from data.processor import add_performance_column


@lru_cache(maxsize=1)
def get_dataframe():
    """Get and cache the main dataframe."""
    df = load_data()
    df = add_performance_column(df)
    return df


def reload_data():
    """Reload data (clear cache)."""
    get_dataframe.cache_clear()
