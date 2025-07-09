"""
Esquema estandarizado de resultados para BioAlgoCompare.

Este módulo define el esquema unificado para todos los resultados generados
por el sistema, asegurando consistencia, completitud y facilidad de análisis.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
import json
import pandas as pd
import numpy as np
from pathlib import Path
import hashlib


class ResultType(Enum):
    """Tipos de resultados soportados."""
    SINGLE_RUN = "single_run"
    MULTI_RUN = "multi_run"
    BENCHMARK = "benchmark"
    COMPARISON = "comparison"
    PARAMETER_TUNING = "parameter_tuning"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"


class MetricType(Enum):
    """Tipos de métricas registradas."""
    FITNESS = "fitness"
    DISTANCE = "distance"
    TIME = "time"
    ITERATIONS = "iterations"
    EVALUATIONS = "evaluations"
    CONVERGENCE_RATE = "convergence_rate"
    DIVERSITY = "diversity"
    GAP_TO_OPTIMAL = "gap_to_optimal"


@dataclass
class ProblemInfo:
    """Información del problema optimizado."""
    name: str
    type: str = "VRP"
    dimension: int = 0
    optimal_value: Optional[float] = None
    instance_file: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


@dataclass
class AlgorithmInfo:
    """Información del algoritmo utilizado."""
    name: str
    version: str = "v2"
    population_size: int = 30
    max_iterations: int = 100
    parameters: Dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)
    
    def get_signature(self) -> str:
        """Genera una firma única para esta configuración."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:12]


@dataclass
class ExecutionInfo:
    """Información de la ejecución."""
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    platform: str
    python_version: str
    cpu_count: int
    memory_gb: float
    parallel: bool = False
    n_workers: Optional[int] = None
    
    @classmethod
    def from_times(cls, start: datetime, end: datetime, **kwargs) -> 'ExecutionInfo':
        """Crea desde tiempos de inicio y fin."""
        duration = (end - start).total_seconds()
        return cls(
            start_time=start,
            end_time=end,
            duration_seconds=duration,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data


@dataclass
class SingleRunResult:
    """Resultado de una ejecución individual."""
    run_id: int
    seed: int
    best_fitness: float
    best_solution: Any
    convergence_curve: List[float]
    execution_time: float
    iterations_completed: int
    evaluations: int
    final_population_fitness: Optional[List[float]] = None
    diversity_metrics: Optional[Dict[str, float]] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def get_convergence_rate(self) -> float:
        """Calcula la tasa de convergencia."""
        if len(self.convergence_curve) < 2:
            return 0.0
        initial = self.convergence_curve[0]
        final = self.convergence_curve[-1]
        return (initial - final) / initial if initial > 0 else 0.0
    
    def get_improvement_per_iteration(self) -> float:
        """Calcula la mejora promedio por iteración."""
        if self.iterations_completed == 0:
            return 0.0
        total_improvement = self.convergence_curve[0] - self.convergence_curve[-1]
        return total_improvement / self.iterations_completed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'run_id': self.run_id,
            'seed': self.seed,
            'best_fitness': self.best_fitness,
            'best_solution': self.best_solution,
            'convergence_curve': self.convergence_curve,
            'execution_time': self.execution_time,
            'iterations_completed': self.iterations_completed,
            'evaluations': self.evaluations,
            'convergence_rate': self.get_convergence_rate(),
            'improvement_per_iteration': self.get_improvement_per_iteration(),
            'final_population_fitness': self.final_population_fitness,
            'diversity_metrics': self.diversity_metrics,
            'custom_metrics': self.custom_metrics
        }


@dataclass
class MultiRunStatistics:
    """Estadísticas consolidadas de múltiples ejecuciones."""
    n_runs: int
    best_fitness: float
    worst_fitness: float
    mean_fitness: float
    std_fitness: float
    median_fitness: float
    q1_fitness: float
    q3_fitness: float
    iqr_fitness: float
    cv_fitness: float  # Coeficiente de variación
    success_rate: float  # Porcentaje de runs exitosos
    mean_convergence_rate: float
    mean_execution_time: float
    total_execution_time: float
    confidence_interval_95: Tuple[float, float]
    
    @classmethod
    def from_runs(cls, runs: List[SingleRunResult], success_threshold: Optional[float] = None) -> 'MultiRunStatistics':
        """Calcula estadísticas desde una lista de runs."""
        fitness_values = [r.best_fitness for r in runs]
        execution_times = [r.execution_time for r in runs]
        convergence_rates = [r.get_convergence_rate() for r in runs]
        
        n = len(runs)
        mean_fit = np.mean(fitness_values)
        std_fit = np.std(fitness_values, ddof=1) if n > 1 else 0.0
        
        # Intervalo de confianza del 95%
        if n > 1:
            se = std_fit / np.sqrt(n)
            ci_lower = mean_fit - 1.96 * se
            ci_upper = mean_fit + 1.96 * se
        else:
            ci_lower = ci_upper = mean_fit
        
        # Tasa de éxito
        if success_threshold is not None:
            success_rate = sum(1 for f in fitness_values if f <= success_threshold) / n
        else:
            success_rate = 1.0
        
        return cls(
            n_runs=n,
            best_fitness=min(fitness_values),
            worst_fitness=max(fitness_values),
            mean_fitness=mean_fit,
            std_fitness=std_fit,
            median_fitness=np.median(fitness_values),
            q1_fitness=np.percentile(fitness_values, 25),
            q3_fitness=np.percentile(fitness_values, 75),
            iqr_fitness=np.percentile(fitness_values, 75) - np.percentile(fitness_values, 25),
            cv_fitness=std_fit / mean_fit if mean_fit > 0 else 0.0,
            success_rate=success_rate,
            mean_convergence_rate=np.mean(convergence_rates),
            mean_execution_time=np.mean(execution_times),
            total_execution_time=sum(execution_times),
            confidence_interval_95=(ci_lower, ci_upper)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = asdict(self)
        data['confidence_interval_95'] = list(self.confidence_interval_95)
        return data


@dataclass
class StandardResult:
    """
    Resultado estandarizado completo.
    
    Esta es la estructura principal que contiene toda la información
    de un experimento o conjunto de experimentos.
    """
    result_id: str
    result_type: ResultType
    timestamp: datetime
    problem_info: ProblemInfo
    algorithm_info: AlgorithmInfo
    execution_info: ExecutionInfo
    runs: List[SingleRunResult]
    statistics: MultiRunStatistics
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        if not self.runs:
            raise ValueError("Debe haber al menos un run")
        
        # Recalcular estadísticas si no coinciden
        if self.statistics.n_runs != len(self.runs):
            self.statistics = MultiRunStatistics.from_runs(self.runs)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen conciso del resultado."""
        return {
            'result_id': self.result_id,
            'timestamp': self.timestamp.isoformat(),
            'algorithm': self.algorithm_info.name,
            'problem': self.problem_info.name,
            'n_runs': self.statistics.n_runs,
            'best_fitness': self.statistics.best_fitness,
            'mean_fitness': self.statistics.mean_fitness,
            'std_fitness': self.statistics.std_fitness,
            'total_time': self.statistics.total_execution_time,
            'gap_to_optimal': self.get_gap_to_optimal()
        }
    
    def get_gap_to_optimal(self) -> Optional[float]:
        """Calcula el gap respecto al óptimo conocido."""
        if self.problem_info.optimal_value is None:
            return None
        return (self.statistics.best_fitness - self.problem_info.optimal_value) / self.problem_info.optimal_value * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario completo."""
        return {
            'result_id': self.result_id,
            'result_type': self.result_type.value,
            'timestamp': self.timestamp.isoformat(),
            'problem_info': self.problem_info.to_dict(),
            'algorithm_info': self.algorithm_info.to_dict(),
            'execution_info': self.execution_info.to_dict(),
            'runs': [r.to_dict() for r in self.runs],
            'statistics': self.statistics.to_dict(),
            'summary': self.get_summary(),
            'metadata': self.metadata
        }
    
    def to_json(self, path: Optional[Union[str, Path]] = None, indent: int = 2) -> str:
        """Serializa a JSON."""
        json_str = json.dumps(self.to_dict(), indent=indent, default=str)
        if path:
            Path(path).write_text(json_str)
        return json_str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardResult':
        """Crea desde un diccionario."""
        # Reconstruir objetos anidados
        problem_info = ProblemInfo(**data['problem_info'])
        algorithm_info = AlgorithmInfo(**data['algorithm_info'])
        
        exec_info_data = data['execution_info'].copy()
        exec_info_data['start_time'] = datetime.fromisoformat(exec_info_data['start_time'])
        exec_info_data['end_time'] = datetime.fromisoformat(exec_info_data['end_time'])
        execution_info = ExecutionInfo(**exec_info_data)
        
        runs = [SingleRunResult(**r) for r in data['runs']]
        
        stats_data = data['statistics'].copy()
        stats_data['confidence_interval_95'] = tuple(stats_data['confidence_interval_95'])
        statistics = MultiRunStatistics(**stats_data)
        
        return cls(
            result_id=data['result_id'],
            result_type=ResultType(data['result_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            execution_info=execution_info,
            runs=runs,
            statistics=statistics,
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'StandardResult':
        """Carga desde archivo JSON."""
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte los runs a DataFrame para análisis."""
        records = []
        for run in self.runs:
            record = {
                'result_id': self.result_id,
                'algorithm': self.algorithm_info.name,
                'problem': self.problem_info.name,
                'run_id': run.run_id,
                'seed': run.seed,
                'best_fitness': run.best_fitness,
                'execution_time': run.execution_time,
                'iterations': run.iterations_completed,
                'convergence_rate': run.get_convergence_rate(),
                'improvement_per_iter': run.get_improvement_per_iteration()
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def export_convergence_curves(self, path: Union[str, Path]) -> None:
        """Exporta las curvas de convergencia a CSV."""
        # Encontrar la longitud máxima
        max_len = max(len(r.convergence_curve) for r in self.runs)
        
        # Crear DataFrame con todas las curvas
        data = {}
        for run in self.runs:
            # Rellenar con el último valor si es necesario
            curve = run.convergence_curve + [run.convergence_curve[-1]] * (max_len - len(run.convergence_curve))
            data[f'run_{run.run_id}'] = curve
        
        df = pd.DataFrame(data)
        df.index.name = 'iteration'
        df.to_csv(path)


@dataclass
class ComparisonResult:
    """Resultado de comparación entre múltiples algoritmos/configuraciones."""
    comparison_id: str
    timestamp: datetime
    problem_info: ProblemInfo
    algorithms: List[AlgorithmInfo]
    results: List[StandardResult]
    statistical_tests: Dict[str, Any] = field(default_factory=dict)
    rankings: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary_table(self) -> pd.DataFrame:
        """Genera tabla resumen de la comparación."""
        records = []
        for result in self.results:
            record = {
                'algorithm': result.algorithm_info.name,
                'configuration': result.algorithm_info.get_signature()[:8],
                'n_runs': result.statistics.n_runs,
                'best': result.statistics.best_fitness,
                'mean': result.statistics.mean_fitness,
                'std': result.statistics.std_fitness,
                'median': result.statistics.median_fitness,
                'iqr': result.statistics.iqr_fitness,
                'cv': result.statistics.cv_fitness,
                'success_rate': result.statistics.success_rate,
                'mean_time': result.statistics.mean_execution_time,
                'gap_to_optimal': result.get_gap_to_optimal()
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        return df.sort_values('mean')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'comparison_id': self.comparison_id,
            'timestamp': self.timestamp.isoformat(),
            'problem_info': self.problem_info.to_dict(),
            'algorithms': [a.to_dict() for a in self.algorithms],
            'results': [r.to_dict() for r in self.results],
            'summary_table': self.get_summary_table().to_dict(),
            'statistical_tests': self.statistical_tests,
            'rankings': self.rankings,
            'metadata': self.metadata
        }


class ResultBuilder:
    """Constructor para crear resultados estandarizados fácilmente."""
    
    @staticmethod
    def create_single_run(
        algorithm_name: str,
        problem_name: str,
        run_result: Any,
        execution_time: float,
        **kwargs
    ) -> StandardResult:
        """Crea un resultado de una sola ejecución."""
        # Información del problema
        problem_info = ProblemInfo(
            name=problem_name,
            dimension=kwargs.get('dimension', 0),
            optimal_value=kwargs.get('optimal_value')
        )
        
        # Información del algoritmo
        algorithm_info = AlgorithmInfo(
            name=algorithm_name,
            population_size=kwargs.get('population_size', 30),
            max_iterations=kwargs.get('max_iterations', 100),
            parameters=kwargs.get('algorithm_params', {}),
            seed=kwargs.get('seed')
        )
        
        # Información de ejecución
        execution_info = ExecutionInfo(
            start_time=kwargs.get('start_time', datetime.now()),
            end_time=kwargs.get('end_time', datetime.now()),
            duration_seconds=execution_time,
            platform=kwargs.get('platform', 'unknown'),
            python_version=kwargs.get('python_version', 'unknown'),
            cpu_count=kwargs.get('cpu_count', 1),
            memory_gb=kwargs.get('memory_gb', 0.0)
        )
        
        # Run individual
        single_run = SingleRunResult(
            run_id=0,
            seed=kwargs.get('seed', 42),
            best_fitness=run_result.fitness() if hasattr(run_result, 'fitness') else run_result,
            best_solution=run_result.position if hasattr(run_result, 'position') else None,
            convergence_curve=kwargs.get('convergence_curve', []),
            execution_time=execution_time,
            iterations_completed=kwargs.get('iterations', 100),
            evaluations=kwargs.get('evaluations', 0)
        )
        
        # Estadísticas (de un solo run)
        statistics = MultiRunStatistics.from_runs([single_run])
        
        # Crear resultado estándar
        result_id = f"{algorithm_name}_{problem_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return StandardResult(
            result_id=result_id,
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            execution_info=execution_info,
            runs=[single_run],
            statistics=statistics,
            metadata=kwargs.get('metadata', {})
        )
    
    @staticmethod
    def create_multi_run(
        algorithm_name: str,
        problem_name: str,
        run_results: List[Dict[str, Any]],
        **kwargs
    ) -> StandardResult:
        """Crea un resultado de múltiples ejecuciones."""
        # Información común
        problem_info = ProblemInfo(
            name=problem_name,
            dimension=kwargs.get('dimension', 0),
            optimal_value=kwargs.get('optimal_value'),
            instance_file=kwargs.get('instance_file')
        )
        
        algorithm_info = AlgorithmInfo(
            name=algorithm_name,
            population_size=kwargs.get('population_size', 30),
            max_iterations=kwargs.get('max_iterations', 100),
            parameters=kwargs.get('algorithm_params', {})
        )
        
        # Procesar runs
        runs = []
        total_time = 0
        
        for i, run_data in enumerate(run_results):
            run = SingleRunResult(
                run_id=i,
                seed=run_data.get('seed', 42 + i),
                best_fitness=run_data['best_fitness'],
                best_solution=run_data.get('best_solution'),
                convergence_curve=run_data.get('convergence_curve', []),
                execution_time=run_data.get('execution_time', 0),
                iterations_completed=run_data.get('iterations', kwargs.get('max_iterations', 100)),
                evaluations=run_data.get('evaluations', 0),
                custom_metrics=run_data.get('custom_metrics', {})
            )
            runs.append(run)
            total_time += run.execution_time
        
        # Información de ejecución
        execution_info = ExecutionInfo(
            start_time=kwargs.get('start_time', datetime.now()),
            end_time=kwargs.get('end_time', datetime.now()),
            duration_seconds=total_time,
            platform=kwargs.get('platform', 'unknown'),
            python_version=kwargs.get('python_version', 'unknown'),
            cpu_count=kwargs.get('cpu_count', 1),
            memory_gb=kwargs.get('memory_gb', 0.0),
            parallel=kwargs.get('parallel', False),
            n_workers=kwargs.get('n_workers')
        )
        
        # Estadísticas
        statistics = MultiRunStatistics.from_runs(runs, kwargs.get('success_threshold'))
        
        # Crear resultado
        result_id = f"{algorithm_name}_{problem_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return StandardResult(
            result_id=result_id,
            result_type=ResultType.MULTI_RUN,
            timestamp=datetime.now(),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            execution_info=execution_info,
            runs=runs,
            statistics=statistics,
            metadata=kwargs.get('metadata', {})
        )


def validate_result(result: StandardResult) -> List[str]:
    """
    Valida que un resultado cumpla con el esquema estándar.
    
    Returns:
        Lista de mensajes de error (vacía si es válido)
    """
    errors = []
    
    # Validar estructura básica
    if not result.result_id:
        errors.append("result_id es requerido")
    
    if not result.runs:
        errors.append("Debe haber al menos un run")
    
    # Validar consistencia
    if result.statistics.n_runs != len(result.runs):
        errors.append(f"Inconsistencia: statistics.n_runs ({result.statistics.n_runs}) != len(runs) ({len(result.runs)})")
    
    # Validar runs individuales
    for i, run in enumerate(result.runs):
        if run.best_fitness <= 0:
            errors.append(f"Run {i}: best_fitness debe ser positivo")
        
        if not run.convergence_curve:
            errors.append(f"Run {i}: convergence_curve vacía")
        
        if run.execution_time < 0:
            errors.append(f"Run {i}: execution_time negativo")
    
    # Validar estadísticas
    if result.statistics.mean_fitness <= 0:
        errors.append("mean_fitness debe ser positivo")
    
    if result.statistics.std_fitness < 0:
        errors.append("std_fitness no puede ser negativo")
    
    if result.statistics.cv_fitness < 0:
        errors.append("cv_fitness no puede ser negativo")
    
    return errors


def merge_results(results: List[StandardResult], new_id: Optional[str] = None) -> StandardResult:
    """
    Combina múltiples resultados en uno solo.
    
    Útil para agregar resultados de ejecuciones distribuidas.
    """
    if not results:
        raise ValueError("No hay resultados para combinar")
    
    # Verificar compatibilidad
    first = results[0]
    for r in results[1:]:
        if r.algorithm_info.name != first.algorithm_info.name:
            raise ValueError("Los algoritmos deben ser iguales")
        if r.problem_info.name != first.problem_info.name:
            raise ValueError("Los problemas deben ser iguales")
    
    # Combinar runs
    all_runs = []
    run_id = 0
    
    for result in results:
        for run in result.runs:
            new_run = SingleRunResult(
                run_id=run_id,
                seed=run.seed,
                best_fitness=run.best_fitness,
                best_solution=run.best_solution,
                convergence_curve=run.convergence_curve,
                execution_time=run.execution_time,
                iterations_completed=run.iterations_completed,
                evaluations=run.evaluations,
                final_population_fitness=run.final_population_fitness,
                diversity_metrics=run.diversity_metrics,
                custom_metrics=run.custom_metrics
            )
            all_runs.append(new_run)
            run_id += 1
    
    # Combinar tiempos de ejecución
    total_duration = sum(r.execution_info.duration_seconds for r in results)
    
    # Crear nuevo resultado combinado
    return StandardResult(
        result_id=new_id or f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        result_type=ResultType.MULTI_RUN,
        timestamp=datetime.now(),
        problem_info=first.problem_info,
        algorithm_info=first.algorithm_info,
        execution_info=ExecutionInfo(
            start_time=min(r.execution_info.start_time for r in results),
            end_time=max(r.execution_info.end_time for r in results),
            duration_seconds=total_duration,
            platform=first.execution_info.platform,
            python_version=first.execution_info.python_version,
            cpu_count=first.execution_info.cpu_count,
            memory_gb=first.execution_info.memory_gb,
            parallel=any(r.execution_info.parallel for r in results),
            n_workers=sum(r.execution_info.n_workers or 1 for r in results)
        ),
        runs=all_runs,
        statistics=MultiRunStatistics.from_runs(all_runs),
        metadata={
            'merged_from': [r.result_id for r in results],
            'merge_timestamp': datetime.now().isoformat()
        }
    )