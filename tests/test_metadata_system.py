"""
Tests para el sistema de metadatos y trazabilidad experimental.
"""

import pytest
import json
from pathlib import Path
import tempfile
from datetime import datetime
import time

from utils.metadata import (
    MetadataManager,
    MetadataLevel,
    ExperimentTracer,
    EventType,
    create_tracked_algorithm,
    enable_metadata_tracking
)
from algorithms.hoa import HOA
from problems.vrp import VRPProblem


class TestMetadataManager:
    """Tests para el gestor de metadatos."""
    
    def test_metadata_manager_creation(self):
        """Test creación básica del manager."""
        manager = MetadataManager()
        
        assert manager is not None
        assert manager.metadata_level == MetadataLevel.STANDARD
        assert manager.auto_capture is True
    
    def test_create_experiment(self):
        """Test creación de experimento."""
        manager = MetadataManager()
        
        experiment = manager.create_experiment(
            experiment_type="test",
            algorithm_name="TestAlgo",
            problem_instance="test-instance",
            parameters={'param1': 10, 'param2': 20},
            description="Test experiment",
            tags=['test', 'unit']
        )
        
        assert experiment.experiment_type == "test"
        assert experiment.algorithm.name == "TestAlgo"
        assert experiment.problem.instance == "test-instance"
        assert experiment.algorithm.parameters == {'param1': 10, 'param2': 20}
        assert 'test' in experiment.tags
        assert 'unit' in experiment.tags
    
    def test_system_metadata_capture(self):
        """Test captura de metadatos del sistema."""
        from utils.metadata.metadata_manager import SystemMetadata
        
        system_meta = SystemMetadata.capture()
        
        assert system_meta.hostname is not None
        assert system_meta.username is not None
        assert 'python_version' in system_meta.platform
        assert 'cpu_count' in system_meta.hardware
        assert system_meta.software['numpy'] is not None
    
    def test_experiment_lifecycle(self):
        """Test ciclo de vida completo de un experimento."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MetadataManager(storage_path=Path(tmpdir))
            
            # Crear experimento
            exp = manager.create_experiment(
                "test", "HOA", "E-n22-k4",
                {'population_size': 10, 'max_iterations': 5}
            )
            
            exp_id = exp.experiment_id
            
            # Actualizar durante ejecución
            for i in range(3):
                manager.update_execution(exp_id, i, {
                    'best_fitness': 100 - i*10,
                    'mean_fitness': 120 - i*5
                })
            
            # Finalizar experimento
            result = {
                'best_fitness': 80.5,
                'best_solution': 'mock_solution',
                'mean_fitness': 95.0
            }
            
            final_exp = manager.finalize_experiment(exp_id, result)
            
            # Verificar
            assert final_exp.result is not None
            assert final_exp.result.best_fitness == 80.5
            assert final_exp.execution.iterations_completed == 2
            assert len(final_exp.execution.convergence_history) == 3
            assert final_exp.execution.end_time is not None
            assert final_exp.execution.duration_seconds > 0
    
    def test_metadata_levels(self):
        """Test diferentes niveles de metadatos."""
        manager = MetadataManager()
        
        exp = manager.create_experiment(
            "test", "HOA", "test",
            {'param': 1},
            custom={'custom_data': 'test'}
        )
        
        # Nivel minimal
        minimal = exp.to_dict(MetadataLevel.MINIMAL)
        assert 'experiment_id' in minimal
        assert 'algorithm' in minimal
        assert 'system' not in minimal
        
        # Nivel standard
        standard = exp.to_dict(MetadataLevel.STANDARD)
        assert 'system' in standard
        assert 'algorithm' in standard
        
        # Nivel complete
        complete = exp.to_dict(MetadataLevel.COMPLETE)
        assert 'system' in complete
        assert 'environment' in complete['system']


class TestTraceability:
    """Tests para el sistema de trazabilidad."""
    
    def test_trace_event_creation(self):
        """Test creación de eventos de traza."""
        from utils.metadata.traceability import TraceEvent
        
        event = TraceEvent(
            event_id="test-001",
            experiment_id="exp-001",
            timestamp=datetime.now().isoformat(),
            event_type=EventType.EXPERIMENT_START,
            component="test_component",
            data={'key': 'value'}
        )
        
        assert event.event_id == "test-001"
        assert event.event_type == EventType.EXPERIMENT_START
        
        # Verificar hash
        hash1 = event.calculate_hash()
        hash2 = event.calculate_hash()
        assert hash1 == hash2  # Debe ser determinístico
    
    def test_traceability_db(self):
        """Test base de datos de trazabilidad."""
        from utils.metadata.traceability import TraceabilityDB, TraceEvent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db = TraceabilityDB(Path(tmpdir) / "test.db")
            
            # Añadir evento
            event = TraceEvent(
                event_id="test-001",
                experiment_id="exp-001",
                timestamp=datetime.now().isoformat(),
                event_type=EventType.SOLUTION_FOUND,
                component="algorithm",
                data={'fitness': 100.5}
            )
            
            db.add_event(event)
            
            # Recuperar eventos
            events = db.get_events(experiment_id="exp-001")
            assert len(events) == 1
            assert events[0].event_id == "test-001"
            assert events[0].data['fitness'] == 100.5
            
            # Verificar integridad
            is_valid, issues = db.verify_integrity("exp-001")
            assert is_valid
            assert len(issues) == 0
    
    def test_experiment_tracer(self):
        """Test trazador de experimentos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MetadataManager(storage_path=Path(tmpdir))
            tracer = ExperimentTracer(manager, db_path=Path(tmpdir) / "trace.db")
            
            # Crear experimento
            exp = manager.create_experiment("test", "HOA", "test", {})
            
            # Usar context manager
            with tracer.trace_experiment(exp.experiment_id):
                # Trazar eventos
                tracer.trace_event(
                    EventType.ITERATION_START,
                    "algorithm",
                    {'iteration': 0}
                )
                
                tracer.trace_solution(
                    solution="mock_solution",
                    fitness=95.5,
                    iteration=0
                )
                
                tracer.annotate("Test annotation", {'extra': 'data'})
            
            # Obtener timeline
            timeline = tracer.get_experiment_timeline(exp.experiment_id)
            
            # Debe tener al menos 5 eventos (start, iteration, solution, annotation, end)
            assert len(timeline) >= 5
            
            # Verificar tipos de eventos
            event_types = [e['event_type'] for e in timeline]
            assert 'EXPERIMENT_START' in event_types
            assert 'EXPERIMENT_END' in event_types
            assert 'SOLUTION_FOUND' in event_types
            assert 'USER_ANNOTATION' in event_types


class TestAlgorithmIntegration:
    """Tests para la integración con algoritmos."""
    
    def test_metadata_tracking_mixin(self):
        """Test mixin de tracking de metadatos."""
        from utils.metadata.algorithm_integration import MetadataTrackingMixin
        
        # Crear clase de prueba con mixin
        class TestAlgorithm(MetadataTrackingMixin):
            def __init__(self, **kwargs):
                self.population_size = 10
                self.max_iterations = 5
                self.seed = 42
                self.problem = type('Problem', (), {'instance_name': 'test'})()
                super().__init__(**kwargs)
            
            def run(self):
                # Simular ejecución
                for i in range(3):
                    self._on_iteration_complete(i, {
                        'best_fitness': 100 - i*10,
                        'mean_fitness': 110 - i*5
                    })
                
                return {
                    'best_fitness': 70,
                    'best_solution': 'solution'
                }
        
        # Crear con metadata habilitado
        algo = TestAlgorithm(metadata_config={'enable': True})
        
        # Verificar que se creó el experimento
        assert hasattr(algo, '_experiment_metadata')
        assert hasattr(algo, '_tracer')
        
        # Ejecutar
        result = algo.run()
        
        assert result['best_fitness'] == 70
    
    def test_enable_metadata_tracking(self):
        """Test añadir tracking a algoritmo existente."""
        # Crear clase simple de algoritmo
        class SimpleAlgorithm:
            def __init__(self, problem, population_size=10, max_iterations=5, seed=None):
                self.problem = problem
                self.population_size = population_size
                self.max_iterations = max_iterations
                self.seed = seed
            
            def run(self):
                return {'best_fitness': 100.0}
        
        # Añadir tracking
        TrackedAlgorithm = enable_metadata_tracking(SimpleAlgorithm)
        
        # Verificar nombre
        assert 'Tracked' in TrackedAlgorithm.__name__
        
        # Crear instancia
        problem = type('Problem', (), {'instance_name': 'test'})()
        algo = TrackedAlgorithm(problem, seed=42)
        
        # Ejecutar
        result = algo.run()
        assert result['best_fitness'] == 100.0
    
    @pytest.mark.slow
    def test_tracked_algorithm_with_vrp(self):
        """Test algoritmo tracked con problema VRP real."""
        # Este test requiere archivos VRP
        try:
            problem = VRPProblem("E-n22-k4")
        except:
            pytest.skip("VRP files not available")
        
        # Crear algoritmo con tracking
        algo = create_tracked_algorithm(
            "HOA",
            problem,
            population_size=5,
            max_iterations=3,
            seed=42
        )
        
        # Ejecutar
        result = algo.run()
        
        # Verificar resultado
        assert 'best_fitness' in result
        assert result['best_fitness'] > 0
        
        # Verificar que se crearon metadatos
        assert hasattr(algo, '_experiment_metadata')
        exp_id = algo._experiment_metadata.experiment_id
        assert exp_id is not None


class TestMetadataChecksum:
    """Tests para verificación de integridad."""
    
    def test_experiment_checksum(self):
        """Test cálculo de checksum de experimento."""
        manager = MetadataManager()
        
        exp = manager.create_experiment(
            "test", "HOA", "test",
            {'seed': 42, 'population_size': 30}
        )
        
        # Simular resultado
        exp.result = type('Result', (), {
            'best_fitness': 100.5
        })()
        
        # Calcular checksum
        checksum1 = exp.calculate_checksum()
        checksum2 = exp.calculate_checksum()
        
        assert checksum1 == checksum2  # Debe ser determinístico
        assert len(checksum1) == 64  # SHA256 hex


class TestMetadataSearch:
    """Tests para búsqueda de experimentos."""
    
    def test_search_experiments(self):
        """Test búsqueda de experimentos por criterios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MetadataManager(storage_path=Path(tmpdir))
            
            # Crear varios experimentos
            exp1 = manager.create_experiment(
                "test", "HOA", "E-n22-k4",
                {}, tags=['benchmark', 'test']
            )
            manager.finalize_experiment(exp1.experiment_id, {'best_fitness': 100})
            
            exp2 = manager.create_experiment(
                "test", "FOA", "E-n22-k4", 
                {}, tags=['test']
            )
            manager.finalize_experiment(exp2.experiment_id, {'best_fitness': 110})
            
            exp3 = manager.create_experiment(
                "test", "HOA", "P-n16-k8",
                {}, tags=['benchmark']
            )
            manager.finalize_experiment(exp3.experiment_id, {'best_fitness': 90})
            
            # Buscar por algoritmo
            results = manager.search_experiments(algorithm="HOA")
            assert len(results) == 2
            
            # Buscar por problema
            results = manager.search_experiments(problem="E-n22-k4")
            assert len(results) == 2
            
            # Buscar por tags
            results = manager.search_experiments(tags=['benchmark'])
            assert len(results) == 2
            
            # Buscar por múltiples criterios
            results = manager.search_experiments(
                algorithm="HOA",
                tags=['benchmark']
            )
            assert len(results) >= 1


class TestExperimentLineage:
    """Tests para linaje de experimentos."""
    
    def test_experiment_chains(self):
        """Test relaciones entre experimentos."""
        from utils.metadata.traceability import TraceabilityDB
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db = TraceabilityDB(Path(tmpdir) / "trace.db")
            
            # Añadir cadena de experimentos
            db.add_experiment_chain(
                "exp-002",
                "exp-001",
                "continuation",
                {'reason': 'parameter_tuning'}
            )
            
            db.add_experiment_chain(
                "exp-003",
                "exp-002",
                "variation",
                {'changes': ['population_size']}
            )
            
            # Obtener linaje
            lineage = db.get_experiment_lineage("exp-002")
            
            assert len(lineage['parents']) == 1
            assert lineage['parents'][0]['experiment_id'] == "exp-001"
            
            assert len(lineage['children']) == 1
            assert lineage['children'][0]['experiment_id'] == "exp-003"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])