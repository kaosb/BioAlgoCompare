"""
Tests para el sistema de manejo de errores.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from utils.error_handling import (
    AlgorithmError, InitializationError, ConvergenceError,
    ParameterError, PopulationError, FitnessError, NumericError,
    validate_parameters, handle_errors, check_numeric_stability,
    ErrorRecoveryMixin, SafeAlgorithmWrapper, create_safe_algorithm
)
from algorithms.mixins.error_handling import ErrorHandlingMixin, with_error_handling


class TestCustomExceptions:
    """Tests para excepciones personalizadas."""
    
    def test_algorithm_error_creation(self):
        """Test creación de AlgorithmError."""
        error = AlgorithmError(
            "Test error",
            algorithm="TestAlgo",
            iteration=10,
            details={'key': 'value'}
        )
        
        assert str(error) == "[TestAlgo] Test error (iteration 10)"
        assert error.algorithm == "TestAlgo"
        assert error.iteration == 10
        assert error.details == {'key': 'value'}
        assert hasattr(error, 'timestamp')
    
    def test_error_to_dict(self):
        """Test conversión de error a diccionario."""
        error = InitializationError("Init failed", algorithm="TestAlgo")
        error_dict = error.to_dict()
        
        assert error_dict['error_type'] == 'InitializationError'
        assert error_dict['algorithm'] == 'TestAlgo'
        assert 'timestamp' in error_dict
    
    def test_specific_error_types(self):
        """Test tipos específicos de error."""
        errors = [
            InitializationError("Init error"),
            ConvergenceError("Convergence error"),
            ParameterError("Parameter error"),
            PopulationError("Population error"),
            FitnessError("Fitness error"),
            NumericError("Numeric error")
        ]
        
        for error in errors:
            assert isinstance(error, AlgorithmError)


class TestValidationDecorators:
    """Tests para decoradores de validación."""
    
    def test_validate_parameters_success(self):
        """Test validación exitosa de parámetros."""
        @validate_parameters(
            x=lambda v: v > 0,
            y=lambda v: 0 <= v <= 1
        )
        def test_func(x, y):
            return x + y
        
        result = test_func(5, 0.5)
        assert result == 5.5
    
    def test_validate_parameters_failure(self):
        """Test fallo en validación de parámetros."""
        @validate_parameters(
            x=lambda v: v > 0
        )
        def test_func(x):
            return x
        
        with pytest.raises(ParameterError) as exc_info:
            test_func(-1)
        
        assert "Invalid value for parameter 'x': -1" in str(exc_info.value)
    
    def test_handle_errors_decorator(self):
        """Test decorador de manejo de errores."""
        @handle_errors(algorithm_name="TestAlgo", fallback_value=0, reraise=False)
        def test_func(self):
            raise ValueError("Test error")
        
        # Mock self
        mock_self = Mock()
        result = test_func(mock_self)
        assert result == 0
    
    def test_handle_errors_numeric(self):
        """Test manejo de errores numéricos."""
        @handle_errors(reraise=True)
        def test_func(self):
            return 1 / 0
        
        mock_self = Mock()
        mock_self.__class__.__name__ = "TestClass"
        
        with pytest.raises(NumericError):
            test_func(mock_self)


class TestNumericStability:
    """Tests para verificación de estabilidad numérica."""
    
    def test_check_numeric_stability_scalar(self):
        """Test estabilidad numérica con escalares."""
        # Valores válidos
        check_numeric_stability(1.0)
        check_numeric_stability(0.0)
        check_numeric_stability(-1.0)
        
        # NaN
        with pytest.raises(NumericError) as exc_info:
            check_numeric_stability(np.nan)
        assert "NaN detected" in str(exc_info.value)
        
        # Inf
        with pytest.raises(NumericError) as exc_info:
            check_numeric_stability(np.inf)
        assert "Inf detected" in str(exc_info.value)
    
    def test_check_numeric_stability_array(self):
        """Test estabilidad numérica con arrays."""
        # Array válido
        check_numeric_stability(np.array([1.0, 2.0, 3.0]))
        
        # Array con NaN
        with pytest.raises(NumericError):
            check_numeric_stability(np.array([1.0, np.nan, 3.0]))
        
        # Array con Inf
        with pytest.raises(NumericError):
            check_numeric_stability(np.array([1.0, np.inf, 3.0]))
    
    def test_check_numeric_stability_bounds(self):
        """Test verificación de límites."""
        # Dentro de límites
        check_numeric_stability(5.0, min_value=0.0, max_value=10.0)
        
        # Bajo el mínimo
        with pytest.raises(NumericError) as exc_info:
            check_numeric_stability(-1.0, min_value=0.0)
        assert "below 0.0" in str(exc_info.value)
        
        # Sobre el máximo
        with pytest.raises(NumericError) as exc_info:
            check_numeric_stability(11.0, max_value=10.0)
        assert "above 10.0" in str(exc_info.value)


class TestErrorRecoveryMixin:
    """Tests para ErrorRecoveryMixin."""
    
    class TestAlgorithm(ErrorRecoveryMixin):
        def __init__(self):
            super().__init__()
            self.population = []
            
        def initialize_population(self):
            self.population = [1, 2, 3]
    
    def test_safe_execute_success(self):
        """Test ejecución segura exitosa."""
        algo = self.TestAlgorithm()
        
        def test_func(x):
            return x * 2
        
        result = algo.safe_execute(test_func, 5)
        assert result == 10
    
    def test_safe_execute_with_recovery(self):
        """Test ejecución segura con recuperación."""
        algo = self.TestAlgorithm()
        
        def failing_func():
            raise PopulationError("Population error")
        
        # Primera vez falla pero se recupera
        with pytest.raises(AlgorithmError):
            algo.safe_execute(failing_func)
        
        # Verificar que se intentó recuperar
        assert len(algo.error_history) > 0
    
    def test_max_retries(self):
        """Test límite de reintentos."""
        algo = self.TestAlgorithm()
        algo.max_retries = 2
        
        def always_failing():
            raise PopulationError("Always fails")
        
        with pytest.raises(AlgorithmError) as exc_info:
            algo.safe_execute(always_failing)
        
        assert "Max retries (2) reached" in str(exc_info.value)


class TestErrorHandlingMixin:
    """Tests para ErrorHandlingMixin."""
    
    class TestAlgorithmWithMixin(ErrorHandlingMixin):
        def __init__(self, **kwargs):
            self.problem = Mock()
            self.problem.capacity = 100  # Set valid capacity
            self.problem.distance_matrix = np.array([[0, 1], [1, 0]])  # Valid distance matrix
            self.population_size = 10
            self.max_iterations = 100
            self.population = []
            super().__init__(**kwargs)
            
        def _create_individual(self):
            individual = Mock()
            individual.fitness.return_value = 100.0
            individual.position = np.random.rand(5)
            return individual
    
    def test_initialization(self):
        """Test inicialización del mixin."""
        algo = self.TestAlgorithmWithMixin()
        
        assert algo.error_tolerance == 1e-10
        assert algo.max_consecutive_errors == 5
        assert algo.enable_recovery == True
        assert len(algo.error_history) == 0
    
    def test_validate_algorithm_state(self):
        """Test validación de estado del algoritmo."""
        algo = self.TestAlgorithmWithMixin()
        algo.validate_algorithm_state()  # No debe lanzar excepción
        
        # Quitar atributo requerido
        delattr(algo, 'problem')
        with pytest.raises(InitializationError):
            algo.validate_algorithm_state()
    
    def test_validate_population(self):
        """Test validación de población."""
        algo = self.TestAlgorithmWithMixin()
        
        # Población vacía
        with pytest.raises(PopulationError) as exc_info:
            algo.validate_population()
        assert "Population is empty" in str(exc_info.value)
        
        # Población válida
        algo.population = [algo._create_individual() for _ in range(10)]
        algo.validate_population()  # No debe lanzar excepción
    
    def test_safe_fitness_evaluation(self):
        """Test evaluación segura de fitness."""
        algo = self.TestAlgorithmWithMixin()
        
        # Individuo válido
        individual = Mock()
        individual.fitness.return_value = 50.0
        
        fitness = algo.safe_fitness_evaluation(individual)
        assert fitness == 50.0
        
        # Individuo con error
        bad_individual = Mock()
        bad_individual.fitness.side_effect = ValueError("Fitness error")
        
        fitness = algo.safe_fitness_evaluation(bad_individual)
        assert fitness == float('inf')
        assert len(algo.error_history) > 0
    
    def test_safe_operation(self):
        """Test operación segura."""
        algo = self.TestAlgorithmWithMixin()
        
        # Operación exitosa
        def good_op(x):
            return x * 2
        
        result = algo.safe_operation(good_op, 5)
        assert result == 10
        
        # Operación con error
        def bad_op():
            raise ValueError("Operation failed")
        
        result = algo.safe_operation(bad_op, error_type='general')
        assert result is None  # Valor fallback
        assert algo.consecutive_errors == 1
    
    def test_recovery_strategies(self):
        """Test estrategias de recuperación."""
        algo = self.TestAlgorithmWithMixin()
        
        # Test recuperación de población
        algo._recover_population(PopulationError("Test"))
        assert len(algo.population) == 10
        
        # Test recuperación numérica
        algo.population = [algo._create_individual() for _ in range(5)]
        algo.population[0].position = np.array([np.nan, np.inf, 1.0])
        
        algo._recover_numeric(NumericError("Test"))
        
        # Verificar que se corrigieron los valores
        assert not np.any(np.isnan(algo.population[0].position))
        assert not np.any(np.isinf(algo.population[0].position))
    
    def test_error_summary(self):
        """Test resumen de errores."""
        algo = self.TestAlgorithmWithMixin()
        
        # Generar algunos errores
        algo.safe_operation(lambda: 1/0, error_type='numeric')
        algo.safe_operation(lambda: [][1], error_type='general')
        
        summary = algo.get_error_summary()
        
        assert summary['total_errors'] == 2
        assert len(summary['error_types']) > 0


class TestSafeAlgorithmWrapper:
    """Tests para SafeAlgorithmWrapper."""
    
    class MockAlgorithm:
        def __init__(self, problem, **kwargs):
            self.problem = problem
            self.population_size = kwargs.get('population_size', 10)
            self.max_iterations = kwargs.get('max_iterations', 100)
            
        def run(self):
            return "Success"
    
    class FailingAlgorithm:
        def __init__(self, problem, **kwargs):
            raise ValueError("Initialization failed")
    
    def test_successful_execution(self):
        """Test ejecución exitosa con wrapper."""
        wrapper = SafeAlgorithmWrapper(
            self.MockAlgorithm,
            problem=Mock(),
            population_size=20
        )
        
        result = wrapper.run()
        assert result == "Success"
    
    def test_initialization_failure(self):
        """Test fallo en inicialización."""
        wrapper = SafeAlgorithmWrapper(
            self.FailingAlgorithm,
            problem=Mock()
        )
        
        result = wrapper.run()
        assert result is None
        assert len(wrapper.error_log) > 0
    
    def test_create_safe_algorithm(self):
        """Test función helper create_safe_algorithm."""
        safe_algo = create_safe_algorithm(
            self.MockAlgorithm,
            problem=Mock()
        )
        
        assert isinstance(safe_algo, SafeAlgorithmWrapper)
        result = safe_algo.run()
        assert result == "Success"


class TestWithErrorHandlingDecorator:
    """Tests para decorador with_error_handling."""
    
    class AlgorithmWithDecorator(ErrorHandlingMixin):
        def __init__(self):
            super().__init__()
            
        @with_error_handling
        def risky_operation(self, x):
            if x < 0:
                raise ValueError("Negative value")
            return x * 2
    
    def test_decorator_success(self):
        """Test decorador con operación exitosa."""
        algo = self.AlgorithmWithDecorator()
        result = algo.risky_operation(5)
        assert result == 10
    
    def test_decorator_with_error(self):
        """Test decorador con error."""
        algo = self.AlgorithmWithDecorator()
        result = algo.risky_operation(-1)
        assert result is None  # Valor fallback
        assert algo.total_errors == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])