"""
Advanced caching system for performance optimization.

This module provides intelligent caching mechanisms for expensive computations,
including memory-based caching, disk persistence, and distributed caching support.
"""

import time
import hashlib
import json
import pickle
import functools
import threading
from typing import Any, Callable, Dict, Optional, Union, Tuple, List
from pathlib import Path
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
import numpy as np
import weakref
import gc

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheStats:
    """Track cache performance statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.computation_time_saved = 0.0
        self.storage_bytes = 0
        self._lock = threading.Lock()
    
    def record_hit(self, time_saved: float = 0.0):
        """Record a cache hit."""
        with self._lock:
            self.hits += 1
            self.computation_time_saved += time_saved
    
    def record_miss(self):
        """Record a cache miss."""
        with self._lock:
            self.misses += 1
    
    def record_eviction(self):
        """Record a cache eviction."""
        with self._lock:
            self.evictions += 1
    
    def update_storage(self, bytes_used: int):
        """Update storage usage."""
        with self._lock:
            self.storage_bytes = bytes_used
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary."""
        with self._lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': self.hit_rate,
                'evictions': self.evictions,
                'time_saved': self.computation_time_saved,
                'storage_mb': self.storage_bytes / (1024 * 1024)
            }


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache implementation.
    
    Features:
    - O(1) get and put operations
    - Automatic eviction of least recently used items
    - TTL (Time To Live) support
    - Size and memory limits
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: Optional[float] = None,
        ttl_seconds: Optional[float] = None
    ):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items
            max_memory_mb: Maximum memory usage in MB
            ttl_seconds: Time to live for cached items
        """
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.ttl_seconds = ttl_seconds
        
        self._cache = OrderedDict()
        self._timestamps = {}
        self._sizes = {}
        self._lock = threading.RLock()
        self._memory_used = 0
        
        self.stats = CacheStats()
        
        logger.info(f"Initialized LRUCache (max_size={max_size}, "
                   f"max_memory_mb={max_memory_mb}, ttl_seconds={ttl_seconds})")
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        with self._lock:
            # Check if key exists
            if key not in self._cache:
                self.stats.record_miss()
                return None
            
            # Check TTL
            if self.ttl_seconds and self._is_expired(key):
                self._remove(key)
                self.stats.record_miss()
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self.stats.record_hit()
            return self._cache[key]
    
    def put(self, key: str, value: Any, size_bytes: Optional[int] = None) -> None:
        """Put item in cache."""
        with self._lock:
            # Remove if already exists
            if key in self._cache:
                self._remove(key)
            
            # Calculate size if not provided
            if size_bytes is None:
                size_bytes = self._estimate_size(value)
            
            # Check memory limit
            if self.max_memory_mb:
                # Evict items until we have space
                while (self._memory_used + size_bytes > 
                       self.max_memory_mb * 1024 * 1024 and self._cache):
                    self._evict_oldest()
            
            # Check size limit
            while len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            # Add new item
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._sizes[key] = size_bytes
            self._memory_used += size_bytes
            
            self.stats.update_storage(self._memory_used)
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._sizes.clear()
            self._memory_used = 0
            self.stats.update_storage(0)
    
    def _is_expired(self, key: str) -> bool:
        """Check if item has expired."""
        if not self.ttl_seconds or key not in self._timestamps:
            return False
        
        age = time.time() - self._timestamps[key]
        return age > self.ttl_seconds
    
    def _remove(self, key: str) -> None:
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            self._memory_used -= self._sizes.get(key, 0)
            self._sizes.pop(key, None)
    
    def _evict_oldest(self) -> None:
        """Evict oldest item from cache."""
        if self._cache:
            key = next(iter(self._cache))
            self._remove(key)
            self.stats.record_eviction()
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        except:
            # Fallback estimation
            return 1000  # 1KB default


class CachingSystem:
    """
    Comprehensive caching system with multiple backends.
    
    Features:
    - Multi-level caching (memory, disk, distributed)
    - Intelligent key generation
    - Async write-through to disk
    - Cache warming and preloading
    - Compression support
    """
    
    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_limit_mb: float = 500,
        disk_cache_dir: Optional[Path] = None,
        redis_config: Optional[Dict[str, Any]] = None,
        enable_compression: bool = True
    ):
        """
        Initialize caching system.
        
        Args:
            memory_cache_size: Max items in memory cache
            memory_limit_mb: Memory limit for cache
            disk_cache_dir: Directory for disk cache
            redis_config: Redis connection configuration
            enable_compression: Whether to compress cached data
        """
        # Memory cache (L1)
        self.memory_cache = LRUCache(
            max_size=memory_cache_size,
            max_memory_mb=memory_limit_mb
        )
        
        # Disk cache (L2)
        self.disk_cache_dir = disk_cache_dir
        if disk_cache_dir:
            disk_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Disk cache enabled at {disk_cache_dir}")
        
        # Redis cache (L3)
        self.redis_client = None
        if redis_config and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(**redis_config)
                self.redis_client.ping()
                logger.info("Redis cache enabled")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        
        self.enable_compression = enable_compression
        self._write_queue = []
        self._write_thread = None
        self._shutdown = False
        
        # Start async write thread for disk cache
        if disk_cache_dir:
            self._start_write_thread()
    
    def get(
        self,
        key: str,
        compute_func: Optional[Callable] = None,
        ttl: Optional[float] = None
    ) -> Any:
        """
        Get value from cache or compute if missing.
        
        Args:
            key: Cache key
            compute_func: Function to compute value if cache miss
            ttl: Time to live for this item
        
        Returns:
            Cached or computed value
        """
        # Try memory cache (L1)
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try disk cache (L2)
        if self.disk_cache_dir:
            value = self._get_from_disk(key)
            if value is not None:
                # Promote to memory cache
                self.memory_cache.put(key, value)
                return value
        
        # Try Redis cache (L3)
        if self.redis_client:
            value = self._get_from_redis(key)
            if value is not None:
                # Promote to memory and disk cache
                self.memory_cache.put(key, value)
                if self.disk_cache_dir:
                    self._queue_disk_write(key, value)
                return value
        
        # Cache miss - compute value
        if compute_func is None:
            return None
        
        start_time = time.time()
        value = compute_func()
        compute_time = time.time() - start_time
        
        # Store in all cache levels
        self.put(key, value, ttl=ttl)
        
        logger.debug(f"Computed value for key {key} in {compute_time:.3f}s")
        
        return value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in all cache levels."""
        # Memory cache (L1)
        self.memory_cache.put(key, value)
        
        # Disk cache (L2) - async write
        if self.disk_cache_dir:
            self._queue_disk_write(key, value)
        
        # Redis cache (L3)
        if self.redis_client:
            self._put_to_redis(key, value, ttl)
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value at all levels."""
        # Memory cache
        with self.memory_cache._lock:
            if key in self.memory_cache._cache:
                self.memory_cache._remove(key)
        
        # Disk cache
        if self.disk_cache_dir:
            cache_file = self._get_disk_path(key)
            if cache_file.exists():
                cache_file.unlink()
        
        # Redis cache
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete from Redis: {e}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        count = 0
        
        # Memory cache
        with self.memory_cache._lock:
            keys_to_remove = [
                k for k in self.memory_cache._cache 
                if pattern in k or k.startswith(pattern)
            ]
            for key in keys_to_remove:
                self.memory_cache._remove(key)
                count += 1
        
        # Disk cache
        if self.disk_cache_dir:
            for cache_file in self.disk_cache_dir.glob(f"*{pattern}*.cache"):
                cache_file.unlink()
                count += 1
        
        # Redis cache
        if self.redis_client:
            try:
                for key in self.redis_client.scan_iter(match=f"*{pattern}*"):
                    self.redis_client.delete(key)
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to scan Redis: {e}")
        
        logger.info(f"Invalidated {count} cache entries matching '{pattern}'")
        return count
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk cache file path for key."""
        # Use hash to avoid filesystem issues
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.disk_cache_dir / f"{key_hash}.cache"
    
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        cache_file = self._get_disk_path(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # Check if expired
            if 'expires' in data and data['expires'] < time.time():
                cache_file.unlink()
                return None
            
            value = data['value']
            
            # Decompress if needed
            if self.enable_compression and 'compressed' in data:
                import zlib
                value = pickle.loads(zlib.decompress(value))
            
            return value
            
        except Exception as e:
            logger.warning(f"Failed to read disk cache: {e}")
            return None
    
    def _queue_disk_write(self, key: str, value: Any) -> None:
        """Queue value for async disk write."""
        self._write_queue.append((key, value, time.time()))
    
    def _start_write_thread(self) -> None:
        """Start background thread for disk writes."""
        def write_loop():
            while not self._shutdown:
                if self._write_queue:
                    key, value, timestamp = self._write_queue.pop(0)
                    self._write_to_disk(key, value)
                else:
                    time.sleep(0.1)
        
        self._write_thread = threading.Thread(target=write_loop, daemon=True)
        self._write_thread.start()
    
    def _write_to_disk(self, key: str, value: Any) -> None:
        """Write value to disk cache."""
        cache_file = self._get_disk_path(key)
        
        try:
            data = {'value': value}
            
            # Compress if enabled
            if self.enable_compression:
                import zlib
                compressed = zlib.compress(pickle.dumps(value))
                if len(compressed) < len(pickle.dumps(value)) * 0.9:
                    data['value'] = compressed
                    data['compressed'] = True
            
            # Write atomically
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            temp_file.replace(cache_file)
            
        except Exception as e:
            logger.warning(f"Failed to write disk cache: {e}")
    
    def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            
            return pickle.loads(data)
            
        except Exception as e:
            logger.warning(f"Failed to get from Redis: {e}")
            return None
    
    def _put_to_redis(self, key: str, value: Any, ttl: Optional[float]) -> None:
        """Put value in Redis cache."""
        if not self.redis_client:
            return
        
        try:
            data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            
            if ttl:
                self.redis_client.setex(key, int(ttl), data)
            else:
                self.redis_client.set(key, data)
                
        except Exception as e:
            logger.warning(f"Failed to put to Redis: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        stats = {
            'memory': self.memory_cache.stats.get_summary()
        }
        
        if self.disk_cache_dir:
            cache_files = list(self.disk_cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            stats['disk'] = {
                'files': len(cache_files),
                'size_mb': total_size / (1024 * 1024),
                'write_queue': len(self._write_queue)
            }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis'] = {
                    'connected': True,
                    'memory_mb': info.get('used_memory', 0) / (1024 * 1024),
                    'keys': self.redis_client.dbsize()
                }
            except:
                stats['redis'] = {'connected': False}
        
        return stats
    
    def shutdown(self) -> None:
        """Shutdown caching system."""
        self._shutdown = True
        
        # Process remaining writes
        while self._write_queue:
            key, value, _ = self._write_queue.pop(0)
            self._write_to_disk(key, value)
        
        if self._write_thread:
            self._write_thread.join(timeout=5)
        
        logger.info("CachingSystem shutdown complete")


# Decorator for function caching

def cache_result(
    cache_key_func: Optional[Callable] = None,
    ttl_seconds: Optional[float] = None,
    cache_instance: Optional[CachingSystem] = None
):
    """
    Decorator to cache function results.
    
    Args:
        cache_key_func: Function to generate cache key from arguments
        ttl_seconds: Time to live for cached results
        cache_instance: CachingSystem instance to use
    
    Example:
        >>> @cache_result(ttl_seconds=3600)
        ... def expensive_computation(x, y):
        ...     return x ** y
    """
    def decorator(func):
        # Use default cache if none provided
        nonlocal cache_instance
        if cache_instance is None:
            cache_instance = _get_default_cache()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                key = cache_key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)
            
            # Get or compute
            return cache_instance.get(
                key,
                compute_func=lambda: func(*args, **kwargs),
                ttl=ttl_seconds
            )
        
        # Add cache control methods
        wrapper.invalidate = lambda *args, **kwargs: cache_instance.invalidate(
            cache_key_func(*args, **kwargs) if cache_key_func else 
            ":".join([func.__name__] + [str(arg) for arg in args])
        )
        
        return wrapper
    
    return decorator


# Simple memoization decorator

def memoize(maxsize: int = 128):
    """
    Simple memoization decorator with LRU eviction.
    
    Args:
        maxsize: Maximum cache size
    
    Example:
        >>> @memoize(maxsize=100)
        ... def fibonacci(n):
        ...     if n < 2:
        ...         return n
        ...     return fibonacci(n-1) + fibonacci(n-2)
    """
    def decorator(func):
        cache = LRUCache(max_size=maxsize)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create hashable key
            key = str((args, tuple(sorted(kwargs.items()))))
            
            # Check cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.put(key, result)
            
            return result
        
        # Add cache info method
        wrapper.cache_info = lambda: cache.stats.get_summary()
        wrapper.cache_clear = lambda: cache.clear()
        
        return wrapper
    
    return decorator


# Global default cache instance
_default_cache = None

def _get_default_cache() -> CachingSystem:
    """Get or create default cache instance."""
    global _default_cache
    if _default_cache is None:
        cache_dir = Path.home() / '.bioalgocompare' / 'cache'
        _default_cache = CachingSystem(
            memory_cache_size=1000,
            memory_limit_mb=100,
            disk_cache_dir=cache_dir
        )
    return _default_cache


# Cache preloading utilities

class CacheWarmer:
    """Utility for warming up caches before execution."""
    
    def __init__(self, cache_system: CachingSystem):
        self.cache_system = cache_system
    
    def warm_from_history(
        self,
        history_file: Path,
        compute_func: Callable[[str], Any],
        max_items: Optional[int] = None
    ) -> int:
        """
        Warm cache from historical access patterns.
        
        Args:
            history_file: File with cache keys (one per line)
            compute_func: Function to compute values for keys
            max_items: Maximum items to preload
        
        Returns:
            Number of items loaded
        """
        if not history_file.exists():
            logger.warning(f"History file not found: {history_file}")
            return 0
        
        loaded = 0
        with open(history_file) as f:
            for i, line in enumerate(f):
                if max_items and i >= max_items:
                    break
                
                key = line.strip()
                if key:
                    # Check if already cached
                    if self.cache_system.memory_cache.get(key) is None:
                        try:
                            value = compute_func(key)
                            self.cache_system.put(key, value)
                            loaded += 1
                        except Exception as e:
                            logger.warning(f"Failed to warm cache for {key}: {e}")
        
        logger.info(f"Warmed cache with {loaded} items")
        return loaded
    
    def warm_common_patterns(
        self,
        pattern_generator: Callable[[], List[Tuple[str, Any]]],
        batch_size: int = 100
    ) -> int:
        """
        Warm cache with common access patterns.
        
        Args:
            pattern_generator: Function that yields (key, value) pairs
            batch_size: Number of items to load at once
        
        Returns:
            Number of items loaded
        """
        loaded = 0
        
        for batch in self._batch_generator(pattern_generator(), batch_size):
            for key, value in batch:
                self.cache_system.put(key, value)
                loaded += 1
        
        logger.info(f"Warmed cache with {loaded} common patterns")
        return loaded
    
    def _batch_generator(self, items, batch_size):
        """Generate batches from items."""
        batch = []
        for item in items:
            batch.append(item)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch