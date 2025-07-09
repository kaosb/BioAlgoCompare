# BioAlgoCompare Code Standards

This document defines the coding standards and conventions for the BioAlgoCompare project.

## Table of Contents
1. [General Principles](#general-principles)
2. [Python Standards](#python-standards)
3. [Algorithm Implementation](#algorithm-implementation)
4. [Testing Standards](#testing-standards)
5. [Documentation Standards](#documentation-standards)
6. [Git Workflow](#git-workflow)
7. [Performance Guidelines](#performance-guidelines)
8. [Security Standards](#security-standards)

## General Principles

### Core Values
1. **Readability**: Code should be clear and self-documenting
2. **Consistency**: Follow established patterns throughout the codebase
3. **Simplicity**: Prefer simple solutions over clever ones
4. **Testability**: Write code that is easy to test
5. **Performance**: Optimize for scientific computing workloads

### File Organization
```
bioalgocompare/
├── algorithms/          # Algorithm implementations
│   ├── __init__.py     # Algorithm registry
│   ├── base.py         # Base classes
│   └── {algo}.py       # Individual algorithms
├── problems/           # Problem definitions
├── utils/              # Utilities and helpers
├── scripts/            # CLI and scripts
├── tests/              # Test suite
├── docs/               # Documentation
└── standards/          # This directory
```

## Python Standards

### Style Guide
We follow PEP 8 with the following specifications:
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Import order**: Standard library, third-party, local
- **String quotes**: Double quotes for docstrings, single quotes for strings

### Code Formatting
All Python code must be formatted with:
```bash
# Format code
ruff format .

# Check style
ruff check .
```

### Type Hints
Type hints are **required** for:
- All function signatures
- Class attributes
- Complex data structures

```python
from typing import List, Dict, Optional, Tuple
import numpy as np
from numpy.typing import NDArray

def calculate_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float]
) -> float:
    """Calculate Euclidean distance between two points."""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

class Algorithm:
    population: List[Individual]
    best_fitness: float
    history: Dict[str, List[float]]
    
    def __init__(
        self,
        population_size: int,
        max_iterations: int,
        seed: Optional[int] = None
    ) -> None:
        ...
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `HorseOptimization`, `VRPProblem`)
- **Functions/Methods**: snake_case (e.g., `calculate_fitness`, `initialize_population`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_ITERATIONS`, `DEFAULT_SEED`)
- **Private**: Leading underscore (e.g., `_internal_method`)
- **Algorithm names**: Uppercase abbreviations (e.g., `HOA`, `FOA`, `EGTO`)

### Docstrings
Use Google-style docstrings:

```python
def complex_function(
    param1: str,
    param2: List[int],
    optional_param: Optional[float] = None
) -> Dict[str, Any]:
    """
    Brief description of function purpose.
    
    Longer description if needed, explaining the algorithm,
    assumptions, or important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        optional_param: Description of optional parameter.
            Defaults to None.
    
    Returns:
        Description of return value, including structure
        if complex.
    
    Raises:
        ValueError: When input validation fails
        RuntimeError: When algorithm fails to converge
    
    Example:
        >>> result = complex_function("test", [1, 2, 3])
        >>> print(result["status"])
        'success'
    
    Note:
        Additional notes about performance, limitations,
        or references to papers.
    """
```

### Error Handling
```python
# Specific exceptions with context
class AlgorithmError(Exception):
    """Base exception for algorithm errors."""
    pass

class ConvergenceError(AlgorithmError):
    """Raised when algorithm fails to converge."""
    pass

# Use specific exceptions
def run_algorithm():
    if not self.population:
        raise ValueError("Population not initialized")
    
    try:
        result = self._optimize()
    except ConvergenceError as e:
        logger.error(f"Algorithm failed to converge: {e}")
        raise
    
    return result
```

## Algorithm Implementation

### Structure Template
```python
"""
Algorithm Name (ABBREVIATION) - Brief description

Based on:
    Author(s). (Year). Paper Title. Journal/Conference.
    DOI: xxx.xxx/xxx

This implementation includes:
    - Feature 1
    - Feature 2
    - Modification/improvement (if any)
"""

from typing import List, Optional, Dict, Any
import numpy as np
from numpy.typing import NDArray

from algorithms.base import MetaheuristicAlgorithm, Individual


class AlgorithmNameIndividual(Individual):
    """Individual representation for Algorithm Name."""
    
    def __init__(self, position: NDArray[np.float64], problem):
        super().__init__(position, problem)
        # Algorithm-specific attributes
        self.velocity: Optional[NDArray[np.float64]] = None
        self.personal_best: Optional[NDArray[np.float64]] = None
    
    def move(self, **kwargs) -> None:
        """
        Update individual position according to algorithm rules.
        
        Args:
            **kwargs: Algorithm-specific parameters
        """
        # Implementation following paper equations
        pass


class AlgorithmAbbreviation(MetaheuristicAlgorithm):
    """
    Full Algorithm Name implementation.
    
    This algorithm mimics the behavior of [inspiration source]
    to solve optimization problems.
    
    Attributes:
        specific_param1: Description
        specific_param2: Description
    """
    
    def __init__(
        self,
        problem,
        population_size: int = 30,
        max_iterations: int = 100,
        specific_param1: float = 0.5,
        specific_param2: float = 2.0,
        seed: Optional[int] = None
    ):
        super().__init__(problem, population_size, max_iterations, seed)
        
        # Validate parameters
        if not 0 < specific_param1 < 1:
            raise ValueError(f"specific_param1 must be in (0, 1), got {specific_param1}")
        
        self.specific_param1 = specific_param1
        self.specific_param2 = specific_param2
        
        # Algorithm-specific attributes
        self.global_best: Optional[Individual] = None
        self.convergence_rate: float = 0.0
    
    def _create_individual(self) -> Individual:
        """Create algorithm-specific individual."""
        return AlgorithmNameIndividual(
            self._generate_random_position(),
            self.problem
        )
    
    def initialize_population(self) -> None:
        """Initialize population with algorithm-specific setup."""
        super().initialize_population()
        
        # Additional initialization
        self.global_best = min(self.population, key=lambda x: x.fitness)
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the algorithm.
        
        Returns:
            Dictionary containing results and metrics
        """
        self.initialize_population()
        
        for iteration in range(self.max_iterations):
            # Update positions
            for individual in self.population:
                individual.move(
                    global_best=self.global_best,
                    param1=self.specific_param1,
                    param2=self.specific_param2
                )
            
            # Update global best
            current_best = min(self.population, key=lambda x: x.fitness)
            if current_best.fitness < self.global_best.fitness:
                self.global_best = current_best
            
            # Track convergence
            self._update_best_solution()
            
            # Optional: Early stopping
            if self._check_convergence():
                break
        
        return self._prepare_results()
```

### Required Methods
Every algorithm must implement:
1. `__init__`: Constructor with standard parameters
2. `_create_individual`: Factory for individuals
3. `initialize_population`: Population initialization
4. `run`: Main execution loop

### Performance Considerations
```python
# Bad: Creating new arrays in loops
for i in range(1000):
    position = np.array([random.random() for _ in range(dim)])

# Good: Vectorized operations
positions = self.random_state.random((1000, dim))

# Bad: Repeated calculations
for individual in population:
    distance = np.sqrt(np.sum((individual.position - target)**2))

# Good: Vectorized distance calculation
positions = np.array([ind.position for ind in population])
distances = np.linalg.norm(positions - target, axis=1)
```

## Testing Standards

### Test Structure
```python
"""Test module for algorithm_name."""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal

from algorithms.algorithm_name import AlgorithmName
from problems.vrp import VRPProblem


class TestAlgorithmName:
    """Test suite for AlgorithmName."""
    
    @pytest.fixture
    def problem(self):
        """Create test problem instance."""
        return VRPProblem("E-n22-k4")
    
    @pytest.fixture
    def algorithm(self, problem):
        """Create algorithm instance with fixed seed."""
        return AlgorithmName(
            problem,
            population_size=10,
            max_iterations=50,
            seed=42
        )
    
    def test_initialization(self, algorithm):
        """Test algorithm initialization."""
        assert algorithm.population_size == 10
        assert algorithm.max_iterations == 50
        assert algorithm.seed == 42
    
    def test_reproducibility(self, problem):
        """Test deterministic behavior with seed."""
        algo1 = AlgorithmName(problem, seed=42)
        algo2 = AlgorithmName(problem, seed=42)
        
        result1 = algo1.run()
        result2 = algo2.run()
        
        assert result1["best_fitness"] == result2["best_fitness"]
        assert_array_almost_equal(
            result1["best_solution"],
            result2["best_solution"]
        )
    
    def test_convergence(self, algorithm):
        """Test algorithm converges."""
        result = algorithm.run()
        
        # Check improvement
        history = result["fitness_history"]
        assert history[-1] <= history[0]
        
        # Check valid solution
        assert result["best_fitness"] > 0
        assert len(result["best_solution"]) > 0
    
    @pytest.mark.parametrize("pop_size", [10, 30, 50])
    def test_different_population_sizes(self, problem, pop_size):
        """Test algorithm with different population sizes."""
        algo = AlgorithmName(problem, population_size=pop_size)
        result = algo.run()
        assert len(algo.population) == pop_size
    
    def test_invalid_parameters(self, problem):
        """Test parameter validation."""
        with pytest.raises(ValueError):
            AlgorithmName(problem, population_size=0)
        
        with pytest.raises(ValueError):
            AlgorithmName(problem, specific_param1=2.0)  # Out of range
```

### Test Requirements
1. **Coverage**: Minimum 80% code coverage
2. **Reproducibility**: Test with fixed seeds
3. **Edge cases**: Test boundary conditions
4. **Performance**: Test with different problem sizes
5. **Integration**: Test with real VRP instances

## Documentation Standards

### Module Documentation
```python
"""
Module brief description.

This module provides [functionality]. It is used for [purpose]
and integrates with [other modules].

Classes:
    ClassName: Brief description
    
Functions:
    function_name: Brief description
    
Constants:
    CONSTANT_NAME: Brief description

Example:
    Basic usage example::
    
        from module import ClassName
        
        obj = ClassName()
        result = obj.method()

Note:
    Important notes about the module, limitations,
    or special considerations.
"""
```

### Algorithm Documentation Must Include:
1. **Paper reference** with DOI
2. **Mathematical formulation** of key equations
3. **Parameter descriptions** with valid ranges
4. **Time complexity** analysis
5. **Usage examples**

### Comments
```python
# Use comments to explain "why", not "what"

# Bad: Increment counter
counter += 1

# Good: Track iterations for early stopping check
counter += 1

# Complex logic requires explanation
# Apply Lévy flight: heavy-tailed distribution for exploration
# See Mantegna's algorithm (1994) for implementation details
levy_step = self._calculate_levy_flight(beta=1.5)
```

## Git Workflow

### Branch Naming
- `feature/algorithm-name`: New algorithms
- `fix/issue-description`: Bug fixes
- `refactor/module-name`: Code refactoring
- `docs/topic`: Documentation updates
- `test/algorithm-name`: Test additions

### Commit Messages
Follow conventional commits:
```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Test additions
- `perf`: Performance improvements

Examples:
```
feat(algorithms): implement Whale Optimization Algorithm

- Add WOA class with spiral updating mechanism
- Include bubble-net attacking strategy
- Add comprehensive tests with 95% coverage

Based on: Mirjalili & Lewis (2016)
DOI: 10.1016/j.advengsoft.2016.01.008

fix(vrp): correct distance calculation for asymmetric instances

The previous implementation assumed symmetric distances.
This fix adds proper handling for asymmetric cost matrices.

Fixes #123
```

### Pull Request Standards
1. **Title**: Clear description of changes
2. **Description**: What, why, and how
3. **Tests**: All tests must pass
4. **Coverage**: No decrease in coverage
5. **Review**: At least one approval required

## Performance Guidelines

### Profiling Requirements
For algorithms and critical paths:
```python
# Use decorators for profiling
from utils.profiling import profile_performance

@profile_performance
def critical_function():
    pass

# Memory profiling for large operations
from memory_profiler import profile

@profile
def memory_intensive_operation():
    pass
```

### Optimization Checklist
- [ ] Use NumPy vectorization over loops
- [ ] Preallocate arrays when size is known
- [ ] Cache expensive calculations
- [ ] Use appropriate data structures
- [ ] Profile before optimizing
- [ ] Document performance characteristics

### Benchmarking
```python
# All algorithms must support benchmarking
def benchmark_algorithm():
    """Benchmark algorithm performance."""
    instances = ["E-n22-k4", "E-n33-k4", "E-n51-k5"]
    sizes = [10, 30, 50, 100]
    
    for instance in instances:
        for size in sizes:
            # Measure time and memory
            # Report iterations per second
            # Track convergence rate
```

## Security Standards

### Input Validation
```python
def process_user_input(value: Any) -> float:
    """Safely process user input."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value)}")
    
    if not 0 <= value <= 1000:
        raise ValueError(f"Value must be in [0, 1000], got {value}")
    
    return float(value)
```

### File Operations
```python
from pathlib import Path

# Safe path handling
def read_instance(filename: str) -> dict:
    """Safely read VRP instance."""
    # Sanitize filename
    safe_name = Path(filename).name
    
    # Restrict to data directory
    filepath = Path("data/vrp") / safe_name
    
    if not filepath.exists():
        raise FileNotFoundError(f"Instance not found: {safe_name}")
    
    if not filepath.is_file():
        raise ValueError(f"Not a file: {safe_name}")
    
    # Read with size limit
    max_size = 10 * 1024 * 1024  # 10MB
    if filepath.stat().st_size > max_size:
        raise ValueError(f"File too large: {safe_name}")
    
    return read_vrp_file(filepath)
```

### Random State Management
```python
# Always use managed random state
from utils.reproducibility import get_random_state

class SecureAlgorithm:
    def __init__(self, seed: Optional[int] = None):
        self.random_state = get_random_state(seed)
        # Never use global random
```

## Enforcement

These standards are enforced through:

1. **Pre-commit hooks**: Automatic formatting and linting
2. **CI/CD pipeline**: Continuous validation
3. **Code review**: Manual verification
4. **Quality gates**: Automated standards checking

Run local checks:
```bash
# Check all standards
bioalgo quality check

# Fix auto-fixable issues
bioalgo quality fix

# Full quality gate
bioalgo quality gate
```

## Exceptions

Exceptions to these standards must be:
1. Documented in code with `# noqa: <rule>` comment
2. Justified in pull request
3. Approved by maintainer

Example:
```python
# Long line with mathematical formula that cannot be broken
result = (alpha * np.exp(-beta * distance) + gamma * np.log(1 + delta * time)) / (epsilon + zeta * complexity)  # noqa: E501
```

## Updates

These standards are living documents. Propose changes through:
1. GitHub issue with rationale
2. Pull request with updated standards
3. Team discussion and approval

Last updated: 2024-01-15
Version: 1.0.0