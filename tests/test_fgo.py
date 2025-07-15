#!/usr/bin/env python3
"""
Test for the FGO (Flamingo Optimization Algorithm) algorithm.
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from algorithms.fgo_v2 import FGOV2, FlamingoV2
from algorithms.base_v2 import MetaheuristicAlgorithm


class MockProblem:
    """Mock problem for testing."""

    def __init__(self, dimension=5):
        self.dimension = dimension
        self.eval_count = 0

    def get_dimension(self):
        return self.dimension
<<<<<<< HEAD
    
    @property
    def lower_bounds(self):
        return np.zeros(self.dimension)
    
    @property
    def upper_bounds(self):
        return np.ones(self.dimension)
    
=======

>>>>>>> develop
    def evaluate(self, solution):
        """Simple evaluation function for testing."""
        self.eval_count += 1
        # Simple function: sum of elements
        return np.sum(solution)


def test_flamingo_initialization():
    """Test for Flamingo individual initialization."""
    np.random.seed(42)  # For reproducibility

    problem = MockProblem(dimension=5)
<<<<<<< HEAD
    flamingo = FlamingoV2(problem)
    
    # Verificar inicialización
=======
    flamingo = Flamingo(problem)

    # Verify initialization
>>>>>>> develop
    assert flamingo.problem == problem
    assert flamingo.dimension == 5
    assert flamingo.position.shape == (5,)
    assert flamingo._fitness is None
    assert np.array_equal(flamingo.personal_best_position, flamingo.position)
    assert flamingo.personal_best_fitness == float("inf")

    # Verify that position is in range [0, 1]
    assert np.all(flamingo.position >= 0) and np.all(flamingo.position <= 1)


def test_flamingo_fitness():
    """Test for Flamingo fitness calculation."""
    problem = MockProblem(dimension=3)
<<<<<<< HEAD
    flamingo = FlamingoV2(problem)
    
    # Establecer una posición conocida
=======
    flamingo = Flamingo(problem)

    # Set a known position
>>>>>>> develop
    flamingo.position = np.array([0.1, 0.2, 0.3])

    # Verify fitness calculation (use almost equal for floats)
    fitness = flamingo.fitness()
    assert np.isclose(fitness, 0.6)  # 0.1 + 0.2 + 0.3

    # Verify that personal best fitness was updated
    assert np.isclose(flamingo.personal_best_fitness, 0.6)
    assert np.array_equal(flamingo.personal_best_position, np.array([0.1, 0.2, 0.3]))

    # Verify that fitness is cached
    flamingo.position = np.array([0.4, 0.5, 0.6])  # Change position
    assert np.isclose(
        flamingo.fitness(), 0.6
    )  # Should still be 0.6 because it's cached

    # Invalidate fitness and recalculate
    flamingo._fitness = None
    assert np.isclose(flamingo.fitness(), 1.5)  # 0.4 + 0.5 + 0.6

    # Verify that personal best fitness was updated al ser peor
    assert np.isclose(flamingo.personal_best_fitness, 0.6)  # Should not change
    assert np.array_equal(flamingo.personal_best_position, np.array([0.1, 0.2, 0.3]))


def test_flamingo_comparison():
    """Test for comparison between Flamingos."""
    problem = MockProblem()
<<<<<<< HEAD
    
    flamingo1 = FlamingoV2(problem)
    flamingo1._fitness = 10
    
    flamingo2 = FlamingoV2(problem)
=======

    flamingo1 = Flamingo(problem)
    flamingo1._fitness = 10

    flamingo2 = Flamingo(problem)
>>>>>>> develop
    flamingo2._fitness = 20

    # Verify comparison
    assert flamingo1.is_better_than(flamingo2)
    assert not flamingo2.is_better_than(flamingo1)


def test_flamingo_is_feasible():
    """Test to verify if solution is feasible."""
    problem = MockProblem()
<<<<<<< HEAD
    flamingo = FlamingoV2(problem)
    
    # En el contexto de VRP, todas las soluciones son factibles
=======
    flamingo = Flamingo(problem)

    # In VRP context, all solutions are feasible
>>>>>>> develop
    assert flamingo.is_feasible()


def test_flamingo_move_forage():
    """Test for Flamingo foraging movement."""
    np.random.seed(42)
    problem = MockProblem(dimension=3)
<<<<<<< HEAD
    
    flamingo = FlamingoV2(problem)
=======

    flamingo = Flamingo(problem)
>>>>>>> develop
    flamingo.position = np.array([0.1, 0.2, 0.3])
    flamingo._fitness = 0.6

    best = Flamingo(problem)
    best.position = np.array([0.05, 0.15, 0.25])
    best._fitness = 0.45

    # Mock fitness calculation to always return a lower value (improvement)
    problem.evaluate = MagicMock(return_value=0.4)

    # Patch random.choice to have predictable values
    with patch("random.choice", side_effect=lambda x: x[0]):
        # Test foraging movement
        flamingo.move(best, 0, 100, mode="forage")

    # Verify that fitness was updated
    assert flamingo._fitness == 0.4


def test_flamingo_move_migrate():
    """Test for Flamingo migration movement."""
    np.random.seed(42)
    problem = MockProblem(dimension=3)
<<<<<<< HEAD
    
    flamingo = FlamingoV2(problem)
=======

    flamingo = Flamingo(problem)
>>>>>>> develop
    flamingo.position = np.array([0.1, 0.2, 0.3])
    flamingo._fitness = 0.6

    best = Flamingo(problem)
    best.position = np.array([0.05, 0.15, 0.25])
    best._fitness = 0.45

    # Mock fitness calculation to always return a lower value (improvement)
    problem.evaluate = MagicMock(return_value=0.4)

    # Test migration movement
    flamingo.move(best, 0, 100, mode="migrate")

    # Verify that fitness was updated
    assert flamingo._fitness == 0.4


def test_flamingo_copy():
    """Test for Flamingo copy function."""
    problem = MockProblem()
<<<<<<< HEAD
    
    flamingo1 = FlamingoV2(problem)
=======

    flamingo1 = Flamingo(problem)
>>>>>>> develop
    flamingo1.position = np.array([0.1, 0.2, 0.3])
    flamingo1._fitness = 0.6
    flamingo1.personal_best_position = np.array([0.1, 0.2, 0.3])
    flamingo1.personal_best_fitness = 0.6
<<<<<<< HEAD
    
    flamingo2 = FlamingoV2(problem)
=======

    flamingo2 = Flamingo(problem)
>>>>>>> develop
    flamingo2.copy(flamingo1)

    # Verify that values have been copied
    assert np.array_equal(flamingo2.position, flamingo1.position)
    assert flamingo2._fitness == flamingo1._fitness
    assert np.array_equal(
        flamingo2.personal_best_position, flamingo1.personal_best_position
    )
    assert flamingo2.personal_best_fitness == flamingo1.personal_best_fitness

    # Verify they are different objects (deep copy)
    flamingo1.position[0] = 0.9
    assert flamingo2.position[0] == 0.1


def test_fgo_initialization():
    """Test for FGO algorithm initialization."""
    np.random.seed(42)
    problem = MockProblem()

    # Algorithm initialization
    fgo = FGO(problem, population_size=10, max_iterations=50, seed=42)

    # Verify parameters
    assert fgo.problem == problem
    assert fgo.population_size == 10
    assert fgo.max_iterations == 50

    # Initialize population
    fgo.initialize_population()

    # Verify population has been created
    assert len(fgo.population) == 10
    assert all(isinstance(ind, Flamingo) for ind in fgo.population)

    # Verify fitness has been calculated for each individual
    assert all(ind._fitness is not None for ind in fgo.population)

    # Verify population is sorted by fitness
    fitnesses = [ind.fitness() for ind in fgo.population]
    assert fitnesses == sorted(fitnesses)

    # Verify best solution has been saved
    assert isinstance(fgo.best_solution, Flamingo)
    assert fgo.best_solution._fitness == fgo.population[0]._fitness

    # Verify convergence curve
    assert len(fgo.convergence_curve) == 1
    assert fgo.convergence_curve[0] == fgo.best_solution.fitness()


def test_fgo_update_population():
    """Test for population update in FGO."""
    np.random.seed(42)
    problem = MockProblem()

    # Algorithm initialization
    fgo = FGO(problem, population_size=10, max_iterations=50, seed=42)
    fgo.initialize_population()

    # Save initial fitness
    initial_best_fitness = fgo.best_solution.fitness()

    # Update population
    fgo.update_population()

    # Verify convergence curve has been updated
    assert len(fgo.convergence_curve) == 2

    # Since we're minimizing, new fitness should be less than or equal
    assert fgo.best_solution.fitness() <= initial_best_fitness


def test_fgo_full_execution():
    """Test for complete FGO algorithm execution."""
    np.random.seed(42)
    problem = MockProblem()

    # Algorithm initialization
    fgo = FGO(problem, population_size=10, max_iterations=5, seed=42)

    # Execute the algorithm
    best_solution = fgo.execute()

    # Verify execution completed iterations
    assert len(fgo.convergence_curve) == 6  # Initial iteration + 5 iterations

    # Verify best solution is a Flamingo instance
    assert isinstance(best_solution, Flamingo)
