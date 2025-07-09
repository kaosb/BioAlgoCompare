"""
Parallel execution system for scalable algorithm runs.

This module provides advanced parallel execution capabilities including
multi-processing, multi-threading, and distributed execution strategies.
"""

import os
import time
import multiprocessing as mp
from multiprocessing import Pool, Process, Queue, Manager
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
import threading
import queue
import numpy as np
from functools import partial
import psutil
import warnings

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Execution strategies for parallel processing."""
    SERIAL = "serial"
    THREAD_POOL = "thread_pool"
    PROCESS_POOL = "process_pool"
    MPI = "mpi"  # For future distributed computing
    RAY = "ray"  # For future Ray integration
    DASK = "dask"  # For future Dask integration


@dataclass
class ExecutionConfig:
    """Configuration for parallel execution."""
    strategy: ExecutionStrategy = ExecutionStrategy.PROCESS_POOL
    n_workers: Optional[int] = None
    chunk_size: int = 1
    timeout: Optional[float] = None
    memory_limit_gb: Optional[float] = None
    use_shared_memory: bool = False
    enable_gpu: bool = False
    dynamic_scheduling: bool = True
    
    def __post_init__(self):
        """Validate and set defaults."""
        if self.n_workers is None:
            # Auto-detect optimal number of workers
            cpu_count = mp.cpu_count()
            # Leave one CPU free for system
            self.n_workers = max(1, cpu_count - 1)
        
        # Validate memory limit
        if self.memory_limit_gb:
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            if self.memory_limit_gb > available_memory_gb:
                warnings.warn(
                    f"Memory limit {self.memory_limit_gb}GB exceeds "
                    f"available memory {available_memory_gb:.1f}GB"
                )


class ParallelExecutor:
    """
    Advanced parallel execution system for algorithm runs.
    
    Features:
    - Multiple execution strategies (serial, threads, processes)
    - Dynamic work distribution
    - Memory-aware scheduling
    - Progress tracking
    - Fault tolerance with retry logic
    - Resource monitoring
    
    Example:
        >>> executor = ParallelExecutor(ExecutionConfig(
        ...     strategy=ExecutionStrategy.PROCESS_POOL,
        ...     n_workers=4
        ... ))
        >>> 
        >>> def run_algorithm(params):
        ...     # Algorithm execution
        ...     return result
        >>> 
        >>> params_list = [{'seed': i} for i in range(100)]
        >>> results = executor.execute(run_algorithm, params_list)
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        """
        Initialize parallel executor.
        
        Args:
            config: Execution configuration
        """
        self.config = config or ExecutionConfig()
        self._setup_executor()
        
        # Progress tracking
        self._progress_queue: Optional[Queue] = None
        self._progress_thread: Optional[threading.Thread] = None
        self._completed_tasks = 0
        self._total_tasks = 0
        
        # Resource monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        self._resource_data = []
        
        logger.info(f"Initialized ParallelExecutor with {self.config.strategy.value} "
                   f"strategy and {self.config.n_workers} workers")
    
    def _setup_executor(self):
        """Setup the appropriate executor based on strategy."""
        if self.config.strategy == ExecutionStrategy.SERIAL:
            self.executor = None
        elif self.config.strategy == ExecutionStrategy.THREAD_POOL:
            self.executor = ThreadPoolExecutor(max_workers=self.config.n_workers)
        elif self.config.strategy == ExecutionStrategy.PROCESS_POOL:
            # Configure process pool
            ctx = mp.get_context('spawn')  # Use spawn for better compatibility
            self.executor = ProcessPoolExecutor(
                max_workers=self.config.n_workers,
                mp_context=ctx
            )
        else:
            raise NotImplementedError(f"Strategy {self.config.strategy} not implemented")
    
    def execute(
        self,
        func: Callable,
        params_list: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        error_handler: Optional[Callable[[Exception, Dict[str, Any]], Any]] = None,
        max_retries: int = 3
    ) -> List[Any]:
        """
        Execute function in parallel with given parameters.
        
        Args:
            func: Function to execute
            params_list: List of parameter dictionaries
            progress_callback: Callback for progress updates
            error_handler: Custom error handling function
            max_retries: Maximum retry attempts for failed tasks
        
        Returns:
            List of results in same order as params_list
        """
        self._total_tasks = len(params_list)
        self._completed_tasks = 0
        
        logger.info(f"Starting parallel execution of {self._total_tasks} tasks")
        
        # Start resource monitoring
        if self.config.memory_limit_gb:
            self._start_resource_monitoring()
        
        try:
            if self.config.strategy == ExecutionStrategy.SERIAL:
                results = self._execute_serial(
                    func, params_list, progress_callback, error_handler
                )
            else:
                results = self._execute_parallel(
                    func, params_list, progress_callback, error_handler, max_retries
                )
            
            logger.info(f"Completed execution of {self._total_tasks} tasks")
            return results
            
        finally:
            self._stop_resource_monitoring()
    
    def _execute_serial(
        self,
        func: Callable,
        params_list: List[Dict[str, Any]],
        progress_callback: Optional[Callable],
        error_handler: Optional[Callable]
    ) -> List[Any]:
        """Execute tasks serially."""
        results = []
        
        for i, params in enumerate(params_list):
            try:
                result = func(**params)
                results.append(result)
            except Exception as e:
                if error_handler:
                    result = error_handler(e, params)
                    results.append(result)
                else:
                    logger.error(f"Task {i} failed: {e}")
                    results.append(None)
            
            self._completed_tasks += 1
            if progress_callback:
                progress_callback(self._completed_tasks, self._total_tasks)
        
        return results
    
    def _execute_parallel(
        self,
        func: Callable,
        params_list: List[Dict[str, Any]],
        progress_callback: Optional[Callable],
        error_handler: Optional[Callable],
        max_retries: int
    ) -> List[Any]:
        """Execute tasks in parallel."""
        # Create futures with indices to maintain order
        future_to_index = {}
        
        # Dynamic chunk sizing based on task count and workers
        if self.config.dynamic_scheduling:
            chunk_size = max(1, len(params_list) // (self.config.n_workers * 4))
        else:
            chunk_size = self.config.chunk_size
        
        # Submit tasks
        for i, params in enumerate(params_list):
            # Check memory limit before submitting
            if self.config.memory_limit_gb:
                self._wait_for_memory()
            
            future = self.executor.submit(self._execute_with_retry, 
                                        func, params, max_retries)
            future_to_index[future] = i
        
        # Collect results
        results = [None] * len(params_list)
        
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            
            try:
                result = future.result(timeout=self.config.timeout)
                results[index] = result
            except Exception as e:
                if error_handler:
                    result = error_handler(e, params_list[index])
                    results[index] = result
                else:
                    logger.error(f"Task {index} failed after retries: {e}")
                    results[index] = None
            
            self._completed_tasks += 1
            if progress_callback:
                progress_callback(self._completed_tasks, self._total_tasks)
        
        return results
    
    def _execute_with_retry(
        self,
        func: Callable,
        params: Dict[str, Any],
        max_retries: int
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(**params)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt * 0.1)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for task: {e}")
        
        raise last_exception
    
    def _wait_for_memory(self):
        """Wait until memory usage is below limit."""
        if not self.config.memory_limit_gb:
            return
        
        memory_limit_bytes = self.config.memory_limit_gb * 1024**3
        
        while True:
            current_usage = psutil.Process().memory_info().rss
            if current_usage < memory_limit_bytes * 0.9:  # 90% threshold
                break
            time.sleep(0.1)
    
    def _start_resource_monitoring(self):
        """Start monitoring resource usage."""
        self._monitoring = True
        self._resource_data = []
        
        def monitor():
            while self._monitoring:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                
                self._resource_data.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_info.percent,
                    'memory_used_gb': memory_info.used / (1024**3)
                })
                
                time.sleep(1)
        
        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
    
    def _stop_resource_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    def map_reduce(
        self,
        map_func: Callable,
        reduce_func: Callable,
        data: List[Any],
        initial_value: Any = None
    ) -> Any:
        """
        Execute map-reduce pattern in parallel.
        
        Args:
            map_func: Function to map over data
            reduce_func: Function to reduce results
            data: Input data list
            initial_value: Initial value for reduction
        
        Returns:
            Reduced result
        """
        # Map phase
        mapped_results = self.execute(
            lambda item: map_func(item),
            [{'item': item} for item in data]
        )
        
        # Reduce phase
        if initial_value is not None:
            result = initial_value
        else:
            result = mapped_results[0]
            mapped_results = mapped_results[1:]
        
        for item in mapped_results:
            result = reduce_func(result, item)
        
        return result
    
    def batch_execute(
        self,
        func: Callable,
        params_list: List[Dict[str, Any]],
        batch_size: int,
        batch_processor: Optional[Callable[[List[Any]], Any]] = None
    ) -> List[Any]:
        """
        Execute in batches with optional batch processing.
        
        Args:
            func: Function to execute
            params_list: List of parameters
            batch_size: Size of each batch
            batch_processor: Optional function to process batch results
        
        Returns:
            List of results or processed batch results
        """
        all_results = []
        
        for i in range(0, len(params_list), batch_size):
            batch_params = params_list[i:i + batch_size]
            batch_results = self.execute(func, batch_params)
            
            if batch_processor:
                processed = batch_processor(batch_results)
                all_results.append(processed)
            else:
                all_results.extend(batch_results)
        
        return all_results
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage during execution."""
        if not self._resource_data:
            return {}
        
        cpu_values = [d['cpu_percent'] for d in self._resource_data]
        memory_values = [d['memory_percent'] for d in self._resource_data]
        
        return {
            'cpu': {
                'mean': np.mean(cpu_values),
                'max': np.max(cpu_values),
                'min': np.min(cpu_values)
            },
            'memory': {
                'mean': np.mean(memory_values),
                'max': np.max(memory_values),
                'min': np.min(memory_values)
            },
            'duration': self._resource_data[-1]['timestamp'] - self._resource_data[0]['timestamp']
        }
    
    def shutdown(self):
        """Shutdown the executor."""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("ParallelExecutor shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Specialized executors for common patterns

class AlgorithmParallelExecutor(ParallelExecutor):
    """
    Specialized executor for running algorithms in parallel.
    
    Handles algorithm-specific requirements like:
    - Seed management for reproducibility
    - Result aggregation
    - Progress tracking per algorithm
    """
    
    def run_experiments(
        self,
        algorithm_class,
        problem,
        param_grid: List[Dict[str, Any]],
        n_runs: int = 30,
        aggregate_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run multiple algorithm experiments in parallel.
        
        Args:
            algorithm_class: Algorithm class to instantiate
            problem: Problem instance
            param_grid: List of parameter configurations
            n_runs: Number of runs per configuration
            aggregate_func: Function to aggregate results
        
        Returns:
            Dictionary with results and statistics
        """
        # Generate all experiment configurations
        experiments = []
        for params in param_grid:
            for run in range(n_runs):
                exp_params = params.copy()
                exp_params['seed'] = run  # Different seed for each run
                experiments.append({
                    'algorithm_class': algorithm_class,
                    'problem': problem,
                    'params': exp_params,
                    'run_id': run,
                    'config_id': param_grid.index(params)
                })
        
        # Run experiments
        def run_single_experiment(algorithm_class, problem, params, run_id, config_id):
            algo = algorithm_class(problem, **params)
            result = algo.run()
            return {
                'config_id': config_id,
                'run_id': run_id,
                'params': params,
                'result': result
            }
        
        results = self.execute(run_single_experiment, experiments)
        
        # Aggregate results by configuration
        aggregated = self._aggregate_results(results, param_grid, aggregate_func)
        
        return aggregated
    
    def _aggregate_results(
        self,
        results: List[Dict[str, Any]],
        param_grid: List[Dict[str, Any]],
        aggregate_func: Optional[Callable]
    ) -> Dict[str, Any]:
        """Aggregate results by configuration."""
        from collections import defaultdict
        
        # Group by configuration
        config_results = defaultdict(list)
        for result in results:
            config_id = result['config_id']
            config_results[config_id].append(result['result'])
        
        # Default aggregation
        if aggregate_func is None:
            def aggregate_func(results_list):
                fitness_values = [r.get('best_fitness', float('inf')) for r in results_list]
                return {
                    'mean': np.mean(fitness_values),
                    'std': np.std(fitness_values),
                    'min': np.min(fitness_values),
                    'max': np.max(fitness_values),
                    'median': np.median(fitness_values)
                }
        
        # Aggregate each configuration
        aggregated = {}
        for config_id, results_list in config_results.items():
            aggregated[config_id] = {
                'params': param_grid[config_id],
                'statistics': aggregate_func(results_list),
                'n_runs': len(results_list)
            }
        
        return aggregated


class PopulationParallelizer:
    """
    Parallelize population-based operations within algorithms.
    
    Useful for parallelizing fitness evaluations, individual updates,
    and other population-level operations.
    """
    
    def __init__(self, n_workers: Optional[int] = None):
        """Initialize population parallelizer."""
        self.n_workers = n_workers or max(1, mp.cpu_count() - 1)
    
    def evaluate_population(
        self,
        population: List[Any],
        evaluation_func: Callable,
        use_multiprocessing: bool = True
    ) -> List[float]:
        """
        Evaluate population in parallel.
        
        Args:
            population: List of individuals
            evaluation_func: Function to evaluate each individual
            use_multiprocessing: Whether to use multiprocessing
        
        Returns:
            List of fitness values
        """
        if len(population) < self.n_workers * 2 or not use_multiprocessing:
            # Serial evaluation for small populations
            return [evaluation_func(ind) for ind in population]
        
        # Parallel evaluation
        with Pool(self.n_workers) as pool:
            fitness_values = pool.map(evaluation_func, population)
        
        return fitness_values
    
    def update_population(
        self,
        population: List[Any],
        update_func: Callable,
        context: Dict[str, Any],
        chunk_size: Optional[int] = None
    ) -> List[Any]:
        """
        Update population in parallel.
        
        Args:
            population: List of individuals
            update_func: Function to update each individual
            context: Shared context for updates
            chunk_size: Chunk size for processing
        
        Returns:
            Updated population
        """
        if len(population) < self.n_workers * 2:
            # Serial update for small populations
            return [update_func(ind, context) for ind in population]
        
        # Prepare partial function with context
        update_with_context = partial(update_func, context=context)
        
        # Parallel update
        chunk_size = chunk_size or max(1, len(population) // (self.n_workers * 4))
        
        with Pool(self.n_workers) as pool:
            updated_population = pool.map(
                update_with_context,
                population,
                chunksize=chunk_size
            )
        
        return updated_population


# Utility functions for parallel execution

def parallelize_independent_runs(
    algorithm_class,
    problem,
    n_runs: int,
    algorithm_params: Optional[Dict[str, Any]] = None,
    n_workers: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run multiple independent algorithm instances in parallel.
    
    Args:
        algorithm_class: Algorithm class
        problem: Problem instance
        n_runs: Number of runs
        algorithm_params: Algorithm parameters
        n_workers: Number of workers
    
    Returns:
        List of results from all runs
    """
    executor = ParallelExecutor(ExecutionConfig(
        strategy=ExecutionStrategy.PROCESS_POOL,
        n_workers=n_workers
    ))
    
    # Prepare parameters for each run
    params_list = []
    for i in range(n_runs):
        params = algorithm_params.copy() if algorithm_params else {}
        params['seed'] = i  # Different seed for each run
        params_list.append({
            'algorithm_class': algorithm_class,
            'problem': problem,
            'params': params
        })
    
    # Run function
    def run_algorithm(algorithm_class, problem, params):
        algo = algorithm_class(problem, **params)
        return algo.run()
    
    # Execute in parallel
    with executor:
        results = executor.execute(run_algorithm, params_list)
    
    return results


def optimize_parallel_config(
    task_count: int,
    task_duration_estimate: float,
    memory_per_task_gb: float = 0.5
) -> ExecutionConfig:
    """
    Automatically determine optimal parallel configuration.
    
    Args:
        task_count: Number of tasks to execute
        task_duration_estimate: Estimated duration per task (seconds)
        memory_per_task_gb: Memory requirement per task
    
    Returns:
        Optimized ExecutionConfig
    """
    # Get system info
    cpu_count = mp.cpu_count()
    available_memory_gb = psutil.virtual_memory().available / (1024**3)
    
    # Determine strategy
    if task_count < 10 or task_duration_estimate < 0.1:
        # Serial for small/fast tasks
        strategy = ExecutionStrategy.SERIAL
        n_workers = 1
    elif task_duration_estimate < 1.0:
        # Threads for medium tasks
        strategy = ExecutionStrategy.THREAD_POOL
        n_workers = min(cpu_count, task_count)
    else:
        # Processes for heavy tasks
        strategy = ExecutionStrategy.PROCESS_POOL
        n_workers = min(
            cpu_count - 1,  # Leave one CPU free
            int(available_memory_gb / memory_per_task_gb),  # Memory constraint
            task_count  # Don't exceed task count
        )
    
    # Dynamic scheduling for uneven workloads
    dynamic_scheduling = task_duration_estimate > 5.0
    
    return ExecutionConfig(
        strategy=strategy,
        n_workers=max(1, n_workers),
        dynamic_scheduling=dynamic_scheduling,
        memory_limit_gb=available_memory_gb * 0.8  # Use 80% of available
    )