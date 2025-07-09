# Performance Optimization Guide

This guide covers the performance optimization tools and strategies available in BioAlgoCompare for maximizing algorithm execution efficiency and scalability.

## Table of Contents

1. [Overview](#overview)
2. [Parallel Execution](#parallel-execution)
3. [Caching System](#caching-system)
4. [Memory Optimization](#memory-optimization)
5. [Vectorized Operations](#vectorized-operations)
6. [Performance Profiling](#performance-profiling)
7. [CLI Commands](#cli-commands)
8. [Best Practices](#best-practices)

## Overview

The performance optimization system provides:
- **Parallel execution** with multiple strategies (threads, processes, MPI)
- **Multi-level caching** (memory, disk, Redis)
- **Memory optimization** with object pooling and GC tuning
- **Vectorized operations** with NumPy and optional GPU support
- **Performance profiling** with detailed bottleneck analysis

## Parallel Execution

### Basic Usage

```python
from utils.optimization import ParallelExecutor, ExecutionStrategy, ExecutionConfig

# Create executor with automatic configuration
config = ExecutionConfig(
    strategy=ExecutionStrategy.PROCESS_POOL,
    n_workers=4,
    memory_limit_gb=8
)

executor = ParallelExecutor(config)

# Define task function
def run_algorithm(params):
    algo = params['algorithm'](params['problem'], seed=params['seed'])
    return algo.run()

# Prepare parameters
params_list = [
    {'algorithm': HOA, 'problem': problem, 'seed': i}
    for i in range(100)
]

# Execute in parallel
with executor:
    results = executor.execute(run_algorithm, params_list)
```

### Execution Strategies

1. **Serial** - For debugging or small tasks
   ```python
   config = ExecutionConfig(strategy=ExecutionStrategy.SERIAL)
   ```

2. **Thread Pool** - For I/O-bound tasks
   ```python
   config = ExecutionConfig(
       strategy=ExecutionStrategy.THREAD_POOL,
       n_workers=8
   )
   ```

3. **Process Pool** - For CPU-bound tasks (default)
   ```python
   config = ExecutionConfig(
       strategy=ExecutionStrategy.PROCESS_POOL,
       n_workers=mp.cpu_count() - 1
   )
   ```

### Auto-Configuration

```python
from utils.optimization.parallel_executor import optimize_parallel_config

# Automatically determine optimal configuration
config = optimize_parallel_config(
    task_count=1000,
    task_duration_estimate=5.0,  # seconds
    memory_per_task_gb=0.5
)
```

### Algorithm-Specific Parallel Execution

```python
from utils.optimization.parallel_executor import AlgorithmParallelExecutor

executor = AlgorithmParallelExecutor()

# Run experiments with parameter grid
param_grid = [
    {'population_size': 30, 'max_iterations': 100},
    {'population_size': 50, 'max_iterations': 200},
]

results = executor.run_experiments(
    algorithm_class=HOA,
    problem=vrp_problem,
    param_grid=param_grid,
    n_runs=30
)
```

## Caching System

### Multi-Level Cache Architecture

```python
from utils.optimization import CachingSystem

# Initialize caching system
cache = CachingSystem(
    memory_cache_size=1000,      # Max items in memory
    memory_limit_mb=500,         # Memory limit
    disk_cache_dir=Path(".cache/results"),
    redis_config={'host': 'localhost', 'port': 6379}
)

# Get or compute value
result = cache.get(
    key="algorithm:hoa:instance:E-n22-k4:seed:42",
    compute_func=lambda: expensive_computation(),
    ttl=3600  # Time to live in seconds
)
```

### Function Result Caching

```python
from utils.optimization import cache_result

@cache_result(ttl_seconds=3600)
def expensive_algorithm_run(algorithm, problem, seed):
    algo = algorithm(problem, seed=seed)
    return algo.run()

# First call computes and caches
result1 = expensive_algorithm_run(HOA, problem, 42)

# Second call retrieves from cache
result2 = expensive_algorithm_run(HOA, problem, 42)  # Fast!
```

### Simple Memoization

```python
from utils.optimization import memoize

@memoize(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### Cache Management

```python
# Invalidate specific key
cache.invalidate("algorithm:hoa:instance:E-n22-k4:seed:42")

# Invalidate pattern
cache.invalidate_pattern("algorithm:hoa:*")

# Get cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['memory']['hit_rate']:.1%}")
```

## Memory Optimization

### Memory Optimizer

```python
from utils.optimization import MemoryOptimizer

# Initialize optimizer
optimizer = MemoryOptimizer(
    target_memory_percent=80.0,  # Target max memory usage
    gc_threshold_mb=100.0        # Trigger GC after this much allocation
)

# Use in critical sections
with optimizer.managed_section("population_update"):
    # Memory-intensive operations
    large_population = np.random.rand(10000, 1000)
    # Process population
    # Memory automatically optimized on exit
```

### Object Pooling

```python
# Create object pool for reusable objects
pool = optimizer.create_pool(
    "individuals",
    object_class=Individual,
    max_size=1000,
    pre_allocate=100
)

# Use pooled objects
with pool.get() as individual:
    # Use individual
    individual.evaluate()
    # Automatically returned to pool
```

### Memory-Efficient Decorators

```python
from utils.optimization import memory_efficient

@memory_efficient(max_memory_mb=500, optimize_threshold_mb=100)
def process_large_dataset(data):
    # Function execution with memory monitoring
    results = complex_processing(data)
    return results
```

### Population Memory Management

```python
from utils.optimization.memory_optimizer import PopulationMemoryManager

# Efficient population storage
manager = PopulationMemoryManager(
    population_size=100,
    individual_size=50
)

# Access individuals efficiently
position = manager.get_position(0)
manager.set_fitness(0, 123.45)

# Get memory usage
usage = manager.get_memory_usage()
print(f"Population memory: {usage['total_mb']:.1f} MB")
```

## Vectorized Operations

### Basic Vectorized Operations

```python
from utils.optimization import VectorizedOperations

# Initialize (with optional GPU support)
vec_ops = VectorizedOperations(use_gpu=True)

# Fast distance calculations
points = np.random.rand(1000, 2)
distances = vec_ops.euclidean_distances_matrix(points)

# Population initialization
population = vec_ops.initialize_population_uniform(
    pop_size=100,
    dimensions=50,
    bounds=(0, 1)
)
```

### Advanced Operations

```python
# Vectorized crossover
offspring1, offspring2 = vec_ops.crossover_arithmetic(
    parent1, parent2, alpha=0.5
)

# Vectorized mutation
mutated = vec_ops.mutation_gaussian(
    population,
    mutation_rate=0.1,
    sigma=0.1,
    bounds=(0, 1)
)

# Tournament selection
selected_indices = vec_ops.tournament_selection(
    population, fitness, n_select=50, tournament_size=3
)
```

### VRP-Specific Operations

```python
from utils.optimization.vectorized_ops import VRPVectorizedOps

# Batch route distance calculation
routes = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
distances = VRPVectorizedOps.calculate_route_distances_batch(
    routes, distance_matrix
)

# Batch capacity checking
valid_routes = VRPVectorizedOps.check_capacity_constraints_batch(
    routes_array, demands, vehicle_capacity
)
```

## Performance Profiling

### Basic Profiling

```python
from utils.optimization import PerformanceProfiler

profiler = PerformanceProfiler(
    enable_memory=True,
    enable_line_profiler=True,
    output_dir=Path("reports/profiles")
)

# Profile code section
with profiler.profile("algorithm_execution"):
    result = algorithm.run()

# Generate report
report = profiler.generate_report()
print(report.get_summary())
```

### Function Profiling Decorator

```python
from utils.optimization import profile_function

@profile_function(output_file="hoa_profile.txt", enable_memory=True)
def run_hoa_algorithm(problem):
    algo = HOA(problem, population_size=30)
    return algo.run()
```

### Algorithm-Specific Profiling

```python
from utils.optimization.profiler import AlgorithmProfiler

profiler = AlgorithmProfiler()

# Profile with algorithm metrics
with profiler.profile("hoa_run"):
    for iteration in range(100):
        start = time.time()
        
        # Algorithm operations
        fitness_values = evaluate_population(population)
        update_population(population)
        
        # Record iteration metrics
        profiler.record_iteration(
            iteration=iteration,
            duration=time.time() - start,
            evaluations=len(population),
            best_fitness=min(fitness_values),
            diversity=calculate_diversity(population)
        )

# Get algorithm-specific summary
summary = profiler.get_algorithm_summary()
```

## CLI Commands

### Parallel Execution

```bash
# Run algorithm with optimal parallel configuration
bioalgo optimize parallel -a hoa -i E-n22-k4 -r 100 --strategy auto

# Run with specific configuration
bioalgo optimize parallel -a hoa -i E-n22-k4 -r 100 --strategy process --workers 4

# Enable profiling and caching
bioalgo optimize parallel -a hoa -i E-n22-k4 -r 100 --profile --cache -o results.json
```

### Performance Profiling

```bash
# Profile a specific function
bioalgo optimize profile -f run_algorithm -m algorithms.hoa --memory --line-profiler

# Profile with arguments
bioalgo optimize profile -f optimize -m utils.optimizer --args '{"iterations": 100}'
```

### System Information

```bash
# Show system optimization recommendations
bioalgo optimize system --show-cpu --show-memory --show-gpu

# Run system benchmark
bioalgo optimize system --benchmark
```

### Cache Management

```bash
# Show cache statistics
bioalgo optimize cache --show-stats

# Clear caches
bioalgo optimize cache --clear-memory --clear-disk

# Warm cache from history
bioalgo optimize cache --warm-cache cache_history.txt
```

### Memory Optimization

```bash
# Monitor memory usage
bioalgo optimize memory --monitor

# Run memory optimization
bioalgo optimize memory --optimize-now

# Show object pool statistics
bioalgo optimize memory --show-pools
```

## Best Practices

### 1. Choose the Right Strategy

- **Serial**: Debugging, small tasks (<10 items)
- **Threads**: I/O-bound tasks, network operations
- **Processes**: CPU-bound tasks, heavy computations
- **GPU**: Large matrix operations, many simple calculations

### 2. Optimize Memory Usage

```python
# Use object pools for frequently created objects
pool = ObjectPool(Individual, max_size=1000)

# Use memory-efficient data structures
from utils.optimization.memory_optimizer import CompactArray
positions = CompactArray(1000, dtype=np.float32)

# Monitor memory in critical sections
with optimizer.managed_section("critical_operation"):
    # Operations that may use lots of memory
    pass
```

### 3. Effective Caching

```python
# Cache expensive computations
@cache_result(ttl_seconds=3600)
def expensive_fitness_calculation(solution):
    return calculate_fitness(solution)

# Use appropriate TTL values
# - Static data: No TTL or very long (days)
# - Dynamic results: Short TTL (minutes to hours)
# - User-specific: Medium TTL with invalidation
```

### 4. Profile Before Optimizing

```python
# Always profile first
with profiler.profile("original_implementation"):
    original_result = original_algorithm()

# Then optimize based on profiling results
if report.hotspots[0][1] > 30:  # Top function > 30% time
    # Focus optimization efforts here
    pass
```

### 5. Batch Operations

```python
# Bad: Individual operations in loop
for individual in population:
    fitness = evaluate(individual)

# Good: Batched operations
fitness_values = vec_ops.evaluate_population_vectorized(
    population, vectorized_fitness_func
)
```

### 6. Monitor Resource Usage

```python
# Set resource limits
config = ExecutionConfig(
    memory_limit_gb=8.0,
    timeout=300  # 5 minutes per task
)

# Monitor during execution
def progress_callback(completed, total):
    stats = executor.get_resource_summary()
    print(f"Progress: {completed}/{total}, CPU: {stats['cpu']['mean']:.1f}%")
```

### 7. Handle Edge Cases

```python
# Gracefully handle failures
def error_handler(exception, params):
    logger.error(f"Task failed with params {params}: {exception}")
    return {'status': 'failed', 'error': str(exception)}

results = executor.execute(
    func, params_list,
    error_handler=error_handler,
    max_retries=3
)
```

## Integration Example

Complete example integrating all optimization features:

```python
from utils.optimization import (
    ParallelExecutor, ExecutionConfig, ExecutionStrategy,
    CachingSystem, PerformanceProfiler,
    MemoryOptimizer, VectorizedOperations
)

# Setup components
cache = CachingSystem(memory_cache_size=1000)
profiler = PerformanceProfiler()
memory_opt = MemoryOptimizer(target_memory_percent=80)
vec_ops = VectorizedOperations(use_gpu=True)

# Configure parallel execution
config = optimize_parallel_config(
    task_count=1000,
    task_duration_estimate=5.0
)
executor = ParallelExecutor(config)

# Define optimized algorithm run
@cache_result(cache_instance=cache)
@memory_efficient(max_memory_mb=500)
def run_optimized_algorithm(algo_class, problem, seed):
    # Use vectorized operations
    algo = algo_class(problem, seed=seed)
    algo.vec_ops = vec_ops  # Inject vectorized operations
    
    # Profile execution
    with profiler.profile(f"{algo_class.__name__}_run"):
        result = algo.run()
    
    return result

# Parallel execution with all optimizations
with memory_opt, executor:
    params_list = [
        {
            'algo_class': HOA,
            'problem': problem,
            'seed': i
        }
        for i in range(1000)
    ]
    
    results = executor.execute(
        run_optimized_algorithm,
        params_list,
        progress_callback=lambda c, t: print(f"Progress: {c}/{t}")
    )

# Analyze performance
report = profiler.generate_report()
cache_stats = cache.get_stats()
resource_summary = executor.get_resource_summary()

print(f"Execution completed in {resource_summary['duration']:.1f}s")
print(f"Cache hit rate: {cache_stats['memory']['hit_rate']:.1%}")
print(f"Peak memory usage: {resource_summary['memory']['max']:.1f}%")
```