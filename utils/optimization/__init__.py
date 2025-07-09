"""
Performance optimization utilities for BioAlgoCompare.

This package provides tools and utilities for optimizing algorithm performance,
parallel execution, caching, and scalability improvements.

Components:
    - ParallelExecutor: Parallel algorithm execution with multiple strategies
    - CachingSystem: Smart caching for expensive computations
    - MemoryOptimizer: Memory usage optimization utilities
    - VectorizedOperations: NumPy-optimized operations
    - ProfilerIntegration: Performance profiling tools
"""

from .parallel_executor import ParallelExecutor, ExecutionStrategy
from .caching_system import CachingSystem, cache_result, memoize
from .memory_optimizer import MemoryOptimizer, memory_efficient
from .vectorized_ops import VectorizedOperations
from .profiler import PerformanceProfiler, profile_function

__all__ = [
    'ParallelExecutor',
    'ExecutionStrategy',
    'CachingSystem',
    'cache_result',
    'memoize',
    'MemoryOptimizer',
    'memory_efficient',
    'VectorizedOperations',
    'PerformanceProfiler',
    'profile_function',
]