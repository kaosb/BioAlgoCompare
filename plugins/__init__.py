"""
Plugin system for BioAlgoCompare.

This package provides a flexible plugin architecture for integrating
external algorithms into the BioAlgoCompare framework.
"""

from .plugin_manager import PluginManager, Plugin, PluginMetadata
from .plugin_loader import PluginLoader, discover_plugins
from .plugin_registry import PluginRegistry, register_plugin

__all__ = [
    'PluginManager',
    'Plugin',
    'PluginMetadata',
    'PluginLoader',
    'discover_plugins',
    'PluginRegistry',
    'register_plugin'
]