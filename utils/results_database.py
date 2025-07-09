"""
Base de datos SQLite para almacenamiento y consulta de resultados.

Este módulo proporciona una interfaz de base de datos para almacenar,
consultar y analizar resultados experimentales de manera eficiente y escalable.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Iterator
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from contextlib import contextmanager

from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics,
    ProblemInfo, AlgorithmInfo, ExecutionInfo, ResultType
)


logger = logging.getLogger(__name__)


class ResultsDatabase:
    """
    Gestor de base de datos SQLite para resultados experimentales.
    
    Características:
    - Almacenamiento eficiente de resultados completos
    - Búsquedas rápidas por múltiples criterios
    - Vistas agregadas para análisis
    - Exportación a DataFrames para análisis
    - Respaldo y recuperación
    """
    
    def __init__(self, db_path: Union[str, Path] = "results.db"):
        """
        Inicializa la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear tablas si no existen
        self._initialize_database()
        
    def _initialize_database(self) -> None:
        """Crea las tablas necesarias si no existen."""
        with self._get_connection() as conn:
            # Tabla principal de resultados
            conn.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    result_id TEXT PRIMARY KEY,
                    result_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    algorithm_name TEXT NOT NULL,
                    algorithm_version TEXT,
                    problem_name TEXT NOT NULL,
                    problem_dimension INTEGER,
                    optimal_value REAL,
                    population_size INTEGER,
                    max_iterations INTEGER,
                    n_runs INTEGER,
                    best_fitness REAL,
                    mean_fitness REAL,
                    std_fitness REAL,
                    median_fitness REAL,
                    gap_to_optimal REAL,
                    total_execution_time REAL,
                    platform TEXT,
                    full_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de runs individuales para búsquedas detalladas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id TEXT NOT NULL,
                    run_id INTEGER NOT NULL,
                    seed INTEGER,
                    best_fitness REAL,
                    execution_time REAL,
                    iterations_completed INTEGER,
                    convergence_rate REAL,
                    FOREIGN KEY (result_id) REFERENCES results(result_id)
                )
            """)
            
            # Tabla de parámetros de algoritmos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS algorithm_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    parameter_value TEXT,
                    FOREIGN KEY (result_id) REFERENCES results(result_id)
                )
            """)
            
            # Tabla de métricas personalizadas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id TEXT NOT NULL,
                    run_id INTEGER,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    FOREIGN KEY (result_id) REFERENCES results(result_id)
                )
            """)
            
            # Índices para búsquedas eficientes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_algorithm ON results(algorithm_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_problem ON results(problem_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON results(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_best_fitness ON results(best_fitness)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_result ON runs(result_id)")
            
            # Vista para análisis rápido
            conn.execute("""
                CREATE VIEW IF NOT EXISTS result_summary AS
                SELECT 
                    r.result_id,
                    r.algorithm_name,
                    r.problem_name,
                    r.n_runs,
                    r.best_fitness,
                    r.mean_fitness,
                    r.std_fitness,
                    r.gap_to_optimal,
                    r.total_execution_time,
                    r.timestamp,
                    COUNT(DISTINCT ap.parameter_name) as n_parameters
                FROM results r
                LEFT JOIN algorithm_parameters ap ON r.result_id = ap.result_id
                GROUP BY r.result_id
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager para conexiones a la base de datos."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_result(self, result: StandardResult) -> bool:
        """
        Inserta un resultado completo en la base de datos.
        
        Args:
            result: Resultado estándar a insertar
            
        Returns:
            True si se insertó correctamente, False en caso contrario
        """
        try:
            with self._get_connection() as conn:
                # Calcular gap si es posible
                gap = result.get_gap_to_optimal()
                
                # Insertar resultado principal
                conn.execute("""
                    INSERT INTO results (
                        result_id, result_type, timestamp,
                        algorithm_name, algorithm_version, problem_name,
                        problem_dimension, optimal_value, population_size,
                        max_iterations, n_runs, best_fitness, mean_fitness,
                        std_fitness, median_fitness, gap_to_optimal,
                        total_execution_time, platform, full_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.result_id,
                    result.result_type.value,
                    result.timestamp,
                    result.algorithm_info.name,
                    result.algorithm_info.version,
                    result.problem_info.name,
                    result.problem_info.dimension,
                    result.problem_info.optimal_value,
                    result.algorithm_info.population_size,
                    result.algorithm_info.max_iterations,
                    result.statistics.n_runs,
                    result.statistics.best_fitness,
                    result.statistics.mean_fitness,
                    result.statistics.std_fitness,
                    result.statistics.median_fitness,
                    gap,
                    result.statistics.total_execution_time,
                    result.execution_info.platform,
                    result.to_json()
                ))
                
                # Insertar runs individuales
                for run in result.runs:
                    conn.execute("""
                        INSERT INTO runs (
                            result_id, run_id, seed, best_fitness,
                            execution_time, iterations_completed, convergence_rate
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.result_id,
                        run.run_id,
                        run.seed,
                        run.best_fitness,
                        run.execution_time,
                        run.iterations_completed,
                        run.get_convergence_rate()
                    ))
                    
                    # Insertar métricas personalizadas del run
                    for metric_name, metric_value in run.custom_metrics.items():
                        if isinstance(metric_value, (int, float)):
                            conn.execute("""
                                INSERT INTO custom_metrics (
                                    result_id, run_id, metric_name, metric_value
                                ) VALUES (?, ?, ?, ?)
                            """, (result.result_id, run.run_id, metric_name, metric_value))
                
                # Insertar parámetros del algoritmo
                for param_name, param_value in result.algorithm_info.parameters.items():
                    conn.execute("""
                        INSERT INTO algorithm_parameters (
                            result_id, parameter_name, parameter_value
                        ) VALUES (?, ?, ?)
                    """, (result.result_id, param_name, json.dumps(param_value)))
                
                conn.commit()
                logger.info(f"Resultado {result.result_id} insertado en base de datos")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"Resultado {result.result_id} ya existe en base de datos")
            return False
        except Exception as e:
            logger.error(f"Error insertando resultado: {e}")
            return False
    
    def get_result(self, result_id: str) -> Optional[StandardResult]:
        """
        Obtiene un resultado completo por su ID.
        
        Args:
            result_id: ID del resultado
            
        Returns:
            StandardResult o None si no se encuentra
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT full_data FROM results WHERE result_id = ?",
                (result_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row['full_data'])
                return StandardResult.from_dict(data)
            
            return None
    
    def search_results(
        self,
        algorithm: Optional[str] = None,
        problem: Optional[str] = None,
        min_fitness: Optional[float] = None,
        max_fitness: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca resultados según criterios.
        
        Args:
            algorithm: Filtrar por nombre de algoritmo
            problem: Filtrar por instancia del problema
            min_fitness: Fitness mínimo
            max_fitness: Fitness máximo
            start_date: Fecha inicial
            end_date: Fecha final
            limit: Límite de resultados
            
        Returns:
            Lista de resultados resumidos
        """
        query = "SELECT * FROM result_summary WHERE 1=1"
        params = []
        
        if algorithm:
            query += " AND algorithm_name = ?"
            params.append(algorithm)
        
        if problem:
            query += " AND problem_name = ?"
            params.append(problem)
        
        if min_fitness is not None:
            query += " AND best_fitness >= ?"
            params.append(min_fitness)
        
        if max_fitness is not None:
            query += " AND best_fitness <= ?"
            params.append(max_fitness)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY best_fitness ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            results = []
            for row in cursor:
                results.append(dict(row))
            
            return results
    
    def get_best_results_by_problem(self) -> pd.DataFrame:
        """
        Obtiene los mejores resultados para cada problema.
        
        Returns:
            DataFrame con mejores resultados por problema
        """
        query = """
            SELECT 
                problem_name,
                algorithm_name,
                MIN(best_fitness) as best_fitness,
                AVG(mean_fitness) as avg_mean_fitness,
                MIN(gap_to_optimal) as best_gap,
                COUNT(*) as n_experiments
            FROM results
            GROUP BY problem_name, algorithm_name
            ORDER BY problem_name, best_fitness
        """
        
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn)
    
    def get_algorithm_performance(self, algorithm: str) -> pd.DataFrame:
        """
        Obtiene estadísticas de rendimiento de un algoritmo.
        
        Args:
            algorithm: Nombre del algoritmo
            
        Returns:
            DataFrame con estadísticas por problema
        """
        query = """
            SELECT 
                problem_name,
                COUNT(*) as n_experiments,
                MIN(best_fitness) as best_fitness,
                AVG(mean_fitness) as avg_mean_fitness,
                AVG(std_fitness) as avg_std_fitness,
                MIN(gap_to_optimal) as best_gap,
                AVG(total_execution_time) as avg_time
            FROM results
            WHERE algorithm_name = ?
            GROUP BY problem_name
            ORDER BY problem_name
        """
        
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=[algorithm])
    
    def get_parameter_analysis(
        self,
        algorithm: str,
        parameter: str,
        problem: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Analiza el efecto de un parámetro en el rendimiento.
        
        Args:
            algorithm: Nombre del algoritmo
            parameter: Nombre del parámetro
            problem: Filtrar por problema (opcional)
            
        Returns:
            DataFrame con análisis del parámetro
        """
        query = """
            SELECT 
                ap.parameter_value,
                r.problem_name,
                COUNT(*) as n_experiments,
                MIN(r.best_fitness) as best_fitness,
                AVG(r.mean_fitness) as avg_fitness,
                AVG(r.std_fitness) as avg_std
            FROM results r
            JOIN algorithm_parameters ap ON r.result_id = ap.result_id
            WHERE r.algorithm_name = ? AND ap.parameter_name = ?
        """
        
        params = [algorithm, parameter]
        
        if problem:
            query += " AND r.problem_name = ?"
            params.append(problem)
        
        query += " GROUP BY ap.parameter_value, r.problem_name"
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            
            # Intentar convertir valores de parámetros
            try:
                df['parameter_value'] = df['parameter_value'].apply(json.loads)
            except:
                pass
            
            return df
    
    def get_convergence_data(self, result_ids: List[str]) -> Dict[str, List[float]]:
        """
        Obtiene curvas de convergencia para múltiples resultados.
        
        Args:
            result_ids: Lista de IDs de resultados
            
        Returns:
            Diccionario con curvas de convergencia
        """
        convergence_data = {}
        
        for result_id in result_ids:
            result = self.get_result(result_id)
            if result:
                # Promedio de curvas si hay múltiples runs
                curves = [run.convergence_curve for run in result.runs]
                if curves:
                    # Alinear longitudes
                    max_len = max(len(c) for c in curves)
                    aligned_curves = []
                    for curve in curves:
                        aligned = curve + [curve[-1]] * (max_len - len(curve))
                        aligned_curves.append(aligned)
                    
                    # Calcular promedio
                    avg_curve = np.mean(aligned_curves, axis=0).tolist()
                    convergence_data[result_id] = avg_curve
        
        return convergence_data
    
    def export_to_csv(self, output_dir: Union[str, Path], prefix: str = "results") -> None:
        """
        Exporta la base de datos a archivos CSV.
        
        Args:
            output_dir: Directorio de salida
            prefix: Prefijo para los archivos
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            # Exportar tabla principal
            results_df = pd.read_sql_query("SELECT * FROM results", conn)
            results_df.to_csv(output_dir / f"{prefix}_main.csv", index=False)
            
            # Exportar runs
            runs_df = pd.read_sql_query("SELECT * FROM runs", conn)
            runs_df.to_csv(output_dir / f"{prefix}_runs.csv", index=False)
            
            # Exportar parámetros
            params_df = pd.read_sql_query("SELECT * FROM algorithm_parameters", conn)
            params_df.to_csv(output_dir / f"{prefix}_parameters.csv", index=False)
            
            # Exportar métricas
            metrics_df = pd.read_sql_query("SELECT * FROM custom_metrics", conn)
            metrics_df.to_csv(output_dir / f"{prefix}_metrics.csv", index=False)
            
        logger.info(f"Base de datos exportada a {output_dir}")
    
    def backup(self, backup_path: Union[str, Path]) -> None:
        """
        Crea un respaldo de la base de datos.
        
        Args:
            backup_path: Ruta del archivo de respaldo
        """
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            # Crear conexión al respaldo
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Copiar base de datos
            conn.backup(backup_conn)
            backup_conn.close()
            
        logger.info(f"Respaldo creado en {backup_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        with self._get_connection() as conn:
            stats = {}
            
            # Total de resultados
            cursor = conn.execute("SELECT COUNT(*) as total FROM results")
            stats['total_results'] = cursor.fetchone()['total']
            
            # Total de runs
            cursor = conn.execute("SELECT COUNT(*) as total FROM runs")
            stats['total_runs'] = cursor.fetchone()['total']
            
            # Algoritmos únicos
            cursor = conn.execute("SELECT COUNT(DISTINCT algorithm_name) as total FROM results")
            stats['unique_algorithms'] = cursor.fetchone()['total']
            
            # Problemas únicos
            cursor = conn.execute("SELECT COUNT(DISTINCT problem_name) as total FROM results")
            stats['unique_problems'] = cursor.fetchone()['total']
            
            # Mejor resultado global
            cursor = conn.execute("""
                SELECT algorithm_name, problem_name, best_fitness
                FROM results
                ORDER BY best_fitness ASC
                LIMIT 1
            """)
            best = cursor.fetchone()
            if best:
                stats['best_result'] = dict(best)
            
            # Rango de fechas
            cursor = conn.execute("""
                SELECT 
                    MIN(timestamp) as first_experiment,
                    MAX(timestamp) as last_experiment
                FROM results
            """)
            dates = cursor.fetchone()
            if dates:
                stats['date_range'] = {
                    'first': dates['first_experiment'],
                    'last': dates['last_experiment']
                }
            
            return stats
    
    def cleanup_old_results(self, days: int = 30) -> int:
        """
        Elimina resultados antiguos.
        
        Args:
            days: Días de antigüedad para eliminar
            
        Returns:
            Número de resultados eliminados
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        with self._get_connection() as conn:
            # Obtener IDs a eliminar
            cursor = conn.execute(
                "SELECT result_id FROM results WHERE timestamp < ?",
                (datetime.fromtimestamp(cutoff_date),)
            )
            result_ids = [row['result_id'] for row in cursor]
            
            if result_ids:
                # Eliminar en cascada
                placeholders = ','.join('?' * len(result_ids))
                
                conn.execute(f"DELETE FROM custom_metrics WHERE result_id IN ({placeholders})", result_ids)
                conn.execute(f"DELETE FROM algorithm_parameters WHERE result_id IN ({placeholders})", result_ids)
                conn.execute(f"DELETE FROM runs WHERE result_id IN ({placeholders})", result_ids)
                conn.execute(f"DELETE FROM results WHERE result_id IN ({placeholders})", result_ids)
                
                conn.commit()
            
            return len(result_ids)


class DatabaseQuery:
    """Constructor de consultas complejas para la base de datos."""
    
    def __init__(self, database: ResultsDatabase):
        """
        Inicializa el constructor de consultas.
        
        Args:
            database: Instancia de ResultsDatabase
        """
        self.db = database
    
    def compare_algorithms(
        self,
        algorithms: List[str],
        problems: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Compara múltiples algoritmos.
        
        Args:
            algorithms: Lista de algoritmos a comparar
            problems: Lista de problemas (opcional)
            
        Returns:
            DataFrame con comparación
        """
        query = """
            SELECT 
                algorithm_name,
                problem_name,
                MIN(best_fitness) as best_fitness,
                AVG(mean_fitness) as avg_fitness,
                AVG(std_fitness) as avg_std,
                COUNT(*) as n_experiments,
                AVG(total_execution_time) as avg_time
            FROM results
            WHERE algorithm_name IN ({})
        """.format(','.join('?' * len(algorithms)))
        
        params = algorithms
        
        if problems:
            query += " AND problem_name IN ({})".format(','.join('?' * len(problems)))
            params.extend(problems)
        
        query += " GROUP BY algorithm_name, problem_name ORDER BY problem_name, best_fitness"
        
        with self.db._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def find_optimal_parameters(
        self,
        algorithm: str,
        problem: str,
        metric: str = "best_fitness"
    ) -> Dict[str, Any]:
        """
        Encuentra los parámetros óptimos para un algoritmo y problema.
        
        Args:
            algorithm: Nombre del algoritmo
            problem: Nombre del problema
            metric: Métrica a optimizar
            
        Returns:
            Diccionario con parámetros óptimos
        """
        query = f"""
            SELECT 
                r.result_id,
                r.{metric} as metric_value,
                r.population_size,
                r.max_iterations
            FROM results r
            WHERE r.algorithm_name = ? AND r.problem_name = ?
            ORDER BY r.{metric} ASC
            LIMIT 1
        """
        
        with self.db._get_connection() as conn:
            cursor = conn.execute(query, [algorithm, problem])
            best = cursor.fetchone()
            
            if best:
                # Obtener parámetros específicos
                params_cursor = conn.execute(
                    "SELECT parameter_name, parameter_value FROM algorithm_parameters WHERE result_id = ?",
                    [best['result_id']]
                )
                
                params = {
                    'population_size': best['population_size'],
                    'max_iterations': best['max_iterations']
                }
                
                for row in params_cursor:
                    try:
                        params[row['parameter_name']] = json.loads(row['parameter_value'])
                    except:
                        params[row['parameter_name']] = row['parameter_value']
                
                return {
                    'result_id': best['result_id'],
                    'metric_value': best['metric_value'],
                    'parameters': params
                }
            
            return {}
    
    def get_improvement_timeline(
        self,
        algorithm: str,
        problem: str
    ) -> pd.DataFrame:
        """
        Obtiene la evolución temporal de mejoras.
        
        Args:
            algorithm: Nombre del algoritmo
            problem: Nombre del problema
            
        Returns:
            DataFrame con timeline de mejoras
        """
        query = """
            SELECT 
                timestamp,
                best_fitness,
                mean_fitness,
                gap_to_optimal,
                total_execution_time
            FROM results
            WHERE algorithm_name = ? AND problem_name = ?
            ORDER BY timestamp
        """
        
        with self.db._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[algorithm, problem])
            
            if not df.empty:
                # Calcular mejor acumulativo
                df['best_so_far'] = df['best_fitness'].cummin()
                
                # Calcular mejora respecto al anterior
                df['improvement'] = -df['best_fitness'].diff()
                df['improvement'] = df['improvement'].fillna(0)
            
            return df