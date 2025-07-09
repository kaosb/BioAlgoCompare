"""
Tests para la integración entre el esquema estandarizado y el sistema de tracking.
"""

import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from utils.result_integration import (
    ResultIntegration, integrate_with_tracker,
    quick_convert_to_standard, quick_convert_to_experiment
)
from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics,
    ProblemInfo, AlgorithmInfo, ExecutionInfo, ResultType
)
from utils.experiment_tracker import (
    ExperimentRecord, ExperimentConfig, ExperimentResult,
    SystemInfo, GitInfo, ExperimentTracker
)


class TestResultIntegration:
    """Tests para ResultIntegration."""
    
    @pytest.fixture
    def sample_experiment_record(self):
        """Crea un ExperimentRecord de ejemplo."""
        config = ExperimentConfig(
            algorithm="woa",
            problem_instance="P-n16-k8.vrp",
            population_size=30,
            max_iterations=100,
            algorithm_params={"a": 2.0, "b": 1.0},
            seed=42
        )
        
        system_info = SystemInfo(
            platform="Linux",
            platform_version="5.4.0",
            python_version="3.9.0",
            cpu_count=8,
            cpu_model="Intel Core i7",
            total_memory_gb=16.0,
            hostname="test-machine"
        )
        
        git_info = GitInfo(
            commit_hash="abc123",
            branch="main",
            is_dirty=False,
            commit_message="Test commit",
            commit_date=datetime.now().isoformat()
        )
        
        results = [
            ExperimentResult(
                run_id=i,
                seed=42 + i,
                best_fitness=465.0 + i,
                convergence_curve=[500.0, 480.0, 465.0 + i],
                execution_time=5.0 + i * 0.1,
                final_solution=[[0, 1, 2, 0], [0, 3, 4, 0]],
                iterations_completed=100,
                metadata={"evaluations": 3000}
            )
            for i in range(3)
        ]
        
        return ExperimentRecord(
            experiment_id="woa_P-n16-k8_20240315_120000",
            timestamp=datetime.now().isoformat(),
            config=config,
            system_info=system_info,
            git_info=git_info,
            results=results,
            summary_stats={
                'n_runs': 3,
                'best_fitness': 465.0,
                'mean_fitness': 466.0,
                'std_fitness': 1.0
            },
            metadata={'experiment_type': 'test'}
        )
    
    @pytest.fixture
    def sample_standard_result(self):
        """Crea un StandardResult de ejemplo."""
        problem_info = ProblemInfo(
            name="P-n16-k8",
            type="VRP",
            dimension=15,
            optimal_value=450.0
        )
        
        algorithm_info = AlgorithmInfo(
            name="woa",
            version="v2",
            population_size=30,
            max_iterations=100,
            parameters={"a": 2.0},
            seed=42
        )
        
        execution_info = ExecutionInfo(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=15),
            duration_seconds=15.0,
            platform="Linux",
            python_version="3.9.0",
            cpu_count=8,
            memory_gb=16.0
        )
        
        runs = [
            SingleRunResult(
                run_id=i,
                seed=42 + i,
                best_fitness=465.0 + i,
                best_solution=[[0, 1, 2, 0]],
                convergence_curve=[500.0, 465.0 + i],
                execution_time=5.0,
                iterations_completed=100,
                evaluations=3000
            )
            for i in range(3)
        ]
        
        statistics = MultiRunStatistics.from_runs(runs)
        
        return StandardResult(
            result_id="woa_P-n16-k8_test",
            result_type=ResultType.MULTI_RUN,
            timestamp=datetime.now(),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            execution_info=execution_info,
            runs=runs,
            statistics=statistics
        )
    
    def test_experiment_to_standard_conversion(self, sample_experiment_record):
        """Test conversión de ExperimentRecord a StandardResult."""
        standard = ResultIntegration.experiment_to_standard(sample_experiment_record)
        
        assert isinstance(standard, StandardResult)
        assert standard.result_id == sample_experiment_record.experiment_id
        assert standard.algorithm_info.name == "woa"
        assert standard.problem_info.name == "P-n16-k8"
        assert len(standard.runs) == 3
        assert standard.statistics.n_runs == 3
        assert standard.statistics.best_fitness == 465.0
        
        # Verificar metadatos
        assert 'git_info' in standard.metadata
        assert 'system_info' in standard.metadata
        assert standard.metadata['system_info']['platform'] == "Linux"
    
    def test_standard_to_experiment_conversion(self, sample_standard_result):
        """Test conversión de StandardResult a ExperimentRecord."""
        record = ResultIntegration.standard_to_experiment(sample_standard_result)
        
        assert isinstance(record, ExperimentRecord)
        assert record.experiment_id == sample_standard_result.result_id
        assert record.config.algorithm == "woa"
        assert record.config.problem_instance == "P-n16-k8.vrp"
        assert len(record.results) == 3
        assert record.summary_stats['best_fitness'] == 465.0
    
    def test_bidirectional_conversion(self, sample_experiment_record):
        """Test conversión bidireccional mantiene información."""
        # ExperimentRecord -> StandardResult -> ExperimentRecord
        standard = ResultIntegration.experiment_to_standard(sample_experiment_record)
        record_back = ResultIntegration.standard_to_experiment(standard)
        
        assert record_back.experiment_id == sample_experiment_record.experiment_id
        assert record_back.config.algorithm == sample_experiment_record.config.algorithm
        assert len(record_back.results) == len(sample_experiment_record.results)
        assert record_back.results[0].best_fitness == sample_experiment_record.results[0].best_fitness
    
    def test_migrate_legacy_experiment_format(self, tmp_path):
        """Test migración de formato legacy de experimento."""
        # Crear archivo legacy
        legacy_data = {
            'experiment_id': 'test_exp',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'algorithm': 'woa',
                'problem_instance': 'P-n16-k8.vrp',
                'population_size': 30,
                'max_iterations': 100,
                'algorithm_params': {},
                'seed': 42
            },
            'system_info': {
                'platform': 'Linux',
                'platform_version': '5.0',
                'python_version': '3.8',
                'cpu_count': 4,
                'cpu_model': 'Intel',
                'total_memory_gb': 8.0,
                'hostname': 'test'
            },
            'git_info': None,
            'results': [{
                'run_id': 0,
                'seed': 42,
                'best_fitness': 465.0,
                'convergence_curve': [500.0, 465.0],
                'execution_time': 5.0,
                'final_solution': [[0, 1, 0]],
                'iterations_completed': 100,
                'metadata': {}
            }],
            'summary_stats': {'best_fitness': 465.0},
            'metadata': {}
        }
        
        legacy_file = tmp_path / "legacy_exp.json"
        with open(legacy_file, 'w') as f:
            json.dump(legacy_data, f)
        
        # Migrar
        output_dir = tmp_path / "migrated"
        migrated_ids = ResultIntegration.migrate_legacy_results(legacy_file, output_dir)
        
        assert len(migrated_ids) == 1
        assert output_dir.exists()
        
        # Verificar archivo migrado
        migrated_files = list(output_dir.glob("*.json"))
        assert len(migrated_files) == 1
        
        # Cargar y verificar
        migrated_result = StandardResult.from_json(migrated_files[0])
        assert migrated_result.algorithm_info.name == "woa"
        assert migrated_result.statistics.best_fitness == 465.0
    
    def test_migrate_simple_legacy_format(self, tmp_path):
        """Test migración de formato legacy simple."""
        # Datos legacy simples
        legacy_data = {
            'algorithm': 'sma',
            'instance': 'E-n22-k4',
            'best_fitness': 380.0,
            'execution_time': 10.5,
            'convergence': [400.0, 390.0, 380.0],
            'seed': 123,
            'population_size': 50,
            'iterations': 200
        }
        
        legacy_file = tmp_path / "simple_legacy.json"
        with open(legacy_file, 'w') as f:
            json.dump(legacy_data, f)
        
        # Migrar
        output_dir = tmp_path / "migrated"
        migrated_ids = ResultIntegration.migrate_legacy_results(legacy_file, output_dir)
        
        assert len(migrated_ids) == 1
        
        # Verificar
        migrated_files = list(output_dir.glob("*.json"))
        result = StandardResult.from_json(migrated_files[0])
        
        assert result.algorithm_info.name == "sma"
        assert result.problem_info.name == "E-n22-k4"
        assert result.statistics.best_fitness == 380.0
        assert result.metadata['migrated_from'] == 'legacy_simple'
    
    def test_integrate_with_tracker_decorator(self, tmp_path):
        """Test del decorador integrate_with_tracker."""
        
        @integrate_with_tracker
        class TestTracker(ExperimentTracker):
            pass
        
        # Crear tracker decorado
        tracker = TestTracker(base_dir=str(tmp_path))
        
        # Configurar experimento
        config = ExperimentConfig(
            algorithm="test",
            problem_instance="test.vrp",
            population_size=10,
            max_iterations=10
        )
        
        # Iniciar experimento
        exp_id = tracker.start_experiment(config)
        
        # Añadir resultado
        result = ExperimentResult(
            run_id=0,
            seed=42,
            best_fitness=100.0,
            convergence_curve=[100.0],
            execution_time=1.0,
            final_solution=[],
            iterations_completed=10
        )
        tracker.log_result(result)
        
        # Guardar (debe crear ambos formatos)
        tracker.save_current()
        
        # Verificar que se guardaron ambos formatos
        original_file = tmp_path / "records" / f"{exp_id}.json"
        standard_dir = tmp_path / "standard"
        
        assert original_file.exists()
        assert standard_dir.exists()
        
        standard_files = list(standard_dir.glob("*.json"))
        assert len(standard_files) == 1
    
    def test_quick_conversion_functions(self, tmp_path):
        """Test funciones de conversión rápida."""
        # Crear archivo de experimento
        experiment_data = {
            'experiment_id': 'quick_test',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'algorithm': 'gto',
                'problem_instance': 'A-n32-k5.vrp',
                'population_size': 40,
                'max_iterations': 150,
                'algorithm_params': {},
                'seed': 99
            },
            'system_info': {
                'platform': 'Darwin',
                'platform_version': '20.0',
                'python_version': '3.9',
                'cpu_count': 8,
                'cpu_model': 'M1',
                'total_memory_gb': 16.0,
                'hostname': 'mac'
            },
            'git_info': None,
            'results': [{
                'run_id': 0,
                'seed': 99,
                'best_fitness': 800.0,
                'convergence_curve': [900.0, 800.0],
                'execution_time': 8.0,
                'final_solution': [],
                'iterations_completed': 150,
                'metadata': {}
            }],
            'summary_stats': {'best_fitness': 800.0},
            'metadata': {}
        }
        
        exp_file = tmp_path / "experiment.json"
        with open(exp_file, 'w') as f:
            json.dump(experiment_data, f)
        
        # Test conversión rápida a estándar
        standard = quick_convert_to_standard(exp_file)
        assert isinstance(standard, StandardResult)
        assert standard.algorithm_info.name == "gto"
        assert standard.statistics.best_fitness == 800.0
        
        # Guardar como estándar
        standard_file = tmp_path / "standard.json"
        standard.to_json(standard_file)
        
        # Test conversión rápida a experimento
        record = quick_convert_to_experiment(standard_file)
        assert isinstance(record, ExperimentRecord)
        assert record.config.algorithm == "gto"
        assert record.results[0].best_fitness == 800.0
    
    def test_conversion_preserves_custom_metrics(self):
        """Test que la conversión preserva métricas personalizadas."""
        # Crear experimento con métricas custom
        result = ExperimentResult(
            run_id=0,
            seed=42,
            best_fitness=100.0,
            convergence_curve=[100.0],
            execution_time=1.0,
            final_solution=[],
            iterations_completed=10,
            metadata={
                'diversity': 0.85,
                'vehicles_used': 5,
                'custom_metric': 123.45
            }
        )
        
        record = ExperimentRecord(
            experiment_id="test_metrics",
            timestamp=datetime.now().isoformat(),
            config=ExperimentConfig("test", "test.vrp", 10, 10),
            system_info=SystemInfo.capture(),
            git_info=None,
            results=[result],
            summary_stats={'best_fitness': 100.0},
            metadata={'test': True}
        )
        
        # Convertir a estándar
        standard = ResultIntegration.experiment_to_standard(record)
        
        # Verificar métricas preservadas
        assert standard.runs[0].custom_metrics['diversity'] == 0.85
        assert standard.runs[0].custom_metrics['vehicles_used'] == 5
        assert standard.runs[0].custom_metrics['custom_metric'] == 123.45
        
        # Convertir de vuelta
        record_back = ResultIntegration.standard_to_experiment(standard)
        
        # Verificar que siguen ahí
        assert record_back.results[0].metadata['diversity'] == 0.85
        assert record_back.results[0].metadata['vehicles_used'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])