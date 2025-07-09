"""
Sistema unificado de resultados para BioAlgoCompare.

Este paquete proporciona un pipeline completo para manejo de resultados,
desde la captura hasta la exportación, con validación y almacenamiento.
"""

# Importar componentes principales
from ..result_schema_v2 import (
    StandardResultV2,
    SystemInfo,
    GitInfo,
    ExecutionInfoV2,
    DependencyInfo
)

from ..result_schema import (
    ResultType,
    MetricType,
    ProblemInfo,
    AlgorithmInfo,
    SingleRunResult,
    MultiRunStatistics,
    ResultBuilder
)

from .pipeline import (
    ResultPipeline,
    ValidationError,
    get_default_pipeline,
    process_result
)

# Alias convenientes
Result = StandardResultV2
Pipeline = ResultPipeline

# Versión del sistema de resultados
__version__ = "2.0.0"

# Exports públicos
__all__ = [
    # Clases principales
    'StandardResultV2',
    'Result',
    'ResultPipeline',
    'Pipeline',
    
    # Componentes de metadatos
    'SystemInfo',
    'GitInfo', 
    'ExecutionInfoV2',
    'DependencyInfo',
    
    # Componentes base
    'ResultType',
    'MetricType',
    'ProblemInfo',
    'AlgorithmInfo',
    'SingleRunResult',
    'MultiRunStatistics',
    'ResultBuilder',
    
    # Funciones de utilidad
    'get_default_pipeline',
    'process_result',
    
    # Excepciones
    'ValidationError',
    
    # Versión
    '__version__'
]