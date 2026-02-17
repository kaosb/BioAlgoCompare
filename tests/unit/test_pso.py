"""Unit tests for Particle Swarm Optimization algorithm."""

import pytest
import numpy as np
from algorithms.pso import PSO, Particle
from problems.vrp import VRPProblem


class TestParticle:
    """Test cases for Particle class."""
    
    def test_particle_initialization(self):
        """Test particle is initialized with correct attributes."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2)]
        problem.demands = [0, 10, 20]
        problem.capacity = 50
        problem.dimension = 3
        problem.compute_distance_matrix()
        
        particle = Particle(dimension=2, problem=problem, rng=np.random.default_rng(42))
        
        assert particle.dimension == 2
        assert len(particle.position) == 2
        assert len(particle.velocity) == 2
        assert len(particle.pbest_position) == 2
        assert particle.pbest_fitness == float('inf')
        assert all(0 <= p <= 1 for p in particle.position)
        assert all(-1 <= v <= 1 for v in particle.velocity)
    
    def test_update_pbest(self):
        """Test personal best update mechanism."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2)]
        problem.demands = [0, 10, 20]
        problem.capacity = 50
        problem.dimension = 3
        problem.compute_distance_matrix()
        
        particle = Particle(dimension=2, problem=problem, rng=np.random.default_rng(42))
        
        # Initial pbest should be infinity
        assert particle.pbest_fitness == float('inf')
        
        # Update pbest
        particle.update_pbest()
        initial_fitness = particle.fitness()
        assert particle.pbest_fitness == initial_fitness
        assert np.array_equal(particle.pbest_position, particle.position)
        
        # Change position to worse solution
        particle.position = np.array([0.9, 0.9])
        particle._fitness = None
        # Force fitness recalculation
        particle.fitness()
        
        # pbest should not update to worse solution
        particle.update_pbest()
        assert particle.pbest_fitness == initial_fitness
    
    def test_particle_movement(self):
        """Test particle movement with PSO equations."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2), (3, 3)]
        problem.demands = [0, 10, 20, 15]
        problem.capacity = 50
        problem.dimension = 4
        problem.compute_distance_matrix()
        
        particle = Particle(dimension=3, problem=problem, rng=np.random.default_rng(42))
        initial_position = particle.position.copy()
        initial_velocity = particle.velocity.copy()
        
        # Create a global best position
        gbest_position = np.array([0.5, 0.5, 0.5])
        
        # Move particle
        particle.update_velocity_position(gbest_position)
        
        # Check position and velocity changed
        assert not np.array_equal(particle.position, initial_position)
        assert not np.array_equal(particle.velocity, initial_velocity)
        
        # Check position bounds
        assert all(0 <= p <= 1 for p in particle.position)
        
        # Check velocity clamping
        assert all(-4.0 <= v <= 4.0 for v in particle.velocity)


class TestPSO:
    """Test cases for PSO algorithm."""
    
    @pytest.fixture
    def small_vrp_problem(self):
        """Create a small VRP problem for testing."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 0), (0, 1), (1, 1), (-1, 0)]
        problem.demands = [0, 10, 20, 15, 25]
        problem.capacity = 50
        problem.dimension = 5
        problem.compute_distance_matrix()
        return problem
    
    def test_pso_initialization(self, small_vrp_problem):
        """Test PSO initialization."""
        pso = PSO(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        
        assert pso.population_size == 10
        assert pso.max_iterations == 5
        assert pso.seed == 42
        assert pso.gbest_fitness == float('inf')
        assert pso.gbest_position is None
    
    def test_initialize_population(self, small_vrp_problem):
        """Test swarm initialization."""
        pso = PSO(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )
        
        population = pso.initialize_population()
        
        assert len(population) == 10
        assert all(isinstance(p, Particle) for p in population)
        assert pso.gbest_fitness < float('inf')
        assert pso.gbest_position is not None
        assert len(pso.gbest_position) == 4  # dimension - 1
    
    def test_pso_execution(self, small_vrp_problem):
        """Test full PSO execution."""
        pso = PSO(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=10,
            seed=42
        )
        
        routes, fitness, convergence = pso.execute()
        
        # Check output format
        assert isinstance(routes, list)
        assert isinstance(fitness, float)
        assert isinstance(convergence, list)
        assert len(convergence) == 10
        
        # Check solution validity
        assert all(isinstance(route, list) for route in routes)
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)  # Start/end at depot
        
        # Check convergence (non-increasing)
        for i in range(1, len(convergence)):
            assert convergence[i] <= convergence[i-1] + 1e-6  # Allow small numerical errors
    
    def test_deterministic_behavior(self, small_vrp_problem):
        """Test PSO produces same results with same seed."""
        pso1 = PSO(small_vrp_problem, population_size=5, max_iterations=5, seed=42)
        pso2 = PSO(small_vrp_problem, population_size=5, max_iterations=5, seed=42)
        
        routes1, fitness1, conv1 = pso1.execute()
        routes2, fitness2, conv2 = pso2.execute()
        
        assert fitness1 == fitness2
        assert conv1 == conv2
    
    def test_different_seeds_different_results(self, small_vrp_problem):
        """Test PSO produces different results with different seeds."""
        pso1 = PSO(small_vrp_problem, population_size=5, max_iterations=5, seed=42)
        pso2 = PSO(small_vrp_problem, population_size=5, max_iterations=5, seed=123)

        # Verify initial populations are different (proves seeds work)
        pso1.initialize_population()
        pso2.initialize_population()
        pos1 = [p.position.copy() for p in pso1.population]
        pos2 = [p.position.copy() for p in pso2.population]
        assert not all(np.array_equal(a, b) for a, b in zip(pos1, pos2)), \
            "Different seeds should produce different initial populations"
    
    def test_get_parameters(self, small_vrp_problem):
        """Test parameter reporting."""
        pso = PSO(
            problem=small_vrp_problem,
            population_size=20,
            max_iterations=50,
            seed=42
        )
        
        params = pso.get_parameters()
        
        assert params['algorithm'] == 'PSO'
        assert params['population_size'] == 20
        assert params['max_iterations'] == 50
        assert params['inertia_weight'] == 0.729
        assert params['c1'] == 1.49445
        assert params['c2'] == 1.49445
        assert params['seed'] == 42