"""
Tests para el esquema estandarizado de resultados.
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

from utils.result_schema import (
    ResultType, MetricType, ProblemInfo, AlgorithmInfo, ExecutionInfo,
    SingleRunResult, MultiRunStatistics, StandardResult, ComparisonResult,
    ResultBuilder, validate_result, merge_results
)


class TestResultSchema:
    """Tests para el esquema de resultados."""
    
    @pytest.fixture
    def sample_problem_info(self):
        """Información de problema de ejemplo."""
        return ProblemInfo(
            name="P-n16-k8",
            type="VRP",
            dimension=15,
            optimal_value=450.0,
            instance_file="data/vrp/P-n16-k8.vrp",
            constraints={"capacity": 35},
            metadata={"source": "CVRPLIB"}
        )
    
    @pytest.fixture
    def sample_algorithm_info(self):
        """Información de algoritmo de ejemplo."""
        return AlgorithmInfo(
            name="woa",
            version="v2",
            population_size=30,
            max_iterations=100,
            parameters={"a": 2.0, "b": 1.0},
            seed=42
        )
    
    @pytest.fixture
    def sample_execution_info(self):
        """Información de ejecución de ejemplo."""
        start = datetime.now()
        end = start + timedelta(seconds=5.5)
        return ExecutionInfo(
            start_time=start,
            end_time=end,
            duration_seconds=5.5,
            platform="Linux",
            python_version="3.9.0",
            cpu_count=8,
            memory_gb=16.0,
            parallel=True,
            n_workers=4
        )
    
    @pytest.fixture
    def sample_single_run(self):
        """Resultado de run individual de ejemplo."""
        return SingleRunResult(
            run_id=0,
            seed=42,
            best_fitness=465.5,
            best_solution=[[0, 1, 2, 0], [0, 3, 4, 5, 0]],
            convergence_curve=[500.0, 490.0, 480.0, 470.0, 465.5],
            execution_time=5.5,
            iterations_completed=100,
            evaluations=3000,
            final_population_fitness=[465.5, 470.0, 475.0, 480.0],
            diversity_metrics={"avg_distance": 0.25, "unique_solutions": 28},
            custom_metrics={"vehicles_used": 2}
        )
    
    @pytest.fixture
    def sample_standard_result(self, sample_problem_info, sample_algorithm_info, 
                              sample_execution_info, sample_single_run):
        """Resultado estándar completo de ejemplo."""
        runs = [sample_single_run]
        statistics = MultiRunStatistics.from_runs(runs)
        
        return StandardResult(
            result_id="woa_P-n16-k8_20240315_120000",
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=sample_problem_info,
            algorithm_info=sample_algorithm_info,
            execution_info=sample_execution_info,
            runs=runs,
            statistics=statistics,
            metadata={"experiment": "test"}
        )
    
    def test_problem_info(self, sample_problem_info):
        """Test de ProblemInfo."""
        assert sample_problem_info.name == "P-n16-k8"
        assert sample_problem_info.dimension == 15
        assert sample_problem_info.optimal_value == 450.0
        
        # Test conversión a dict
        data = sample_problem_info.to_dict()
        assert data['name'] == "P-n16-k8"
        assert data['constraints']['capacity'] == 35
    
    def test_algorithm_info(self, sample_algorithm_info):
        """Test de AlgorithmInfo."""
        assert sample_algorithm_info.name == "woa"
        assert sample_algorithm_info.population_size == 30
        assert sample_algorithm_info.parameters['a'] == 2.0
        
        # Test firma única
        signature = sample_algorithm_info.get_signature()
        assert len(signature) == 12
        
        # La misma configuración debe dar la misma firma
        algo2 = AlgorithmInfo(
            name="woa",
            version="v2",
            population_size=30,
            max_iterations=100,
            parameters={"a": 2.0, "b": 1.0},
            seed=42
        )
        assert algo2.get_signature() == signature
        
        # Diferente configuración debe dar diferente firma
        algo3 = AlgorithmInfo(name="woa", population_size=50)
        assert algo3.get_signature() != signature
    
    def test_execution_info(self):
        """Test de ExecutionInfo."""
        start = datetime.now()
        end = start + timedelta(seconds=10.5)
        
        exec_info = ExecutionInfo.from_times(
            start, end,
            platform="Darwin",
            python_version="3.9.0",
            cpu_count=8,
            memory_gb=16.0
        )
        
        assert exec_info.duration_seconds == 10.5
        assert exec_info.platform == "Darwin"
        
        # Test conversión a dict
        data = exec_info.to_dict()
        assert isinstance(data['start_time'], str)
        assert isinstance(data['end_time'], str)
    
    def test_single_run_result(self, sample_single_run):
        """Test de SingleRunResult."""
        assert sample_single_run.best_fitness == 465.5
        assert len(sample_single_run.convergence_curve) == 5
        
        # Test métricas calculadas
        conv_rate = sample_single_run.get_convergence_rate()
        assert 0 <= conv_rate <= 1
        assert conv_rate == (500.0 - 465.5) / 500.0
        
        improvement = sample_single_run.get_improvement_per_iteration()
        assert improvement > 0
        assert improvement == (500.0 - 465.5) / 100
        
        # Test conversión a dict
        data = sample_single_run.to_dict()
        assert data['convergence_rate'] == conv_rate
        assert data['custom_metrics']['vehicles_used'] == 2
    
    def test_multi_run_statistics(self):
        """Test de MultiRunStatistics."""
        # Crear múltiples runs
        runs = []
        fitness_values = [465.5, 470.0, 468.0, 472.0, 466.0]
        
        for i, fitness in enumerate(fitness_values):
            run = SingleRunResult(
                run_id=i,
                seed=42 + i,
                best_fitness=fitness,
                best_solution=[],
                convergence_curve=[500.0, fitness],
                execution_time=5.0 + i * 0.5,
                iterations_completed=100,
                evaluations=3000
            )
            runs.append(run)
        
        # Calcular estadísticas
        stats = MultiRunStatistics.from_runs(runs, success_threshold=470.0)
        
        assert stats.n_runs == 5
        assert stats.best_fitness == 465.5
        assert stats.worst_fitness == 472.0
        assert stats.mean_fitness == np.mean(fitness_values)
        assert stats.median_fitness == np.median(fitness_values)
        assert stats.success_rate == 3/5  # 3 runs <= 470.0
        
        # Verificar intervalo de confianza
        assert stats.confidence_interval_95[0] < stats.mean_fitness
        assert stats.confidence_interval_95[1] > stats.mean_fitness
    
    def test_standard_result(self, sample_standard_result):
        """Test de StandardResult."""
        result = sample_standard_result
        
        assert result.result_id == "woa_P-n16-k8_20240315_120000"
        assert result.result_type == ResultType.SINGLE_RUN
        assert len(result.runs) == 1
        
        # Test resumen
        summary = result.get_summary()
        assert summary['algorithm'] == "woa"
        assert summary['problem'] == "P-n16-k8"
        assert summary['best_fitness'] == 465.5
        
        # Test gap al óptimo
        gap = result.get_gap_to_optimal()
        assert gap == (465.5 - 450.0) / 450.0 * 100
        
        # Test conversión a dict
        data = result.to_dict()
        assert 'result_id' in data
        assert 'statistics' in data
        assert 'summary' in data
    
    def test_result_serialization(self, sample_standard_result, tmp_path):
        """Test de serialización JSON."""
        # Guardar a JSON
        json_path = tmp_path / "test_result.json"
        sample_standard_result.to_json(json_path)
        
        assert json_path.exists()
        
        # Cargar desde JSON
        loaded = StandardResult.from_json(json_path)
        
        assert loaded.result_id == sample_standard_result.result_id
        assert loaded.statistics.best_fitness == sample_standard_result.statistics.best_fitness
        assert len(loaded.runs) == len(sample_standard_result.runs)
    
    def test_result_to_dataframe(self, sample_standard_result):
        """Test de conversión a DataFrame."""
        df = sample_standard_result.to_dataframe()
        
        assert len(df) == 1  # Un solo run
        assert df.iloc[0]['algorithm'] == "woa"
        assert df.iloc[0]['best_fitness'] == 465.5
        assert 'convergence_rate' in df.columns
    
    def test_export_convergence_curves(self, tmp_path):
        """Test de exportación de curvas de convergencia."""
        # Crear resultado con múltiples runs
        runs = []
        for i in range(3):
            run = SingleRunResult(
                run_id=i,
                seed=42 + i,
                best_fitness=465.0 + i,
                best_solution=[],
                convergence_curve=[500.0, 480.0, 470.0, 465.0 + i],
                execution_time=5.0,
                iterations_completed=3,
                evaluations=90
            )
            runs.append(run)
        
        result = StandardResult(
            result_id="test",
            result_type=ResultType.MULTI_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo("test", dimension=10),
            algorithm_info=AlgorithmInfo("test"),
            execution_info=ExecutionInfo(
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=15.0,
                platform="test",
                python_version="3.9",
                cpu_count=1,
                memory_gb=1.0
            ),
            runs=runs,
            statistics=MultiRunStatistics.from_runs(runs)
        )
        
        # Exportar curvas
        csv_path = tmp_path / "convergence.csv"
        result.export_convergence_curves(csv_path)
        
        # Verificar
        df = pd.read_csv(csv_path, index_col=0)
        assert len(df.columns) == 3  # 3 runs
        assert len(df) == 4  # 4 iteraciones
    
    def test_result_builder_single_run(self):
        """Test de ResultBuilder para un solo run."""
        # Simular resultado de algoritmo
        class MockResult:
            def fitness(self):
                return 465.5
            position = [[0, 1, 2, 0]]
        
        result = ResultBuilder.create_single_run(
            algorithm_name="woa",
            problem_name="P-n16-k8",
            run_result=MockResult(),
            execution_time=5.5,
            dimension=15,
            optimal_value=450.0,
            population_size=30,
            max_iterations=100,
            convergence_curve=[500.0, 480.0, 465.5],
            iterations=100,
            seed=42
        )
        
        assert result.algorithm_info.name == "woa"
        assert result.problem_info.name == "P-n16-k8"
        assert result.statistics.best_fitness == 465.5
        assert len(result.runs) == 1
    
    def test_result_builder_multi_run(self):
        """Test de ResultBuilder para múltiples runs."""
        run_results = [
            {
                'best_fitness': 465.5,
                'best_solution': [[0, 1, 2, 0]],
                'convergence_curve': [500.0, 465.5],
                'execution_time': 5.0,
                'seed': 42
            },
            {
                'best_fitness': 470.0,
                'best_solution': [[0, 3, 4, 0]],
                'convergence_curve': [500.0, 470.0],
                'execution_time': 5.5,
                'seed': 43
            }
        ]
        
        result = ResultBuilder.create_multi_run(
            algorithm_name="sma",
            problem_name="E-n22-k4",
            run_results=run_results,
            dimension=21,
            optimal_value=375.0,
            population_size=50,
            max_iterations=200,
            parallel=True,
            n_workers=2
        )
        
        assert result.algorithm_info.name == "sma"
        assert result.statistics.n_runs == 2
        assert result.statistics.best_fitness == 465.5
        assert result.execution_info.parallel == True
    
    def test_validate_result(self, sample_standard_result):
        """Test de validación de resultados."""
        # Resultado válido
        errors = validate_result(sample_standard_result)
        assert len(errors) == 0
        
        # Crear resultado inválido
        invalid_result = StandardResult(
            result_id="",  # ID vacío
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo("test", dimension=10),
            algorithm_info=AlgorithmInfo("test"),
            execution_info=ExecutionInfo(
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=1.0,
                platform="test",
                python_version="3.9",
                cpu_count=1,
                memory_gb=1.0
            ),
            runs=[],  # Sin runs
            statistics=MultiRunStatistics(
                n_runs=0,
                best_fitness=-1,  # Fitness negativo
                worst_fitness=0,
                mean_fitness=0,
                std_fitness=-1,  # Std negativo
                median_fitness=0,
                q1_fitness=0,
                q3_fitness=0,
                iqr_fitness=0,
                cv_fitness=-1,  # CV negativo
                success_rate=0,
                mean_convergence_rate=0,
                mean_execution_time=0,
                total_execution_time=0,
                confidence_interval_95=(0, 0)
            )
        )
        
        errors = validate_result(invalid_result)
        assert len(errors) > 0
        assert any("result_id" in e for e in errors)
        assert any("runs" in e for e in errors)
    
    def test_merge_results(self):
        """Test de fusión de resultados."""
        # Crear múltiples resultados compatibles
        results = []
        
        for i in range(3):
            runs = [
                SingleRunResult(
                    run_id=0,
                    seed=100 + i,
                    best_fitness=465.0 + i,
                    best_solution=[],
                    convergence_curve=[500.0, 465.0 + i],
                    execution_time=5.0,
                    iterations_completed=100,
                    evaluations=3000
                )
            ]
            
            result = StandardResult(
                result_id=f"test_{i}",
                result_type=ResultType.SINGLE_RUN,
                timestamp=datetime.now(),
                problem_info=ProblemInfo("P-n16-k8", dimension=15),
                algorithm_info=AlgorithmInfo("woa", population_size=30),
                execution_info=ExecutionInfo(
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(seconds=5),
                    duration_seconds=5.0,
                    platform="Linux",
                    python_version="3.9",
                    cpu_count=8,
                    memory_gb=16.0
                ),
                runs=runs,
                statistics=MultiRunStatistics.from_runs(runs)
            )
            results.append(result)
        
        # Fusionar
        merged = merge_results(results, "merged_test")
        
        assert merged.result_id == "merged_test"
        assert merged.result_type == ResultType.MULTI_RUN
        assert len(merged.runs) == 3
        assert merged.statistics.n_runs == 3
        assert merged.execution_info.duration_seconds == 15.0
        
        # Verificar metadatos
        assert 'merged_from' in merged.metadata
        assert len(merged.metadata['merged_from']) == 3
    
    def test_merge_incompatible_results(self):
        """Test de fusión de resultados incompatibles."""
        # Crear resultados con diferentes algoritmos
        result1 = StandardResult(
            result_id="test1",
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo("P-n16-k8", dimension=15),
            algorithm_info=AlgorithmInfo("woa"),  # WOA
            execution_info=ExecutionInfo(
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=1.0,
                platform="test",
                python_version="3.9",
                cpu_count=1,
                memory_gb=1.0
            ),
            runs=[SingleRunResult(
                run_id=0, seed=42, best_fitness=100,
                best_solution=[], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=1
            )],
            statistics=MultiRunStatistics(
                n_runs=1, best_fitness=100, worst_fitness=100,
                mean_fitness=100, std_fitness=0, median_fitness=100,
                q1_fitness=100, q3_fitness=100, iqr_fitness=0,
                cv_fitness=0, success_rate=1, mean_convergence_rate=0,
                mean_execution_time=1, total_execution_time=1,
                confidence_interval_95=(100, 100)
            )
        )
        
        result2 = StandardResult(
            result_id="test2",
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo("P-n16-k8", dimension=15),
            algorithm_info=AlgorithmInfo("sma"),  # SMA (diferente)
            execution_info=result1.execution_info,
            runs=result1.runs,
            statistics=result1.statistics
        )
        
        # Debe fallar
        with pytest.raises(ValueError, match="algoritmos deben ser iguales"):
            merge_results([result1, result2])
    
    def test_comparison_result(self):
        """Test de ComparisonResult."""
        # Crear resultados para comparar
        results = []
        algorithms = ["woa", "sma", "gto"]
        
        for algo in algorithms:
            runs = []
            for i in range(5):
                run = SingleRunResult(
                    run_id=i,
                    seed=42 + i,
                    best_fitness=460 + len(algo) + i,  # Diferente por algoritmo
                    best_solution=[],
                    convergence_curve=[500, 460 + len(algo) + i],
                    execution_time=5.0,
                    iterations_completed=100,
                    evaluations=3000
                )
                runs.append(run)
            
            result = StandardResult(
                result_id=f"{algo}_test",
                result_type=ResultType.MULTI_RUN,
                timestamp=datetime.now(),
                problem_info=ProblemInfo("P-n16-k8", dimension=15, optimal_value=450),
                algorithm_info=AlgorithmInfo(algo, population_size=30),
                execution_info=ExecutionInfo(
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    duration_seconds=25.0,
                    platform="Linux",
                    python_version="3.9",
                    cpu_count=8,
                    memory_gb=16.0
                ),
                runs=runs,
                statistics=MultiRunStatistics.from_runs(runs)
            )
            results.append(result)
        
        # Crear comparación
        comparison = ComparisonResult(
            comparison_id="comp_test",
            timestamp=datetime.now(),
            problem_info=ProblemInfo("P-n16-k8", dimension=15),
            algorithms=[r.algorithm_info for r in results],
            results=results,
            statistical_tests={
                "kruskal_wallis": {"statistic": 12.5, "p_value": 0.002},
                "friedman": {"statistic": 8.4, "p_value": 0.015}
            },
            rankings={
                "by_mean": ["woa", "gto", "sma"],
                "by_best": ["woa", "gto", "sma"]
            }
        )
        
        # Test tabla resumen
        summary_table = comparison.get_summary_table()
        assert len(summary_table) == 3
        assert set(summary_table['algorithm'].values) == {'woa', 'sma', 'gto'}
        assert 'gap_to_optimal' in summary_table.columns
        
        # Test conversión a dict
        data = comparison.to_dict()
        assert data['comparison_id'] == "comp_test"
        assert len(data['results']) == 3
        assert 'summary_table' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])