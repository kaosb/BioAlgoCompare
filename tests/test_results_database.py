"""
Tests para la base de datos SQLite de resultados.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from utils.results_database import ResultsDatabase, DatabaseQuery
from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics,
    ProblemInfo, AlgorithmInfo, ExecutionInfo, ResultType
)


class TestResultsDatabase:
    """Tests para ResultsDatabase."""
    
    @pytest.fixture
    def temp_db(self):
        """Crea una base de datos temporal."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_results.db"
        db = ResultsDatabase(db_path)
        yield db
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_result(self):
        """Crea un resultado de ejemplo."""
        problem_info = ProblemInfo(
            name="P-n16-k8",
            dimension=15,
            optimal_value=450.0
        )
        
        algorithm_info = AlgorithmInfo(
            name="woa",
            version="v2",
            population_size=30,
            max_iterations=100,
            parameters={"a": 2.0, "b": 1.0},
            seed=42
        )
        
        execution_info = ExecutionInfo(
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=10),
            duration_seconds=10.0,
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
                convergence_curve=[500.0, 480.0, 465.0 + i],
                execution_time=3.0 + i * 0.1,
                iterations_completed=100,
                evaluations=3000,
                custom_metrics={'vehicles_used': 3, 'diversity': 0.85}
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
    
    def test_database_initialization(self, temp_db):
        """Test de inicialización de la base de datos."""
        # Verificar que se crearon las tablas
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row['name'] for row in cursor]
            
            assert 'results' in tables
            assert 'runs' in tables
            assert 'algorithm_parameters' in tables
            assert 'custom_metrics' in tables
            
            # Verificar vista
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"
            )
            views = [row['name'] for row in cursor]
            assert 'result_summary' in views
    
    def test_insert_result(self, temp_db, sample_result):
        """Test de inserción de resultado."""
        # Insertar resultado
        success = temp_db.insert_result(sample_result)
        assert success is True
        
        # Verificar que no se puede insertar duplicado
        success2 = temp_db.insert_result(sample_result)
        assert success2 is False
        
        # Verificar datos insertados
        with temp_db._get_connection() as conn:
            # Verificar resultado principal
            cursor = conn.execute(
                "SELECT * FROM results WHERE result_id = ?",
                (sample_result.result_id,)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row['algorithm_name'] == 'woa'
            assert row['best_fitness'] == 465.0
            assert row['n_runs'] == 3
            
            # Verificar runs
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM runs WHERE result_id = ?",
                (sample_result.result_id,)
            )
            assert cursor.fetchone()['count'] == 3
            
            # Verificar parámetros
            cursor = conn.execute(
                "SELECT * FROM algorithm_parameters WHERE result_id = ?",
                (sample_result.result_id,)
            )
            params = list(cursor)
            assert len(params) == 2  # a y b
            
            # Verificar métricas custom
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM custom_metrics WHERE result_id = ?",
                (sample_result.result_id,)
            )
            assert cursor.fetchone()['count'] == 6  # 2 métricas x 3 runs
    
    def test_get_result(self, temp_db, sample_result):
        """Test de obtención de resultado."""
        # Insertar resultado
        temp_db.insert_result(sample_result)
        
        # Obtener resultado
        retrieved = temp_db.get_result(sample_result.result_id)
        
        assert retrieved is not None
        assert retrieved.result_id == sample_result.result_id
        assert retrieved.algorithm_info.name == 'woa'
        assert len(retrieved.runs) == 3
        assert retrieved.statistics.best_fitness == 465.0
        
        # Intentar obtener resultado inexistente
        none_result = temp_db.get_result("inexistente")
        assert none_result is None
    
    def test_search_results(self, temp_db):
        """Test de búsqueda de resultados."""
        # Insertar múltiples resultados
        algorithms = ['woa', 'sma', 'gto']
        problems = ['P-n16-k8', 'E-n22-k4']
        
        for algo in algorithms:
            for prob in problems:
                result = StandardResult(
                    result_id=f"{algo}_{prob}_test",
                    result_type=ResultType.SINGLE_RUN,
                    timestamp=datetime.now(),
                    problem_info=ProblemInfo(prob, dimension=20),
                    algorithm_info=AlgorithmInfo(algo),
                    execution_info=ExecutionInfo(
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration_seconds=5.0,
                        platform="Linux",
                        python_version="3.9",
                        cpu_count=4,
                        memory_gb=8.0
                    ),
                    runs=[SingleRunResult(
                        run_id=0,
                        seed=42,
                        best_fitness=100.0 + len(algo) + len(prob),
                        best_solution=[],
                        convergence_curve=[200.0, 100.0],
                        execution_time=5.0,
                        iterations_completed=100,
                        evaluations=3000
                    )],
                    statistics=MultiRunStatistics(
                        n_runs=1,
                        best_fitness=100.0 + len(algo) + len(prob),
                        worst_fitness=100.0 + len(algo) + len(prob),
                        mean_fitness=100.0 + len(algo) + len(prob),
                        std_fitness=0.0,
                        median_fitness=100.0 + len(algo) + len(prob),
                        q1_fitness=100.0,
                        q3_fitness=100.0,
                        iqr_fitness=0.0,
                        cv_fitness=0.0,
                        success_rate=1.0,
                        mean_convergence_rate=0.5,
                        mean_execution_time=5.0,
                        total_execution_time=5.0,
                        confidence_interval_95=(100.0, 100.0)
                    )
                )
                temp_db.insert_result(result)
        
        # Buscar por algoritmo
        woa_results = temp_db.search_results(algorithm='woa')
        assert len(woa_results) == 2
        
        # Buscar por problema
        pn16_results = temp_db.search_results(problem='P-n16-k8')
        assert len(pn16_results) == 3
        
        # Buscar con múltiples criterios
        specific = temp_db.search_results(algorithm='sma', problem='E-n22-k4')
        assert len(specific) == 1
        
        # Buscar con límite
        limited = temp_db.search_results(limit=2)
        assert len(limited) == 2
    
    def test_get_best_results_by_problem(self, temp_db):
        """Test de obtención de mejores resultados por problema."""
        # Insertar resultados variados
        for i, algo in enumerate(['woa', 'sma', 'gto']):
            for j in range(2):  # 2 experimentos por algoritmo
                result = StandardResult(
                    result_id=f"{algo}_P-n16-k8_exp{j}",
                    result_type=ResultType.SINGLE_RUN,
                    timestamp=datetime.now(),
                    problem_info=ProblemInfo("P-n16-k8", optimal_value=450.0),
                    algorithm_info=AlgorithmInfo(algo),
                    execution_info=ExecutionInfo(
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration_seconds=5.0,
                        platform="Linux",
                        python_version="3.9",
                        cpu_count=4,
                        memory_gb=8.0
                    ),
                    runs=[SingleRunResult(
                        run_id=0,
                        seed=42,
                        best_fitness=460.0 + i * 5 + j,  # Variación por algoritmo
                        best_solution=[],
                        convergence_curve=[500.0, 460.0],
                        execution_time=5.0,
                        iterations_completed=100,
                        evaluations=3000
                    )],
                    statistics=MultiRunStatistics.from_runs([SingleRunResult(
                        run_id=0,
                        seed=42,
                        best_fitness=460.0 + i * 5 + j,
                        best_solution=[],
                        convergence_curve=[],
                        execution_time=5.0,
                        iterations_completed=100,
                        evaluations=3000
                    )])
                )
                temp_db.insert_result(result)
        
        # Obtener mejores resultados
        df = temp_db.get_best_results_by_problem()
        
        assert not df.empty
        assert len(df) == 3  # 3 algoritmos
        
        # Verificar que woa tiene el mejor resultado
        woa_row = df[df['algorithm_name'] == 'woa'].iloc[0]
        assert woa_row['best_fitness'] == 460.0
        assert woa_row['n_experiments'] == 2
    
    def test_get_algorithm_performance(self, temp_db):
        """Test de análisis de rendimiento de algoritmo."""
        # Insertar resultados para un algoritmo en múltiples problemas
        problems = ['P-n16-k8', 'E-n22-k4', 'A-n32-k5']
        
        for prob in problems:
            for i in range(3):  # 3 experimentos por problema
                result = StandardResult(
                    result_id=f"woa_{prob}_exp{i}",
                    result_type=ResultType.SINGLE_RUN,
                    timestamp=datetime.now(),
                    problem_info=ProblemInfo(prob, optimal_value=100.0),
                    algorithm_info=AlgorithmInfo("woa"),
                    execution_info=ExecutionInfo(
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration_seconds=5.0 + i,
                        platform="Linux",
                        python_version="3.9",
                        cpu_count=4,
                        memory_gb=8.0
                    ),
                    runs=[SingleRunResult(
                        run_id=0,
                        seed=42,
                        best_fitness=105.0 + i,
                        best_solution=[],
                        convergence_curve=[],
                        execution_time=5.0 + i,
                        iterations_completed=100,
                        evaluations=3000
                    )],
                    statistics=MultiRunStatistics.from_runs([SingleRunResult(
                        run_id=0,
                        seed=42,
                        best_fitness=105.0 + i,
                        best_solution=[],
                        convergence_curve=[],
                        execution_time=5.0 + i,
                        iterations_completed=100,
                        evaluations=3000
                    )])
                )
                temp_db.insert_result(result)
        
        # Obtener rendimiento
        df = temp_db.get_algorithm_performance("woa")
        
        assert len(df) == 3  # 3 problemas
        assert df['n_experiments'].sum() == 9  # 3 exp x 3 problemas
        
        # Verificar cálculos
        pn16_row = df[df['problem_name'] == 'P-n16-k8'].iloc[0]
        assert pn16_row['best_fitness'] == 105.0
        assert pn16_row['best_gap'] == 5.0  # (105-100)/100 * 100
    
    def test_backup_restore(self, temp_db, sample_result):
        """Test de respaldo y restauración."""
        # Insertar datos
        temp_db.insert_result(sample_result)
        
        # Crear respaldo
        backup_path = Path(temp_db.db_path).parent / "backup.db"
        temp_db.backup(backup_path)
        
        assert backup_path.exists()
        
        # Crear nueva DB desde respaldo
        restored_db = ResultsDatabase(backup_path)
        
        # Verificar que los datos están
        result = restored_db.get_result(sample_result.result_id)
        assert result is not None
        assert result.algorithm_info.name == 'woa'
        
        # Limpiar
        backup_path.unlink()
    
    def test_export_to_csv(self, temp_db, sample_result):
        """Test de exportación a CSV."""
        # Insertar datos
        temp_db.insert_result(sample_result)
        
        # Exportar
        export_dir = Path(temp_db.db_path).parent / "export"
        temp_db.export_to_csv(export_dir)
        
        # Verificar archivos
        assert (export_dir / "results_main.csv").exists()
        assert (export_dir / "results_runs.csv").exists()
        assert (export_dir / "results_parameters.csv").exists()
        assert (export_dir / "results_metrics.csv").exists()
        
        # Verificar contenido
        main_df = pd.read_csv(export_dir / "results_main.csv")
        assert len(main_df) == 1
        assert main_df.iloc[0]['algorithm_name'] == 'woa'
        
        # Limpiar
        shutil.rmtree(export_dir)
    
    def test_statistics(self, temp_db, sample_result):
        """Test de estadísticas de la base de datos."""
        # Base de datos vacía
        stats = temp_db.get_statistics()
        assert stats['total_results'] == 0
        assert stats['total_runs'] == 0
        
        # Insertar datos
        temp_db.insert_result(sample_result)
        
        # Estadísticas con datos
        stats = temp_db.get_statistics()
        assert stats['total_results'] == 1
        assert stats['total_runs'] == 3
        assert stats['unique_algorithms'] == 1
        assert stats['unique_problems'] == 1
        assert 'best_result' in stats
        assert stats['best_result']['best_fitness'] == 465.0
    
    def test_cleanup_old_results(self, temp_db):
        """Test de limpieza de resultados antiguos."""
        # Insertar resultado antiguo
        old_result = StandardResult(
            result_id="old_result",
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now() - timedelta(days=40),
            problem_info=ProblemInfo("test"),
            algorithm_info=AlgorithmInfo("test"),
            execution_info=ExecutionInfo(
                start_time=datetime.now() - timedelta(days=40),
                end_time=datetime.now() - timedelta(days=40),
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
            statistics=MultiRunStatistics.from_runs([SingleRunResult(
                run_id=0, seed=42, best_fitness=100,
                best_solution=[], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=1
            )])
        )
        
        # Forzar timestamp antiguo
        with temp_db._get_connection() as conn:
            temp_db.insert_result(old_result)
            old_timestamp = (datetime.now() - timedelta(days=40)).isoformat()
            conn.execute(
                "UPDATE results SET timestamp = ? WHERE result_id = ?",
                (old_timestamp, old_result.result_id)
            )
            conn.commit()
        
        # Insertar resultado reciente
        recent_result = StandardResult(
            result_id="recent_result",
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo("test"),
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
            runs=[SingleRunResult(
                run_id=0, seed=42, best_fitness=100,
                best_solution=[], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=1
            )],
            statistics=MultiRunStatistics.from_runs([SingleRunResult(
                run_id=0, seed=42, best_fitness=100,
                best_solution=[], convergence_curve=[100],
                execution_time=1, iterations_completed=1, evaluations=1
            )])
        )
        temp_db.insert_result(recent_result)
        
        # Limpiar resultados de más de 30 días
        deleted = temp_db.cleanup_old_results(days=30)
        assert deleted == 1
        
        # Verificar que solo queda el reciente
        assert temp_db.get_result("old_result") is None
        assert temp_db.get_result("recent_result") is not None


class TestDatabaseQuery:
    """Tests para DatabaseQuery."""
    
    @pytest.fixture
    def query_db(self):
        """Crea base de datos con datos de prueba."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_query.db"
        db = ResultsDatabase(db_path)
        
        # Insertar datos de prueba
        algorithms = ['woa', 'sma', 'gto']
        problems = ['P-n16-k8', 'E-n22-k4']
        
        for algo in algorithms:
            for prob in problems:
                for exp in range(2):
                    result = StandardResult(
                        result_id=f"{algo}_{prob}_exp{exp}",
                        result_type=ResultType.SINGLE_RUN,
                        timestamp=datetime.now() - timedelta(days=exp),
                        problem_info=ProblemInfo(prob, optimal_value=100.0),
                        algorithm_info=AlgorithmInfo(
                            algo,
                            population_size=30 + exp * 10,
                            parameters={'param1': exp}
                        ),
                        execution_info=ExecutionInfo(
                            start_time=datetime.now(),
                            end_time=datetime.now(),
                            duration_seconds=5.0,
                            platform="Linux",
                            python_version="3.9",
                            cpu_count=4,
                            memory_gb=8.0
                        ),
                        runs=[SingleRunResult(
                            run_id=0,
                            seed=42,
                            best_fitness=105.0 + len(algo) + exp,
                            best_solution=[],
                            convergence_curve=[150.0, 105.0],
                            execution_time=5.0,
                            iterations_completed=100,
                            evaluations=3000
                        )],
                        statistics=MultiRunStatistics.from_runs([SingleRunResult(
                            run_id=0,
                            seed=42,
                            best_fitness=105.0 + len(algo) + exp,
                            best_solution=[],
                            convergence_curve=[],
                            execution_time=5.0,
                            iterations_completed=100,
                            evaluations=3000
                        )])
                    )
                    db.insert_result(result)
        
        query = DatabaseQuery(db)
        yield query
        shutil.rmtree(temp_dir)
    
    def test_compare_algorithms(self, query_db):
        """Test de comparación de algoritmos."""
        df = query_db.compare_algorithms(['woa', 'sma'])
        
        assert len(df) == 4  # 2 algoritmos x 2 problemas
        
        # Verificar agrupación
        woa_pn16 = df[(df['algorithm_name'] == 'woa') & 
                      (df['problem_name'] == 'P-n16-k8')].iloc[0]
        assert woa_pn16['n_experiments'] == 2
        assert woa_pn16['best_fitness'] == 108.0  # 105 + len('woa') + 0
    
    def test_find_optimal_parameters(self, query_db):
        """Test de búsqueda de parámetros óptimos."""
        result = query_db.find_optimal_parameters('woa', 'P-n16-k8')
        
        assert result is not None
        assert 'parameters' in result
        assert result['parameters']['population_size'] == 30  # exp0 tiene mejor fitness
        assert result['parameters']['param1'] == 0
    
    def test_get_improvement_timeline(self, query_db):
        """Test de timeline de mejoras."""
        df = query_db.get_improvement_timeline('woa', 'P-n16-k8')
        
        assert len(df) == 2  # 2 experimentos
        assert 'best_so_far' in df.columns
        assert 'improvement' in df.columns
        
        # El mejor acumulativo debe decrecer o mantenerse
        assert df['best_so_far'].is_monotonic_decreasing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])