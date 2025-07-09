"""
CLI commands for performance optimization and profiling.

This module provides command-line interfaces for performance optimization tools,
parallel execution configuration, and profiling analysis.
"""

import click
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import psutil
import numpy as np

from utils.optimization import (
    ParallelExecutor, ExecutionStrategy, ExecutionConfig,
    CachingSystem, PerformanceProfiler,
    MemoryOptimizer, VectorizedOperations
)
from utils.optimization.parallel_executor import (
    optimize_parallel_config, parallelize_independent_runs
)
from algorithms.factories import get_algorithm
from problems.vrp import VRPProblem
from utils.benchmarking import OPTIMAL_VALUES

logger = logging.getLogger(__name__)


@click.group()
def optimize():
    """Performance optimization and profiling commands."""
    pass


@optimize.command()
@click.option('--algorithm', '-a', required=True, help='Algorithm name')
@click.option('--instance', '-i', required=True, help='Problem instance')
@click.option('--runs', '-r', default=30, help='Number of runs')
@click.option('--strategy', '-s', 
              type=click.Choice(['serial', 'thread', 'process', 'auto']),
              default='auto', help='Execution strategy')
@click.option('--workers', '-w', type=int, help='Number of workers')
@click.option('--profile', is_flag=True, help='Enable profiling')
@click.option('--cache', is_flag=True, help='Enable result caching')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def parallel(algorithm: str, instance: str, runs: int, strategy: str,
            workers: Optional[int], profile: bool, cache: bool,
            output: Optional[str]):
    """Run algorithm in parallel with optimized configuration."""
    click.echo(f"Running {algorithm} on {instance} with {runs} runs in parallel")
    
    # Load problem
    instance_path = Path(f"data/vrp/{instance}.vrp")
    if not instance_path.exists():
        click.echo(f"Error: Instance {instance} not found", err=True)
        return
    
    problem = VRPProblem(instance_path)
    
    # Get algorithm class
    try:
        algo_class = get_algorithm(algorithm)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return
    
    # Determine execution strategy
    if strategy == 'auto':
        config = optimize_parallel_config(
            task_count=runs,
            task_duration_estimate=5.0,  # Estimate based on problem size
            memory_per_task_gb=0.5
        )
    else:
        strategy_map = {
            'serial': ExecutionStrategy.SERIAL,
            'thread': ExecutionStrategy.THREAD_POOL,
            'process': ExecutionStrategy.PROCESS_POOL
        }
        config = ExecutionConfig(
            strategy=strategy_map[strategy],
            n_workers=workers
        )
    
    click.echo(f"Using {config.strategy.value} strategy with {config.n_workers} workers")
    
    # Setup profiler if requested
    profiler = None
    if profile:
        profiler = PerformanceProfiler(output_dir=Path("reports/profiles"))
    
    # Setup caching if requested
    cache_system = None
    if cache:
        cache_system = CachingSystem(
            memory_cache_size=1000,
            disk_cache_dir=Path(".cache/results")
        )
    
    # Run parallel execution
    start_time = time.time()
    
    if profiler:
        with profiler.profile("parallel_execution"):
            results = _run_parallel_execution(
                algo_class, problem, runs, config, cache_system
            )
    else:
        results = _run_parallel_execution(
            algo_class, problem, runs, config, cache_system
        )
    
    duration = time.time() - start_time
    
    # Analyze results
    fitness_values = [r['best_fitness'] for r in results]
    best_fitness = min(fitness_values)
    mean_fitness = np.mean(fitness_values)
    std_fitness = np.std(fitness_values)
    
    # Calculate gap to optimal
    gap = None
    if instance in OPTIMAL_VALUES:
        optimal = OPTIMAL_VALUES[instance]
        gap = ((best_fitness - optimal) / optimal) * 100
    
    # Display results
    click.echo("\nResults:")
    click.echo(f"  Best fitness: {best_fitness:.2f}")
    click.echo(f"  Mean fitness: {mean_fitness:.2f} ± {std_fitness:.2f}")
    if gap is not None:
        click.echo(f"  Gap to optimal: {gap:.2f}%")
    click.echo(f"  Total time: {duration:.2f}s")
    click.echo(f"  Time per run: {duration/runs:.2f}s")
    
    # Display profiling results if available
    if profiler:
        report = profiler.generate_report()
        click.echo("\n" + report.get_summary())
        profiler.save_report(report)
    
    # Display cache statistics if available
    if cache_system:
        cache_stats = cache_system.get_stats()
        click.echo("\nCache Statistics:")
        click.echo(f"  Hit rate: {cache_stats['memory']['hit_rate']:.1%}")
        click.echo(f"  Time saved: {cache_stats['memory']['time_saved']:.1f}s")
    
    # Save results if requested
    if output:
        output_data = {
            'algorithm': algorithm,
            'instance': instance,
            'runs': runs,
            'strategy': config.strategy.value,
            'workers': config.n_workers,
            'results': results,
            'summary': {
                'best_fitness': best_fitness,
                'mean_fitness': mean_fitness,
                'std_fitness': std_fitness,
                'gap': gap,
                'duration': duration
            }
        }
        
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        click.echo(f"\nResults saved to {output}")


def _run_parallel_execution(algo_class, problem, runs, config, cache_system):
    """Execute algorithm runs in parallel."""
    executor = ParallelExecutor(config)
    
    # Prepare parameters
    params_list = []
    for i in range(runs):
        params = {
            'seed': i,
            'population_size': 30,
            'max_iterations': 100
        }
        
        # Check cache
        if cache_system:
            cache_key = f"{algo_class.__name__}:{problem.instance_name}:{i}"
            cached_result = cache_system.get(cache_key)
            if cached_result:
                continue
        
        params_list.append({
            'algo_class': algo_class,
            'problem': problem,
            'params': params,
            'run_id': i,
            'cache_key': cache_key if cache_system else None
        })
    
    # Define execution function
    def run_algorithm(algo_class, problem, params, run_id, cache_key=None):
        algo = algo_class(problem, **params)
        result = algo.run()
        
        # Add run metadata
        result['run_id'] = run_id
        
        # Cache result if requested
        if cache_key and cache_system:
            cache_system.put(cache_key, result, ttl=3600)
        
        return result
    
    # Progress callback
    def progress_callback(completed, total):
        click.echo(f"\rProgress: {completed}/{total} ({completed/total*100:.1f}%)", nl=False)
    
    # Execute
    with executor:
        results = executor.execute(
            run_algorithm,
            params_list,
            progress_callback=progress_callback
        )
    
    click.echo()  # New line after progress
    return results


@optimize.command()
@click.option('--function', '-f', required=True, help='Function to profile')
@click.option('--module', '-m', help='Module containing the function')
@click.option('--args', help='Arguments as JSON string')
@click.option('--memory', is_flag=True, help='Enable memory profiling')
@click.option('--line-profiler', is_flag=True, help='Enable line profiling')
@click.option('--output', '-o', type=click.Path(), help='Output directory')
def profile(function: str, module: Optional[str], args: Optional[str],
           memory: bool, line_profiler: bool, output: Optional[str]):
    """Profile a specific function or code section."""
    click.echo(f"Profiling function: {function}")
    
    # Import function
    if module:
        import importlib
        mod = importlib.import_module(module)
        func = getattr(mod, function)
    else:
        # Try to find in globals
        func = globals().get(function)
        if not func:
            click.echo(f"Error: Function {function} not found", err=True)
            return
    
    # Parse arguments
    func_args = []
    func_kwargs = {}
    if args:
        try:
            parsed_args = json.loads(args)
            if isinstance(parsed_args, list):
                func_args = parsed_args
            elif isinstance(parsed_args, dict):
                func_kwargs = parsed_args
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON arguments", err=True)
            return
    
    # Setup profiler
    output_dir = Path(output) if output else Path("reports/profiles")
    profiler = PerformanceProfiler(
        enable_memory=memory,
        enable_line_profiler=line_profiler,
        output_dir=output_dir
    )
    
    # Profile function
    click.echo("Running profiler...")
    
    with profiler.profile(function):
        result = func(*func_args, **func_kwargs)
    
    # Generate report
    report = profiler.generate_report()
    click.echo("\n" + report.get_summary())
    
    # Save report
    profiler.save_report(report, f"{function}_profile.txt")
    
    # Display detailed hotspots
    click.echo("\nDetailed Hotspots:")
    for func_name, percentage in report.hotspots[:10]:
        if percentage > 1:  # Only show significant functions
            click.echo(f"  {func_name}: {percentage:.1f}%")


@optimize.command()
@click.option('--show-cpu', is_flag=True, help='Show CPU information')
@click.option('--show-memory', is_flag=True, help='Show memory information')
@click.option('--show-gpu', is_flag=True, help='Show GPU information')
@click.option('--benchmark', is_flag=True, help='Run system benchmark')
def system(show_cpu: bool, show_memory: bool, show_gpu: bool, benchmark: bool):
    """Display system information and optimization recommendations."""
    click.echo("System Information and Optimization Analysis")
    click.echo("=" * 50)
    
    # CPU Information
    if show_cpu or not any([show_cpu, show_memory, show_gpu]):
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        click.echo("\nCPU Information:")
        click.echo(f"  Physical cores: {cpu_count}")
        click.echo(f"  Logical cores: {cpu_count_logical}")
        if cpu_freq:
            click.echo(f"  Current frequency: {cpu_freq.current:.0f} MHz")
            click.echo(f"  Max frequency: {cpu_freq.max:.0f} MHz")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        click.echo(f"  Current usage: {np.mean(cpu_percent):.1f}%")
        
        # Recommendations
        click.echo("\n  Recommendations:")
        click.echo(f"    - Optimal worker count for CPU-bound tasks: {cpu_count - 1}")
        click.echo(f"    - Optimal thread count for I/O-bound tasks: {cpu_count_logical * 2}")
    
    # Memory Information
    if show_memory or not any([show_cpu, show_memory, show_gpu]):
        memory = psutil.virtual_memory()
        
        click.echo("\nMemory Information:")
        click.echo(f"  Total: {memory.total / (1024**3):.1f} GB")
        click.echo(f"  Available: {memory.available / (1024**3):.1f} GB")
        click.echo(f"  Used: {memory.used / (1024**3):.1f} GB ({memory.percent:.1f}%)")
        
        # Recommendations
        available_gb = memory.available / (1024**3)
        click.echo("\n  Recommendations:")
        click.echo(f"    - Max parallel processes (0.5GB each): {int(available_gb / 0.5)}")
        click.echo(f"    - Safe memory limit for caching: {available_gb * 0.3:.1f} GB")
    
    # GPU Information
    if show_gpu:
        try:
            import cupy as cp
            click.echo("\nGPU Information:")
            click.echo("  CuPy available: Yes")
            
            # Get GPU properties
            device = cp.cuda.Device()
            click.echo(f"  Device name: {device.name}")
            click.echo(f"  Compute capability: {device.compute_capability}")
            
            # Memory info
            meminfo = cp.cuda.MemoryPool().used_bytes()
            click.echo(f"  Memory used: {meminfo / (1024**2):.1f} MB")
            
        except ImportError:
            click.echo("\nGPU Information:")
            click.echo("  CuPy not available - GPU acceleration disabled")
    
    # System benchmark
    if benchmark:
        click.echo("\nRunning system benchmark...")
        
        # CPU benchmark
        click.echo("\n1. CPU Performance:")
        vec_ops = VectorizedOperations(use_gpu=False)
        
        # Matrix multiplication benchmark
        size = 1000
        matrix = np.random.rand(size, size)
        
        start = time.time()
        result = np.dot(matrix, matrix)
        cpu_time = time.time() - start
        
        click.echo(f"   Matrix multiplication ({size}x{size}): {cpu_time:.3f}s")
        click.echo(f"   GFLOPS: {(2 * size**3) / (cpu_time * 1e9):.1f}")
        
        # Memory bandwidth benchmark
        click.echo("\n2. Memory Bandwidth:")
        data_size = 100 * 1024 * 1024  # 100MB
        data = np.random.rand(data_size // 8)  # 8 bytes per float64
        
        start = time.time()
        copy = data.copy()
        _ = np.sum(copy)
        mem_time = time.time() - start
        
        bandwidth = (data_size * 2) / (mem_time * 1024**3)  # GB/s
        click.echo(f"   Bandwidth: {bandwidth:.1f} GB/s")
        
        # Parallel execution benchmark
        click.echo("\n3. Parallel Execution:")
        
        def dummy_task(x):
            return sum(i**2 for i in range(x))
        
        # Serial
        start = time.time()
        serial_results = [dummy_task(10000) for _ in range(100)]
        serial_time = time.time() - start
        
        # Parallel
        executor = ParallelExecutor(ExecutionConfig(
            strategy=ExecutionStrategy.PROCESS_POOL,
            n_workers=cpu_count - 1
        ))
        
        start = time.time()
        with executor:
            parallel_results = executor.execute(
                dummy_task,
                [{'x': 10000} for _ in range(100)]
            )
        parallel_time = time.time() - start
        
        speedup = serial_time / parallel_time
        click.echo(f"   Serial time: {serial_time:.3f}s")
        click.echo(f"   Parallel time: {parallel_time:.3f}s")
        click.echo(f"   Speedup: {speedup:.2f}x")
        click.echo(f"   Efficiency: {(speedup / (cpu_count - 1)) * 100:.1f}%")


@optimize.command()
@click.option('--clear-memory', is_flag=True, help='Clear memory caches')
@click.option('--clear-disk', is_flag=True, help='Clear disk caches')
@click.option('--warm-cache', type=click.Path(exists=True), 
              help='Warm cache from history file')
@click.option('--show-stats', is_flag=True, help='Show cache statistics')
def cache(clear_memory: bool, clear_disk: bool, warm_cache: Optional[str],
         show_stats: bool):
    """Manage caching system."""
    cache_system = CachingSystem(
        memory_cache_size=1000,
        memory_limit_mb=500,
        disk_cache_dir=Path(".cache/results")
    )
    
    if clear_memory:
        cache_system.memory_cache.clear()
        click.echo("Memory cache cleared")
    
    if clear_disk:
        if cache_system.disk_cache_dir and cache_system.disk_cache_dir.exists():
            import shutil
            shutil.rmtree(cache_system.disk_cache_dir)
            cache_system.disk_cache_dir.mkdir(parents=True, exist_ok=True)
            click.echo("Disk cache cleared")
    
    if warm_cache:
        from utils.optimization.caching_system import CacheWarmer
        warmer = CacheWarmer(cache_system)
        
        # Define compute function (example)
        def compute_func(key):
            # This would be replaced with actual computation
            return {"key": key, "value": "computed"}
        
        loaded = warmer.warm_from_history(Path(warm_cache), compute_func)
        click.echo(f"Warmed cache with {loaded} items")
    
    if show_stats or not any([clear_memory, clear_disk, warm_cache]):
        stats = cache_system.get_stats()
        
        click.echo("Cache Statistics:")
        click.echo("\nMemory Cache:")
        for key, value in stats['memory'].items():
            click.echo(f"  {key}: {value}")
        
        if 'disk' in stats:
            click.echo("\nDisk Cache:")
            for key, value in stats['disk'].items():
                click.echo(f"  {key}: {value}")
        
        if 'redis' in stats:
            click.echo("\nRedis Cache:")
            for key, value in stats['redis'].items():
                click.echo(f"  {key}: {value}")


@optimize.command()
@click.option('--target-memory', type=float, default=80.0,
              help='Target memory usage percentage')
@click.option('--show-pools', is_flag=True, help='Show object pool statistics')
@click.option('--optimize-now', is_flag=True, help='Run memory optimization')
@click.option('--monitor', is_flag=True, help='Monitor memory usage')
def memory(target_memory: float, show_pools: bool, optimize_now: bool,
          monitor: bool):
    """Memory optimization and monitoring."""
    optimizer = MemoryOptimizer(target_memory_percent=target_memory)
    
    if show_pools:
        click.echo("Object Pool Statistics:")
        for name, pool in optimizer._pools.items():
            stats = pool.get_stats()
            click.echo(f"\n{name}:")
            for key, value in stats.items():
                click.echo(f"  {key}: {value}")
    
    if optimize_now:
        click.echo("Running memory optimization...")
        initial_stats = optimizer._initial_stats
        optimizer.optimize_if_needed(force=True)
        current_stats = MemoryOptimizer._initial_stats.current()
        
        click.echo(f"Memory before: {initial_stats.used_mb:.1f} MB")
        click.echo(f"Memory after: {current_stats.used_mb:.1f} MB")
        click.echo(f"Freed: {initial_stats.used_mb - current_stats.used_mb:.1f} MB")
    
    if monitor:
        click.echo("Monitoring memory usage (Ctrl+C to stop)...")
        
        try:
            while True:
                stats = MemoryOptimizer._initial_stats.current()
                
                # Clear line and print
                click.echo(f"\rMemory: {stats.used_mb:.1f} MB "
                          f"({stats.percent:.1f}%) | "
                          f"Available: {stats.available_mb:.1f} MB", nl=False)
                
                # Check if optimization needed
                if stats.percent > target_memory:
                    click.echo("\nHigh memory usage detected! Running optimization...")
                    optimizer.optimize_if_needed(force=True)
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            click.echo("\nMonitoring stopped")
    
    if not any([show_pools, optimize_now, monitor]):
        # Show current memory status
        stats = MemoryOptimizer._initial_stats.current()
        
        click.echo("Memory Status:")
        click.echo(f"  Used: {stats.used_mb:.1f} MB ({stats.percent:.1f}%)")
        click.echo(f"  Available: {stats.available_mb:.1f} MB")
        click.echo(f"  Peak: {stats.peak_mb:.1f} MB")
        click.echo(f"  Target: {target_memory:.1f}%")
        
        if stats.percent > target_memory:
            click.echo("\n⚠️  Memory usage exceeds target! Consider optimization.")


# Add the optimize group to main CLI
def add_to_cli(cli):
    """Add optimize commands to main CLI."""
    cli.add_command(optimize)