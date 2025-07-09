"""
Sistema de metadatos y trazabilidad experimental.

Este paquete proporciona capacidades completas de gestión de metadatos
y trazabilidad para experimentos de optimización.

Componentes principales:
- MetadataManager: Gestión integral de metadatos experimentales
- ExperimentTracer: Sistema de trazabilidad con eventos y auditoría
- MetadataTrackingMixin: Integración transparente con algoritmos
- TraceabilityDB: Almacenamiento persistente de eventos

Ejemplo de uso básico:

    from utils.metadata import MetadataManager, create_tracked_algorithm
    
    # Crear gestor de metadatos
    manager = MetadataManager()
    
    # Crear experimento
    experiment = manager.create_experiment(
        experiment_type="benchmark",
        algorithm_name="HOA",
        problem_instance="E-n22-k4",
        parameters={'population_size': 50, 'max_iterations': 100}
    )
    
    # O usar algoritmo con tracking automático
    algo = create_tracked_algorithm("HOA", problem, seed=42)
    result = algo.run()
"""

from .metadata_manager import (
    MetadataManager,
    MetadataLevel,
    SystemMetadata,
    AlgorithmMetadata,
    ProblemMetadata,
    ExecutionMetadata,
    ResultMetadata,
    ExperimentMetadata,
    create_metadata_manager
)

from .traceability import (
    EventType,
    TraceEvent,
    TraceabilityDB,
    ExperimentTracer,
    create_experiment_tracer
)

from .algorithm_integration import (
    MetadataTrackingMixin,
    TrackedMetaheuristicAlgorithm,
    track_execution,
    track_population_changes,
    enable_metadata_tracking,
    create_tracked_algorithm
)

__all__ = [
    # Metadata Manager
    'MetadataManager',
    'MetadataLevel',
    'SystemMetadata',
    'AlgorithmMetadata', 
    'ProblemMetadata',
    'ExecutionMetadata',
    'ResultMetadata',
    'ExperimentMetadata',
    'create_metadata_manager',
    
    # Traceability
    'EventType',
    'TraceEvent',
    'TraceabilityDB',
    'ExperimentTracer',
    'create_experiment_tracer',
    
    # Algorithm Integration
    'MetadataTrackingMixin',
    'TrackedMetaheuristicAlgorithm',
    'track_execution',
    'track_population_changes',
    'enable_metadata_tracking',
    'create_tracked_algorithm'
]