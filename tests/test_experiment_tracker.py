"""
Tests para el sistema de registro de experimentos.
"""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
import numpy as np

from utils.experiment_tracker import (
    ExperimentTracker, ExperimentConfig, ExperimentResult,
    SystemInfo, GitInfo, create_experiment_result, track_experiment
)


class TestExperimentTracker:
    """Tests para ExperimentTracker."""
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Crea un directorio temporal para los tests."""
        return tmp_path / "test_experiments"
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Crea un tracker de experimentos para tests."""
        return ExperimentTracker(base_dir=str(temp_dir), auto_save=False)
    
    @pytest.fixture
    def sample_config(self):
        """Crea una configuración de ejemplo."""
        return ExperimentConfig(
            algorithm="woa",
            problem_instance="P-n16-k8",
            population_size=30,
            max_iterations=100,
            algorithm_params={"a": 2.0, "b": 1.0},
            seed=42
        )
    
    @pytest.fixture
    def sample_result(self):
        """Crea un resultado de ejemplo."""
        return ExperimentResult(
            run_id=1,
            seed=42,
            best_fitness=123.45,
            convergence_curve=[200.0, 180.0, 160.0, 140.0, 123.45],
            execution_time=5.67,
            final_solution=[1, 2, 3, 4, 5],
            iterations_completed=100,
            metadata={"custom": "data"}
        )
    
    def test_tracker_initialization(self, tracker, temp_dir):
        """Test de inicialización del tracker."""
        assert tracker.base_dir == temp_dir
        assert tracker.auto_save == False
        
        # Verificar que se crearon los subdirectorios
        assert (temp_dir / "records").exists()
        assert (temp_dir / "metadata").exists()
        assert (temp_dir / "summaries").exists()
    
    def test_start_experiment(self, tracker, sample_config):
        """Test de inicio de experimento."""
        exp_id = tracker.start_experiment(sample_config, metadata={"test": True})
        
        assert exp_id is not None
        assert tracker.current_experiment is not None
        assert tracker.current_experiment.experiment_id == exp_id
        assert tracker.current_experiment.config == sample_config
        assert tracker.current_experiment.metadata["test"] == True
        
        # Verificar que se capturó información del sistema
        assert isinstance(tracker.current_experiment.system_info, SystemInfo)
        assert tracker.current_experiment.system_info.platform is not None
    
    def test_log_result(self, tracker, sample_config, sample_result):
        """Test de registro de resultados."""
        # Iniciar experimento
        exp_id = tracker.start_experiment(sample_config)
        
        # Registrar resultado
        tracker.log_result(sample_result)
        
        assert len(tracker.current_experiment.results) == 1
        assert tracker.current_experiment.results[0] == sample_result
        
        # Verificar estadísticas actualizadas
        stats = tracker.current_experiment.summary_stats
        assert stats['total_runs'] == 1
        assert stats['best_fitness'] == 123.45
        assert stats['mean_fitness'] == 123.45
    
    def test_log_multiple_results(self, tracker, sample_config):
        """Test de registro de múltiples resultados."""
        tracker.start_experiment(sample_config)
        
        # Registrar múltiples resultados
        for i in range(5):
            result = ExperimentResult(
                run_id=i,
                seed=42 + i,
                best_fitness=120.0 + i * 2,
                convergence_curve=[200.0, 150.0, 120.0 + i * 2],
                execution_time=5.0 + i * 0.5,
                final_solution=[],
                iterations_completed=100
            )
            tracker.log_result(result)
        
        assert len(tracker.current_experiment.results) == 5
        
        # Verificar estadísticas
        stats = tracker.current_experiment.summary_stats
        assert stats['total_runs'] == 5
        assert stats['best_fitness'] == 120.0
        assert stats['worst_fitness'] == 128.0
        assert abs(stats['mean_fitness'] - 124.0) < 0.01
    
    def test_save_and_load_experiment(self, tracker, sample_config, sample_result):
        """Test de guardar y cargar experimento."""
        # Crear y guardar experimento
        exp_id = tracker.start_experiment(sample_config)
        tracker.log_result(sample_result)
        tracker.save_current()
        
        # Cargar experimento
        loaded = tracker.load_experiment(exp_id)
        
        assert loaded.experiment_id == exp_id
        assert loaded.config.algorithm == sample_config.algorithm
        assert len(loaded.results) == 1
        assert loaded.results[0].best_fitness == sample_result.best_fitness
    
    def test_list_experiments(self, tracker, sample_config):
        """Test de listar experimentos."""
        # Crear múltiples experimentos
        for i in range(3):
            config = ExperimentConfig(
                algorithm=f"alg_{i}",
                problem_instance="test.vrp",
                population_size=30,
                max_iterations=100
            )
            tracker.start_experiment(config)
            tracker.log_result(ExperimentResult(
                run_id=1, seed=42, best_fitness=100.0 + i,
                convergence_curve=[150.0, 100.0 + i],
                execution_time=1.0, final_solution=[],
                iterations_completed=100
            ))
            tracker.save_current()
        
        # Listar experimentos
        df = tracker.list_experiments()
        
        assert len(df) == 3
        assert set(df['algorithm'].values) == {'alg_0', 'alg_1', 'alg_2'}
    
    def test_filter_experiments(self, tracker):
        """Test de filtrado de experimentos."""
        # Crear experimentos con diferentes algoritmos
        algorithms = ['woa', 'woa', 'sma']
        for alg in algorithms:
            config = ExperimentConfig(
                algorithm=alg,
                problem_instance="test.vrp",
                population_size=30,
                max_iterations=100
            )
            tracker.start_experiment(config)
            tracker.log_result(ExperimentResult(
                run_id=1, seed=42, best_fitness=100.0,
                convergence_curve=[150.0, 100.0],
                execution_time=1.0, final_solution=[],
                iterations_completed=100
            ))
            tracker.save_current()
        
        # Filtrar por algoritmo
        df = tracker.list_experiments(filter_criteria={'algorithm': 'woa'})
        assert len(df) == 2
        assert all(df['algorithm'] == 'woa')
    
    def test_compare_experiments(self, tracker):
        """Test de comparación de experimentos."""
        exp_ids = []
        
        # Crear experimentos para comparar
        for i, alg in enumerate(['woa', 'sma']):
            config = ExperimentConfig(
                algorithm=alg,
                problem_instance="test.vrp",
                population_size=30,
                max_iterations=100
            )
            exp_id = tracker.start_experiment(config)
            exp_ids.append(exp_id)
            
            # Añadir resultados
            for j in range(3):
                tracker.log_result(ExperimentResult(
                    run_id=j, seed=42 + j, 
                    best_fitness=100.0 + i * 10 + j,
                    convergence_curve=[150.0, 100.0 + i * 10 + j],
                    execution_time=1.0, final_solution=[],
                    iterations_completed=100
                ))
            tracker.save_current()
        
        # Comparar experimentos
        comparison = tracker.compare_experiments(exp_ids)
        
        assert len(comparison) == 2
        assert comparison.iloc[0]['algorithm'] == 'woa'
        assert comparison.iloc[1]['algorithm'] == 'sma'
        assert comparison.iloc[0]['best_fitness'] < comparison.iloc[1]['best_fitness']
    
    def test_export_json(self, tracker, sample_config, sample_result):
        """Test de exportación a JSON."""
        exp_id = tracker.start_experiment(sample_config)
        tracker.log_result(sample_result)
        tracker.save_current()
        
        # Exportar a JSON
        output_file = tracker.export_experiment(exp_id, format='json')
        
        assert Path(output_file).exists()
        
        # Verificar contenido
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data['experiment_id'] == exp_id
        assert data['config']['algorithm'] == 'woa'
        assert len(data['results']) == 1
    
    def test_export_csv(self, tracker, sample_config, sample_result):
        """Test de exportación a CSV."""
        exp_id = tracker.start_experiment(sample_config)
        tracker.log_result(sample_result)
        tracker.save_current()
        
        # Exportar a CSV
        output_file = tracker.export_experiment(exp_id, format='csv')
        
        # Verificar que se crearon los archivos
        output_dir = Path(output_file).parent
        assert (output_dir / f"{exp_id}_results.csv").exists()
        assert (output_dir / f"{exp_id}_convergence.csv").exists()
    
    def test_export_latex(self, tracker, sample_config, sample_result):
        """Test de exportación a LaTeX."""
        exp_id = tracker.start_experiment(sample_config)
        tracker.log_result(sample_result)
        tracker.save_current()
        
        # Exportar a LaTeX
        output_file = tracker.export_experiment(exp_id, format='latex')
        
        assert Path(output_file).exists()
        
        # Verificar contenido básico
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert r'\begin{table}' in content
        assert 'woa' in content
        assert 'P-n16-k8' in content
    
    def test_export_html(self, tracker, sample_config, sample_result):
        """Test de exportación a HTML."""
        exp_id = tracker.start_experiment(sample_config)
        tracker.log_result(sample_result)
        tracker.save_current()
        
        # Exportar a HTML
        output_file = tracker.export_experiment(exp_id, format='html')
        
        assert Path(output_file).exists()
        
        # Verificar contenido básico
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert '<html>' in content
        assert 'woa' in content
        assert 'P-n16-k8' in content
    
    def test_auto_save(self, temp_dir):
        """Test de auto-guardado."""
        tracker = ExperimentTracker(base_dir=str(temp_dir), auto_save=True)
        
        config = ExperimentConfig(
            algorithm="test",
            problem_instance="test.vrp",
            population_size=10,
            max_iterations=10
        )
        
        exp_id = tracker.start_experiment(config)
        
        # Registrar resultado (debe auto-guardar)
        result = ExperimentResult(
            run_id=1, seed=42, best_fitness=100.0,
            convergence_curve=[150.0, 100.0],
            execution_time=1.0, final_solution=[],
            iterations_completed=10
        )
        tracker.log_result(result)
        
        # Verificar que se guardó
        record_file = tracker.records_dir / f"{exp_id}.json"
        assert record_file.exists()
    
    def test_experiment_hash(self, sample_config):
        """Test de generación de hash para configuración."""
        hash1 = sample_config.to_hash()
        assert len(hash1) == 8
        
        # El mismo config debe generar el mismo hash
        hash2 = sample_config.to_hash()
        assert hash1 == hash2
        
        # Cambiar un parámetro debe cambiar el hash
        sample_config.population_size = 50
        hash3 = sample_config.to_hash()
        assert hash1 != hash3
    
    def test_convergence_rate_calculation(self, tracker, sample_config):
        """Test del cálculo de tasa de convergencia."""
        tracker.start_experiment(sample_config)
        
        # Añadir resultados con diferentes convergencias
        curves = [
            [200.0, 180.0, 160.0, 140.0, 120.0],  # 40% mejora
            [200.0, 190.0, 180.0, 170.0, 160.0],  # 20% mejora
            [200.0, 200.0, 200.0, 200.0, 200.0],  # 0% mejora
        ]
        
        for i, curve in enumerate(curves):
            result = ExperimentResult(
                run_id=i, seed=42 + i, best_fitness=curve[-1],
                convergence_curve=curve, execution_time=1.0,
                final_solution=[], iterations_completed=len(curve) - 1
            )
            tracker.log_result(result)
        
        # La tasa promedio debe ser (0.4 + 0.2 + 0.0) / 3 = 0.2
        rate = tracker.current_experiment._calculate_convergence_rate()
        assert abs(rate - 0.2) < 0.01
    
    def test_system_info_capture(self):
        """Test de captura de información del sistema."""
        info = SystemInfo.capture()
        
        assert info.platform is not None
        assert info.python_version is not None
        assert info.cpu_count > 0
        assert info.total_memory_gb > 0
        assert info.hostname is not None
    
    def test_create_experiment_result_utility(self):
        """Test de la función de utilidad create_experiment_result."""
        # Simular resultado de algoritmo
        class MockAlgorithmResult:
            def fitness(self):
                return 123.45
            
            def get_convergence_curve(self):
                return [200.0, 150.0, 123.45]
            
            position = [1, 2, 3, 4, 5]
        
        mock_result = MockAlgorithmResult()
        
        # Crear ExperimentResult
        exp_result = create_experiment_result(
            run_id=1,
            seed=42,
            algorithm_result=mock_result,
            execution_time=5.67
        )
        
        assert exp_result.run_id == 1
        assert exp_result.seed == 42
        assert exp_result.best_fitness == 123.45
        assert exp_result.convergence_curve == [200.0, 150.0, 123.45]
        assert exp_result.execution_time == 5.67
        assert exp_result.final_solution == [1, 2, 3, 4, 5]
        assert exp_result.iterations_completed == 2
    
    def test_track_experiment_decorator(self, tracker, sample_config):
        """Test del decorador track_experiment."""
        
        @track_experiment(tracker)
        def mock_algorithm(config: ExperimentConfig):
            # Simular ejecución de algoritmo
            return ExperimentResult(
                run_id=1, seed=config.seed or 42,
                best_fitness=100.0,
                convergence_curve=[150.0, 100.0],
                execution_time=1.0, final_solution=[],
                iterations_completed=100
            )
        
        # Ejecutar función decorada
        result = mock_algorithm(sample_config)
        
        # Verificar que se registró el experimento
        assert tracker.current_experiment is not None
        assert len(tracker.current_experiment.results) == 1
        assert tracker.current_experiment.results[0].best_fitness == 100.0
        
        # Verificar que se guardó
        exp_id = tracker.current_experiment.experiment_id
        record_file = tracker.records_dir / f"{exp_id}.json"
        assert record_file.exists()
    
    def test_error_handling_in_decorator(self, tracker, sample_config):
        """Test del manejo de errores en el decorador."""
        
        @track_experiment(tracker)
        def failing_algorithm(config: ExperimentConfig):
            raise ValueError("Algorithm failed!")
        
        # Ejecutar función que falla
        with pytest.raises(ValueError):
            failing_algorithm(sample_config)
        
        # Verificar que se registró el error
        assert tracker.current_experiment is not None
        assert 'error' in tracker.current_experiment.metadata
        assert 'Algorithm failed!' in tracker.current_experiment.metadata['error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])