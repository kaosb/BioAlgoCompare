# TSP Problem Implementation

## Overview

The Traveling Salesman Problem (TSP) has been successfully implemented as part of the new problems hierarchy. This implementation provides a complete framework for solving TSP instances using bio-inspired algorithms.

## Features

### Core Functionality
- **Multiple Construction Methods**:
  - From coordinate array
  - From distance matrix
  - From TSPLIB format files
  - Random generation

- **Encoding/Decoding**:
  - Random keys encoding for continuous representation
  - Automatic conversion between continuous and discrete representations
  - Maintains feasibility of permutations

- **Heuristics**:
  - Nearest Neighbor construction
  - 2-opt local search improvement
  - Neighborhood generation for advanced search

### Integration
- Fully compatible with all v2 algorithms through `ContinuousAdapter`
- Extends `PermutationProblem` base class
- Supports all problem metrics (evaluations, distance to optimum)

## Usage Examples

### Basic Usage
```python
from problems import TSPProblem, ContinuousAdapter
from algorithms.woa_v2 import WOAV2

# Create TSP instance
tsp = TSPProblem.generate_random(n_cities=20, seed=42)

# Adapt for continuous algorithms
adapted = ContinuousAdapter(tsp)

# Solve with any algorithm
algo = WOAV2(adapted, population_size=50, max_iterations=100)
best = algo.execute()

# Convert to tour
tour = tsp.encode_continuous(best.position)
distance = tsp.evaluate(tour)
print(f"Best tour distance: {distance}")
```

### Loading from TSPLIB
```python
# Load standard TSP instance
tsp = TSPProblem.from_tsplib("data/tsp/berlin52.tsp")

# Use nearest neighbor for initial solution
nn_tour, nn_dist = tsp.nearest_neighbor_heuristic()

# Improve with 2-opt
improved_tour, improved_dist = tsp.two_opt_improvement(nn_tour)
```

### Visualization
```python
# Plot tour (requires matplotlib)
tsp.plot_tour(tour, title="Best TSP Tour")

# Save solution to file
tsp.save_solution(tour, "solution.tour")
```

## Implementation Details

### Continuous Encoding
The TSP uses "random keys" encoding to convert between continuous and discrete representations:
- Continuous: Vector of real values in [0,1]
- Discrete: Permutation obtained by sorting indices by continuous values
- This maintains feasibility automatically

### Distance Calculations
- Supports both Euclidean distances (from coordinates) and explicit distance matrices
- Efficient matrix-based evaluation
- Symmetric TSP assumed (distance[i,j] = distance[j,i])

### Local Search
The 2-opt implementation:
- Systematically checks all edge exchanges
- Accepts only improving moves
- Continues until no improvement found
- Efficient O(n²) implementation per iteration

## Testing

Comprehensive test suite includes:
- Construction methods validation
- Encoding/decoding correctness
- Heuristic performance
- Integration with algorithms
- TSPLIB format parsing
- Edge cases handling

All tests pass with 76% code coverage for TSPProblem.

## Performance Considerations

- Distance matrix pre-computed for efficiency
- 2-opt uses incremental evaluation when possible
- Evaluation counter tracks algorithm efficiency
- Suitable for instances up to ~1000 cities

## Next Steps

1. **Additional Features**:
   - Or-opt local search
   - Lin-Kernighan heuristic
   - Asymmetric TSP support

2. **Benchmarks**:
   - Standard TSPLIB instances
   - Performance comparison tables
   - Algorithm parameter tuning

3. **Variants**:
   - TSP with time windows
   - Multiple TSP
   - Capacitated TSP

## Files

- Implementation: `/problems/discrete/routing/tsp.py`
- Tests: `/tests/test_tsp_problem.py`
- Example: `/examples/tsp_example.py`
- Data: `/data/tsp/`