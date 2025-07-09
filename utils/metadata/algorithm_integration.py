"""
Integración de metadatos y trazabilidad con el framework de algoritmos.

Proporciona decoradores y mixins para añadir capacidades de metadata
y trazabilidad a los algoritmos existentes.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, Type
from datetime import datetime
import inspect

from algorithms.core.base import MetaheuristicAlgorithm, Individual
from utils.metadata.metadata_manager import MetadataManager, MetadataLevel
from utils.metadata.traceability import ExperimentTracer, EventType
from utils.reproducibility import ReproducibilityManager


class MetadataTrackingMixin:
    """
    Mixin para añadir capacidades de tracking de metadatos a algoritmos.
    
    Este mixin se puede añadir a cualquier algoritmo para obtener
    automáticamente capacidades de metadata y trazabilidad.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa el mixin."""
        # Extraer configuración de metadata si existe
        self._metadata_config = kwargs.pop('metadata_config', {})
        self._enable_metadata = self._metadata_config.get('enable', True)
        self._metadata_level = self._metadata_config.get('level', MetadataLevel.STANDARD)
        
        # Inicializar clase padre
        super().__init__(*args, **kwargs)
        
        # Configurar metadata y trazabilidad si está habilitado
        if self._enable_metadata:
            self._setup_metadata_tracking()
    
    def _setup_metadata_tracking(self):
        """Configura el sistema de tracking de metadatos."""
        # Crear gestor de metadatos
        self._metadata_manager = MetadataManager(
            metadata_level=self._metadata_level,
            auto_capture=True
        )
        
        # Crear experimento
        self._experiment_metadata = self._metadata_manager.create_experiment(
            experiment_type="algorithm_run",
            algorithm_name=self.__class__.__name__,
            problem_instance=getattr(self.problem, 'instance_name', 'unknown'),
            parameters={
                'population_size': self.population_size,
                'max_iterations': self.max_iterations,
                'seed': self.seed
            },
            description=f"Automated run of {self.__class__.__name__}",
            tags=['automated', 'tracked']
        )
        
        # Crear trazador
        self._tracer = ExperimentTracer(
            metadata_manager=self._metadata_manager,
            auto_trace=True,
            trace_level=self._metadata_config.get('trace_level', 'standard')
        )
        
        # Capturar parámetros adicionales del algoritmo
        self._capture_algorithm_parameters()
    
    def _capture_algorithm_parameters(self):
        """Captura parámetros específicos del algoritmo."""
        # Obtener todos los atributos que parecen parámetros
        params = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                try:
                    value = getattr(self, attr_name)
                    # Solo incluir tipos básicos
                    if isinstance(value, (int, float, str, bool, list, dict)):
                        params[attr_name] = value
                except:
                    pass
        
        # Actualizar metadatos del algoritmo
        if hasattr(self, '_experiment_metadata'):
            self._experiment_metadata.algorithm.hyperparameters = params
    
    def run(self, *args, **kwargs):
        """Ejecuta el algoritmo con tracking de metadatos."""
        if not self._enable_metadata:
            # Si metadata está deshabilitado, ejecutar normalmente
            return super().run(*args, **kwargs)
        
        # Ejecutar con contexto de trazabilidad
        with self._tracer.trace_experiment(self._experiment_metadata.experiment_id):
            try:
                # Trazar inicio de ejecución
                self._tracer.trace_event(
                    EventType.EXPERIMENT_START,
                    component=self.__class__.__name__,
                    data={
                        'algorithm': self.__class__.__name__,
                        'parameters': self._experiment_metadata.algorithm.parameters
                    }
                )
                
                # Ejecutar algoritmo
                result = super().run(*args, **kwargs)
                
                # Finalizar experimento con éxito
                self._metadata_manager.finalize_experiment(
                    self._experiment_metadata.experiment_id,
                    result
                )
                
                return result
                
            except Exception as e:
                # Trazar error
                self._tracer.trace_error(e, component=self.__class__.__name__)
                
                # Finalizar experimento con error
                self._metadata_manager.finalize_experiment(
                    self._experiment_metadata.experiment_id,
                    result={},
                    error=e
                )
                
                raise
    
    def _on_iteration_complete(self, iteration: int, metrics: Dict[str, Any]):
        """
        Callback para cuando se completa una iteración.
        
        Los algoritmos deben llamar este método al final de cada iteración.
        """
        if self._enable_metadata and hasattr(self, '_tracer'):
            self._tracer.trace_iteration(iteration, metrics)
    
    def _on_solution_found(self, solution: Any, fitness: float, iteration: int):
        """
        Callback para cuando se encuentra una nueva solución.
        
        Los algoritmos deben llamar este método cuando encuentran una mejor solución.
        """
        if self._enable_metadata and hasattr(self, '_tracer'):
            is_improvement = True  # Asumir que es mejora
            if hasattr(self, '_best_fitness_history') and self._best_fitness_history:
                is_improvement = fitness < self._best_fitness_history[-1]
            
            self._tracer.trace_solution(solution, fitness, iteration, is_improvement)
    
    def create_checkpoint(self, name: str, data: Any = None) -> Optional[str]:
        """
        Crea un checkpoint del estado actual.
        
        Args:
            name: Nombre del checkpoint
            data: Datos adicionales a guardar
            
        Returns:
            ID del checkpoint si se creó
        """
        if self._enable_metadata and hasattr(self, '_tracer'):
            checkpoint_data = {
                'iteration': getattr(self, 'current_iteration', 0),
                'population': getattr(self, 'population', None),
                'best_solution': getattr(self, 'best_solution', None),
                'custom_data': data
            }
            
            return self._tracer.create_checkpoint(
                checkpoint_data,
                name,
                metadata={'algorithm': self.__class__.__name__}
            )
        
        return None
    
    def annotate(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Añade anotación al experimento.
        
        Args:
            message: Mensaje de anotación
            data: Datos adicionales
        """
        if self._enable_metadata and hasattr(self, '_tracer'):
            self._tracer.annotate(message, data)


def track_execution(method: Callable) -> Callable:
    """
    Decorador para trackear la ejecución de métodos.
    
    Registra automáticamente el inicio, fin y métricas de un método.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # Verificar si el tracking está habilitado
        if not getattr(self, '_enable_metadata', False):
            return method(self, *args, **kwargs)
        
        # Obtener tracer si existe
        tracer = getattr(self, '_tracer', None)
        if not tracer:
            return method(self, *args, **kwargs)
        
        # Trazar inicio
        method_name = method.__name__
        start_time = time.time()
        
        tracer.trace_event(
            EventType.ITERATION_START if 'iteration' in method_name else EventType.POPULATION_UPDATE,
            component=self.__class__.__name__,
            data={
                'method': method_name,
                'args': str(args)[:100],  # Resumen de argumentos
                'start_time': datetime.now().isoformat()
            }
        )
        
        try:
            # Ejecutar método
            result = method(self, *args, **kwargs)
            
            # Trazar fin exitoso
            end_time = time.time()
            tracer.trace_event(
                EventType.ITERATION_END if 'iteration' in method_name else EventType.POPULATION_UPDATE,
                component=self.__class__.__name__,
                data={
                    'method': method_name,
                    'duration': end_time - start_time,
                    'success': True
                }
            )
            
            return result
            
        except Exception as e:
            # Trazar error
            tracer.trace_error(
                e,
                component=self.__class__.__name__,
                context={'method': method_name}
            )
            raise
    
    return wrapper


def track_population_changes(method: Callable) -> Callable:
    """
    Decorador específico para trackear cambios en la población.
    
    Registra estadísticas de la población antes y después del método.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # Verificar si el tracking está habilitado
        if not getattr(self, '_enable_metadata', False):
            return method(self, *args, **kwargs)
        
        tracer = getattr(self, '_tracer', None)
        if not tracer or not hasattr(self, 'population'):
            return method(self, *args, **kwargs)
        
        # Capturar estado antes
        before_stats = _calculate_population_stats(self.population)
        
        # Ejecutar método
        result = method(self, *args, **kwargs)
        
        # Capturar estado después
        after_stats = _calculate_population_stats(self.population)
        
        # Trazar cambios
        tracer.trace_event(
            EventType.POPULATION_UPDATE,
            component=self.__class__.__name__,
            data={
                'method': method.__name__,
                'before': before_stats,
                'after': after_stats,
                'changes': {
                    'fitness_improvement': after_stats['best_fitness'] - before_stats['best_fitness'],
                    'diversity_change': after_stats['diversity'] - before_stats['diversity']
                }
            }
        )
        
        return result
    
    return wrapper


def _calculate_population_stats(population: list) -> Dict[str, float]:
    """Calcula estadísticas de una población."""
    if not population:
        return {
            'size': 0,
            'best_fitness': float('inf'),
            'mean_fitness': float('inf'),
            'diversity': 0.0
        }
    
    fitnesses = [ind.fitness for ind in population]
    
    # Calcular diversidad (simplificado)
    unique_fitnesses = len(set(fitnesses))
    diversity = unique_fitnesses / len(fitnesses) if fitnesses else 0
    
    return {
        'size': len(population),
        'best_fitness': min(fitnesses),
        'mean_fitness': sum(fitnesses) / len(fitnesses),
        'worst_fitness': max(fitnesses),
        'diversity': diversity
    }


class TrackedMetaheuristicAlgorithm(MetadataTrackingMixin, MetaheuristicAlgorithm):
    """
    Clase base para algoritmos con tracking automático de metadatos.
    
    Los algoritmos pueden heredar de esta clase para obtener automáticamente
    capacidades de metadata y trazabilidad.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa algoritmo con tracking."""
        super().__init__(*args, **kwargs)
        
        # Inicializar historial para tracking
        self._best_fitness_history = []
        self._iteration_times = []
    
    @track_execution
    def run(self):
        """Ejecuta el algoritmo con tracking completo."""
        # Implementación base que los algoritmos pueden sobrescribir
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            start_time = time.time()
            
            # Ejecutar iteración (debe ser implementado por subclases)
            self._execute_iteration(iteration)
            
            # Calcular métricas
            iteration_time = time.time() - start_time
            self._iteration_times.append(iteration_time)
            
            # Obtener mejor fitness
            best_fitness = min(ind.fitness for ind in self.population)
            self._best_fitness_history.append(best_fitness)
            
            # Trackear iteración
            self._on_iteration_complete(iteration, {
                'best_fitness': best_fitness,
                'mean_fitness': sum(ind.fitness for ind in self.population) / len(self.population),
                'iteration_time': iteration_time
            })
            
            # Verificar si hay mejora
            if len(self._best_fitness_history) > 1 and best_fitness < self._best_fitness_history[-2]:
                best_individual = min(self.population, key=lambda x: x.fitness)
                self._on_solution_found(best_individual, best_fitness, iteration)
        
        # Preparar resultado
        best_individual = min(self.population, key=lambda x: x.fitness)
        return {
            'best_solution': best_individual,
            'best_fitness': best_individual.fitness,
            'convergence_history': self._best_fitness_history,
            'execution_times': self._iteration_times,
            'final_population': self.population
        }
    
    def _execute_iteration(self, iteration: int):
        """
        Ejecuta una iteración del algoritmo.
        
        Debe ser implementado por las subclases.
        """
        raise NotImplementedError("Subclasses must implement _execute_iteration")


def enable_metadata_tracking(algorithm_class: Type[MetaheuristicAlgorithm],
                           metadata_config: Optional[Dict[str, Any]] = None) -> Type[MetaheuristicAlgorithm]:
    """
    Añade capacidades de metadata tracking a una clase de algoritmo existente.
    
    Args:
        algorithm_class: Clase de algoritmo a mejorar
        metadata_config: Configuración de metadata
        
    Returns:
        Nueva clase con capacidades de tracking
    """
    # Crear nueva clase que hereda de mixin y algoritmo original
    class TrackedAlgorithm(MetadataTrackingMixin, algorithm_class):
        """Versión con tracking del algoritmo original."""
        
        def __init__(self, *args, **kwargs):
            # Inyectar configuración de metadata
            if metadata_config:
                kwargs['metadata_config'] = metadata_config
            super().__init__(*args, **kwargs)
    
    # Preservar nombre y documentación
    TrackedAlgorithm.__name__ = f"Tracked{algorithm_class.__name__}"
    TrackedAlgorithm.__doc__ = f"{algorithm_class.__doc__}\n\nEnhanced with metadata tracking."
    
    return TrackedAlgorithm


# Ejemplo de uso con un algoritmo existente
def create_tracked_algorithm(algorithm_name: str,
                           problem: Any,
                           **kwargs) -> MetaheuristicAlgorithm:
    """
    Crea una instancia de algoritmo con tracking habilitado.
    
    Args:
        algorithm_name: Nombre del algoritmo
        problem: Instancia del problema
        **kwargs: Parámetros del algoritmo
        
    Returns:
        Instancia del algoritmo con tracking
    """
    from algorithms import ALGORITHMS
    
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"Algorithm {algorithm_name} not found")
    
    # Obtener clase del algoritmo
    algorithm_class = ALGORITHMS[algorithm_name]
    
    # Crear versión con tracking
    tracked_class = enable_metadata_tracking(
        algorithm_class,
        metadata_config={
            'enable': True,
            'level': MetadataLevel.STANDARD,
            'trace_level': 'standard'
        }
    )
    
    # Crear instancia
    return tracked_class(problem=problem, **kwargs)