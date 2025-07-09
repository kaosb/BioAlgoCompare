"""
Algorithm Name (ABBREVIATION) - Brief one-line description.

Based on:
    Author(s). (Year). Paper Title. Journal/Conference, Volume(Issue), pages.
    DOI: xxx.xxx/xxx
    
    Secondary reference (if applicable):
    Author(s). (Year). Title. Source.
    DOI: xxx.xxx/xxx

This implementation includes:
    - Key feature 1 from the original paper
    - Key feature 2
    - Any modifications or improvements made
    
Mathematical formulation:
    Position update: x_i(t+1) = x_i(t) + v_i(t)
    Velocity update: v_i(t+1) = w*v_i(t) + c1*r1*(pbest_i - x_i(t)) + c2*r2*(gbest - x_i(t))
    
    Where:
    - x_i: position of individual i
    - v_i: velocity of individual i
    - w: inertia weight
    - c1, c2: acceleration coefficients
    - r1, r2: random values in [0, 1]
    - pbest_i: personal best position
    - gbest: global best position

Performance characteristics:
    - Time complexity: O(n * d * max_iterations) where n is population size, d is dimension
    - Space complexity: O(n * d)
    - Typical convergence: 100-500 iterations for standard benchmarks

Usage example:
    >>> from problems.vrp import VRPProblem
    >>> from algorithms.abbreviation import Abbreviation
    >>> 
    >>> # Load problem
    >>> problem = VRPProblem("E-n22-k4")
    >>> 
    >>> # Configure algorithm
    >>> algorithm = Abbreviation(
    ...     problem,
    ...     population_size=50,
    ...     max_iterations=200,
    ...     specific_param1=0.7,
    ...     specific_param2=2.0,
    ...     seed=42  # For reproducibility
    ... )
    >>> 
    >>> # Run optimization
    >>> result = algorithm.run()
    >>> print(f"Best fitness: {result['best_fitness']:.2f}")
    >>> print(f"Convergence at iteration: {result['convergence_iteration']}")
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from numpy.typing import NDArray
import logging

from algorithms.base import MetaheuristicAlgorithm, Individual

# Configure module logger
logger = logging.getLogger(__name__)


class AlgorithmNameIndividual(Individual):
    """
    Individual representation for Algorithm Name.
    
    Extends base Individual with algorithm-specific attributes needed
    for the optimization process.
    
    Attributes:
        velocity: Movement velocity vector (if applicable)
        personal_best: Best position found by this individual
        personal_best_fitness: Fitness of personal best position
        specific_attribute: Algorithm-specific attribute
    """
    
    def __init__(self, position: NDArray[np.float64], problem):
        """
        Initialize algorithm-specific individual.
        
        Args:
            position: Initial position in solution space
            problem: Problem instance being solved
        """
        super().__init__(position, problem)
        
        # Algorithm-specific attributes
        self.velocity: Optional[NDArray[np.float64]] = None
        self.personal_best: Optional[NDArray[np.float64]] = None
        self.personal_best_fitness: float = float('inf')
        self.specific_attribute: float = 0.0
        
        # Initialize if needed
        self._initialize_specific_attributes()
    
    def _initialize_specific_attributes(self) -> None:
        """Initialize algorithm-specific attributes."""
        # Example: Initialize velocity for swarm-based algorithms
        if self.velocity is None:
            self.velocity = np.zeros_like(self.position)
        
        # Initialize personal best
        self.personal_best = self.position.copy()
        self.personal_best_fitness = self.fitness
    
    def move(self, **kwargs) -> None:
        """
        Update individual position according to algorithm rules.
        
        This method implements the core movement logic specific to
        the algorithm being implemented.
        
        Args:
            **kwargs: Algorithm-specific parameters including:
                - global_best: Best solution found so far
                - neighbors: Neighboring individuals (if applicable)
                - iteration: Current iteration number
                - parameters: Algorithm-specific parameters
        
        Note:
            After movement, fitness is automatically recalculated.
        """
        # Extract parameters
        global_best = kwargs.get('global_best')
        iteration = kwargs.get('iteration', 0)
        params = kwargs.get('parameters', {})
        
        # Example movement logic (customize for specific algorithm)
        if self.velocity is not None and global_best is not None:
            # Update velocity
            w = params.get('inertia', 0.7)
            c1 = params.get('cognitive', 2.0)
            c2 = params.get('social', 2.0)
            
            r1 = np.random.random(len(self.position))
            r2 = np.random.random(len(self.position))
            
            self.velocity = (
                w * self.velocity +
                c1 * r1 * (self.personal_best - self.position) +
                c2 * r2 * (global_best.position - self.position)
            )
            
            # Update position
            self.position = self.position + self.velocity
            
            # Apply bounds
            self.position = np.clip(self.position, 0, 1)
        
        # Update fitness after movement
        self._evaluate_fitness()
        
        # Update personal best if improved
        if self.fitness < self.personal_best_fitness:
            self.personal_best = self.position.copy()
            self.personal_best_fitness = self.fitness
    
    def local_search(self) -> None:
        """
        Apply local search to improve solution (optional).
        
        This method can be used to apply problem-specific local
        search operators to improve solution quality.
        """
        # Example: 2-opt for VRP
        if hasattr(self.problem, 'apply_2opt'):
            improved_solution = self.problem.apply_2opt(self.solution)
            improved_position = self.problem.encode_solution(improved_solution)
            
            # Evaluate improvement
            temp_fitness = self.problem.evaluate(improved_solution)
            if temp_fitness < self.fitness:
                self.position = improved_position
                self.solution = improved_solution
                self.fitness = temp_fitness


class AlgorithmAbbreviation(MetaheuristicAlgorithm):
    """
    Full Algorithm Name (ABBREVIATION) implementation.
    
    This algorithm mimics [brief description of natural phenomenon or
    mathematical concept] to solve optimization problems. It was proposed
    by [Authors] in [Year] and has shown effectiveness in solving
    [problem types].
    
    Key features:
        - Feature 1: Description
        - Feature 2: Description
        - Feature 3: Description
    
    Parameters:
        problem: Problem instance to solve
        population_size: Number of individuals in the population (default: 30)
        max_iterations: Maximum number of iterations (default: 100)
        specific_param1: Description of parameter 1 (default: 0.5)
            Valid range: (0, 1)
        specific_param2: Description of parameter 2 (default: 2.0)
            Valid range: [1, 5]
        seed: Random seed for reproducibility (default: None)
    
    Attributes:
        global_best: Best solution found across all individuals
        param_schedule: Parameter adaptation schedule (if applicable)
        convergence_threshold: Threshold for early stopping
    
    References:
        .. [1] Author et al. (Year). "Title". Journal.
        .. [2] Author2 et al. (Year). "Title2". Conference.
    """
    
    def __init__(
        self,
        problem,
        population_size: int = 30,
        max_iterations: int = 100,
        specific_param1: float = 0.5,
        specific_param2: float = 2.0,
        use_local_search: bool = False,
        adaptive_parameters: bool = False,
        seed: Optional[int] = None
    ):
        """
        Initialize Algorithm with given parameters.
        
        Args:
            problem: Problem instance to solve
            population_size: Number of individuals (must be > 0)
            max_iterations: Maximum iterations (must be > 0)
            specific_param1: Description (must be in valid range)
            specific_param2: Description (must be in valid range)
            use_local_search: Whether to apply local search
            adaptive_parameters: Whether to adapt parameters during run
            seed: Random seed for reproducibility
        
        Raises:
            ValueError: If parameters are outside valid ranges
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validate algorithm-specific parameters
        if not 0 < specific_param1 < 1:
            raise ValueError(
                f"specific_param1 must be in (0, 1), got {specific_param1}"
            )
        if not 1 <= specific_param2 <= 5:
            raise ValueError(
                f"specific_param2 must be in [1, 5], got {specific_param2}"
            )
        
        # Store parameters
        self.specific_param1 = specific_param1
        self.specific_param2 = specific_param2
        self.use_local_search = use_local_search
        self.adaptive_parameters = adaptive_parameters
        
        # Algorithm-specific attributes
        self.global_best: Optional[Individual] = None
        self.convergence_threshold: float = 1e-6
        self.stagnation_counter: int = 0
        self.max_stagnation: int = 20
        
        # Parameter schedules (if adaptive)
        self.param_schedule: Dict[str, List[float]] = {}
        if adaptive_parameters:
            self._initialize_parameter_schedules()
        
        # Performance tracking
        self.diversity_history: List[float] = []
        self.convergence_rate: float = 0.0
        
        logger.info(
            f"Initialized {self.__class__.__name__} with "
            f"pop_size={population_size}, max_iter={max_iterations}, "
            f"param1={specific_param1}, param2={specific_param2}"
        )
    
    def _create_individual(self) -> Individual:
        """
        Create algorithm-specific individual.
        
        Returns:
            New individual with algorithm-specific attributes
        """
        return AlgorithmNameIndividual(
            self._generate_random_position(),
            self.problem
        )
    
    def _initialize_parameter_schedules(self) -> None:
        """Initialize adaptive parameter schedules."""
        # Example: Linear decrease for param1
        self.param_schedule['param1'] = np.linspace(
            self.specific_param1,
            self.specific_param1 * 0.3,
            self.max_iterations
        ).tolist()
        
        # Example: Exponential increase for param2
        self.param_schedule['param2'] = (
            self.specific_param2 * np.exp(
                np.linspace(0, 1, self.max_iterations)
            )
        ).tolist()
    
    def initialize_population(self) -> None:
        """
        Initialize population with algorithm-specific setup.
        
        This method extends the base initialization with any
        algorithm-specific requirements.
        """
        super().initialize_population()
        
        # Find initial global best
        self.global_best = min(self.population, key=lambda x: x.fitness)
        
        # Algorithm-specific initialization
        self._initialize_algorithm_structures()
        
        logger.debug(f"Initial best fitness: {self.global_best.fitness:.4f}")
    
    def _initialize_algorithm_structures(self) -> None:
        """Initialize any algorithm-specific data structures."""
        # Example: Initialize pheromone matrix for ant-based algorithms
        # self.pheromone_matrix = np.ones((n, n)) * initial_pheromone
        
        # Example: Initialize neighborhood structure
        # self.neighborhoods = self._create_neighborhoods()
        
        pass
    
    def _update_parameters(self, iteration: int) -> Dict[str, float]:
        """
        Update algorithm parameters based on iteration.
        
        Args:
            iteration: Current iteration number
        
        Returns:
            Dictionary of current parameter values
        """
        params = {
            'param1': self.specific_param1,
            'param2': self.specific_param2
        }
        
        if self.adaptive_parameters and self.param_schedule:
            if 'param1' in self.param_schedule:
                params['param1'] = self.param_schedule['param1'][iteration]
            if 'param2' in self.param_schedule:
                params['param2'] = self.param_schedule['param2'][iteration]
        
        return params
    
    def _calculate_diversity(self) -> float:
        """
        Calculate population diversity.
        
        Returns:
            Diversity measure (0 = converged, 1 = maximum diversity)
        """
        if len(self.population) < 2:
            return 0.0
        
        # Calculate pairwise distances
        positions = np.array([ind.position for ind in self.population])
        mean_position = np.mean(positions, axis=0)
        
        # Average distance from centroid
        distances = np.linalg.norm(positions - mean_position, axis=1)
        diversity = np.mean(distances)
        
        # Normalize by problem dimension
        max_distance = np.sqrt(len(mean_position))
        normalized_diversity = diversity / max_distance
        
        return min(normalized_diversity, 1.0)
    
    def _check_convergence(self) -> bool:
        """
        Check if algorithm has converged.
        
        Returns:
            True if converged, False otherwise
        """
        # Check fitness improvement
        if len(self.fitness_history) > self.max_stagnation:
            recent_best = min(self.fitness_history[-self.max_stagnation:])
            previous_best = min(
                self.fitness_history[-2*self.max_stagnation:-self.max_stagnation]
            )
            
            improvement = abs(previous_best - recent_best)
            if improvement < self.convergence_threshold:
                self.stagnation_counter += 1
            else:
                self.stagnation_counter = 0
        
        # Check diversity
        diversity = self._calculate_diversity()
        if diversity < 0.01:  # Population has converged
            logger.info(f"Population converged (diversity={diversity:.4f})")
            return True
        
        # Check stagnation
        if self.stagnation_counter >= self.max_stagnation:
            logger.info(f"Stagnation detected ({self.stagnation_counter} iterations)")
            return True
        
        return False
    
    def _apply_algorithm_operators(self, iteration: int) -> None:
        """
        Apply algorithm-specific operators.
        
        This method implements the core algorithm logic that
        distinguishes this algorithm from others.
        
        Args:
            iteration: Current iteration number
        """
        # Get current parameters
        params = self._update_parameters(iteration)
        
        # Apply main algorithm logic
        for individual in self.population:
            # Example: Apply movement operator
            individual.move(
                global_best=self.global_best,
                iteration=iteration,
                parameters=params,
                neighbors=self._get_neighbors(individual)
            )
            
            # Optional: Apply local search
            if self.use_local_search and np.random.random() < 0.1:
                individual.local_search()
        
        # Update global best
        current_best = min(self.population, key=lambda x: x.fitness)
        if current_best.fitness < self.global_best.fitness:
            self.global_best = current_best
            logger.debug(
                f"New best found at iteration {iteration}: "
                f"{self.global_best.fitness:.4f}"
            )
        
        # Apply population-level operators
        self._apply_population_operators(iteration)
    
    def _get_neighbors(self, individual: Individual) -> List[Individual]:
        """
        Get neighbors of an individual (if applicable).
        
        Args:
            individual: Individual to find neighbors for
        
        Returns:
            List of neighboring individuals
        """
        # Example: k-nearest neighbors
        k = 5
        distances = []
        
        for other in self.population:
            if other is not individual:
                dist = np.linalg.norm(
                    individual.position - other.position
                )
                distances.append((dist, other))
        
        distances.sort(key=lambda x: x[0])
        return [ind for _, ind in distances[:k]]
    
    def _apply_population_operators(self, iteration: int) -> None:
        """
        Apply population-level operators.
        
        Examples include selection, crossover, mutation,
        or population resizing.
        
        Args:
            iteration: Current iteration number
        """
        # Example: Worst individual replacement
        if iteration % 10 == 0:
            worst_idx = np.argmax([ind.fitness for ind in self.population])
            self.population[worst_idx] = self._create_individual()
            logger.debug("Replaced worst individual")
        
        # Example: Population perturbation for diversity
        if self.stagnation_counter > 5:
            num_perturb = int(self.population_size * 0.2)
            indices = self.random_state.choice(
                self.population_size,
                num_perturb,
                replace=False
            )
            for idx in indices:
                # Perturb position
                noise = self.random_state.normal(0, 0.1, len(self.population[0].position))
                self.population[idx].position += noise
                self.population[idx].position = np.clip(
                    self.population[idx].position, 0, 1
                )
                self.population[idx]._evaluate_fitness()
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the algorithm.
        
        Returns:
            Dictionary containing:
                - best_fitness: Best fitness value found
                - best_solution: Best solution found
                - convergence_iteration: Iteration where convergence occurred
                - fitness_history: History of best fitness values
                - diversity_history: History of population diversity
                - execution_time: Total execution time in seconds
                - algorithm_info: Algorithm configuration and metadata
        """
        import time
        start_time = time.time()
        
        # Initialize
        self.initialize_population()
        convergence_iteration = self.max_iterations
        
        # Main optimization loop
        for iteration in range(self.max_iterations):
            # Record diversity
            diversity = self._calculate_diversity()
            self.diversity_history.append(diversity)
            
            # Apply algorithm operators
            self._apply_algorithm_operators(iteration)
            
            # Update tracking
            self._update_best_solution()
            
            # Check convergence
            if self._check_convergence():
                convergence_iteration = iteration
                logger.info(f"Algorithm converged at iteration {iteration}")
                break
            
            # Progress logging
            if iteration % 50 == 0:
                logger.info(
                    f"Iteration {iteration}: "
                    f"Best={self.best_fitness:.4f}, "
                    f"Diversity={diversity:.4f}"
                )
        
        # Calculate final metrics
        execution_time = time.time() - start_time
        
        # Prepare comprehensive results
        results = self._prepare_results()
        results.update({
            'convergence_iteration': convergence_iteration,
            'diversity_history': self.diversity_history,
            'execution_time': execution_time,
            'final_population': [
                {
                    'position': ind.position.tolist(),
                    'fitness': float(ind.fitness)
                }
                for ind in self.population
            ],
            'algorithm_info': {
                'name': self.__class__.__name__,
                'parameters': {
                    'population_size': self.population_size,
                    'max_iterations': self.max_iterations,
                    'specific_param1': self.specific_param1,
                    'specific_param2': self.specific_param2,
                    'use_local_search': self.use_local_search,
                    'adaptive_parameters': self.adaptive_parameters
                },
                'problem': str(self.problem),
                'seed': self.seed
            }
        })
        
        logger.info(
            f"Optimization completed: "
            f"Best fitness = {results['best_fitness']:.4f}, "
            f"Time = {execution_time:.2f}s"
        )
        
        return results


# Algorithm registration
if __name__ == "__main__":
    # Example usage and testing
    from problems.vrp import VRPProblem
    
    # Load problem
    problem = VRPProblem("E-n22-k4")
    
    # Create algorithm instance
    algorithm = AlgorithmAbbreviation(
        problem=problem,
        population_size=50,
        max_iterations=200,
        specific_param1=0.7,
        specific_param2=2.0,
        use_local_search=True,
        adaptive_parameters=True,
        seed=42
    )
    
    # Run algorithm
    print("Running Algorithm Name optimization...")
    result = algorithm.run()
    
    # Display results
    print(f"\nOptimization Results:")
    print(f"Best Fitness: {result['best_fitness']:.2f}")
    print(f"Convergence Iteration: {result['convergence_iteration']}")
    print(f"Execution Time: {result['execution_time']:.2f} seconds")
    print(f"Final Diversity: {result['diversity_history'][-1]:.4f}")
    
    # Verify solution
    solution = result['best_solution']
    if hasattr(problem, 'validate_solution'):
        is_valid = problem.validate_solution(solution)
        print(f"Solution Valid: {is_valid}")