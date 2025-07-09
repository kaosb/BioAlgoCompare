"""
Esquema estandarizado de resultados v2 para BioAlgoCompare.

Esta versión extiende StandardResult con metadatos completos para
garantizar reproducibilidad científica y trazabilidad total.
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
import platform
import sys
import os
import psutil
import subprocess
import uuid
import pkg_resources

# Importar clases base del esquema original
from .result_schema import (
    ResultType, MetricType, ProblemInfo, AlgorithmInfo,
    SingleRunResult, MultiRunStatistics, ResultBuilder,
    validate_result as validate_result_v1
)


@dataclass
class SystemInfo:
    """Información completa del sistema."""
    platform: str
    platform_release: str
    platform_version: str
    architecture: str
    processor: str
    cpu_count: int
    cpu_freq_mhz: float
    memory_total_gb: float
    memory_available_gb: float
    python_version: str
    python_implementation: str
    python_compiler: str
    
    @classmethod
    def capture(cls) -> 'SystemInfo':
        """Captura información actual del sistema."""
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        
        return cls(
            platform=platform.system(),
            platform_release=platform.release(),
            platform_version=platform.version(),
            architecture=platform.machine(),
            processor=platform.processor(),
            cpu_count=psutil.cpu_count(logical=True),
            cpu_freq_mhz=cpu_freq.current if cpu_freq else 0.0,
            memory_total_gb=memory.total / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            python_version=sys.version,
            python_implementation=platform.python_implementation(),
            python_compiler=platform.python_compiler()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


@dataclass
class GitInfo:
    """Información del estado de git."""
    commit_hash: str
    branch: str
    is_dirty: bool
    uncommitted_changes: int
    remote_url: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    commit_message: Optional[str] = None
    commit_date: Optional[str] = None
    
    @classmethod
    def capture(cls) -> Optional['GitInfo']:
        """Captura información actual de git."""
        try:
            # Verificar si estamos en un repositorio git
            subprocess.run(['git', 'rev-parse', '--git-dir'], 
                         capture_output=True, check=True)
            
            # Obtener información
            commit_hash = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            # Verificar cambios no commiteados
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, check=True
            ).stdout
            
            is_dirty = bool(status.strip())
            uncommitted_changes = len(status.strip().split('\n')) if status.strip() else 0
            
            # Intentar obtener remote URL
            try:
                remote_url = subprocess.run(
                    ['git', 'config', '--get', 'remote.origin.url'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
            except:
                remote_url = None
            
            # Información del último commit
            try:
                author_name = subprocess.run(
                    ['git', 'log', '-1', '--format=%an'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                
                author_email = subprocess.run(
                    ['git', 'log', '-1', '--format=%ae'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                
                commit_message = subprocess.run(
                    ['git', 'log', '-1', '--format=%s'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                
                commit_date = subprocess.run(
                    ['git', 'log', '-1', '--format=%ai'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
            except:
                author_name = author_email = commit_message = commit_date = None
            
            return cls(
                commit_hash=commit_hash,
                branch=branch,
                is_dirty=is_dirty,
                uncommitted_changes=uncommitted_changes,
                remote_url=remote_url,
                author_name=author_name,
                author_email=author_email,
                commit_message=commit_message,
                commit_date=commit_date
            )
        except:
            # No es un repositorio git o git no está disponible
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


@dataclass
class DependencyInfo:
    """Información de dependencias del proyecto."""
    name: str
    version: str
    
    @classmethod
    def capture_all(cls) -> List['DependencyInfo']:
        """Captura todas las dependencias instaladas."""
        deps = []
        for dist in pkg_resources.working_set:
            deps.append(cls(name=dist.key, version=dist.version))
        return sorted(deps, key=lambda x: x.name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


@dataclass
class ExecutionInfoV2:
    """Información extendida de la ejecución."""
    # Tiempos
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Recursos
    cpu_percent_avg: float
    memory_peak_mb: float
    memory_avg_mb: float
    
    # Configuración de ejecución
    random_seed: int
    parallel: bool = False
    n_workers: Optional[int] = None
    thread_count: Optional[int] = None
    
    # Ambiente
    working_directory: str = field(default_factory=os.getcwd)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def start_tracking(cls, seed: int, parallel: bool = False, 
                      n_workers: Optional[int] = None) -> 'ExecutionInfoV2':
        """Inicia el tracking de una ejecución."""
        # Capturar variables de entorno relevantes
        env_vars = {
            k: v for k, v in os.environ.items()
            if k.startswith(('PYTHON', 'PATH', 'BIOALGO', 'OMP', 'MKL'))
        }
        
        return cls(
            start_time=datetime.now(),
            end_time=datetime.now(),  # Se actualizará al finalizar
            duration_seconds=0.0,
            cpu_percent_avg=0.0,
            memory_peak_mb=0.0,
            memory_avg_mb=0.0,
            random_seed=seed,
            parallel=parallel,
            n_workers=n_workers,
            thread_count=psutil.cpu_count(logical=True),
            working_directory=os.getcwd(),
            environment_variables=env_vars
        )
    
    def finalize(self, cpu_samples: List[float] = None, 
                memory_samples: List[float] = None):
        """Finaliza el tracking con estadísticas."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        if cpu_samples:
            self.cpu_percent_avg = np.mean(cpu_samples)
        
        if memory_samples:
            self.memory_peak_mb = max(memory_samples)
            self.memory_avg_mb = np.mean(memory_samples)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data


@dataclass
class StandardResultV2:
    """
    Resultado estandarizado v2 con metadatos completos.
    
    Extiende StandardResult con información de sistema, git,
    dependencias y validación mejorada.
    """
    # Información del experimento (campos requeridos primero)
    result_type: ResultType
    problem_info: ProblemInfo
    algorithm_info: AlgorithmInfo
    runs: List[SingleRunResult]
    statistics: MultiRunStatistics
    
    # Identificación única
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = field(default="2.0.0")
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Metadatos extendidos
    system_info: SystemInfo = field(default_factory=SystemInfo.capture)
    git_info: Optional[GitInfo] = field(default_factory=GitInfo.capture)
    execution_info: Optional[ExecutionInfoV2] = field(default=None)
    dependencies: List[DependencyInfo] = field(default_factory=DependencyInfo.capture_all)
    
    # Validación e integridad
    checksum: Optional[str] = field(default=None)
    validated: bool = field(default=False)
    validation_errors: List[str] = field(default_factory=list)
    
    # Metadatos adicionales
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones y cálculos post-inicialización."""
        # Generar ID si no se proporcionó
        if not self.result_id:
            self.result_id = str(uuid.uuid4())
        
        # Capturar información si no se proporcionó
        if self.system_info is None:
            self.system_info = SystemInfo.capture()
        
        if self.git_info is None:
            self.git_info = GitInfo.capture()
        
        if not self.dependencies:
            self.dependencies = DependencyInfo.capture_all()
        
        # Validar estructura
        self.validate()
        
        # Calcular checksum si no existe
        if not self.checksum:
            self.checksum = self.calculate_checksum()
    
    def calculate_checksum(self) -> str:
        """Calcula SHA256 de los resultados para integridad."""
        # Datos esenciales para el checksum
        essential_data = {
            'algorithm': self.algorithm_info.name,
            'algorithm_params': self.algorithm_info.parameters,
            'problem': self.problem_info.name,
            'problem_dimension': self.problem_info.dimension,
            'seeds': [r.seed for r in self.runs],
            'results': [r.best_fitness for r in self.runs],
            'convergence_curves': [r.convergence_curve for r in self.runs]
        }
        
        # Serializar de forma determinística
        json_str = json.dumps(essential_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def validate(self) -> bool:
        """Valida el resultado completo."""
        self.validation_errors = []
        
        # Validación básica del esquema v1
        v1_errors = validate_result_v1(self)
        self.validation_errors.extend(v1_errors)
        
        # Validaciones adicionales v2
        if not self.result_id:
            self.validation_errors.append("result_id es requerido")
        
        if not self.version:
            self.validation_errors.append("version es requerida")
        
        if self.execution_info and self.execution_info.random_seed is None:
            self.validation_errors.append("random_seed es requerido para reproducibilidad")
        
        # Verificar consistencia de semillas
        if self.runs and self.execution_info:
            for i, run in enumerate(self.runs):
                if run.seed is None:
                    self.validation_errors.append(f"Run {i}: seed es requerida")
        
        self.validated = len(self.validation_errors) == 0
        return self.validated
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen conciso del resultado."""
        summary = {
            'result_id': self.result_id,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'algorithm': self.algorithm_info.name,
            'problem': self.problem_info.name,
            'n_runs': self.statistics.n_runs,
            'best_fitness': self.statistics.best_fitness,
            'mean_fitness': self.statistics.mean_fitness,
            'std_fitness': self.statistics.std_fitness,
            'total_time': self.statistics.total_execution_time,
            'gap_to_optimal': self.get_gap_to_optimal(),
            'checksum': self.checksum[:12] if self.checksum else None,
            'validated': self.validated
        }
        
        # Añadir información de git si está disponible
        if self.git_info:
            summary['git_commit'] = self.git_info.commit_hash[:8]
            summary['git_branch'] = self.git_info.branch
            summary['git_dirty'] = self.git_info.is_dirty
        
        return summary
    
    def get_gap_to_optimal(self) -> Optional[float]:
        """Calcula el gap respecto al óptimo conocido."""
        if self.problem_info.optimal_value is None:
            return None
        return (self.statistics.best_fitness - self.problem_info.optimal_value) / \
               self.problem_info.optimal_value * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario completo."""
        return {
            'result_id': self.result_id,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'result_type': self.result_type.value,
            'problem_info': self.problem_info.to_dict(),
            'algorithm_info': self.algorithm_info.to_dict(),
            'runs': [r.to_dict() for r in self.runs],
            'statistics': self.statistics.to_dict(),
            'system_info': self.system_info.to_dict() if self.system_info else None,
            'git_info': self.git_info.to_dict() if self.git_info else None,
            'execution_info': self.execution_info.to_dict() if self.execution_info else None,
            'dependencies': [d.to_dict() for d in self.dependencies],
            'checksum': self.checksum,
            'validated': self.validated,
            'validation_errors': self.validation_errors,
            'summary': self.get_summary(),
            'metadata': self.metadata
        }
    
    def to_json(self, path: Optional[Union[str, Path]] = None, 
                indent: int = 2, compressed: bool = False) -> str:
        """
        Serializa a JSON con opciones de compresión.
        
        Args:
            path: Ruta donde guardar el archivo
            indent: Indentación para formato legible
            compressed: Si True, minimiza el tamaño del JSON
        """
        data = self.to_dict()
        
        if compressed:
            json_str = json.dumps(data, separators=(',', ':'), default=str)
        else:
            json_str = json.dumps(data, indent=indent, default=str)
        
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(json_str)
        
        return json_str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardResultV2':
        """Crea desde un diccionario."""
        # Reconstruir objetos anidados
        problem_info = ProblemInfo(**data['problem_info'])
        algorithm_info = AlgorithmInfo(**data['algorithm_info'])
        
        # System info
        system_info = SystemInfo(**data['system_info']) if data.get('system_info') else None
        
        # Git info
        git_info = GitInfo(**data['git_info']) if data.get('git_info') else None
        
        # Execution info
        if data.get('execution_info'):
            exec_data = data['execution_info'].copy()
            exec_data['start_time'] = datetime.fromisoformat(exec_data['start_time'])
            exec_data['end_time'] = datetime.fromisoformat(exec_data['end_time'])
            execution_info = ExecutionInfoV2(**exec_data)
        else:
            execution_info = None
        
        # Dependencies
        dependencies = [DependencyInfo(**d) for d in data.get('dependencies', [])]
        
        # Runs
        runs = [SingleRunResult(**r) for r in data['runs']]
        
        # Statistics
        stats_data = data['statistics'].copy()
        stats_data['confidence_interval_95'] = tuple(stats_data['confidence_interval_95'])
        statistics = MultiRunStatistics(**stats_data)
        
        return cls(
            result_id=data['result_id'],
            version=data.get('version', '2.0.0'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            result_type=ResultType(data['result_type']),
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=runs,
            statistics=statistics,
            system_info=system_info,
            git_info=git_info,
            execution_info=execution_info,
            dependencies=dependencies,
            checksum=data.get('checksum'),
            validated=data.get('validated', False),
            validation_errors=data.get('validation_errors', []),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'StandardResultV2':
        """Carga desde archivo JSON."""
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)
    
    def to_dataframe(self, include_metadata: bool = False) -> pd.DataFrame:
        """
        Convierte los runs a DataFrame para análisis.
        
        Args:
            include_metadata: Si incluir metadatos del sistema en cada fila
        """
        records = []
        
        for run in self.runs:
            record = {
                'result_id': self.result_id,
                'version': self.version,
                'timestamp': self.timestamp,
                'algorithm': self.algorithm_info.name,
                'problem': self.problem_info.name,
                'problem_dimension': self.problem_info.dimension,
                'run_id': run.run_id,
                'seed': run.seed,
                'best_fitness': run.best_fitness,
                'execution_time': run.execution_time,
                'iterations': run.iterations_completed,
                'evaluations': run.evaluations,
                'convergence_rate': run.get_convergence_rate(),
                'improvement_per_iter': run.get_improvement_per_iteration(),
                'gap_to_optimal': self.get_gap_to_optimal()
            }
            
            # Añadir parámetros del algoritmo
            for param, value in self.algorithm_info.parameters.items():
                record[f'param_{param}'] = value
            
            # Añadir metadatos si se solicita
            if include_metadata:
                if self.system_info:
                    record['platform'] = self.system_info.platform
                    record['cpu_count'] = self.system_info.cpu_count
                    record['memory_gb'] = self.system_info.memory_total_gb
                
                if self.git_info:
                    record['git_commit'] = self.git_info.commit_hash[:8]
                    record['git_branch'] = self.git_info.branch
                
                if self.execution_info:
                    record['random_seed'] = self.execution_info.random_seed
                    record['parallel'] = self.execution_info.parallel
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    def export_to_latex(self, path: Union[str, Path], 
                       caption: str = None, label: str = None) -> None:
        """
        Exporta tabla resumen a LaTeX para publicación.
        
        Args:
            path: Ruta del archivo .tex
            caption: Caption de la tabla
            label: Label para referencias
        """
        # Crear DataFrame resumen
        summary_data = {
            'Algorithm': [self.algorithm_info.name],
            'Problem': [self.problem_info.name],
            'Runs': [self.statistics.n_runs],
            'Best': [f"{self.statistics.best_fitness:.2f}"],
            'Mean ± Std': [f"{self.statistics.mean_fitness:.2f} ± {self.statistics.std_fitness:.2f}"],
            'Median': [f"{self.statistics.median_fitness:.2f}"],
            'Time (s)': [f"{self.statistics.mean_execution_time:.2f}"],
            'Gap (%)': [f"{self.get_gap_to_optimal():.2f}" if self.get_gap_to_optimal() else "N/A"]
        }
        
        df = pd.DataFrame(summary_data)
        
        # Generar LaTeX
        latex = df.to_latex(
            index=False,
            escape=False,
            column_format='l' + 'c' * (len(df.columns) - 1),
            caption=caption or f"Results for {self.algorithm_info.name} on {self.problem_info.name}",
            label=label or f"tab:results_{self.result_id[:8]}"
        )
        
        # Guardar
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(latex)
    
    def export_convergence_curves(self, path: Union[str, Path], 
                                 format: str = 'csv') -> None:
        """
        Exporta las curvas de convergencia.
        
        Args:
            path: Ruta del archivo
            format: Formato ('csv', 'json', 'npy')
        """
        if format == 'csv':
            # Encontrar la longitud máxima
            max_len = max(len(r.convergence_curve) for r in self.runs)
            
            # Crear DataFrame con todas las curvas
            data = {}
            for run in self.runs:
                # Rellenar con el último valor si es necesario
                curve = run.convergence_curve + [run.convergence_curve[-1]] * \
                        (max_len - len(run.convergence_curve))
                data[f'run_{run.run_id}_seed_{run.seed}'] = curve
            
            df = pd.DataFrame(data)
            df.index.name = 'iteration'
            df.to_csv(path)
            
        elif format == 'json':
            data = {
                f'run_{r.run_id}': {
                    'seed': r.seed,
                    'curve': r.convergence_curve
                }
                for r in self.runs
            }
            Path(path).write_text(json.dumps(data, indent=2))
            
        elif format == 'npy':
            # Formato NumPy para análisis eficiente
            curves = [r.convergence_curve for r in self.runs]
            np.save(path, curves, allow_pickle=True)
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def verify_integrity(self) -> bool:
        """
        Verifica la integridad del resultado comparando checksums.
        
        Returns:
            True si la integridad es válida
        """
        if not self.checksum:
            return False
        
        calculated = self.calculate_checksum()
        return calculated == self.checksum
    
    def get_reproducibility_info(self) -> Dict[str, Any]:
        """
        Obtiene toda la información necesaria para reproducir el experimento.
        """
        info = {
            'algorithm': self.algorithm_info.to_dict(),
            'problem': self.problem_info.to_dict(),
            'seeds': [r.seed for r in self.runs],
            'system': self.system_info.to_dict() if self.system_info else None,
            'dependencies': [d.to_dict() for d in self.dependencies],
            'git': self.git_info.to_dict() if self.git_info else None,
            'execution': {
                'random_seed': self.execution_info.random_seed if self.execution_info else None,
                'parallel': self.execution_info.parallel if self.execution_info else False,
                'n_workers': self.execution_info.n_workers if self.execution_info else None
            }
        }
        
        return info


class ResultBuilderV2(ResultBuilder):
    """Constructor extendido para crear resultados v2."""
    
    @staticmethod
    def create_from_algorithm_run(
        algorithm: Any,
        problem: Any,
        execution_info: ExecutionInfoV2,
        runs_data: List[Dict[str, Any]],
        **kwargs
    ) -> StandardResultV2:
        """
        Crea un resultado v2 directamente desde una ejecución de algoritmo.
        
        Args:
            algorithm: Instancia del algoritmo ejecutado
            problem: Instancia del problema
            execution_info: Información de la ejecución
            runs_data: Lista de datos de cada run
            **kwargs: Metadatos adicionales
        """
        # Información del problema
        problem_info = ProblemInfo(
            name=problem.name if hasattr(problem, 'name') else str(problem),
            type=problem.__class__.__name__,
            dimension=problem.dimension if hasattr(problem, 'dimension') else 0,
            optimal_value=kwargs.get('optimal_value'),
            instance_file=kwargs.get('instance_file'),
            metadata={'problem_class': problem.__class__.__module__}
        )
        
        # Información del algoritmo
        algorithm_info = AlgorithmInfo(
            name=algorithm.__class__.__name__,
            version=getattr(algorithm, 'version', 'v2'),
            population_size=algorithm.population_size,
            max_iterations=algorithm.max_iterations,
            parameters=algorithm.get_parameters() if hasattr(algorithm, 'get_parameters') else {},
            seed=execution_info.random_seed
        )
        
        # Procesar runs
        runs = []
        for i, run_data in enumerate(runs_data):
            run = SingleRunResult(
                run_id=i,
                seed=run_data['seed'],
                best_fitness=run_data['best_fitness'],
                best_solution=run_data.get('best_solution'),
                convergence_curve=run_data.get('convergence_curve', []),
                execution_time=run_data.get('execution_time', 0),
                iterations_completed=run_data.get('iterations', algorithm.max_iterations),
                evaluations=run_data.get('evaluations', 0),
                final_population_fitness=run_data.get('final_population_fitness'),
                diversity_metrics=run_data.get('diversity_metrics'),
                custom_metrics=run_data.get('custom_metrics', {})
            )
            runs.append(run)
        
        # Estadísticas
        statistics = MultiRunStatistics.from_runs(runs, kwargs.get('success_threshold'))
        
        # Determinar tipo de resultado
        result_type = ResultType.SINGLE_RUN if len(runs) == 1 else ResultType.MULTI_RUN
        
        # Crear resultado v2
        return StandardResultV2(
            result_type=result_type,
            problem_info=problem_info,
            algorithm_info=algorithm_info,
            runs=runs,
            statistics=statistics,
            execution_info=execution_info,
            metadata=kwargs.get('metadata', {})
        )


def migrate_v1_to_v2(v1_result: Any) -> StandardResultV2:
    """
    Migra un resultado v1 a v2.
    
    Args:
        v1_result: Resultado en formato v1 (StandardResult o dict)
    
    Returns:
        Resultado en formato v2
    """
    # Si es un dict, convertir primero a StandardResult v1
    if isinstance(v1_result, dict):
        from .result_schema import StandardResult
        v1_result = StandardResult.from_dict(v1_result)
    
    # Crear ExecutionInfoV2 desde ExecutionInfo v1
    if hasattr(v1_result, 'execution_info'):
        exec_v1 = v1_result.execution_info
        execution_info = ExecutionInfoV2(
            start_time=exec_v1.start_time,
            end_time=exec_v1.end_time,
            duration_seconds=exec_v1.duration_seconds,
            cpu_percent_avg=0.0,  # No disponible en v1
            memory_peak_mb=exec_v1.memory_gb * 1024 if hasattr(exec_v1, 'memory_gb') else 0.0,
            memory_avg_mb=0.0,  # No disponible en v1
            random_seed=v1_result.algorithm_info.seed or 42,
            parallel=exec_v1.parallel if hasattr(exec_v1, 'parallel') else False,
            n_workers=exec_v1.n_workers if hasattr(exec_v1, 'n_workers') else None
        )
    else:
        execution_info = None
    
    # Crear resultado v2
    return StandardResultV2(
        result_id=v1_result.result_id,
        version="2.0.0",
        timestamp=v1_result.timestamp,
        result_type=v1_result.result_type,
        problem_info=v1_result.problem_info,
        algorithm_info=v1_result.algorithm_info,
        runs=v1_result.runs,
        statistics=v1_result.statistics,
        execution_info=execution_info,
        metadata=v1_result.metadata
    )