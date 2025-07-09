"""
Sistema integral de gestión de metadatos y trazabilidad experimental.

Este módulo proporciona un framework completo para capturar, gestionar y
analizar metadatos de experimentos, garantizando trazabilidad completa.
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import platform
import psutil
import socket
import getpass
from dataclasses import dataclass, field, asdict
import numpy as np
from enum import Enum

from utils.reproducibility import ReproducibilityManager


class MetadataLevel(Enum):
    """Niveles de detalle de metadatos."""
    MINIMAL = "minimal"        # Solo información esencial
    STANDARD = "standard"      # Información estándar para publicación
    DETAILED = "detailed"      # Información detallada para debug
    COMPLETE = "complete"      # Toda la información disponible


@dataclass
class SystemMetadata:
    """Metadatos del sistema de ejecución."""
    timestamp: str
    hostname: str
    username: str
    platform: Dict[str, str]
    hardware: Dict[str, Any]
    software: Dict[str, str]
    environment: Dict[str, str]
    
    @classmethod
    def capture(cls) -> 'SystemMetadata':
        """Captura metadatos del sistema actual."""
        return cls(
            timestamp=datetime.now().isoformat(),
            hostname=socket.gethostname(),
            username=getpass.getuser(),
            platform={
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation()
            },
            hardware={
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': {
                    str(p.mountpoint): psutil.disk_usage(p.mountpoint)._asdict()
                    for p in psutil.disk_partitions() if p.fstype
                }
            },
            software={
                'numpy': np.__version__,
                'python': platform.python_version(),
                # Añadir más versiones según necesidad
            },
            environment={
                k: v for k, v in os.environ.items()
                if any(prefix in k for prefix in ['PYTHON', 'PATH', 'BIOALGO'])
            }
        )


@dataclass
class AlgorithmMetadata:
    """Metadatos específicos del algoritmo."""
    name: str
    version: str
    parameters: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    random_seed: int
    implementation_details: Dict[str, str] = field(default_factory=dict)
    
    def add_implementation_detail(self, key: str, value: str):
        """Añade detalle de implementación."""
        self.implementation_details[key] = value


@dataclass
class ProblemMetadata:
    """Metadatos del problema a resolver."""
    type: str
    instance: str
    dimensions: Dict[str, int]
    constraints: Dict[str, Any]
    optimal_value: Optional[float] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetadata:
    """Metadatos de la ejecución del experimento."""
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    iterations_completed: int = 0
    convergence_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ResultMetadata:
    """Metadatos del resultado obtenido."""
    best_solution: Any
    best_fitness: float
    final_population: Optional[Any] = None
    statistics: Dict[str, float] = field(default_factory=dict)
    quality_indicators: Dict[str, float] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentMetadata:
    """Metadatos completos del experimento."""
    experiment_id: str
    experiment_type: str
    description: str
    tags: List[str]
    system: SystemMetadata
    algorithm: AlgorithmMetadata
    problem: ProblemMetadata
    execution: ExecutionMetadata
    result: Optional[ResultMetadata] = None
    reproducibility: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self, level: MetadataLevel = MetadataLevel.STANDARD) -> Dict[str, Any]:
        """Convierte a diccionario según nivel de detalle."""
        data = asdict(self)
        
        if level == MetadataLevel.MINIMAL:
            # Solo información esencial
            return {
                'experiment_id': data['experiment_id'],
                'algorithm': data['algorithm']['name'],
                'problem': data['problem']['instance'],
                'best_fitness': data['result']['best_fitness'] if data['result'] else None,
                'timestamp': data['system']['timestamp']
            }
        
        elif level == MetadataLevel.STANDARD:
            # Excluir información sensible/verbosa
            if 'environment' in data['system']:
                data['system']['environment'] = {
                    k: v for k, v in data['system']['environment'].items()
                    if 'PATH' not in k
                }
            if 'hardware' in data['system']:
                data['system']['hardware'].pop('disk_usage', None)
            return data
        
        elif level == MetadataLevel.DETAILED:
            # Incluir casi todo
            return data
        
        else:  # COMPLETE
            # Todo
            return data
    
    def calculate_checksum(self) -> str:
        """Calcula checksum del experimento para verificación."""
        # Serializar datos clave
        key_data = {
            'experiment_id': self.experiment_id,
            'algorithm': self.algorithm.name,
            'parameters': self.algorithm.parameters,
            'problem': self.problem.instance,
            'seed': self.algorithm.random_seed,
            'result': self.result.best_fitness if self.result else None
        }
        
        # Calcular hash
        data_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class MetadataManager:
    """Gestor principal de metadatos experimentales."""
    
    def __init__(self, 
                 storage_path: Optional[Path] = None,
                 auto_capture: bool = True,
                 metadata_level: MetadataLevel = MetadataLevel.STANDARD):
        """
        Inicializa el gestor de metadatos.
        
        Args:
            storage_path: Directorio para almacenar metadatos
            auto_capture: Si capturar automáticamente metadatos del sistema
            metadata_level: Nivel de detalle por defecto
        """
        self.storage_path = storage_path or Path("metadata")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.auto_capture = auto_capture
        self.metadata_level = metadata_level
        
        # Cache de experimentos activos
        self.active_experiments: Dict[str, ExperimentMetadata] = {}
        
        # Sistema de metadatos si auto_capture
        self.system_metadata = SystemMetadata.capture() if auto_capture else None
        
        # Integración con reproducibilidad
        self.reproducibility_manager = ReproducibilityManager()
    
    def create_experiment(self,
                         experiment_type: str,
                         algorithm_name: str,
                         problem_instance: str,
                         parameters: Dict[str, Any],
                         description: str = "",
                         tags: Optional[List[str]] = None) -> ExperimentMetadata:
        """
        Crea un nuevo experimento con metadatos completos.
        
        Args:
            experiment_type: Tipo de experimento (single_run, benchmark, etc.)
            algorithm_name: Nombre del algoritmo
            problem_instance: Instancia del problema
            parameters: Parámetros del algoritmo
            description: Descripción del experimento
            tags: Etiquetas para categorización
            
        Returns:
            ExperimentMetadata configurado
        """
        # Generar ID único
        experiment_id = f"{algorithm_name}_{problem_instance}_{uuid.uuid4().hex[:8]}"
        
        # Capturar metadatos del sistema si necesario
        system_meta = self.system_metadata or SystemMetadata.capture()
        
        # Crear metadatos del algoritmo
        algorithm_meta = AlgorithmMetadata(
            name=algorithm_name,
            version=self._get_algorithm_version(algorithm_name),
            parameters=parameters,
            hyperparameters={},  # Se llenarán durante ejecución
            random_seed=parameters.get('seed', 42)
        )
        
        # Crear metadatos del problema
        problem_meta = self._create_problem_metadata(problem_instance)
        
        # Crear metadatos de ejecución
        execution_meta = ExecutionMetadata(
            start_time=datetime.now().isoformat()
        )
        
        # Crear experimento completo
        experiment = ExperimentMetadata(
            experiment_id=experiment_id,
            experiment_type=experiment_type,
            description=description,
            tags=tags or [],
            system=system_meta,
            algorithm=algorithm_meta,
            problem=problem_meta,
            execution=execution_meta
        )
        
        # Añadir información de reproducibilidad
        repro_context = self.reproducibility_manager.create_experiment(
            experiment_id=experiment_id,
            algorithm=algorithm_name,
            problem=problem_instance,
            parameters=parameters
        )
        
        experiment.reproducibility = {
            'base_seed': self.reproducibility_manager.base_seed,
            'algorithm_seed': repro_context.algorithm_seed,
            'problem_seed': repro_context.problem_seed,
            'enforce_determinism': self.reproducibility_manager.enforce_determinism
        }
        
        # Registrar experimento activo
        self.active_experiments[experiment_id] = experiment
        
        return experiment
    
    def update_execution(self,
                        experiment_id: str,
                        iteration: int,
                        metrics: Dict[str, Any],
                        population_stats: Optional[Dict[str, float]] = None):
        """
        Actualiza metadatos durante la ejecución.
        
        Args:
            experiment_id: ID del experimento
            iteration: Iteración actual
            metrics: Métricas de la iteración
            population_stats: Estadísticas de la población
        """
        if experiment_id not in self.active_experiments:
            raise ValueError(f"Experimento {experiment_id} no encontrado")
        
        experiment = self.active_experiments[experiment_id]
        
        # Actualizar iteraciones
        experiment.execution.iterations_completed = iteration
        
        # Añadir a historial de convergencia
        convergence_point = {
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'best_fitness': metrics.get('best_fitness'),
            'mean_fitness': metrics.get('mean_fitness'),
            'std_fitness': metrics.get('std_fitness')
        }
        
        if population_stats:
            convergence_point.update(population_stats)
        
        experiment.execution.convergence_history.append(convergence_point)
        
        # Actualizar métricas de rendimiento
        if 'execution_time' in metrics:
            experiment.execution.performance_metrics['avg_iteration_time'] = (
                metrics['execution_time'] / iteration if iteration > 0 else 0
            )
    
    def finalize_experiment(self,
                           experiment_id: str,
                           result: Dict[str, Any],
                           error: Optional[Exception] = None) -> ExperimentMetadata:
        """
        Finaliza un experimento y guarda metadatos.
        
        Args:
            experiment_id: ID del experimento
            result: Resultado del experimento
            error: Error si hubo fallo
            
        Returns:
            ExperimentMetadata completo
        """
        if experiment_id not in self.active_experiments:
            raise ValueError(f"Experimento {experiment_id} no encontrado")
        
        experiment = self.active_experiments[experiment_id]
        
        # Marcar tiempo de fin
        experiment.execution.end_time = datetime.now().isoformat()
        
        # Calcular duración
        start = datetime.fromisoformat(experiment.execution.start_time)
        end = datetime.fromisoformat(experiment.execution.end_time)
        experiment.execution.duration_seconds = (end - start).total_seconds()
        
        if error:
            # Registrar error
            experiment.execution.errors.append({
                'timestamp': datetime.now().isoformat(),
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc() if hasattr(error, '__traceback__') else None
            })
        else:
            # Crear metadatos del resultado
            experiment.result = ResultMetadata(
                best_solution=result.get('best_solution'),
                best_fitness=result['best_fitness'],
                final_population=result.get('final_population'),
                statistics={
                    'final_mean': result.get('mean_fitness'),
                    'final_std': result.get('std_fitness'),
                    'improvement': self._calculate_improvement(experiment)
                },
                quality_indicators=self._calculate_quality_indicators(experiment, result)
            )
        
        # Calcular checksum
        experiment.provenance['checksum'] = experiment.calculate_checksum()
        
        # Guardar metadatos
        self._save_metadata(experiment)
        
        # Limpiar de activos
        del self.active_experiments[experiment_id]
        
        return experiment
    
    def add_custom_metadata(self,
                           experiment_id: str,
                           key: str,
                           value: Any):
        """
        Añade metadatos personalizados.
        
        Args:
            experiment_id: ID del experimento
            key: Clave del metadato
            value: Valor del metadato
        """
        if experiment_id in self.active_experiments:
            experiment = self.active_experiments[experiment_id]
        else:
            experiment = self.load_experiment(experiment_id)
        
        experiment.custom[key] = value
        
        if experiment_id in self.active_experiments:
            # Si está activo, se guardará al finalizar
            pass
        else:
            # Si no está activo, guardar ahora
            self._save_metadata(experiment)
    
    def search_experiments(self,
                          algorithm: Optional[str] = None,
                          problem: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None) -> List[ExperimentMetadata]:
        """
        Busca experimentos según criterios.
        
        Args:
            algorithm: Filtrar por algoritmo
            problem: Filtrar por problema
            tags: Filtrar por etiquetas
            date_from: Fecha desde
            date_to: Fecha hasta
            
        Returns:
            Lista de experimentos que cumplen criterios
        """
        experiments = []
        
        # Buscar en archivos guardados
        for meta_file in self.storage_path.glob("*.json"):
            try:
                with open(meta_file) as f:
                    data = json.load(f)
                
                # Aplicar filtros
                if algorithm and data['algorithm']['name'] != algorithm:
                    continue
                
                if problem and data['problem']['instance'] != problem:
                    continue
                
                if tags and not any(tag in data['tags'] for tag in tags):
                    continue
                
                if date_from or date_to:
                    exp_date = datetime.fromisoformat(data['system']['timestamp'])
                    if date_from and exp_date < date_from:
                        continue
                    if date_to and exp_date > date_to:
                        continue
                
                # Reconstruir objeto
                # (Simplificado, en producción usar deserialización completa)
                experiments.append(data)
                
            except Exception as e:
                print(f"Error loading {meta_file}: {e}")
        
        return experiments
    
    def generate_traceability_report(self,
                                   experiment_ids: List[str],
                                   output_path: Optional[Path] = None) -> str:
        """
        Genera reporte de trazabilidad para experimentos.
        
        Args:
            experiment_ids: IDs de experimentos a incluir
            output_path: Ruta para guardar reporte
            
        Returns:
            Reporte en formato markdown
        """
        report = "# Experiment Traceability Report\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        for exp_id in experiment_ids:
            try:
                exp = self.load_experiment(exp_id)
                
                report += f"## Experiment: {exp_id}\n\n"
                report += f"**Description:** {exp.description}\n"
                report += f"**Tags:** {', '.join(exp.tags)}\n\n"
                
                # Sistema
                report += "### System Information\n"
                report += f"- **Host:** {exp.system.hostname}\n"
                report += f"- **User:** {exp.system.username}\n"
                report += f"- **Platform:** {exp.system.platform['system']} {exp.system.platform['release']}\n"
                report += f"- **Python:** {exp.system.platform['python_version']}\n\n"
                
                # Algoritmo
                report += "### Algorithm Configuration\n"
                report += f"- **Name:** {exp.algorithm.name} v{exp.algorithm.version}\n"
                report += f"- **Seed:** {exp.algorithm.random_seed}\n"
                report += "- **Parameters:**\n"
                for k, v in exp.algorithm.parameters.items():
                    report += f"  - {k}: {v}\n"
                report += "\n"
                
                # Problema
                report += "### Problem Information\n"
                report += f"- **Type:** {exp.problem.type}\n"
                report += f"- **Instance:** {exp.problem.instance}\n"
                if exp.problem.optimal_value:
                    report += f"- **Optimal:** {exp.problem.optimal_value}\n"
                report += "\n"
                
                # Ejecución
                report += "### Execution Details\n"
                report += f"- **Start:** {exp.execution.start_time}\n"
                report += f"- **End:** {exp.execution.end_time}\n"
                report += f"- **Duration:** {exp.execution.duration_seconds:.2f}s\n"
                report += f"- **Iterations:** {exp.execution.iterations_completed}\n\n"
                
                # Resultado
                if exp.result:
                    report += "### Results\n"
                    report += f"- **Best Fitness:** {exp.result.best_fitness}\n"
                    if exp.result.quality_indicators:
                        report += "- **Quality Indicators:**\n"
                        for k, v in exp.result.quality_indicators.items():
                            report += f"  - {k}: {v:.4f}\n"
                    report += "\n"
                
                # Reproducibilidad
                report += "### Reproducibility Information\n"
                report += f"- **Base Seed:** {exp.reproducibility.get('base_seed')}\n"
                report += f"- **Algorithm Seed:** {exp.reproducibility.get('algorithm_seed')}\n"
                report += f"- **Checksum:** {exp.provenance.get('checksum')}\n\n"
                
                report += "---\n\n"
                
            except Exception as e:
                report += f"## Error loading experiment {exp_id}: {e}\n\n"
        
        if output_path:
            output_path.write_text(report)
        
        return report
    
    def _get_algorithm_version(self, algorithm_name: str) -> str:
        """Obtiene versión del algoritmo."""
        # En producción, esto podría leer de __version__ o git
        return "1.0.0"
    
    def _create_problem_metadata(self, instance: str) -> ProblemMetadata:
        """Crea metadatos del problema."""
        from utils.benchmarking import OPTIMAL_VALUES
        
        return ProblemMetadata(
            type="VRP",
            instance=instance,
            dimensions={
                'nodes': self._extract_nodes_from_instance(instance),
                'vehicles': self._extract_vehicles_from_instance(instance)
            },
            constraints={
                'capacity': True,
                'time_windows': False,
                'pickups_deliveries': False
            },
            optimal_value=OPTIMAL_VALUES.get(instance)
        )
    
    def _extract_nodes_from_instance(self, instance: str) -> int:
        """Extrae número de nodos del nombre de instancia."""
        import re
        match = re.search(r'n(\d+)', instance)
        return int(match.group(1)) if match else 0
    
    def _extract_vehicles_from_instance(self, instance: str) -> int:
        """Extrae número de vehículos del nombre de instancia."""
        import re
        match = re.search(r'k(\d+)', instance)
        return int(match.group(1)) if match else 0
    
    def _calculate_improvement(self, experiment: ExperimentMetadata) -> float:
        """Calcula mejora durante la ejecución."""
        if not experiment.execution.convergence_history:
            return 0.0
        
        first = experiment.execution.convergence_history[0]['best_fitness']
        last = experiment.execution.convergence_history[-1]['best_fitness']
        
        if first == 0:
            return 0.0
        
        return ((first - last) / first) * 100
    
    def _calculate_quality_indicators(self, 
                                    experiment: ExperimentMetadata,
                                    result: Dict[str, Any]) -> Dict[str, float]:
        """Calcula indicadores de calidad."""
        indicators = {}
        
        # Gap con respecto al óptimo
        if experiment.problem.optimal_value:
            gap = ((result['best_fitness'] - experiment.problem.optimal_value) / 
                   experiment.problem.optimal_value * 100)
            indicators['gap_to_optimal'] = gap
        
        # Convergencia
        if experiment.execution.convergence_history:
            # Tasa de convergencia
            history = [p['best_fitness'] for p in experiment.execution.convergence_history]
            improvements = [history[i-1] - history[i] for i in range(1, len(history))]
            indicators['avg_improvement_rate'] = np.mean(improvements) if improvements else 0
            
            # Estabilidad
            last_quarter = history[int(len(history)*0.75):]
            indicators['final_stability'] = np.std(last_quarter) if last_quarter else 0
        
        return indicators
    
    def _save_metadata(self, experiment: ExperimentMetadata):
        """Guarda metadatos en archivo."""
        filename = f"{experiment.experiment_id}_metadata.json"
        filepath = self.storage_path / filename
        
        # Convertir a dict según nivel
        data = experiment.to_dict(self.metadata_level)
        
        # Guardar
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Carga metadatos de un experimento."""
        filename = f"{experiment_id}_metadata.json"
        filepath = self.storage_path / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Experiment {experiment_id} not found")
        
        with open(filepath) as f:
            return json.load(f)


# Imports necesarios
import os
import traceback


def create_metadata_manager(**kwargs) -> MetadataManager:
    """Factory function para crear MetadataManager."""
    return MetadataManager(**kwargs)