# Algorithm Mixins Documentation

## Overview

The algorithm mixins system provides reusable components for implementing metaheuristic algorithms for the Vehicle Routing Problem (VRP). This modular approach promotes code reuse, consistency, and easier maintenance across different algorithm implementations.

## Architecture

The mixin system is organized into four main categories:

1. **VRP Operators** - Problem-specific operators for VRP
2. **Selection Operators** - Population selection strategies
3. **Initialization Operators** - Solution initialization methods
4. **Convergence Operators** - Convergence control and monitoring

## VRP Operators

### VRPCrossoverMixin

Provides crossover operators for permutation-based representations:

```python
from algorithms.mixins import VRPCrossoverMixin

class MyAlgorithm(VRPCrossoverMixin, BaseAlgorithm):
    def crossover(self, parent1, parent2):
        # Order Crossover (OX)
        child1, child2 = self.order_crossover(parent1, parent2)
        
        # Partially Mapped Crossover (PMX)
        child1, child2 = self.pmx_crossover(parent1, parent2)
        
        # Route-based crossover
        routes1, routes2 = self.route_based_crossover(routes1, routes2)
```

### VRPMutationMixin

Provides mutation operators for VRP solutions:

```python
from algorithms.mixins import VRPMutationMixin

class MyAlgorithm(VRPMutationMixin, BaseAlgorithm):
    def mutate(self, individual):
        # Various mutation operators
        mutated = self.swap_mutation(individual)
        mutated = self.insertion_mutation(individual)
        mutated = self.inversion_mutation(individual)
        mutated = self.scramble_mutation(individual, probability=0.3)
```

### VRPLocalSearchMixin

Provides local search operators for route improvement:

```python
from algorithms.mixins import VRPLocalSearchMixin

class MyAlgorithm(VRPLocalSearchMixin, BaseAlgorithm):
    def improve_solution(self, solution):
        for route in solution.routes:
            # Apply various local search operators
            improved_route = self.two_opt(route)
            improved_route = self.three_opt(route)
            improved_route = self.or_opt(route, segment_size=2)
        
        # Inter-route improvements
        self.relocate_operator(solution.routes)
        self.exchange_operator(solution.routes)
```

### VRPRepairMixin

Provides solution repair mechanisms:

```python
from algorithms.mixins import VRPRepairMixin

class MyAlgorithm(VRPRepairMixin, BaseAlgorithm):
    def ensure_feasibility(self, solution):
        # Repair capacity violations
        repaired = self.repair_capacity_violations(solution)
        
        # Ensure all customers are visited
        complete = self.repair_missing_customers(solution)
```

### VRPDiversityMixin

Provides diversity measurement and maintenance:

```python
from algorithms.mixins import VRPDiversityMixin

class MyAlgorithm(VRPDiversityMixin, BaseAlgorithm):
    def maintain_diversity(self, population):
        # Measure diversity
        diversity = self.population_diversity(population)
        
        # Apply diversity preservation
        if diversity < threshold:
            self.apply_diversity_preservation(population)
```

## Selection Operators

### TournamentSelectionMixin

Tournament-based selection strategies:

```python
from algorithms.mixins import TournamentSelectionMixin

class MyAlgorithm(TournamentSelectionMixin, BaseAlgorithm):
    def select_parents(self, population):
        # Standard tournament
        selected = self.tournament_selection(population, tournament_size=3, n_select=2)
        
        # Binary tournament
        winner = self.binary_tournament(population)
        
        # Probabilistic tournament
        selected = self.probabilistic_tournament(population, selection_pressure=0.8)
```

### RouletteSelectionMixin

Fitness-proportionate selection:

```python
from algorithms.mixins import RouletteSelectionMixin

class MyAlgorithm(RouletteSelectionMixin, BaseAlgorithm):
    def select_parents(self, population):
        # Roulette wheel selection
        selected = self.roulette_wheel_selection(population, n_select=2)
        
        # Stochastic universal sampling (reduced variance)
        selected = self.stochastic_universal_sampling(population, n_select=10)
```

### RankSelectionMixin

Rank-based selection strategies:

```python
from algorithms.mixins import RankSelectionMixin

class MyAlgorithm(RankSelectionMixin, BaseAlgorithm):
    def select_parents(self, population):
        # Linear ranking
        selected = self.rank_selection(population, selection_pressure=2.0)
        
        # Exponential ranking
        selected = self.exponential_rank_selection(population, base=0.95)
```

### ElitismMixin

Elite preservation strategies:

```python
from algorithms.mixins import ElitismMixin

class MyAlgorithm(ElitismMixin, BaseAlgorithm):
    def evolve_population(self, population, offspring):
        # Select elite individuals
        elite = self.select_elite(population, n_elite=5)
        
        # Generational replacement with elitism
        new_pop = self.generational_replacement(population, offspring, elitism_rate=0.1)
        
        # Steady-state replacement
        new_pop = self.steady_state_replacement(population, offspring)
```

## Initialization Operators

### RandomInitializationMixin

Random solution generation:

```python
from algorithms.mixins import RandomInitializationMixin

class MyAlgorithm(RandomInitializationMixin, BaseAlgorithm):
    def initialize_population(self):
        for _ in range(self.population_size):
            # Random permutation
            perm = self.random_permutation(n_customers)
            
            # Random keys for ordinal encoding
            keys = self.random_keys_initialization(n_customers)
            
            # Random routes respecting capacity
            routes = self.random_routes_initialization(
                n_customers, capacity, demands
            )
```

### NearestNeighborInitializationMixin

Greedy construction heuristics:

```python
from algorithms.mixins import NearestNeighborInitializationMixin

class MyAlgorithm(NearestNeighborInitializationMixin, BaseAlgorithm):
    def generate_initial_solution(self):
        # Basic nearest neighbor
        routes = self.nearest_neighbor_solution(
            distance_matrix, capacity, demands
        )
        
        # Multiple starting points
        best_routes = self.parallel_nearest_neighbor(
            distance_matrix, capacity, demands, n_starts=5
        )
        
        # Randomized version
        routes = self.randomized_nearest_neighbor(
            distance_matrix, capacity, demands, randomization_factor=0.1
        )
```

### SavingsInitializationMixin

Clarke-Wright savings algorithm:

```python
from algorithms.mixins import SavingsInitializationMixin

class MyAlgorithm(SavingsInitializationMixin, BaseAlgorithm):
    def generate_initial_solution(self):
        # Classic savings algorithm
        routes = self.savings_algorithm(distance_matrix, capacity, demands)
        
        # Parallel version with lambda parameter
        routes = self.parallel_savings(
            distance_matrix, capacity, demands, lambda_param=0.8
        )
```

### ClusterInitializationMixin

Clustering-based initialization:

```python
from algorithms.mixins import ClusterInitializationMixin

class MyAlgorithm(ClusterInitializationMixin, BaseAlgorithm):
    def generate_initial_solution(self):
        # Sweep algorithm
        routes = self.sweep_algorithm(
            coordinates, capacity, demands, start_angle=0.0
        )
        
        # Cluster-first route-second
        routes = self.cluster_first_route_second(
            distance_matrix, capacity, demands, n_clusters=5
        )
```

## Convergence Operators

### ConvergenceTrackingMixin

Monitor and track algorithm convergence:

```python
from algorithms.mixins import ConvergenceTrackingMixin

class MyAlgorithm(ConvergenceTrackingMixin, BaseAlgorithm):
    def run(self):
        for iteration in range(max_iterations):
            # Track iteration metrics
            self.track_iteration(population, iteration, execution_time)
            
            # Get convergence metrics
            metrics = self.get_convergence_metrics()
            print(f"Convergence rate: {metrics['convergence_rate']}")
            
            # Check stagnation
            if self.get_stagnation_counter() > 50:
                print("Algorithm stagnated")
        
        # Plot convergence history
        self.plot_convergence(save_path="convergence.png")
```

### AdaptiveParameterMixin

Dynamic parameter adjustment:

```python
from algorithms.mixins import AdaptiveParameterMixin

class MyAlgorithm(AdaptiveParameterMixin, BaseAlgorithm):
    def __init__(self):
        super().__init__()
        
        # Register adaptive parameters
        self.register_adaptive_parameter(
            'mutation_rate', initial_value=0.2, min_value=0.01, max_value=0.5,
            adaptation_rule=self.exponential_decay_rule(0.99)
        )
        
        # Performance-based adaptation
        self.register_adaptive_parameter(
            'population_size', initial_value=50, min_value=20, max_value=200,
            adaptation_rule=self.performance_based_rule(1.1, 0.9)
        )
    
    def iterate(self):
        # Update parameters
        self.update_adaptive_parameters(
            iteration, total_iterations, performance_metrics
        )
        
        # Use current values
        mutation_rate = self.get_adaptive_parameter('mutation_rate')
```

### StagnationDetectionMixin

Detect and respond to stagnation:

```python
from algorithms.mixins import StagnationDetectionMixin

class MyAlgorithm(StagnationDetectionMixin, BaseAlgorithm):
    def __init__(self):
        super().__init__()
        
        # Configure detection
        self.configure_stagnation_detection(window=20, threshold=0.001)
        
        # Register callback
        self.register_stagnation_callback(self.on_stagnation)
    
    def iterate(self):
        # Check for stagnation
        stagnation = self.check_stagnation(best_fitness, diversity)
        
        if stagnation['complete_stagnation']:
            # Take action
            self.increase_diversity()
```

### RestartMixin

Population restart strategies:

```python
from algorithms.mixins import RestartMixin

class MyAlgorithm(RestartMixin, BaseAlgorithm):
    def __init__(self):
        super().__init__()
        
        # Configure restart
        self.configure_restart(
            enabled=True, threshold=50, 
            strategy='adaptive', preserve_elite=3
        )
    
    def iterate(self):
        # Check restart condition
        if self.check_restart_condition(stagnation_count):
            # Perform restart
            self.population = self.perform_restart(population, iteration)
            
        # Get restart statistics
        stats = self.get_restart_statistics()
        print(f"Total restarts: {stats['total_restarts']}")
```

## Complete Example

Here's a complete example showing how to create an enhanced algorithm using multiple mixins:

```python
from algorithms.genetic_algorithm_v2 import GeneticAlgorithmV2
from algorithms.mixins import (
    VRPCrossoverMixin, VRPMutationMixin, VRPLocalSearchMixin,
    TournamentSelectionMixin, ElitismMixin,
    ConvergenceTrackingMixin, AdaptiveParameterMixin,
    StagnationDetectionMixin, RestartMixin
)

class EnhancedGA(
    VRPCrossoverMixin,
    VRPMutationMixin,
    VRPLocalSearchMixin,
    TournamentSelectionMixin,
    ElitismMixin,
    ConvergenceTrackingMixin,
    AdaptiveParameterMixin,
    StagnationDetectionMixin,
    RestartMixin,
    GeneticAlgorithmV2
):
    def __init__(self, problem, **kwargs):
        super().__init__(problem, **kwargs)
        
        # Configure adaptive mutation
        self.register_adaptive_parameter(
            'mutation_rate', 0.2, 0.01, 0.5,
            self.performance_based_rule()
        )
        
        # Configure stagnation detection
        self.configure_stagnation_detection(window=20)
        
        # Configure restart
        self.configure_restart(enabled=True, threshold=50)
    
    def run(self):
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            # Track convergence
            self.track_iteration(self.population, iteration)
            
            # Update adaptive parameters
            self.update_adaptive_parameters(iteration, self.max_iterations)
            
            # Check stagnation
            stagnation = self.check_stagnation(self.best_fitness)
            
            # Restart if needed
            if self.check_restart_condition(self.get_stagnation_counter()):
                self.population = self.perform_restart(self.population, iteration)
            
            # Evolution step
            offspring = []
            
            # Select parents using tournament
            for _ in range(self.population_size // 2):
                parent1 = self.tournament_selection(self.population, 3, 1)[0]
                parent2 = self.tournament_selection(self.population, 3, 1)[0]
                
                # Crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self.order_crossover(
                        parent1.position, parent2.position
                    )
                    offspring.extend([child1, child2])
                
                # Mutation
                mutation_rate = self.get_adaptive_parameter('mutation_rate')
                for child in offspring:
                    if random.random() < mutation_rate:
                        child.position = self.scramble_mutation(child.position)
                
                # Local search
                if random.random() < 0.1:
                    for route in child.routes:
                        self.two_opt(route)
            
            # Replace population with elitism
            self.population = self.elitist_replacement(
                self.population, offspring, n_elite=3
            )
        
        return self.best_solution
```

## Best Practices

1. **Mixin Order**: When using multiple mixins, order matters. Place more specific mixins before general ones:
   ```python
   class MyAlgorithm(VRPCrossoverMixin, SelectionMixin, BaseAlgorithm):
   ```

2. **Initialization**: Always call `super().__init__()` in your `__init__` method to ensure all mixins are properly initialized.

3. **Parameter Conflicts**: If multiple mixins use the same parameter names, be explicit about which one you're using.

4. **Performance**: Some mixins (like local search) can be computationally expensive. Use them judiciously.

5. **Testing**: Test mixin combinations thoroughly, as interactions between mixins can sometimes produce unexpected behavior.

## Adding New Mixins

To create a new mixin:

1. Create a class that follows the mixin naming convention (`*Mixin`)
2. Implement focused, reusable functionality
3. Use descriptive method names that don't conflict with common names
4. Document all methods thoroughly
5. Add appropriate type hints
6. Create unit tests

Example:

```python
class MyCustomMixin:
    """Mixin that provides custom functionality."""
    
    def my_custom_operation(self, individual: Any) -> Any:
        """
        Performs custom operation on individual.
        
        Args:
            individual: Individual to operate on
            
        Returns:
            Modified individual
        """
        # Implementation here
        return modified_individual
```

## Performance Considerations

- **Local Search**: Use sparingly (e.g., 5-10% of population per iteration)
- **Diversity Calculations**: Can be expensive for large populations
- **Adaptive Parameters**: Update less frequently for stable behavior
- **Restart Strategies**: Full restarts are expensive; prefer partial restarts

## Troubleshooting

Common issues and solutions:

1. **Method Resolution Order (MRO) errors**: Check mixin order and avoid diamond inheritance
2. **Missing attributes**: Ensure all mixins call `super().__init__()`
3. **Performance degradation**: Profile code to identify expensive operations
4. **Convergence issues**: Adjust parameters for your specific problem size

## Future Extensions

Planned additions to the mixin system:

1. **Multi-objective mixins** for Pareto-based selection
2. **Parallel execution mixins** for distributed computing
3. **Machine learning mixins** for parameter prediction
4. **Visualization mixins** for real-time monitoring