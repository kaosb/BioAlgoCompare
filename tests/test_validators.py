"""
Tests para el sistema de validación de parámetros.
"""

import pytest
import numpy as np
from algorithms.validators import (
    ValidationError,
    ParameterValidator,
    validate_algorithm_params,
    validate_bounds,
    validate_algorithm_specific_params,
    with_validation
)


class TestParameterValidator:
    """Tests para ParameterValidator."""
    
    def test_validate_positive_integer(self):
        """Test para validación de enteros positivos."""
        # Valores válidos
        assert ParameterValidator.validate_positive_integer(5, "test") == 5
        assert ParameterValidator.validate_positive_integer("10", "test") == 10
        assert ParameterValidator.validate_positive_integer(1, "test", min_value=1) == 1
        
        # Valores inválidos
        with pytest.raises(ValidationError, match="debe ser un número entero"):
            ParameterValidator.validate_positive_integer("abc", "test")
        
        with pytest.raises(ValidationError, match="debe ser >= 1"):
            ParameterValidator.validate_positive_integer(0, "test")
        
        with pytest.raises(ValidationError, match="debe ser >= 5"):
            ParameterValidator.validate_positive_integer(3, "test", min_value=5)
    
    def test_validate_positive_float(self):
        """Test para validación de flotantes positivos."""
        # Valores válidos
        assert ParameterValidator.validate_positive_float(0.5, "test") == 0.5
        assert ParameterValidator.validate_positive_float("0.7", "test") == 0.7
        assert ParameterValidator.validate_positive_float(
            0.0, "test", min_value=0.0, inclusive_min=True
        ) == 0.0
        
        # Con límite máximo
        assert ParameterValidator.validate_positive_float(
            0.8, "test", max_value=1.0
        ) == 0.8
        
        # Valores inválidos
        with pytest.raises(ValidationError, match="debe ser un número"):
            ParameterValidator.validate_positive_float("xyz", "test")
        
        with pytest.raises(ValidationError, match="debe ser > 0.0"):
            ParameterValidator.validate_positive_float(0.0, "test")
        
        with pytest.raises(ValidationError, match="debe ser >= 0.5"):
            ParameterValidator.validate_positive_float(
                0.3, "test", min_value=0.5, inclusive_min=True
            )
        
        with pytest.raises(ValidationError, match="debe ser <= 1.0"):
            ParameterValidator.validate_positive_float(
                1.5, "test", max_value=1.0
            )
    
    def test_validate_probability(self):
        """Test para validación de probabilidades."""
        # Valores válidos
        assert ParameterValidator.validate_probability(0.0, "test") == 0.0
        assert ParameterValidator.validate_probability(0.5, "test") == 0.5
        assert ParameterValidator.validate_probability(1.0, "test") == 1.0
        
        # Valores inválidos
        with pytest.raises(ValidationError, match="debe ser <= 1.0"):
            ParameterValidator.validate_probability(1.1, "test")
        
        with pytest.raises(ValidationError, match="debe ser >= 0.0"):
            ParameterValidator.validate_probability(-0.1, "test")
    
    def test_validate_optional_integer(self):
        """Test para validación de enteros opcionales."""
        # None devuelve el default
        assert ParameterValidator.validate_optional_integer(None, "test") is None
        assert ParameterValidator.validate_optional_integer(
            None, "test", default=42
        ) == 42
        
        # Valores válidos
        assert ParameterValidator.validate_optional_integer(10, "test") == 10
        assert ParameterValidator.validate_optional_integer(
            5, "test", min_value=1
        ) == 5
        
        # Valores inválidos
        with pytest.raises(ValidationError):
            ParameterValidator.validate_optional_integer("abc", "test")


class TestValidateAlgorithmParams:
    """Tests para validate_algorithm_params."""
    
    def test_valid_params(self):
        """Test con parámetros válidos."""
        pop, iters, seed = validate_algorithm_params(30, 100, 42)
        assert pop == 30
        assert iters == 100
        assert seed == 42
        
        # Sin seed
        pop, iters, seed = validate_algorithm_params(50, 200, None)
        assert pop == 50
        assert iters == 200
        assert seed is None
    
    def test_minimum_values(self):
        """Test con valores mínimos."""
        pop, iters, seed = validate_algorithm_params(2, 1, None)
        assert pop == 2
        assert iters == 1
    
    def test_invalid_population(self):
        """Test con población inválida."""
        with pytest.raises(ValidationError, match="population_size debe ser >= 2"):
            validate_algorithm_params(1, 100, None)
        
        with pytest.raises(ValidationError, match="population_size debe ser un número entero"):
            validate_algorithm_params("abc", 100, None)
    
    def test_invalid_iterations(self):
        """Test con iteraciones inválidas."""
        with pytest.raises(ValidationError, match="max_iterations debe ser >= 1"):
            validate_algorithm_params(30, 0, None)
    
    def test_warnings(self, recwarn):
        """Test que se generan warnings para valores pequeños."""
        # Población pequeña
        validate_algorithm_params(5, 100, None)
        assert len(recwarn) == 1
        assert "population_size=5 es muy pequeño" in str(recwarn[0].message)
        
        # Iteraciones pequeñas
        recwarn.clear()
        validate_algorithm_params(30, 5, None)
        assert len(recwarn) == 1
        assert "max_iterations=5 es muy pequeño" in str(recwarn[0].message)


class TestValidateBounds:
    """Tests para validate_bounds."""
    
    def test_valid_bounds(self):
        """Test con límites válidos."""
        lower = np.array([0.0, -1.0, 10.0])
        upper = np.array([1.0, 1.0, 20.0])
        
        l, u = validate_bounds(lower, upper, 3)
        np.testing.assert_array_equal(l, lower)
        np.testing.assert_array_equal(u, upper)
    
    def test_invalid_dimensions(self):
        """Test con dimensiones incorrectas."""
        lower = np.array([0.0, 1.0])
        upper = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValidationError, match="lower_bounds debe tener forma"):
            validate_bounds(lower, upper, 3)
    
    def test_invalid_bounds_order(self):
        """Test con límites en orden incorrecto."""
        lower = np.array([0.0, 2.0, 10.0])
        upper = np.array([1.0, 1.0, 20.0])  # upper[1] < lower[1]
        
        with pytest.raises(ValidationError, match="lower_bounds debe ser < upper_bounds"):
            validate_bounds(lower, upper, 3)
    
    def test_list_to_array_conversion(self):
        """Test conversión de listas a arrays."""
        lower = [0.0, -1.0]
        upper = [1.0, 1.0]
        
        l, u = validate_bounds(lower, upper, 2)
        assert isinstance(l, np.ndarray)
        assert isinstance(u, np.ndarray)


class TestValidateAlgorithmSpecificParams:
    """Tests para validate_algorithm_specific_params."""
    
    def test_woa_params(self):
        """Test parámetros específicos de WOA."""
        params = {"a_decrease": 1.5}
        validated = validate_algorithm_specific_params("woa", params)
        assert validated["a_decrease"] == 1.5
        
        # Valor fuera de rango
        params = {"a_decrease": 2.5}
        with pytest.raises(ValidationError):
            validate_algorithm_specific_params("woa", params)
    
    def test_sma_params(self):
        """Test parámetros específicos de SMA."""
        params = {"z": 0.03}
        validated = validate_algorithm_specific_params("sma", params)
        assert validated["z"] == 0.03
        
        # Valor fuera de rango
        params = {"z": 1.5}
        with pytest.raises(ValidationError):
            validate_algorithm_specific_params("sma", params)
    
    def test_gto_params(self):
        """Test parámetros específicos de GTO."""
        params = {"p": 0.5, "beta": 1.2}
        validated = validate_algorithm_specific_params("gto", params)
        assert validated["p"] == 0.5
        assert validated["beta"] == 1.2
        
        # Probabilidad inválida
        params = {"p": 1.5}
        with pytest.raises(ValidationError):
            validate_algorithm_specific_params("gto", params)
    
    def test_smo_params(self):
        """Test parámetros específicos de SMO."""
        params = {"mu": 0.8, "k": 5}
        validated = validate_algorithm_specific_params("smo", params)
        assert validated["mu"] == 0.8
        assert validated["k"] == 5
        
        # k debe ser entero positivo
        params = {"k": 0}
        with pytest.raises(ValidationError):
            validate_algorithm_specific_params("smo", params)
    
    def test_unknown_algorithm(self):
        """Test con algoritmo desconocido."""
        params = {"some_param": 1.0}
        validated = validate_algorithm_specific_params("unknown_algo", params)
        assert validated == {}  # No valida nada para algoritmos desconocidos


class TestWithValidationDecorator:
    """Tests para el decorador with_validation."""
    
    def test_decorator_validates_params(self):
        """Test que el decorador valida parámetros."""
        from algorithms.base_v2 import AbstractProblem
        
        # Crear un problema mock
        class MockProblem(AbstractProblem):
            @property
            def dimension(self):
                return 10
            
            @property
            def lower_bounds(self):
                return np.zeros(10)
            
            @property
            def upper_bounds(self):
                return np.ones(10)
            
            def evaluate(self, solution):
                return np.sum(solution)
        
        # Crear una clase con el decorador
        class TestAlgorithm:
            @with_validation
            def __init__(self, problem, population_size=30, max_iterations=100, 
                        seed=None, **kwargs):
                self.problem = problem
                self.population_size = population_size
                self.max_iterations = max_iterations
                self.seed = seed
                self.kwargs = kwargs
        
        # Test con parámetros válidos
        problem = MockProblem("test")
        algo = TestAlgorithm(problem, population_size=50, max_iterations=200)
        assert algo.population_size == 50
        assert algo.max_iterations == 200
        
        # Test con parámetros inválidos
        with pytest.raises(ValidationError):
            TestAlgorithm(problem, population_size=0)
        
        with pytest.raises(ValidationError):
            TestAlgorithm(problem, max_iterations=-1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])