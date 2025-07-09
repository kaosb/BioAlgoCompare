"""
Scientific Export Module for BioAlgoCompare.

Provides unified export capabilities for scientific publications.
"""

from .unified_exporter import (
    ScientificExportPipeline,
    ExportFormat,
    CSVExporter,
    JSONExporter,
    LaTeXExporter,
    ExcelExporter,
    export_scientific_results
)

__all__ = [
    'ScientificExportPipeline',
    'ExportFormat',
    'CSVExporter',
    'JSONExporter',
    'LaTeXExporter',
    'ExcelExporter',
    'export_scientific_results'
]

# Version info
__version__ = '2.0.0'