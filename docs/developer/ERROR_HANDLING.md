# Error Handling System Documentation

## Overview

The error handling system provides robust error management capabilities for bio-inspired algorithms. It includes custom exceptions, validation decorators, recovery strategies, and comprehensive error tracking to ensure algorithms can handle unexpected situations gracefully.

## Architecture

The error handling system consists of three main components:

1. **Core Error Handling** (`utils/error_handling.py`)
   - Custom exception hierarchy
   - Validation decorators
   - Numeric stability checks
   - Recovery mechanisms
   - Safe algorithm wrapper

2. **Error Handling Mixin** (`algorithms/mixins/error_handling.py`)
   - Integration with algorithm classes
   - Automatic validation
   - Recovery strategies
   - Error tracking

3. **Integration Tools**
   - Decorators for method protection
   - Safe execution wrappers
   - Fallback mechanisms

## Custom Exceptions

### Exception Hierarchy

```
AlgorithmError (base)
├── InitializationError
├── ConvergenceError
├── ParameterError
├── PopulationError
├── FitnessError
├── OperatorError
├── ConstraintViolationError
├── NumericError
├── TimeoutError
└── MemoryError
```

### Usage Examples

```python
from utils.error_handling import (
    AlgorithmError, InitializationError, ParameterError
)

# Creating custom errors with context
error = AlgorithmError(
    "Operation failed",
    algorithm="GeneticAlgorithm",
    iteration=42,
    details={'population_size': 50}
)

# Raising specific errors
if population_size <= 0:
    raise ParameterError(
        "Population size must be positive",
        algorithm="GA",
        details={'value': population_size}
    )
```

## Validation Decorators

### Parameter Validation

```python
from utils.error_handling import validate_parameters

class MyAlgorithm:
    @validate_parameters(
        population_size=lambda x: x > 0,
        mutation_rate=lambda x: 0 <= x <= 1,
        iterations=lambda x: x > 0 and x <= 10000
    )
    def __init__(self, population_size, mutation_rate, iterations):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.iterations = iterations
```

### Error Handling Decorator

```python
from utils.error_handling import handle_errors

class MyAlgorithm:
    @handle_errors(
        algorithm_name="MyAlgorithm",
        fallback_value=None,
        log_errors=True,
        reraise=False
    )
    def risky_operation(self):
        # Operation that might fail
        return 1 / self.some_value
```

## Numeric Stability

### Checking Numeric Values

```python
from utils.error_handling import check_numeric_stability

# Check scalar values
check_numeric_stability(
    value=fitness_value,
    name="fitness",
    check_nan=True,
    check_inf=True,
    min_value=0.0,
    max_value=1e6
)

# Check arrays
check_numeric_stability(
    value=position_vector,
    name="position",
    check_nan=True,
    check_inf=True,
    min_value=-10.0,
    max_value=10.0
)
```

## Error Handling Mixin

### Basic Usage

```python
from algorithms.mixins import ErrorHandlingMixin

class RobustAlgorithm(ErrorHandlingMixin, BaseAlgorithm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validate initial state
        self.validate_algorithm_state()
    
    def iterate(self):
        # Use safe operations
        result = self.safe_operation(
            self.complex_calculation,
            error_type='numeric'
        )
        
        # Safe fitness evaluation
        fitness = self.safe_fitness_evaluation(individual)
```

### Configuration Options

```python
algorithm = RobustAlgorithm(
    problem=problem,
    # Error handling options
    error_tolerance=1e-10,          # Numeric tolerance
    max_consecutive_errors=5,       # Max errors before stopping
    enable_recovery=True            # Enable automatic recovery
)
```

### Available Methods

1. **Validation Methods**
   - `validate_algorithm_state()`: Validate complete algorithm state
   - `validate_population()`: Validate population integrity
   - `validate_individual(individual)`: Validate single individual
   - `validate_problem()`: Validate problem instance

2. **Safe Operations**
   - `safe_operation(func, *args, error_type='general')`: Execute with error handling
   - `safe_fitness_evaluation(individual)`: Evaluate fitness safely
   - `with_error_handling` decorator: Add error handling to any method

3. **Recovery Methods**
   - `_recover_population(error)`: Recover from population errors
   - `_recover_numeric(error)`: Fix numeric instabilities
   - `_recover_convergence(error)`: Handle convergence issues
   - `_recover_fitness(error)`: Handle fitness evaluation errors

4. **Error Tracking**
   - `get_error_summary()`: Get error statistics
   - `clear_error_history()`: Reset error tracking

## Recovery Strategies

### Population Recovery

When population errors occur, the system can:
1. Reinitialize the entire population
2. Create new individuals to replace corrupted ones
3. Use fallback initialization methods

```python
def _recover_population(self, error):
    # Try to reinitialize
    if hasattr(self, 'initialize_population'):
        self.initialize_population()
        return self.population
    
    # Create minimal valid population
    if hasattr(self, '_create_individual'):
        new_population = []
        for _ in range(self.population_size):
            new_population.append(self._create_individual())
        self.population = new_population
        return new_population
```

### Numeric Recovery

For numeric errors (NaN, Inf), the system:
1. Replaces invalid values with safe defaults
2. Clips values to valid ranges
3. Applies normalization if needed

```python
def _recover_numeric(self, error):
    for individual in self.population:
        if hasattr(individual, 'position'):
            # Replace NaN and Inf
            individual.position = np.nan_to_num(
                individual.position,
                nan=0.5,
                posinf=1.0,
                neginf=0.0
            )
            # Clip to valid range
            individual.position = np.clip(individual.position, 0.0, 1.0)
```

### Convergence Recovery

When convergence issues are detected:
1. Apply diversity preservation mechanisms
2. Perform partial population restart
3. Adjust algorithm parameters

## Safe Algorithm Wrapper

### Creating Safe Algorithms

```python
from utils.error_handling import create_safe_algorithm

# Wrap any algorithm class
safe_algo = create_safe_algorithm(
    GeneticAlgorithm,
    problem=vrp_problem,
    population_size=50,
    max_iterations=1000
)

# Run with automatic error handling
result = safe_algo.run()

# Check error log
if safe_algo.error_log:
    print(f"Errors encountered: {len(safe_algo.error_log)}")
```

### Custom Recovery

```python
class SafeAlgorithmWrapper:
    def _fallback_solution(self):
        """Return a fallback solution if algorithm fails."""
        # Create a simple greedy solution
        return self._create_greedy_solution()
    
    def _save_error_state(self, error):
        """Save state for debugging."""
        state = {
            'error': str(error),
            'algorithm_state': self._capture_state()
        }
        self.error_log.append(state)
```

## Complete Example

```python
from algorithms.mixins import ErrorHandlingMixin, with_error_handling
from utils.error_handling import validate_parameters, ParameterError

class RobustGeneticAlgorithm(ErrorHandlingMixin, GeneticAlgorithm):
    @validate_parameters(
        population_size=lambda x: x > 0,
        mutation_rate=lambda x: 0 <= x <= 1
    )
    def __init__(self, problem, population_size=50, mutation_rate=0.2, **kwargs):
        super().__init__(problem, population_size, mutation_rate, **kwargs)
        
        # Configure error handling
        self.max_consecutive_errors = 10
        self.enable_recovery = True
        
        # Validate initial state
        self.validate_algorithm_state()
    
    @with_error_handling
    def crossover(self, parent1, parent2):
        """Crossover with automatic error handling."""
        if parent1 is None or parent2 is None:
            raise ValueError("Invalid parents")
        
        return super().crossover(parent1, parent2)
    
    def run(self):
        """Run algorithm with comprehensive error handling."""
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            try:
                # Track iteration for error context
                self.current_iteration = iteration
                
                # Safe fitness evaluation
                fitness_values = []
                for ind in self.population:
                    fitness = self.safe_fitness_evaluation(ind)
                    fitness_values.append(fitness)
                
                # Evolution step with error recovery
                new_population = self.safe_operation(
                    self.evolve_population,
                    error_type='population'
                )
                
                if new_population:
                    self.population = new_population
                
                # Check for numeric issues
                if iteration % 10 == 0:
                    self._check_numeric_health()
                
            except AlgorithmError as e:
                # Check consecutive errors
                if self.consecutive_errors >= self.max_consecutive_errors:
                    print(f"Too many errors. Stopping at iteration {iteration}")
                    break
                
                # Try recovery
                if self.enable_recovery:
                    self._attempt_recovery(e)
        
        # Return best solution or None
        return self.get_best_solution()
    
    def _check_numeric_health(self):
        """Check population for numeric issues."""
        for ind in self.population:
            if hasattr(ind, 'position'):
                check_numeric_stability(
                    ind.position,
                    name=f"individual position"
                )
    
    def _attempt_recovery(self, error):
        """Attempt to recover from error."""
        if isinstance(error, NumericError):
            self._recover_numeric(error)
        elif isinstance(error, PopulationError):
            self._recover_population(error)
        else:
            # Generic recovery: partial restart
            self._partial_restart()
```

## Best Practices

1. **Always validate inputs**: Use `@validate_parameters` for critical methods
2. **Wrap risky operations**: Use `safe_operation()` for operations that might fail
3. **Track errors**: Monitor `error_history` to identify patterns
4. **Configure recovery**: Set appropriate `max_consecutive_errors` and recovery strategies
5. **Test error scenarios**: Include error cases in unit tests
6. **Log appropriately**: Use proper logging levels for different error types
7. **Provide fallbacks**: Always have a plan B for critical operations

## Error Monitoring

### During Development

```python
# Enable detailed error logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run algorithm
algo = RobustAlgorithm(problem, enable_recovery=True)
result = algo.run()

# Analyze errors
summary = algo.get_error_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"Error types: {summary['error_types']}")
print(f"Recovery success rate: {summary['successful_recoveries'] / summary['recovery_attempts']}")
```

### In Production

```python
# Configure for production
algo = RobustAlgorithm(
    problem,
    error_tolerance=1e-8,
    max_consecutive_errors=20,
    enable_recovery=True
)

# Run with monitoring
try:
    result = algo.run()
except AlgorithmError as e:
    # Log to monitoring system
    logger.error(f"Algorithm failed: {e.to_dict()}")
    # Use fallback
    result = create_fallback_solution(problem)
```

## Troubleshooting

### Common Issues

1. **Too many false positives**
   - Adjust `error_tolerance` parameter
   - Review validation rules
   - Check for edge cases in data

2. **Recovery not working**
   - Ensure `enable_recovery=True`
   - Implement algorithm-specific recovery methods
   - Check recovery strategy implementation

3. **Performance impact**
   - Use `@with_error_handling` selectively
   - Disable in performance-critical sections
   - Consider sampling-based validation

4. **Missing error context**
   - Always set `self.current_iteration`
   - Pass algorithm name to error constructors
   - Include relevant details in error `details` dict