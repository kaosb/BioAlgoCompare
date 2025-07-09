"""
Test the new problems hierarchy.
"""

import pytest
import numpy as np
from problems import (
    # Base classes
    ContinuousProblem,
    
    # Continuous problems
    SphereProblem,
    RastriginProblem,
    AckleyProblem,
    RosenbrockProblem,
    GriewankProblem,
    SchwefelProblem,
    
    # Adapters
    ContinuousAdapter
)
from algorithms.woa_v2 import WOAV2
from algorithms.sma_v2 import SMAV2
from algorithms.gto_v2 import GTOV2


class TestContinuousProblems:
    """Test continuous benchmark problems."""
    
    def test_sphere_problem(self):
        """Test Sphere function."""
        problem = SphereProblem(dimension=10)
        
        # Test properties
        assert problem.dimension == 10
        assert problem.best_known_value == 0.0
        assert len(problem.lower_bounds) == 10
        assert len(problem.upper_bounds) == 10
        
        # Test evaluation at optimum
        optimum = problem.optimum_position
        assert problem.evaluate(optimum) == pytest.approx(0.0)
        
        # Test random solution
        random_sol = problem.random_solution()
        assert len(random_sol) == 10
        assert problem.is_feasible(random_sol)
        
        # Test gradient
        assert problem.has_gradient()
        grad = problem.gradient(np.ones(10))
        assert np.allclose(grad, 2 * np.ones(10))
    
    def test_rastrigin_problem(self):
        """Test Rastrigin function."""
        problem = RastriginProblem(dimension=10)
        
        # Test at optimum
        optimum = np.zeros(10)
        assert problem.evaluate(optimum) == pytest.approx(0.0)
        
        # Test multimodality
        # Point at (pi, pi, ...) should have high value
        point = np.full(10, np.pi)
        value = problem.evaluate(point)
        assert value > 50.0  # Rastrigin has many local minima
    
    def test_ackley_problem(self):
        """Test Ackley function."""
        problem = AckleyProblem(dimension=10)
        
        # Test at optimum
        optimum = np.zeros(10)
        assert problem.evaluate(optimum) == pytest.approx(0.0, abs=1e-10)
        
        # Test bounds
        assert problem.lower_bounds[0] == -32.768
        assert problem.upper_bounds[0] == 32.768
    
    def test_rosenbrock_problem(self):
        """Test Rosenbrock function."""
        problem = RosenbrockProblem(dimension=10)
        
        # Test at optimum (all ones)
        optimum = np.ones(10)
        assert problem.evaluate(optimum) == pytest.approx(0.0)
        
        # Test at origin (should be high)
        origin = np.zeros(10)
        value = problem.evaluate(origin)
        assert value > 1.0
    
    def test_griewank_problem(self):
        """Test Griewank function."""
        problem = GriewankProblem(dimension=10)
        
        # Test at optimum
        optimum = np.zeros(10)
        assert problem.evaluate(optimum) == pytest.approx(0.0)
        
        # Test bounds
        assert problem.lower_bounds[0] == -600.0
        assert problem.upper_bounds[0] == 600.0
    
    def test_schwefel_problem(self):
        """Test Schwefel function."""
        problem = SchwefelProblem(dimension=10)
        
        # Test at optimum
        optimum = problem.optimum_position
        assert np.allclose(optimum, 420.9687 * np.ones(10))
        assert problem.evaluate(optimum) == pytest.approx(0.0, abs=1e-3)


class TestAdapters:
    """Test problem adapters."""
    
    def test_continuous_adapter_with_sphere(self):
        """Test ContinuousAdapter with Sphere problem."""
        # Create Sphere problem
        sphere = SphereProblem(dimension=10)
        
        # Adapt for legacy interface
        adapted = ContinuousAdapter(sphere)
        
        # Test legacy interface
        assert adapted.get_dimension() == 10
        assert len(adapted.get_lower_bounds()) == 10
        assert len(adapted.get_upper_bounds()) == 10
        
        # Test evaluation
        solution = np.zeros(10)
        assert adapted.evaluate(solution) == pytest.approx(0.0)
        
        # Test with algorithm
        algo = WOAV2(adapted, population_size=20, max_iterations=50)
        best = algo.execute()
        assert best.fitness() < 1.0  # Should find good solution
    
    def test_multiple_algorithms_with_adapted_problems(self):
        """Test different algorithms with adapted problems."""
        problems = [
            SphereProblem(dimension=10),
            RastriginProblem(dimension=10),
            AckleyProblem(dimension=10)
        ]
        
        algorithms = [WOAV2, SMAV2, GTOV2]
        
        for problem in problems:
            adapted = ContinuousAdapter(problem)
            
            for AlgoClass in algorithms:
                algo = AlgoClass(adapted, population_size=20, max_iterations=30)
                best = algo.execute()
                
                # All algorithms should make progress
                assert best.fitness() < problem.evaluate(problem.random_solution())


class TestProblemMetrics:
    """Test problem metrics and statistics."""
    
    def test_evaluation_counting(self):
        """Test evaluation counter."""
        problem = SphereProblem(dimension=10)
        
        # Initial count
        assert problem.evaluations == 0
        
        # Evaluate some solutions
        for _ in range(5):
            solution = problem.random_solution()
            problem.evaluate(solution)
        
        assert problem.evaluations == 5
        
        # Reset counter
        problem.reset_evaluations()
        assert problem.evaluations == 0
    
    def test_distance_to_optimum(self):
        """Test distance calculation."""
        problem = SphereProblem(dimension=10)
        
        # At optimum
        optimum = problem.optimum_position
        assert problem.distance_to_optimum(optimum) == pytest.approx(0.0)
        
        # At distance
        point = np.ones(10)
        distance = problem.distance_to_optimum(point)
        expected = np.sqrt(10)  # sqrt(sum of 1^2)
        assert distance == pytest.approx(expected)
    
    def test_gap_to_optimum(self):
        """Test fitness gap calculation."""
        problem = SphereProblem(dimension=10)
        
        # Perfect fitness
        assert problem.gap_to_optimum(0.0) == pytest.approx(0.0)
        
        # With gap
        assert problem.gap_to_optimum(10.0) == pytest.approx(10.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])