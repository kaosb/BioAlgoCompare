"""
Template for creating new bio-inspired algorithms using the improved architecture.
This file demonstrates best practices and reduces code duplication.
"""

import numpy as np
from typing import Optional
from algorithms.base_v2_migration import Individual, MetaheuristicAlgorithm, MoveContext, AbstractProblem


class TemplateIndividual(Individual):
    """
    Individual for the Template Algorithm.
    Replace 'Template' with your algorithm name (e.g., 'Ant', 'Bee', 'Wolf').
    """
    
    def initialize(self) -> None:
        """Initialize the individual's position and algorithm-specific attributes."""
        # Initialize position within problem bounds
        self.position = self.problem.random_solution()
        
        # Add any algorithm-specific attributes here
        # Example: self.velocity = np.zeros(self.problem.dimension)
        # Example: self.memory = []
        # Example: self.fitness_history = []
    
    def move(self, context: MoveContext) -> None:
        """
        Move the individual according to the algorithm's rules.
        
        Args:
            context: MoveContext containing all necessary parameters
        """
        # Get common parameters
        iteration = context.iteration
        max_iterations = context.max_iterations
        population = context.population
        best_individual = context.best_individual
        
        # Get algorithm-specific parameters from context
        # Example: alpha = context.get_param('alpha', 0.5)
        # Example: beta = context.get_param('beta', 0.8)
        
        # Implement your movement logic here
        # This is where the bio-inspired behavior is implemented
        
        # Example movement (random walk - replace with your algorithm's logic):
        step_size = 1.0 - (iteration / max_iterations)  # Decreasing step size
        random_direction = np.random.uniform(-1, 1, self.problem.dimension)
        self.position += step_size * random_direction
        
        # Ensure position stays within bounds
        self.position = self.problem.repair(self.position)


class TEMPLATEV2(MetaheuristicAlgorithm[TemplateIndividual]):
    """
    Template for Bio-Inspired Algorithm.
    
    Replace this with your algorithm's description, including:
    - The biological inspiration
    - Key parameters and their meanings
    - Any special characteristics
    
    References:
        [1] Author, A. (Year). Title of the paper. Journal Name.
    """
    
    def __init__(
        self,
        problem: AbstractProblem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None,
        # Add algorithm-specific parameters here
        alpha: float = 0.5,
        beta: float = 0.8,
    ):
        """
        Initialize the Template Algorithm.
        
        Args:
            problem: The optimization problem to solve
            population_size: Size of the population
            max_iterations: Maximum number of iterations
            seed: Random seed for reproducibility
            alpha: Algorithm-specific parameter (describe its purpose)
            beta: Another algorithm-specific parameter
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Store algorithm-specific parameters
        self.alpha = alpha
        self.beta = beta
        
        # Initialize any algorithm-specific attributes
        # Example: self.leaders = []
        # Example: self.archive = []
    
    def _create_individual(self) -> TemplateIndividual:
        """Create a new individual for this algorithm."""
        return TemplateIndividual(self.problem)
    
    def _create_move_context(self) -> MoveContext:
        """
        Create context with algorithm-specific parameters.
        
        This method is called once per iteration to create the context
        that will be passed to all individuals' move() method.
        """
        context = super()._create_move_context()
        
        # Add algorithm-specific parameters to context
        context.set_param('alpha', self.alpha)
        context.set_param('beta', self.beta)
        
        # Add any iteration-dependent parameters
        # Example: exploration_rate = 1.0 - (self.iteration / self.max_iterations)
        # context.set_param('exploration_rate', exploration_rate)
        
        return context
    
    def _should_sort_population(self) -> bool:
        """
        Determine if population should be sorted after each iteration.
        
        Return True if your algorithm needs a sorted population
        (e.g., for selecting best individuals, tournament selection, etc.)
        """
        return False  # Change to True if needed
    
    def initialize_population(self) -> None:
        """
        Initialize the population.
        
        Override this method only if you need special initialization logic.
        Otherwise, the base class implementation is sufficient.
        """
        super().initialize_population()
        
        # Add any algorithm-specific initialization here
        # Example: Select initial leaders
        # Example: Initialize pheromone matrix
        # Example: Create initial archive
    
    def update_population(self) -> None:
        """
        Update the population for one iteration.
        
        Override this method only if you need special update logic.
        Otherwise, the base class implementation is sufficient.
        """
        super().update_population()
        
        # Add any algorithm-specific updates here
        # Example: Update pheromone levels
        # Example: Update archive
        # Example: Apply selection pressure
    
    def _on_iteration_complete(self) -> None:
        """
        Optional callback executed after each iteration.
        
        Use this for:
        - Logging/debugging
        - Adaptive parameter updates
        - Special selection mechanisms
        """
        # Example: Adaptive parameter update
        # self.alpha = self.alpha * 0.99  # Decay alpha
        
        # Example: Log progress every 10 iterations
        # if self.iteration % 10 == 0:
        #     print(f"Iteration {self.iteration}: Best = {self.best_solution.fitness()}")
        pass


# Example usage and testing
if __name__ == "__main__":
    # This section demonstrates how to use the algorithm
    from algorithms.base_v2_migration import AbstractProblem
    import numpy as np
    
    # Create a simple test problem
    class SphereProblem(AbstractProblem):
        def __init__(self, dimension: int = 10):
            super().__init__(f"Sphere{dimension}D")
            self._dimension = dimension
            self._lower_bounds = np.full(dimension, -5.0)
            self._upper_bounds = np.full(dimension, 5.0)
        
        @property
        def dimension(self) -> int:
            return self._dimension
        
        @property
        def lower_bounds(self) -> np.ndarray:
            return self._lower_bounds
        
        @property
        def upper_bounds(self) -> np.ndarray:
            return self._upper_bounds
        
        def evaluate(self, solution: np.ndarray) -> float:
            return np.sum(solution ** 2)
    
    # Create and run the algorithm
    problem = SphereProblem(dimension=30)
    algorithm = TEMPLATEV2(
        problem=problem,
        population_size=50,
        max_iterations=100,
        seed=42,
        alpha=0.7,
        beta=0.3
    )
    
    # Execute
    best_solution = algorithm.execute()
    
    # Print results
    print(f"Best fitness: {best_solution.fitness()}")
    print(f"Execution time: {algorithm.get_execution_time():.2f} seconds")
    print(f"Convergence: {algorithm.convergence_curve[-1]}")