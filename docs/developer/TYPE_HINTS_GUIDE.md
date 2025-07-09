# Type Hints Guide

## Overview

This guide documents the type hint conventions used throughout the BioAlgoCompare project. Type hints improve code readability, enable better IDE support, and help catch bugs early through static type checking.

## Python Type Hints Basics

### Common Type Imports

```python
from typing import (
    List, Dict, Tuple, Set, Optional, Union, Any, 
    Callable, TypeVar, Generic, Protocol, Literal,
    ClassVar, Final, cast, overload
)
from typing_extensions import TypedDict, NotRequired  # For Python < 3.11
from collections.abc import Sequence, Mapping, Iterable
import numpy as np
from numpy.typing import NDArray
```

### Basic Type Annotations

```python
# Basic types
name: str = "Algorithm"
iterations: int = 100
rate: float = 0.8
is_valid: bool = True

# Optional types (can be None)
seed: Optional[int] = None  # Same as Union[int, None]

# Lists and collections
population: List[Individual] = []
routes: List[List[int]] = [[0, 1, 2, 0], [0, 3, 4, 0]]
parameters: Dict[str, float] = {"mutation_rate": 0.2}
coordinates: Tuple[float, float] = (10.5, 20.3)
unique_nodes: Set[int] = {1, 2, 3}

# Union types (multiple possible types)
value: Union[int, float] = 10.5
result: Union[Individual, None] = None

# Any type (use sparingly)
data: Any = {"flexible": "structure"}
```

## Project-Specific Conventions

### Algorithm Classes

```python
from typing import List, Optional, Dict, Any, Type
from abc import ABC, abstractmethod

class Individual(ABC):
    """Base class for individuals."""
    
    def __init__(self, problem: 'Problem', position: Optional[np.ndarray] = None) -> None:
        self.problem = problem
        self.position = position
        self._fitness: Optional[float] = None
    
    @abstractmethod
    def move(self, context: 'MoveContext') -> None:
        """Move the individual."""
        pass
    
    def fitness(self) -> float:
        """Calculate and return fitness."""
        if self._fitness is None:
            self._fitness = self.problem.evaluate(self.position)
        return self._fitness
    
    def copy(self) -> 'Individual':
        """Create a deep copy."""
        return self.__class__(self.problem, self.position.copy())
```

### Algorithm Implementation

```python
from typing import List, Optional, Dict, Any, TypeVar, Generic

T = TypeVar('T', bound=Individual)

class MetaheuristicAlgorithm(Generic[T], ABC):
    """Base class for metaheuristic algorithms."""
    
    def __init__(
        self, 
        problem: Problem,
        population_size: int = 30,
        max_iterations: int = 100,
        seed: Optional[int] = None
    ) -> None:
        self.problem = problem
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.population: List[T] = []
        self.best_solution: Optional[T] = None
    
    @abstractmethod
    def _create_individual(self) -> T:
        """Create a new individual."""
        pass
    
    def initialize_population(self) -> None:
        """Initialize the population."""
        self.population = [
            self._create_individual() 
            for _ in range(self.population_size)
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get algorithm statistics."""
        return {
            'best_fitness': self.best_solution.fitness() if self.best_solution else None,
            'population_size': len(self.population),
            'iterations': self.max_iterations
        }
```

### VRP-Specific Types

```python
from typing import List, Tuple, Dict, Optional
import numpy as np
from numpy.typing import NDArray

# Type aliases for clarity
NodeIndex = int
Route = List[NodeIndex]
Solution = List[Route]
Coordinates = Tuple[float, float]
DistanceMatrix = NDArray[np.float64]

class VRPProblem:
    """Vehicle Routing Problem."""
    
    def __init__(
        self,
        nodes: List[Coordinates],
        demands: List[float],
        capacity: float,
        num_vehicles: Optional[int] = None
    ) -> None:
        self.nodes = nodes
        self.demands = demands
        self.capacity = capacity
        self.num_vehicles = num_vehicles
        self.distance_matrix: DistanceMatrix = self._calculate_distances()
    
    def evaluate_solution(self, routes: Solution) -> float:
        """Evaluate total distance of solution."""
        total_distance: float = 0.0
        for route in routes:
            total_distance += self._calculate_route_distance(route)
        return total_distance
    
    def _calculate_route_distance(self, route: Route) -> float:
        """Calculate distance of a single route."""
        distance: float = 0.0
        for i in range(len(route) - 1):
            distance += self.distance_matrix[route[i], route[i+1]]
        return distance
```

### Callback and Function Types

```python
from typing import Callable, Protocol, TypeVar, Optional

# Simple callback
ProgressCallback = Callable[[int, float], None]

# More complex callback with named parameters
ErrorHandler = Callable[[Exception, str], Optional[Any]]

# Protocol for duck typing
class Optimizable(Protocol):
    """Protocol for optimizable objects."""
    
    def fitness(self) -> float: ...
    def improve(self) -> None: ...

# Generic function type
T = TypeVar('T')
Comparator = Callable[[T, T], bool]

# Usage
def run_algorithm(
    algorithm: MetaheuristicAlgorithm,
    progress_callback: Optional[ProgressCallback] = None,
    error_handler: Optional[ErrorHandler] = None
) -> Individual:
    """Run algorithm with callbacks."""
    try:
        for i in range(algorithm.max_iterations):
            algorithm.iterate()
            if progress_callback:
                progress_callback(i, algorithm.best_solution.fitness())
    except Exception as e:
        if error_handler:
            return error_handler(e, "algorithm_error")
        raise
    return algorithm.best_solution
```

### Mixin Types

```python
from typing import List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from algorithms.base import Individual

class SelectionMixin:
    """Mixin for selection operators."""
    
    def tournament_selection(
        self, 
        population: List['Individual'],
        tournament_size: int = 3,
        n_select: int = 1
    ) -> List['Individual']:
        """Tournament selection."""
        selected: List['Individual'] = []
        for _ in range(n_select):
            tournament = random.sample(population, tournament_size)
            winner = min(tournament, key=lambda x: x.fitness())
            selected.append(winner)
        return selected
```

### Complex Return Types

```python
from typing import Tuple, List, Dict, Optional, NamedTuple
from dataclasses import dataclass

# Using NamedTuple for structured returns
class BenchmarkResult(NamedTuple):
    """Result of a benchmark run."""
    algorithm: str
    instance: str
    best_fitness: float
    mean_fitness: float
    std_fitness: float
    execution_time: float

# Using dataclass
@dataclass
class AlgorithmMetrics:
    """Comprehensive algorithm metrics."""
    convergence_rate: float
    diversity: float
    stagnation_count: int
    best_improvement: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'convergence_rate': self.convergence_rate,
            'diversity': self.diversity,
            'stagnation_count': float(self.stagnation_count),
            'best_improvement': self.best_improvement
        }

# Function with complex return
def analyze_algorithm(
    algorithm: MetaheuristicAlgorithm,
    instances: List[str]
) -> Tuple[List[BenchmarkResult], AlgorithmMetrics, Optional[str]]:
    """
    Analyze algorithm performance.
    
    Returns:
        Tuple of (results, metrics, error_message)
    """
    results: List[BenchmarkResult] = []
    # ... implementation ...
    metrics = AlgorithmMetrics(
        convergence_rate=0.95,
        diversity=0.3,
        stagnation_count=5,
        best_improvement=100.0
    )
    error_message: Optional[str] = None
    
    return results, metrics, error_message
```

### Error Handling Types

```python
from typing import TypeVar, Optional, Callable, Any, Union

E = TypeVar('E', bound=Exception)
T = TypeVar('T')

def safe_execute(
    func: Callable[[], T],
    fallback: Optional[T] = None,
    error_handler: Optional[Callable[[Exception], Any]] = None
) -> Union[T, None]:
    """
    Execute function safely with error handling.
    
    Args:
        func: Function to execute
        fallback: Fallback value on error
        error_handler: Optional error handler
        
    Returns:
        Function result or fallback value
    """
    try:
        return func()
    except Exception as e:
        if error_handler:
            error_handler(e)
        return fallback
```

## Best Practices

### 1. Use Optional for Nullable Values

```python
# Good
def find_best(population: List[Individual]) -> Optional[Individual]:
    if not population:
        return None
    return min(population, key=lambda x: x.fitness())

# Bad
def find_best(population: List[Individual]) -> Individual:
    # This can return None but type doesn't indicate it
    if not population:
        return None
    return min(population, key=lambda x: x.fitness())
```

### 2. Use Type Aliases for Complex Types

```python
# Define aliases at module level
PopulationType = List[Individual]
FitnessHistory = List[float]
ParameterDict = Dict[str, Union[int, float, bool]]

# Use in functions
def evolve(
    population: PopulationType,
    parameters: ParameterDict
) -> Tuple[PopulationType, FitnessHistory]:
    """Evolve population."""
    pass
```

### 3. Use Protocols for Duck Typing

```python
from typing import Protocol

class Evaluable(Protocol):
    """Protocol for evaluable objects."""
    def evaluate(self, solution: Any) -> float: ...

# Any class with evaluate method can be used
def optimize(problem: Evaluable, iterations: int) -> float:
    """Optimize any evaluable problem."""
    # Works with any object that has evaluate method
    return problem.evaluate(solution)
```

### 4. Type Checking Imports

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Imports only for type checking
    from heavy_module import HeavyClass

def process(obj: 'HeavyClass') -> None:
    """Process heavy class without runtime import."""
    pass
```

### 5. Overloading for Different Signatures

```python
from typing import overload, Union, List

@overload
def process_data(data: int) -> float: ...

@overload
def process_data(data: List[int]) -> List[float]: ...

def process_data(data: Union[int, List[int]]) -> Union[float, List[float]]:
    """Process single value or list."""
    if isinstance(data, int):
        return float(data)
    return [float(x) for x in data]
```

## Type Checking Tools

### mypy

```bash
# Install mypy
pip install mypy

# Check specific file
mypy algorithms/genetic_algorithm.py

# Check entire project
mypy .

# With configuration file (mypy.ini)
mypy --config-file mypy.ini
```

### pyright/pylance

Used by VS Code for real-time type checking:

```json
// settings.json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.autoImportCompletions": true
}
```

### Example mypy.ini Configuration

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-numpy.*]
ignore_missing_imports = True

[mypy-matplotlib.*]
ignore_missing_imports = True

[mypy-scipy.*]
ignore_missing_imports = True
```

## Common Patterns in BioAlgoCompare

### Algorithm Factory Pattern

```python
from typing import Type, Dict, Optional

AlgorithmClass = Type[MetaheuristicAlgorithm]
AlgorithmRegistry = Dict[str, AlgorithmClass]

class AlgorithmFactory:
    """Factory for creating algorithms."""
    
    _registry: AlgorithmRegistry = {}
    
    @classmethod
    def register(
        cls, 
        name: str, 
        algorithm_class: AlgorithmClass
    ) -> None:
        """Register an algorithm."""
        cls._registry[name] = algorithm_class
    
    @classmethod
    def create(
        cls,
        name: str,
        problem: Problem,
        **kwargs: Any
    ) -> Optional[MetaheuristicAlgorithm]:
        """Create algorithm instance."""
        if name not in cls._registry:
            return None
        return cls._registry[name](problem, **kwargs)
```

### Result Container Pattern

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ExperimentResult:
    """Container for experiment results."""
    algorithm: str
    instance: str
    fitness_history: List[float]
    best_solution: Any
    execution_time: float
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'algorithm': self.algorithm,
            'instance': self.instance,
            'best_fitness': min(self.fitness_history),
            'execution_time': self.execution_time,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat()
        }
```

## Migration Guide

### Converting Untyped Code

Before:
```python
def calculate_distance(point1, point2):
    return np.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2)))
```

After:
```python
from typing import Tuple, Union
import numpy as np
from numpy.typing import NDArray

Coordinate = Union[Tuple[float, float], NDArray[np.float64]]

def calculate_distance(
    point1: Coordinate,
    point2: Coordinate
) -> float:
    """Calculate Euclidean distance between two points."""
    return np.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2)))
```

### Common Type Hint Fixes

1. **Missing return type for `__init__`**:
   ```python
   def __init__(self, value: int) -> None:
       self.value = value
   ```

2. **Property methods**:
   ```python
   @property
   def fitness(self) -> float:
       return self._fitness
   ```

3. **Class methods**:
   ```python
   @classmethod
   def from_config(cls, config: Dict[str, Any]) -> 'MyClass':
       return cls(**config)
   ```

4. **Static methods**:
   ```python
   @staticmethod
   def validate_input(value: float) -> bool:
       return 0 <= value <= 1
   ```

## Resources

- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 526 - Variable Annotations](https://www.python.org/dev/peps/pep-0526/)
- [PEP 563 - Postponed Evaluation](https://www.python.org/dev/peps/pep-0563/)