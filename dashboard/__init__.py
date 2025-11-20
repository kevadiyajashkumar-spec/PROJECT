# ==============================================================================
# FILE: dashboard/__init__.py
# ==============================================================================
"""Dashboard UI and callback components."""

from .layout import create_layout
from .callbacks import register_callbacks

__all__ = ['create_layout', 'register_callbacks']

