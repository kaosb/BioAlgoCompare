"""
Integración del sistema unificado de resultados con algoritmos base.

Este módulo proporciona adaptadores y utilidades para integrar
el pipeline de resultados con la arquitectura de algoritmos.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

from algorithms.core.base import MetaheuristicAlgorithm
from ..result_schema_v2 import (
    StandardResultV2, ExecutionInfoV2, SystemInfo, GitInfo
)
from ..result_schema import (
    ResultType, ProblemInfo, AlgorithmInfo, 
    SingleRunResult, MultiRunStatistics
)
from .pipeline import ResultPipeline, get_default_pipeline


class AlgorithmResultAdapter:
    """
    Adaptador para convertir resultados de algoritmos a StandardResultV2.
    """
    
    @staticmethod
    def create_result_from_algorithm(
        algorithm: MetaheuristicAlgorithm,
        execution_time: float,
        convergence_curve: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> StandardResultV2:
        """
        Crea un StandardResultV2 desde un algoritmo ejecutado.
        
        Args:
            algorithm: Algoritmo ejecutado
            execution_time: Tiempo de ejecución en segundos
            convergence_curve: Curva de convergencia
            metadata: Metadatos adicionales
            
        Returns:
            StandardResultV2 con toda la información
        """
        # Información del problema
        problem_info = ProblemInfo(
            name=algorithm.problem.name,
            dimension=algorithm.problem.dimension,
            instance_path=getattr(algorithm.problem, 'instance_path', None),
            optimal_value=getattr(algorithm.problem, 'optimal_value', None),
            metadata=getattr(algorithm.problem, 'metadata', {})
        )
        
        # Información del algoritmo
        algorithm_params = {
            'population_size': algorithm.population_size,
            'max_iterations': algorithm.max_iterations,
            'seed': algorithm.seed
        }
        
        # Añadir parámetros específicos del algoritmo
        for attr in dir(algorithm):
            if not attr.startswith('_') and attr not in ['population_size', 'max_iterations', 'seed']:
                value = getattr(algorithm, attr, None)
                if isinstance(value, (int, float, str, bool)):
                    algorithm_params[attr] = value
        
        algorithm_info = AlgorithmInfo(
            name=algorithm.__class__.__name__.replace('V2', ''),
            version=getattr(algorithm, 'version', '2.0'),
            parameters=algorithm_params,
            metadata={}
        )
        
        # Crear run único
        best_individual = algorithm.best_individual
        single_run = SingleRunResult(
            run_id=0,
            seed=algorithm.seed,
            best_fitness=best_individual.fitness() if best_individual else float('inf'),
            best_solution=best_individual.position.tolist() if best_individual else [],
            convergence_curve=convergence_curve,
            execution_time=execution_time,
            iterations_completed=len(convergence_curve),
            metadata={}
        )
        
        # Estadísticas (para un solo run)
        statistics = MultiRunStatistics(
            n_runs=1,
            best_fitness=single_run.best_fitness,
            worst_fitness=single_run.best_fitness,
            mean_fitness=single_run.best_fitness,
            std_fitness=0.0,
            median_fitness=single_run.best_fitness,
            confidence_interval_95=(single_run.best_fitness, single_run.best_fitness),
            total_execution_time=execution_time,
            mean_execution_time=execution_time,
            convergence_analysis={
                'final_improvement': convergence_curve[0] - convergence_curve[-1] if convergence_curve else 0,
                'iterations_to_converge': len(convergence_curve),
                'convergence_rate': 0.0  # TODO: Calcular tasa de convergencia
            },
            metadata={}
        )
        
        # Información de ejecución
        execution_info = ExecutionInfoV2(
            start_time=datetime.now(),  # TODO: Capturar tiempo real
            end_time=datetime.now(),
            duration_seconds=execution_time,
            cpu_percent_avg=0.0,  # TODO: Implementar monitoreo
            memory_peak_mb=0.0,
            memory_avg_mb=0.0,
            random_seed=algorithm.seed,
            parallel=False,
            n_workers=None,
            thread_count=None,
            working_directory='',
            environment_variables={}
        )
        
        # Crear resultado completo
        result = StandardResultV2(
            result_type=ResultType.SINGLE_RUN,
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=[single_run],
            statistics=statistics,
            execution_info=execution_info,
            metadata=metadata or {}
        )
        
        return result
    
    @staticmethod
    def create_multi_run_result(
        algorithm_class: type,
        problem: Any,
        runs_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> StandardResultV2:
        """
        Crea un StandardResultV2 para múltiples ejecuciones.
        
        Args:
            algorithm_class: Clase del algoritmo
            problem: Problema utilizado
            runs_data: Lista de datos de cada run
            metadata: Metadatos adicionales
            
        Returns:
            StandardResultV2 con estadísticas agregadas
        """
        # Información del problema
        problem_info = ProblemInfo(
            name=problem.name,
            dimension=problem.dimension,
            instance_path=getattr(problem, 'instance_path', None),
            optimal_value=getattr(problem, 'optimal_value', None),
            metadata=getattr(problem, 'metadata', {})
        )
        
        # Información del algoritmo (desde primer run)
        first_run = runs_data[0]
        algorithm_info = AlgorithmInfo(
            name=algorithm_class.__name__.replace('V2', ''),
            version='2.0',
            parameters=first_run.get('parameters', {}),
            metadata={}
        )
        
        # Crear runs individuales
        single_runs = []
        for i, run_data in enumerate(runs_data):
            single_runs.append(SingleRunResult(
                run_id=i,
                seed=run_data['seed'],
                best_fitness=run_data['best_fitness'],
                best_solution=run_data.get('best_solution', []),
                convergence_curve=run_data['convergence_curve'],
                execution_time=run_data['execution_time'],
                iterations_completed=len(run_data['convergence_curve']),
                metadata=run_data.get('metadata', {})
            ))
        
        # Calcular estadísticas agregadas
        fitness_values = [r.best_fitness for r in single_runs]
        exec_times = [r.execution_time for r in single_runs]
        
        statistics = MultiRunStatistics(
            n_runs=len(single_runs),
            best_fitness=min(fitness_values),
            worst_fitness=max(fitness_values),
            mean_fitness=np.mean(fitness_values),
            std_fitness=np.std(fitness_values),
            median_fitness=np.median(fitness_values),
            confidence_interval_95=(
                np.percentile(fitness_values, 2.5),
                np.percentile(fitness_values, 97.5)
            ),
            total_execution_time=sum(exec_times),
            mean_execution_time=np.mean(exec_times),
            convergence_analysis={
                'mean_final_improvement': np.mean([
                    r.convergence_curve[0] - r.convergence_curve[-1] 
                    for r in single_runs if r.convergence_curve
                ]),
                'std_iterations': np.std([r.iterations_completed for r in single_runs])
            },
            metadata={}
        )
        
        # Información de ejecución agregada
        execution_info = ExecutionInfoV2(
            start_time=datetime.now(),  # TODO: Usar tiempos reales
            end_time=datetime.now(),
            duration_seconds=sum(exec_times),
            cpu_percent_avg=0.0,
            memory_peak_mb=0.0,
            memory_avg_mb=0.0,
            random_seed=single_runs[0].seed,  # Semilla del primer run
            parallel=metadata.get('parallel', False) if metadata else False,
            n_workers=metadata.get('n_workers') if metadata else None,
            thread_count=None,
            working_directory='',
            environment_variables={}
        )
        
        # Crear resultado completo
        result = StandardResultV2(
            result_type=ResultType.MULTI_RUN,
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=single_runs,
            statistics=statistics,
            execution_info=execution_info,
            metadata=metadata or {}
        )
        
        return result


def track_algorithm_execution(algorithm_class: type, 
                            problem: Any,
                            **kwargs) -> StandardResultV2:
    """
    Decorator/wrapper para tracking automático de ejecución.
    
    Args:
        algorithm_class: Clase del algoritmo
        problem: Problema a resolver
        **kwargs: Parámetros del algoritmo
        
    Returns:
        StandardResultV2 con resultado completo
    """
    # Iniciar tracking de ejecución
    start_time = time.time()
    
    # Crear y ejecutar algoritmo
    algorithm = algorithm_class(problem, **kwargs)
    best_solution = algorithm.execute()
    
    # Finalizar tracking
    execution_time = time.time() - start_time
    convergence_curve = algorithm.get_convergence_curve()
    
    # Crear resultado
    result = AlgorithmResultAdapter.create_result_from_algorithm(
        algorithm,
        execution_time,
        convergence_curve
    )
    
    # Procesar con pipeline
    pipeline = get_default_pipeline()
    return pipeline.process(result)