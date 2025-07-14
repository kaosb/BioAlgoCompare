"""
Tests for mathematical functions used across algorithms.
"""
import pytest
import numpy as np
from utils.math_functions import (
    levy_flight,
    cauchy_distribution,
    sigmoid,
    tanh,
    gaussian_mutation,
    polynomial_mutation,
    spiral_movement,
    s_shaped_transfer,
    v_shaped_transfer,
    euclidean_distance,
    manhattan_distance,
    minkowski_distance
)


class TestLevyFlight:
    """Tests for Lévy flight generation."""
    
    def test_levy_flight_basic(self):
        """Test basic Lévy flight generation."""
        dim = 10
        step = levy_flight(dim)
        
        assert isinstance(step, np.ndarray)
        assert step.shape == (dim,)
        assert step.dtype == np.float64
    
    def test_levy_flight_different_beta(self):
        """Test Lévy flight with different beta values."""
        dim = 5
        for beta in [1.0, 1.5, 2.0]:
            step = levy_flight(dim, beta=beta)
            assert step.shape == (dim,)
    
    def test_levy_flight_reproducibility(self):
        """Test reproducibility with seed."""
        np.random.seed(42)
        step1 = levy_flight(10)
        
        np.random.seed(42)
        step2 = levy_flight(10)
        
        assert np.allclose(step1, step2)


class TestDistributions:
    """Tests for probability distributions."""
    
    def test_cauchy_distribution_shape(self):
        """Test Cauchy distribution with different shapes."""
        # Single dimension
        samples = cauchy_distribution(100)
        assert samples.shape == (100,)
        
        # Multi-dimensional
        samples = cauchy_distribution((10, 5))
        assert samples.shape == (10, 5)
    
    def test_cauchy_distribution_properties(self):
        """Test that Cauchy distribution has heavy tails."""
        samples = cauchy_distribution(10000)
        # Cauchy has undefined mean/variance, but should have heavy tails
        assert np.any(np.abs(samples) > 10)  # Should have some large values


class TestActivationFunctions:
    """Tests for activation functions."""
    
    def test_sigmoid(self):
        """Test sigmoid function."""
        x = np.array([-100, -1, 0, 1, 100])
        y = sigmoid(x)
        
        # Check range
        assert np.all(y >= 0) and np.all(y <= 1)
        
        # Check specific values
        assert np.isclose(y[2], 0.5)  # sigmoid(0) = 0.5
        assert y[0] < 0.01  # sigmoid(-100) ≈ 0
        assert y[4] > 0.99  # sigmoid(100) ≈ 1
    
    def test_tanh_wrapper(self):
        """Test tanh wrapper function."""
        x = np.array([-100, -1, 0, 1, 100])
        y = tanh(x)
        
        # Check range
        assert np.all(y >= -1) and np.all(y <= 1)
        
        # Check specific values
        assert np.isclose(y[2], 0)  # tanh(0) = 0
        assert y[0] < -0.99  # tanh(-100) ≈ -1
        assert y[4] > 0.99  # tanh(100) ≈ 1


class TestMutationOperators:
    """Tests for mutation operators."""
    
    def test_gaussian_mutation(self):
        """Test Gaussian mutation."""
        position = np.array([0.5, 0.5, 0.5])
        mutated = gaussian_mutation(position, sigma=0.1)
        
        assert mutated.shape == position.shape
        # Should be close but not identical
        assert not np.array_equal(mutated, position)
        
        # Test with zero sigma
        mutated_zero = gaussian_mutation(position, sigma=0.0)
        assert np.allclose(mutated_zero, position)
    
    def test_polynomial_mutation(self):
        """Test polynomial mutation."""
        position = np.array([0.5, 0.5, 0.5])
        mutated = polynomial_mutation(position, eta=20.0)
        
        assert mutated.shape == position.shape
        # Should be in [0, 1]
        assert np.all(mutated >= 0) and np.all(mutated <= 1)
        
        # Test boundary handling
        position_boundary = np.array([0.0, 1.0, 0.5])
        mutated_boundary = polynomial_mutation(position_boundary)
        assert np.all(mutated_boundary >= 0) and np.all(mutated_boundary <= 1)


class TestMovementFunctions:
    """Tests for movement functions."""
    
    def test_spiral_movement(self):
        """Test spiral movement."""
        current = np.array([0.0, 0.0])
        target = np.array([1.0, 1.0])
        
        # Test with default l
        new_pos = spiral_movement(current, target, b=1.0)
        assert new_pos.shape == current.shape
        
        # Test with specific l
        new_pos_l = spiral_movement(current, target, b=1.0, l=0.5)
        assert new_pos_l.shape == current.shape
        
        # Test with l=0
        new_pos_zero = spiral_movement(current, target, b=1.0, l=0.0)
        # With l=0: exp(0)*cos(0) = 1*1 = 1, so new_pos = distance * 1 + target
        distance = np.abs(target - current)
        expected = distance + target
        assert np.allclose(new_pos_zero, expected)


class TestTransferFunctions:
    """Tests for transfer functions."""
    
    def test_s_shaped_transfer(self):
        """Test S-shaped transfer functions."""
        x = np.array([-2, -1, 0, 1, 2])
        
        for version in [1, 2, 3, 4]:
            y = s_shaped_transfer(x, version=version)
            # Check range
            assert np.all(y >= 0) and np.all(y <= 1)
            # Check monotonicity
            assert np.all(np.diff(y) >= 0)
        
        # Test invalid version
        with pytest.raises(ValueError):
            s_shaped_transfer(x, version=5)
    
    def test_v_shaped_transfer(self):
        """Test V-shaped transfer functions."""
        x = np.array([-2, -1, 0, 1, 2])
        
        for version in [1, 2, 3, 4]:
            y = v_shaped_transfer(x, version=version)
            # Check range
            assert np.all(y >= 0) and np.all(y <= 1)
            # Check symmetry (V-shaped)
            assert np.isclose(y[0], y[4])  # f(-2) = f(2)
            assert np.isclose(y[1], y[3])  # f(-1) = f(1)
        
        # Test invalid version
        with pytest.raises(ValueError):
            v_shaped_transfer(x, version=5)


class TestDistanceFunctions:
    """Tests for distance functions."""
    
    def test_euclidean_distance(self):
        """Test Euclidean distance."""
        a = np.array([0, 0])
        b = np.array([3, 4])
        
        dist = euclidean_distance(a, b)
        assert np.isclose(dist, 5.0)  # 3-4-5 triangle
        
        # Test zero distance
        assert euclidean_distance(a, a) == 0.0
    
    def test_manhattan_distance(self):
        """Test Manhattan distance."""
        a = np.array([0, 0])
        b = np.array([3, 4])
        
        dist = manhattan_distance(a, b)
        assert dist == 7.0  # |3-0| + |4-0| = 7
        
        # Test zero distance
        assert manhattan_distance(a, a) == 0.0
    
    def test_minkowski_distance(self):
        """Test Minkowski distance."""
        a = np.array([0, 0])
        b = np.array([3, 4])
        
        # p=1 should equal Manhattan
        assert np.isclose(minkowski_distance(a, b, p=1), manhattan_distance(a, b))
        
        # p=2 should equal Euclidean
        assert np.isclose(minkowski_distance(a, b, p=2), euclidean_distance(a, b))
        
        # Test with p=3
        dist_p3 = minkowski_distance(a, b, p=3)
        expected = (3**3 + 4**3) ** (1/3)
        assert np.isclose(dist_p3, expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])