"""
Real-time dashboard for BioAlgoCompare.
"""

from .app import create_app, DashboardApp
from .callbacks import register_callbacks
from .layouts import get_main_layout

__all__ = [
    'create_app',
    'DashboardApp',
    'register_callbacks',
    'get_main_layout'
]