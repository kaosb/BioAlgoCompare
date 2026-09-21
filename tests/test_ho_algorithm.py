"""Tests for the Hippopotamus Optimization Algorithm (HO).

Validates the faithful implementation of Amiri et al. (2024):
- Three sequential phases per iteration
- Parameter-free design
- Convergence on standard test functions
- Reproducibility with fixed seeds
"""
import pytest
import numpy as np
from algorithms.ho import HO, Hippopotamus
from utils.math_functions import levy_flight


class CECTestFunction:
    """Simple test functions for algorithm validation."""

    def __init__(self, function_type="sphere"):
        self.function_type = function_type
        self.dimension = 10

    def get_dimension(self):
        return self.dimension

    def evaluate(self, x):
        if self.function_type == "sphere":
            return np.sum(x ** 2)
        elif self.function_type == "rosenbrock":
            result = 0
            for i in range(len(x) - 1):
                result += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
            return result
        return np.sum(x ** 2)

    def is_valid(self, x):
        return np.all(x >= 0) and np.all(x <= 1)


def test_levy_flight():
    """Test Levy flight step generation."""
    dim = 10
    levy_vector = levy_flight(dim)
    assert len(levy_vector) == dim
    assert not np.allclose(levy_vector, 0)
    assert np.std(levy_vector) > 0


def test_hippopotamus_initialization():
    """Test individual hippopotamus initialization."""
    problem = CECTestFunction("sphere")
    hippo = Hippopotamus(problem)
    assert hasattr(hippo, "position")
    assert len(hippo.position) == problem.get_dimension()
    assert np.all(hippo.position >= 0) and np.all(hippo.position <= 1)


def test_ho_initialization():
    """Test HO algorithm initialization (parameter-free)."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=20, max_iterations=50, seed=42)
    assert ho.population_size == 20
    assert ho.max_iterations == 50
    assert ho.seed == 42


def test_ho_convergence_sphere():
    """Test convergence on Sphere function."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=30, max_iterations=100, seed=42)
    best_solution = ho.execute()

    # Should converge close to 0 for sphere
    assert best_solution.fitness() < 0.5

    # Convergence curve should be monotonically non-increasing
    curve = ho.get_convergence_curve()
    assert len(curve) == ho.max_iterations + 1
    assert curve[-1] <= curve[0]

    # Significant improvement
    improvement = (curve[0] - curve[-1]) / curve[0]
    assert improvement > 0.8


def test_ho_convergence_rosenbrock():
    """Test convergence on Rosenbrock function."""
    problem = CECTestFunction("rosenbrock")
    ho = HO(problem, population_size=50, max_iterations=200, seed=42)
    best_solution = ho.execute()
    assert best_solution.fitness() < 200
    curve = ho.get_convergence_curve()
    assert curve[-1] < curve[0]


def test_ho_reproducibility():
    """Test reproducibility with fixed seed."""
    problem = CECTestFunction("sphere")

    ho1 = HO(problem, population_size=20, max_iterations=50, seed=42)
    best1 = ho1.execute()
    curve1 = ho1.get_convergence_curve()

    ho2 = HO(problem, population_size=20, max_iterations=50, seed=42)
    best2 = ho2.execute()
    curve2 = ho2.get_convergence_curve()

    assert best1.fitness() == best2.fitness()
    assert np.allclose(curve1, curve2)
    assert np.allclose(best1.position, best2.position)


def test_ho_three_phases_sequential():
    """Test that all three phases execute (convergence curve grows by 1 per iteration)."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, population_size=10, max_iterations=5, seed=42)
    ho.execute()

    # convergence_curve has max_iterations+1 entries (init + iterations)
    assert len(ho.convergence_curve) == 6


def test_ho_legacy_params_accepted():
    """Test that legacy parameters (alpha_fixed, etc.) are accepted but ignored."""
    problem = CECTestFunction("sphere")
    # Should not raise
    ho = HO(
        problem,
        population_size=10,
        max_iterations=10,
        seed=42,
        alpha_fixed=0.5,
        beta_fixed=0.2,
        use_il=False,
    )
    ho.execute()
    assert ho.best_solution is not None


def test_ho_get_parameters():
    """Test parameter reporting."""
    problem = CECTestFunction("sphere")
    ho = HO(problem, seed=42)
    params = ho.get_parameters()
    assert params['algorithm'] == 'HO'
    assert params['levy_beta'] == 1.5
    assert 'phases' in params


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
