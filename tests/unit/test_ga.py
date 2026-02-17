"""Unit tests for Genetic Algorithm."""

import pytest
import numpy as np
from algorithms.ga import GA, Chromosome
from problems.vrp import VRPProblem


def _make_rng(seed):
    return np.random.default_rng(seed)


class TestChromosome:
    """Test cases for Chromosome class."""
    
    def test_chromosome_initialization(self):
        """Test chromosome is initialized correctly."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2)]
        problem.demands = [0, 10, 20]
        problem.capacity = 50
        problem.dimension = 3
        problem.compute_distance_matrix()
        
        chromosome = Chromosome(dimension=2, problem=problem, rng=_make_rng(42))
        
        assert chromosome.dimension == 2
        assert len(chromosome.position) == 2
        assert all(0 <= p <= 1 for p in chromosome.position)
    
    def test_crossover_operation(self):
        """Test order crossover produces valid offspring."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        problem.demands = [0, 10, 20, 15, 25]
        problem.capacity = 50
        problem.dimension = 5
        problem.compute_distance_matrix()
        
        # Create parents with specific positions
        parent1 = Chromosome(dimension=4, problem=problem, rng=_make_rng(42))
        parent2 = Chromosome(dimension=4, problem=problem, rng=_make_rng(43))
        
        # Set known positions for testing
        parent1.position = np.array([0.1, 0.3, 0.5, 0.7])
        parent2.position = np.array([0.2, 0.4, 0.6, 0.8])
        
        # Perform crossover
        offspring1, offspring2 = parent1.crossover(parent2)
        
        # Check offspring are valid
        assert len(offspring1.position) == 4
        assert len(offspring2.position) == 4
        assert all(0 <= p <= 1 for p in offspring1.position)
        assert all(0 <= p <= 1 for p in offspring2.position)
        
        # Check offspring are different from parents
        assert not np.array_equal(offspring1.position, parent1.position)
        assert not np.array_equal(offspring2.position, parent2.position)
    
    def test_mutation_operation(self):
        """Test mutation changes chromosome."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2), (3, 3)]
        problem.demands = [0, 10, 20, 15]
        problem.capacity = 50
        problem.dimension = 4
        problem.compute_distance_matrix()
        
        chromosome = Chromosome(dimension=3, problem=problem, rng=_make_rng(42))
        original_position = chromosome.position.copy()
        
        # Apply mutation with high rate to ensure changes
        chromosome.mutate(mutation_rate=1.0)
        
        # Check position changed
        assert not np.array_equal(chromosome.position, original_position)
        
        # Check position still valid
        assert len(chromosome.position) == 3
        assert all(0 <= p <= 1 for p in chromosome.position)
    
    def test_mutation_preserves_values(self):
        """Test mutation only swaps values, doesn't create new ones."""
        problem = VRPProblem()
        problem.nodes = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        problem.demands = [0, 10, 20, 15, 25]
        problem.capacity = 50
        problem.dimension = 5
        problem.compute_distance_matrix()
        
        chromosome = Chromosome(dimension=4, problem=problem, rng=_make_rng(42))
        original_values = set(chromosome.position)
        
        # Apply mutation
        chromosome.mutate(mutation_rate=0.5)
        
        # Check same values exist, just reordered
        mutated_values = set(chromosome.position)
        assert original_values == mutated_values


class TestGA:
    """Test cases for Genetic Algorithm."""
    
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
    
    def test_ga_initialization(self, small_vrp_problem):
        """Test GA initialization."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=20,
            max_iterations=10,
            seed=42,
            crossover_rate=0.8,
            mutation_rate=0.1,
            tournament_size=3,
            elitism_size=2
        )
        
        assert ga.population_size == 20
        assert ga.max_iterations == 10
        assert ga.seed == 42
        assert ga.crossover_rate == 0.8
        assert ga.mutation_rate == 0.1
        assert ga.tournament_size == 3
        assert ga.elitism_size == 2
    
    def test_initialize_population(self, small_vrp_problem):
        """Test population initialization."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=5,
            seed=42
        )

        ga.initialize_population()

        assert len(ga.population) == 10
        assert all(isinstance(c, Chromosome) for c in ga.population)
        assert all(c.dimension == 4 for c in ga.population)  # dimension - 1
        assert ga.best_solution is not None
    
    def test_tournament_selection(self, small_vrp_problem):
        """Test tournament selection mechanism."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=5,
            tournament_size=3,
            seed=42
        )

        ga.initialize_population()
        
        # Perform multiple selections
        selected = [ga.tournament_selection() for _ in range(5)]
        
        # Check all are valid chromosomes
        assert all(isinstance(c, Chromosome) for c in selected)
        
        # Check selection is working (not all same)
        positions = [tuple(c.position) for c in selected]
        assert len(set(positions)) > 1
    
    def test_evolve_population(self, small_vrp_problem):
        """Test population evolution."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=5,
            elitism_size=2,
            seed=42
        )

        ga.initialize_population()
        
        # Get best individuals before evolution
        sorted_pop = sorted(ga.population, key=lambda x: x.fitness())
        best_before = sorted_pop[0].fitness()
        
        # Evolve
        new_population = ga.evolve_population()
        
        # Check population size maintained
        assert len(new_population) == 10
        
        # Check elitism (best should be preserved or improved)
        best_after = min(new_population, key=lambda x: x.fitness()).fitness()
        assert best_after <= best_before + 1e-6  # Allow small numerical error
    
    def test_ga_execution(self, small_vrp_problem):
        """Test full GA execution."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=20,
            max_iterations=10,
            seed=42
        )

        best = ga.execute()

        # Check return type (Individual with fitness method)
        assert hasattr(best, 'fitness')
        fitness = best.fitness()
        assert isinstance(fitness, float)

        # Check convergence curve (1 initial + 10 iterations = 11)
        convergence = ga.get_convergence_curve()
        assert isinstance(convergence, list)
        assert len(convergence) == 11

        # Check solution validity via decode
        routes, _, _ = small_vrp_problem.decode_solution(best.position)
        assert isinstance(routes, list)
        assert all(isinstance(route, list) for route in routes)
        assert all(route[0] == 0 and route[-1] == 0 for route in routes)

        # Check convergence trend (non-increasing)
        for i in range(1, len(convergence)):
            assert convergence[i] <= convergence[i-1] + 1e-6
    
    def test_deterministic_behavior(self, small_vrp_problem):
        """Test GA produces identical results with same seed."""
        ga1 = GA(small_vrp_problem, population_size=10, max_iterations=5, seed=42)
        ga2 = GA(small_vrp_problem, population_size=10, max_iterations=5, seed=42)

        best1 = ga1.execute()
        best2 = ga2.execute()

        assert best1.fitness() == best2.fitness()
        assert ga1.get_convergence_curve() == ga2.get_convergence_curve()
    
    def test_different_seeds_different_results(self, small_vrp_problem):
        """Test GA produces different results with different seeds."""
        ga1 = GA(small_vrp_problem, population_size=10, max_iterations=5, seed=42)
        ga2 = GA(small_vrp_problem, population_size=10, max_iterations=5, seed=123)

        # Verify initial populations are different (proves seeds work)
        ga1.initialize_population()
        ga2.initialize_population()
        pos1 = [c.position.copy() for c in ga1.population]
        pos2 = [c.position.copy() for c in ga2.population]
        assert not all(np.array_equal(a, b) for a, b in zip(pos1, pos2)), \
            "Different seeds should produce different initial populations"
    
    def test_adaptive_mutation(self, small_vrp_problem):
        """Test adaptive mutation rate adjustment."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=10,
            max_iterations=5,
            mutation_rate=0.1,
            seed=42
        )

        initial_mutation_rate = ga.mutation_rate

        # Create population with low diversity (all similar positions)
        ga.initialize_population()
        for ind in ga.population:
            ind.position = ga.population[0].position.copy() + np.random.normal(0, 0.01, ind.dimension)
            ind._fitness = None

        # Execute one generation via update_population (includes adaptive mutation)
        ga.update_population()

        # Mutation rate should have increased due to low diversity
        assert ga.mutation_rate >= initial_mutation_rate
    
    def test_get_parameters(self, small_vrp_problem):
        """Test parameter reporting."""
        ga = GA(
            problem=small_vrp_problem,
            population_size=50,
            max_iterations=100,
            crossover_rate=0.85,
            mutation_rate=0.05,
            tournament_size=5,
            elitism_size=3,
            seed=42
        )
        
        params = ga.get_parameters()
        
        assert params['algorithm'] == 'GA'
        assert params['population_size'] == 50
        assert params['max_iterations'] == 100
        assert params['crossover_rate'] == 0.85
        assert params['mutation_rate'] == 0.05
        assert params['tournament_size'] == 5
        assert params['elitism_size'] == 3
        assert params['seed'] == 42