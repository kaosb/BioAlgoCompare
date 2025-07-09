"""
Sistema de manejo robusto de errores para algoritmos.

Este módulo proporciona excepciones personalizadas, decoradores
y utilidades para el manejo consistente de errores en toda la
plataforma de algoritmos bio-inspirados.
"""

import functools
import logging
import traceback
import warnings
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime
import numpy as np


# Configurar logging
logger = logging.getLogger(__name__)


class AlgorithmError(Exception):
    """Excepción base para errores en algoritmos."""
    
    def __init__(self, message: str, algorithm: Optional[str] = None,
                 iteration: Optional[int] = None, details: Optional[Dict] = None):
        """
        Inicializa excepción de algoritmo.
        
        Args:
            message: Mensaje de error
            algorithm: Nombre del algoritmo
            iteration: Iteración donde ocurrió el error
            details: Detalles adicionales del error
        """
        self.algorithm = algorithm
        self.iteration = iteration
        self.details = details or {}
        self.timestamp = datetime.now()
        
        # Construir mensaje completo
        full_message = message
        if algorithm:
            full_message = f"[{algorithm}] {full_message}"
        if iteration is not None:
            full_message = f"{full_message} (iteration {iteration})"
        
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario."""
        return {
            'error_type': self.__class__.__name__,
            'message': str(self),
            'algorithm': self.algorithm,
            'iteration': self.iteration,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class InitializationError(AlgorithmError):
    """Error durante la inicialización del algoritmo."""
    pass


class ConvergenceError(AlgorithmError):
    """Error relacionado con la convergencia del algoritmo."""
    pass


class ParameterError(AlgorithmError):
    """Error en parámetros del algoritmo."""
    pass


class PopulationError(AlgorithmError):
    """Error relacionado con la población."""
    pass


class FitnessError(AlgorithmError):
    """Error al calcular fitness."""
    pass


class OperatorError(AlgorithmError):
    """Error en operadores del algoritmo."""
    pass


class ConstraintViolationError(AlgorithmError):
    """Error por violación de restricciones."""
    pass


class NumericError(AlgorithmError):
    """Error numérico (overflow, NaN, etc.)."""
    pass


class TimeoutError(AlgorithmError):
    """Error por tiempo de ejecución excedido."""
    pass


class MemoryError(AlgorithmError):
    """Error por memoria insuficiente."""
    pass


def validate_parameters(**param_rules) -> Callable:
    """
    Decorador para validar parámetros de funciones.
    
    Args:
        **param_rules: Reglas de validación para cada parámetro
        
    Example:
        @validate_parameters(
            population_size=lambda x: x > 0,
            mutation_rate=lambda x: 0 <= x <= 1
        )
        def my_function(population_size, mutation_rate):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener nombres de parámetros de la función
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validar cada parámetro
            for param_name, validator in param_rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        if not validator(value):
                            raise ParameterError(
                                f"Invalid value for parameter '{param_name}': {value}",
                                details={'parameter': param_name, 'value': value}
                            )
                    except Exception as e:
                        raise ParameterError(
                            f"Error validating parameter '{param_name}': {str(e)}",
                            details={'parameter': param_name, 'value': value}
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def handle_errors(algorithm_name: Optional[str] = None,
                  fallback_value: Any = None,
                  log_errors: bool = True,
                  reraise: bool = True) -> Callable:
    """
    Decorador para manejo robusto de errores en métodos de algoritmos.
    
    Args:
        algorithm_name: Nombre del algoritmo para logging
        fallback_value: Valor a retornar en caso de error
        log_errors: Si se deben loggear los errores
        reraise: Si se debe relanzar la excepción después de manejarla
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                # Intentar obtener nombre del algoritmo si no se proporciona
                algo_name = algorithm_name or getattr(self, '__class__', type(self)).__name__
                
                # Ejecutar función
                return func(self, *args, **kwargs)
                
            except AlgorithmError:
                # Re-lanzar errores de algoritmo con información adicional
                raise
                
            except (ValueError, TypeError) as e:
                # Convertir a ParameterError
                error = ParameterError(
                    f"Parameter error in {func.__name__}: {str(e)}",
                    algorithm=algo_name,
                    iteration=getattr(self, 'current_iteration', None)
                )
                
                if log_errors:
                    logger.error(f"{error} - Traceback: {traceback.format_exc()}")
                
                if reraise:
                    raise error
                return fallback_value
                
            except (FloatingPointError, ZeroDivisionError, OverflowError) as e:
                # Convertir a NumericError
                error = NumericError(
                    f"Numeric error in {func.__name__}: {str(e)}",
                    algorithm=algo_name,
                    iteration=getattr(self, 'current_iteration', None)
                )
                
                if log_errors:
                    logger.error(f"{error} - Traceback: {traceback.format_exc()}")
                
                if reraise:
                    raise error
                return fallback_value
                
            except Exception as e:
                # Cualquier otro error
                error = AlgorithmError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    algorithm=algo_name,
                    iteration=getattr(self, 'current_iteration', None),
                    details={'error_type': type(e).__name__}
                )
                
                if log_errors:
                    logger.error(f"{error} - Traceback: {traceback.format_exc()}")
                
                if reraise:
                    raise error
                return fallback_value
        
        return wrapper
    return decorator


def check_numeric_stability(value: Union[float, np.ndarray],
                          name: str = "value",
                          check_nan: bool = True,
                          check_inf: bool = True,
                          min_value: Optional[float] = None,
                          max_value: Optional[float] = None) -> None:
    """
    Verifica estabilidad numérica de valores.
    
    Args:
        value: Valor o array a verificar
        name: Nombre del valor para mensajes de error
        check_nan: Verificar NaN
        check_inf: Verificar infinitos
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        
    Raises:
        NumericError: Si se detecta inestabilidad numérica
    """
    if isinstance(value, np.ndarray):
        if check_nan and np.any(np.isnan(value)):
            raise NumericError(f"NaN detected in {name}")
        
        if check_inf and np.any(np.isinf(value)):
            raise NumericError(f"Inf detected in {name}")
        
        if min_value is not None and np.any(value < min_value):
            raise NumericError(f"{name} contains values below {min_value}")
        
        if max_value is not None and np.any(value > max_value):
            raise NumericError(f"{name} contains values above {max_value}")
    else:
        if check_nan and np.isnan(value):
            raise NumericError(f"NaN detected in {name}")
        
        if check_inf and np.isinf(value):
            raise NumericError(f"Inf detected in {name}")
        
        if min_value is not None and value < min_value:
            raise NumericError(f"{name} ({value}) is below {min_value}")
        
        if max_value is not None and value > max_value:
            raise NumericError(f"{name} ({value}) is above {max_value}")


class ErrorRecoveryMixin:
    """
    Mixin que proporciona capacidades de recuperación de errores.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa sistema de recuperación."""
        super().__init__(*args, **kwargs)
        self.error_history: List[AlgorithmError] = []
        self.max_retries = 3
        self.recovery_strategies = {
            PopulationError: self._recover_from_population_error,
            NumericError: self._recover_from_numeric_error,
            ConvergenceError: self._recover_from_convergence_error
        }
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta función con recuperación automática de errores.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                return func(*args, **kwargs)
                
            except AlgorithmError as e:
                last_error = e
                self.error_history.append(e)
                
                # Buscar estrategia de recuperación
                recovery_func = None
                for error_type, strategy in self.recovery_strategies.items():
                    if isinstance(e, error_type):
                        recovery_func = strategy
                        break
                
                if recovery_func:
                    logger.warning(f"Attempting recovery from {type(e).__name__}")
                    recovery_func(e)
                    retries += 1
                else:
                    # No hay estrategia de recuperación
                    raise
                    
            except Exception as e:
                # Error no manejado
                algo_error = AlgorithmError(
                    f"Unhandled error: {str(e)}",
                    algorithm=getattr(self, '__class__', type(self)).__name__
                )
                self.error_history.append(algo_error)
                raise algo_error
        
        # Máximo de reintentos alcanzado
        raise AlgorithmError(
            f"Max retries ({self.max_retries}) reached. Last error: {last_error}",
            algorithm=getattr(self, '__class__', type(self)).__name__
        )
    
    def _recover_from_population_error(self, error: PopulationError):
        """Recuperación de errores de población."""
        logger.info("Recovering from population error: reinitializing population")
        if hasattr(self, 'initialize_population'):
            self.initialize_population()
    
    def _recover_from_numeric_error(self, error: NumericError):
        """Recuperación de errores numéricos."""
        logger.info("Recovering from numeric error: resetting numeric values")
        
        # Reinicializar población con valores seguros
        if hasattr(self, 'population'):
            for individual in self.population:
                if hasattr(individual, 'position'):
                    # Clip valores a rango seguro
                    individual.position = np.clip(individual.position, -1e6, 1e6)
                    # Reemplazar NaN/Inf
                    individual.position = np.nan_to_num(individual.position, 
                                                      nan=0.0, posinf=1e6, neginf=-1e6)
    
    def _recover_from_convergence_error(self, error: ConvergenceError):
        """Recuperación de errores de convergencia."""
        logger.info("Recovering from convergence error: applying restart strategy")
        
        # Aplicar estrategia de reinicio si está disponible
        if hasattr(self, 'perform_restart') and hasattr(self, 'population'):
            self.population = self.perform_restart(self.population, 
                                                 getattr(self, 'current_iteration', 0))


class SafeAlgorithmWrapper:
    """
    Wrapper que añade manejo robusto de errores a cualquier algoritmo.
    """
    
    def __init__(self, algorithm_class: Type, **kwargs):
        """
        Inicializa wrapper de algoritmo seguro.
        
        Args:
            algorithm_class: Clase del algoritmo a wrappear
            **kwargs: Argumentos para el algoritmo
        """
        self.algorithm_class = algorithm_class
        self.algorithm = None
        self.kwargs = kwargs
        self.error_log = []
        
    def run(self, **run_kwargs) -> Any:
        """
        Ejecuta el algoritmo con manejo robusto de errores.
        
        Args:
            **run_kwargs: Argumentos para el método run
            
        Returns:
            Resultado del algoritmo o None si falla
        """
        try:
            # Inicializar algoritmo
            self.algorithm = self.algorithm_class(**self.kwargs)
            
            # Ejecutar con monitoreo
            return self._monitored_run(**run_kwargs)
            
        except Exception as e:
            # Loggear error
            error = AlgorithmError(
                f"Algorithm failed: {str(e)}",
                algorithm=self.algorithm_class.__name__,
                details={'original_error': str(e), 'type': type(e).__name__}
            )
            self.error_log.append(error)
            logger.error(f"Algorithm execution failed: {error}")
            
            # Intentar recuperación básica
            if hasattr(self, '_fallback_solution'):
                logger.info("Returning fallback solution")
                return self._fallback_solution()
            
            return None
    
    def _monitored_run(self, **kwargs):
        """Ejecuta el algoritmo con monitoreo."""
        # Añadir validaciones y checkpoints
        result = None
        
        try:
            # Validar estado inicial
            self._validate_initial_state()
            
            # Ejecutar algoritmo
            if hasattr(self.algorithm, 'run'):
                result = self.algorithm.run(**kwargs)
            else:
                result = self.algorithm(**kwargs)
            
            # Validar resultado
            self._validate_result(result)
            
            return result
            
        except Exception as e:
            # Guardar estado para debugging
            self._save_error_state(e)
            raise
    
    def _validate_initial_state(self):
        """Valida el estado inicial del algoritmo."""
        if not self.algorithm:
            raise InitializationError("Algorithm not initialized")
        
        # Validar atributos requeridos
        required_attrs = ['problem', 'population_size', 'max_iterations']
        for attr in required_attrs:
            if not hasattr(self.algorithm, attr):
                raise InitializationError(f"Missing required attribute: {attr}")
    
    def _validate_result(self, result):
        """Valida el resultado del algoritmo."""
        if result is None:
            warnings.warn("Algorithm returned None", RuntimeWarning)
        
        # Validar fitness si es posible
        if hasattr(result, 'fitness'):
            fitness = result.fitness()
            check_numeric_stability(fitness, "result fitness")
    
    def _save_error_state(self, error: Exception):
        """Guarda el estado del error para debugging."""
        state = {
            'error': str(error),
            'error_type': type(error).__name__,
            'algorithm_state': {}
        }
        
        # Capturar estado del algoritmo
        if self.algorithm:
            state['algorithm_state'] = {
                'iteration': getattr(self.algorithm, 'current_iteration', None),
                'best_fitness': getattr(self.algorithm, 'best_fitness', None),
                'population_size': len(getattr(self.algorithm, 'population', []))
            }
        
        self.error_log.append(state)


def create_safe_algorithm(algorithm_class: Type, **kwargs) -> SafeAlgorithmWrapper:
    """
    Crea una versión segura de un algoritmo con manejo robusto de errores.
    
    Args:
        algorithm_class: Clase del algoritmo
        **kwargs: Argumentos para el algoritmo
        
    Returns:
        Wrapper seguro del algoritmo
    """
    return SafeAlgorithmWrapper(algorithm_class, **kwargs)