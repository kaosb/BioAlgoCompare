"""
Memory optimization utilities for efficient algorithm execution.

This module provides tools for optimizing memory usage including object pooling,
memory profiling, garbage collection optimization, and memory-efficient data structures.
"""

import gc
import sys
import weakref
import psutil
import numpy as np
from typing import Any, Dict, List, Optional, Type, Callable, TypeVar, Generic
from collections import deque
from contextlib import contextmanager
import logging
import threading
from dataclasses import dataclass
import tracemalloc
from functools import wraps
import warnings

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    used_mb: float
    available_mb: float
    percent: float
    peak_mb: float
    gc_collections: Dict[int, int]
    
    @classmethod
    def current(cls) -> 'MemoryStats':
        """Get current memory statistics."""
        memory = psutil.virtual_memory()
        gc_stats = gc.get_stats()
        
        return cls(
            used_mb=memory.used / (1024 * 1024),
            available_mb=memory.available / (1024 * 1024),
            percent=memory.percent,
            peak_mb=psutil.Process().memory_info().rss / (1024 * 1024),
            gc_collections={i: s.get('collections', 0) for i, s in enumerate(gc_stats)}
        )


class ObjectPool(Generic[T]):
    """
    Thread-safe object pool for reusing expensive objects.
    
    Reduces memory allocation overhead by reusing objects instead of
    creating new ones. Particularly useful for population-based algorithms.
    
    Example:
        >>> pool = ObjectPool(Individual, max_size=100)
        >>> ind = pool.acquire()
        >>> # Use individual
        >>> pool.release(ind)
    """
    
    def __init__(
        self,
        object_class: Type[T],
        max_size: int = 1000,
        init_func: Optional[Callable[[], T]] = None,
        reset_func: Optional[Callable[[T], None]] = None,
        pre_allocate: int = 0
    ):
        """
        Initialize object pool.
        
        Args:
            object_class: Class of objects to pool
            max_size: Maximum pool size
            init_func: Custom initialization function
            reset_func: Function to reset object state
            pre_allocate: Number of objects to pre-allocate
        """
        self.object_class = object_class
        self.max_size = max_size
        self.init_func = init_func or object_class
        self.reset_func = reset_func
        
        self._pool: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._created_count = 0
        self._in_use = weakref.WeakSet()
        
        # Pre-allocate objects
        if pre_allocate > 0:
            self._pre_allocate(min(pre_allocate, max_size))
        
        logger.info(f"Initialized ObjectPool for {object_class.__name__} "
                   f"(max_size={max_size}, pre_allocated={pre_allocate})")
    
    def _pre_allocate(self, count: int) -> None:
        """Pre-allocate objects to pool."""
        for _ in range(count):
            obj = self.init_func()
            self._pool.append(obj)
            self._created_count += 1
    
    def acquire(self) -> T:
        """Acquire object from pool or create new one."""
        with self._lock:
            # Try to get from pool
            if self._pool:
                obj = self._pool.popleft()
                if self.reset_func:
                    self.reset_func(obj)
            else:
                # Create new object
                obj = self.init_func()
                self._created_count += 1
            
            self._in_use.add(obj)
            return obj
    
    def release(self, obj: T) -> None:
        """Release object back to pool."""
        with self._lock:
            # Only add back if pool not full and object was from this pool
            if obj in self._in_use and len(self._pool) < self.max_size:
                self._in_use.discard(obj)
                self._pool.append(obj)
    
    def clear(self) -> None:
        """Clear the pool."""
        with self._lock:
            self._pool.clear()
            # Force garbage collection of unused objects
            gc.collect()
    
    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        with self._lock:
            return {
                'created': self._created_count,
                'pooled': len(self._pool),
                'in_use': len(self._in_use),
                'max_size': self.max_size
            }
    
    @contextmanager
    def get(self):
        """Context manager for acquiring and releasing objects."""
        obj = self.acquire()
        try:
            yield obj
        finally:
            self.release(obj)


class MemoryOptimizer:
    """
    Central memory optimization controller.
    
    Provides tools and strategies for optimizing memory usage during
    algorithm execution including monitoring, garbage collection tuning,
    and memory pressure management.
    """
    
    def __init__(
        self,
        target_memory_percent: float = 80.0,
        gc_threshold_mb: float = 100.0,
        enable_profiling: bool = False
    ):
        """
        Initialize memory optimizer.
        
        Args:
            target_memory_percent: Target maximum memory usage percentage
            gc_threshold_mb: Trigger GC when this much memory allocated
            enable_profiling: Enable detailed memory profiling
        """
        self.target_memory_percent = target_memory_percent
        self.gc_threshold_mb = gc_threshold_mb
        self.enable_profiling = enable_profiling
        
        self._initial_stats = MemoryStats.current()
        self._peak_memory = 0
        self._gc_enabled = gc.isenabled()
        self._original_thresholds = gc.get_threshold()
        
        # Object pools
        self._pools: Dict[str, ObjectPool] = {}
        
        # Profiling
        if enable_profiling:
            tracemalloc.start()
        
        # Configure garbage collection
        self._configure_gc()
        
        logger.info(f"MemoryOptimizer initialized (target={target_memory_percent}%, "
                   f"gc_threshold={gc_threshold_mb}MB)")
    
    def _configure_gc(self) -> None:
        """Configure garbage collection for optimal performance."""
        # Tune GC thresholds for less frequent but more thorough collection
        # This reduces overhead for algorithms with many small allocations
        gc.set_threshold(
            self._original_thresholds[0] * 2,  # Generation 0
            self._original_thresholds[1] * 2,  # Generation 1
            self._original_thresholds[2]       # Generation 2
        )
        
        # Disable GC during critical sections (will be managed manually)
        gc.disable()
        self._gc_enabled = False
    
    def create_pool(
        self,
        name: str,
        object_class: Type[T],
        max_size: int = 1000,
        **kwargs
    ) -> ObjectPool[T]:
        """
        Create or get object pool.
        
        Args:
            name: Pool name
            object_class: Class to pool
            max_size: Maximum pool size
            **kwargs: Additional arguments for ObjectPool
        
        Returns:
            ObjectPool instance
        """
        if name not in self._pools:
            self._pools[name] = ObjectPool(object_class, max_size, **kwargs)
        return self._pools[name]
    
    def check_memory_pressure(self) -> bool:
        """
        Check if memory pressure is high.
        
        Returns:
            True if memory usage exceeds target
        """
        stats = MemoryStats.current()
        return stats.percent > self.target_memory_percent
    
    def optimize_if_needed(self, force: bool = False) -> bool:
        """
        Run optimization if memory pressure is high.
        
        Args:
            force: Force optimization regardless of pressure
        
        Returns:
            True if optimization was performed
        """
        if force or self.check_memory_pressure():
            self._run_optimization()
            return True
        return False
    
    def _run_optimization(self) -> None:
        """Run memory optimization routine."""
        logger.info("Running memory optimization...")
        
        # Clear object pools
        for pool in self._pools.values():
            pool.clear()
        
        # Force garbage collection
        gc.collect(2)  # Full collection
        
        # Clear NumPy caches
        if hasattr(np, 'clear_caches'):
            np.clear_caches()
        
        # Log results
        stats = MemoryStats.current()
        logger.info(f"Memory after optimization: {stats.used_mb:.1f}MB ({stats.percent:.1f}%)")
    
    @contextmanager
    def managed_section(self, name: str = ""):
        """
        Context manager for memory-managed code sections.
        
        Args:
            name: Section name for logging
        
        Example:
            >>> with optimizer.managed_section("population_update"):
            ...     # Memory-intensive operations
            ...     pass
        """
        # Record initial state
        initial_stats = MemoryStats.current()
        
        # Enable GC for this section
        gc.enable()
        
        try:
            yield self
        finally:
            # Check if optimization needed
            self.optimize_if_needed()
            
            # Restore GC state
            if not self._gc_enabled:
                gc.disable()
            
            # Log memory usage
            final_stats = MemoryStats.current()
            delta_mb = final_stats.used_mb - initial_stats.used_mb
            
            if delta_mb > self.gc_threshold_mb:
                logger.warning(f"Section '{name}' allocated {delta_mb:.1f}MB")
    
    def get_memory_profile(self) -> Dict[str, Any]:
        """Get detailed memory profile."""
        profile = {
            'current': MemoryStats.current().__dict__,
            'initial': self._initial_stats.__dict__,
            'pools': {name: pool.get_stats() for name, pool in self._pools.items()}
        }
        
        if self.enable_profiling and tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')[:10]
            
            profile['top_allocations'] = [
                {
                    'file': stat.traceback.format()[0],
                    'size_mb': stat.size / (1024 * 1024),
                    'count': stat.count
                }
                for stat in top_stats
            ]
        
        return profile
    
    def reset(self) -> None:
        """Reset optimizer state."""
        # Clear pools
        for pool in self._pools.values():
            pool.clear()
        self._pools.clear()
        
        # Reset GC
        gc.set_threshold(*self._original_thresholds)
        if self._gc_enabled:
            gc.enable()
        
        # Stop profiling
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        logger.info("MemoryOptimizer reset")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.reset()


# Memory-efficient data structures

class CompactArray:
    """
    Memory-efficient array for numerical data.
    
    Uses appropriate dtype to minimize memory usage while maintaining precision.
    """
    
    def __init__(self, size: int, dtype: Optional[np.dtype] = None, fill_value: float = 0):
        """
        Initialize compact array.
        
        Args:
            size: Array size
            dtype: NumPy dtype (auto-detected if None)
            fill_value: Initial fill value
        """
        if dtype is None:
            # Auto-detect appropriate dtype
            if fill_value == int(fill_value) and abs(fill_value) < 32768:
                dtype = np.int16
            elif fill_value == int(fill_value) and abs(fill_value) < 2147483648:
                dtype = np.int32
            else:
                dtype = np.float32  # Use float32 instead of float64
        
        self._array = np.full(size, fill_value, dtype=dtype)
        self._dtype = dtype
    
    def __getitem__(self, index):
        return self._array[index]
    
    def __setitem__(self, index, value):
        self._array[index] = value
    
    def __len__(self):
        return len(self._array)
    
    @property
    def memory_usage(self) -> int:
        """Get memory usage in bytes."""
        return self._array.nbytes
    
    def resize(self, new_size: int, fill_value: float = 0) -> None:
        """Resize array efficiently."""
        if new_size == len(self._array):
            return
        
        if new_size < len(self._array):
            self._array = self._array[:new_size]
        else:
            # Extend with fill value
            extension = np.full(new_size - len(self._array), fill_value, dtype=self._dtype)
            self._array = np.concatenate([self._array, extension])


class SparseMatrix:
    """
    Memory-efficient sparse matrix implementation.
    
    Useful for large matrices with many zero values.
    """
    
    def __init__(self, shape: Tuple[int, int], dtype: np.dtype = np.float32):
        """Initialize sparse matrix."""
        self.shape = shape
        self.dtype = dtype
        self._data: Dict[Tuple[int, int], Any] = {}
    
    def __getitem__(self, key: Tuple[int, int]) -> Any:
        """Get element."""
        return self._data.get(key, 0)
    
    def __setitem__(self, key: Tuple[int, int], value: Any) -> None:
        """Set element."""
        if value == 0:
            # Don't store zeros
            self._data.pop(key, None)
        else:
            self._data[key] = value
    
    @property
    def nnz(self) -> int:
        """Number of non-zero elements."""
        return len(self._data)
    
    @property
    def density(self) -> float:
        """Matrix density (fraction of non-zero elements)."""
        total_elements = self.shape[0] * self.shape[1]
        return self.nnz / total_elements if total_elements > 0 else 0
    
    @property
    def memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        # Dictionary overhead + data
        return sys.getsizeof(self._data) + sum(
            sys.getsizeof(k) + sys.getsizeof(v) 
            for k, v in self._data.items()
        )
    
    def to_dense(self) -> np.ndarray:
        """Convert to dense NumPy array."""
        dense = np.zeros(self.shape, dtype=self.dtype)
        for (i, j), value in self._data.items():
            dense[i, j] = value
        return dense


# Decorators for memory optimization

def memory_efficient(
    max_memory_mb: Optional[float] = None,
    optimize_threshold_mb: float = 100,
    use_pool: Optional[str] = None
):
    """
    Decorator for memory-efficient function execution.
    
    Args:
        max_memory_mb: Maximum memory usage allowed
        optimize_threshold_mb: Run optimization if this much allocated
        use_pool: Object pool name to use
    
    Example:
        >>> @memory_efficient(max_memory_mb=500)
        ... def process_large_data(data):
        ...     # Process data
        ...     return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check initial memory
            initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            # Check memory limit
            if max_memory_mb:
                available = psutil.virtual_memory().available / (1024 * 1024)
                if available < max_memory_mb:
                    warnings.warn(f"Low memory: {available:.1f}MB available, "
                                f"{max_memory_mb:.1f}MB requested")
            
            # Create memory optimizer
            optimizer = MemoryOptimizer(
                gc_threshold_mb=optimize_threshold_mb
            )
            
            try:
                # Execute function
                with optimizer.managed_section(func.__name__):
                    result = func(*args, **kwargs)
                
                # Check memory usage
                final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                delta = final_memory - initial_memory
                
                if delta > optimize_threshold_mb:
                    logger.info(f"{func.__name__} allocated {delta:.1f}MB")
                    optimizer.optimize_if_needed(force=True)
                
                return result
                
            finally:
                optimizer.reset()
        
        return wrapper
    
    return decorator


def with_memory_limit(limit_mb: float):
    """
    Decorator to enforce memory limit on function.
    
    Args:
        limit_mb: Memory limit in megabytes
    
    Raises:
        MemoryError: If memory limit exceeded
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Monitor memory usage
            def check_memory():
                while True:
                    current_mb = psutil.Process().memory_info().rss / (1024 * 1024)
                    if current_mb > limit_mb:
                        raise MemoryError(f"Memory limit exceeded: {current_mb:.1f}MB > {limit_mb}MB")
                    time.sleep(0.1)
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=check_memory, daemon=True)
            monitor_thread.start()
            
            try:
                return func(*args, **kwargs)
            finally:
                # Thread will be terminated when main thread exits
                pass
        
        return wrapper
    
    return decorator


# Memory optimization strategies for algorithms

class PopulationMemoryManager:
    """
    Memory manager specifically for population-based algorithms.
    
    Provides strategies for efficient population storage and manipulation.
    """
    
    def __init__(self, population_size: int, individual_size: int):
        """
        Initialize population memory manager.
        
        Args:
            population_size: Number of individuals
            individual_size: Size of each individual (dimensions)
        """
        self.population_size = population_size
        self.individual_size = individual_size
        
        # Use compact storage
        self._positions = CompactArray(
            population_size * individual_size,
            dtype=np.float32
        ).reshape(population_size, individual_size)
        
        self._fitness = CompactArray(population_size, dtype=np.float32)
        
        # Object pool for temporary individuals
        self._temp_pool = ObjectPool(
            lambda: np.zeros(individual_size, dtype=np.float32),
            max_size=population_size // 10
        )
    
    def get_position(self, index: int) -> np.ndarray:
        """Get individual position."""
        return self._positions[index]
    
    def set_position(self, index: int, position: np.ndarray) -> None:
        """Set individual position."""
        self._positions[index] = position
    
    def get_fitness(self, index: int) -> float:
        """Get individual fitness."""
        return self._fitness[index]
    
    def set_fitness(self, index: int, fitness: float) -> None:
        """Set individual fitness."""
        self._fitness[index] = fitness
    
    def swap_individuals(self, i: int, j: int) -> None:
        """Efficiently swap two individuals."""
        # Swap positions
        self._positions[[i, j]] = self._positions[[j, i]]
        # Swap fitness
        self._fitness[i], self._fitness[j] = self._fitness[j], self._fitness[i]
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        return {
            'positions_mb': self._positions.memory_usage / (1024 * 1024),
            'fitness_mb': self._fitness.memory_usage / (1024 * 1024),
            'total_mb': (self._positions.memory_usage + self._fitness.memory_usage) / (1024 * 1024)
        }
    
    @contextmanager
    def temporary_individual(self):
        """Get temporary individual from pool."""
        with self._temp_pool.get() as temp:
            yield temp