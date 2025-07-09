"""
Plugin registry for managing algorithm registration.
"""

import logging
from typing import Dict, Type, List, Optional, Any, Callable
from functools import wraps

from algorithms.base_v2 import MetaheuristicAlgorithm
from .plugin_base import Plugin, AlgorithmPlugin, PluginMetadata


logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for algorithm plugins.
    """
    
    # Class-level storage
    _plugins: Dict[str, Plugin] = {}
    _algorithms: Dict[str, Type[MetaheuristicAlgorithm]] = {}
    _hooks: Dict[str, List[Callable]] = {}
    
    @classmethod
    def register_plugin(cls, plugin: Plugin) -> bool:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance
            
        Returns:
            True if registered successfully
        """
        try:
            metadata = plugin.get_metadata()
            name = metadata.name
            
            if name in cls._plugins:
                logger.warning(f"Plugin {name} already registered, overwriting")
            
            # Validate plugin
            if not plugin.validate_environment():
                logger.error(f"Plugin {name} failed environment validation")
                return False
            
            # Register plugin
            cls._plugins[name] = plugin
            
            # Register algorithm
            algo_class = plugin.get_algorithm_class()
            algo_name = metadata.algorithm_class
            cls._algorithms[algo_name] = algo_class
            
            # Setup plugin
            plugin.setup()
            
            # Call registration hooks
            cls._call_hooks('on_plugin_register', plugin)
            
            logger.info(f"Registered plugin: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False
    
    @classmethod
    def unregister_plugin(cls, name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if unregistered successfully
        """
        if name not in cls._plugins:
            return False
        
        plugin = cls._plugins[name]
        metadata = plugin.get_metadata()
        
        # Call hooks
        cls._call_hooks('on_plugin_unregister', plugin)
        
        # Teardown
        try:
            plugin.teardown()
        except Exception as e:
            logger.error(f"Error during plugin teardown: {e}")
        
        # Remove from registries
        del cls._plugins[name]
        
        algo_name = metadata.algorithm_class
        if algo_name in cls._algorithms:
            del cls._algorithms[algo_name]
        
        logger.info(f"Unregistered plugin: {name}")
        return True
    
    @classmethod
    def get_plugin(cls, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return cls._plugins.get(name)
    
    @classmethod
    def get_algorithm(cls, name: str) -> Optional[Type[MetaheuristicAlgorithm]]:
        """Get algorithm class by name."""
        return cls._algorithms.get(name)
    
    @classmethod
    def list_plugins(cls) -> List[str]:
        """List all registered plugin names."""
        return list(cls._plugins.keys())
    
    @classmethod
    def list_algorithms(cls) -> List[str]:
        """List all registered algorithm names."""
        return list(cls._algorithms.keys())
    
    @classmethod
    def get_plugin_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information."""
        plugin = cls.get_plugin(name)
        if not plugin:
            return None
        
        metadata = plugin.get_metadata()
        return {
            'metadata': metadata.to_dict(),
            'parameter_schema': plugin.get_parameter_schema(),
            'custom_operators': list(plugin.get_custom_operators().keys()),
            'individual_class': plugin.get_individual_class() is not None
        }
    
    @classmethod
    def add_hook(cls, event: str, callback: Callable) -> None:
        """
        Add a hook for plugin events.
        
        Args:
            event: Event name ('on_plugin_register', 'on_plugin_unregister')
            callback: Callback function
        """
        if event not in cls._hooks:
            cls._hooks[event] = []
        cls._hooks[event].append(callback)
    
    @classmethod
    def remove_hook(cls, event: str, callback: Callable) -> None:
        """Remove a hook."""
        if event in cls._hooks and callback in cls._hooks[event]:
            cls._hooks[event].remove(callback)
    
    @classmethod
    def _call_hooks(cls, event: str, *args, **kwargs) -> None:
        """Call all hooks for an event."""
        if event in cls._hooks:
            for callback in cls._hooks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in hook {callback.__name__}: {e}")
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registrations."""
        # Teardown all plugins
        for plugin in cls._plugins.values():
            try:
                plugin.teardown()
            except:
                pass
        
        cls._plugins.clear()
        cls._algorithms.clear()
        cls._hooks.clear()


# Decorator for automatic registration
def register_plugin(name: str, 
                   version: str = "1.0",
                   author: str = "Unknown",
                   description: str = "",
                   problem_types: Optional[List[str]] = None,
                   dependencies: Optional[List[str]] = None):
    """
    Decorator to register an algorithm as a plugin.
    
    Usage:
        @register_plugin("MyAlgorithm", version="1.0", author="Me")
        class MyAlgorithm(MetaheuristicAlgorithm):
            ...
    """
    def decorator(algorithm_class: Type[MetaheuristicAlgorithm]):
        # Create plugin
        plugin = AlgorithmPlugin(
            name=name,
            version=version,
            author=author,
            description=description or f"{algorithm_class.__name__} algorithm",
            algorithm_class=algorithm_class,
            problem_types=problem_types,
            dependencies=dependencies
        )
        
        # Register
        PluginRegistry.register_plugin(plugin)
        
        # Add reference to class
        algorithm_class._plugin = plugin
        
        return algorithm_class
    
    return decorator


# Factory function for creating algorithms
def create_algorithm(name: str, problem, **kwargs) -> Optional[MetaheuristicAlgorithm]:
    """
    Create algorithm instance from registry.
    
    Args:
        name: Algorithm name
        problem: Problem instance
        **kwargs: Algorithm parameters
        
    Returns:
        Algorithm instance or None
    """
    algo_class = PluginRegistry.get_algorithm(name)
    if not algo_class:
        # Try plugin name
        plugin = PluginRegistry.get_plugin(name)
        if plugin:
            algo_class = plugin.get_algorithm_class()
    
    if algo_class:
        return algo_class(problem, **kwargs)
    
    return None


# Integration with existing algorithm loader
class PluginAlgorithmLoader:
    """
    Loader that integrates plugins with existing algorithm loading.
    """
    
    def __init__(self, base_algorithms: Optional[Dict[str, Type[MetaheuristicAlgorithm]]] = None):
        """
        Initialize loader.
        
        Args:
            base_algorithms: Base algorithms to include
        """
        self.base_algorithms = base_algorithms or {}
    
    def get_available_algorithms(self) -> Dict[str, Type[MetaheuristicAlgorithm]]:
        """Get all available algorithms including plugins."""
        algorithms = self.base_algorithms.copy()
        
        # Add plugin algorithms
        algorithms.update(PluginRegistry._algorithms)
        
        return algorithms
    
    def create_algorithm(self, name: str, problem, **kwargs) -> MetaheuristicAlgorithm:
        """
        Create algorithm instance.
        
        Args:
            name: Algorithm name
            problem: Problem instance
            **kwargs: Algorithm parameters
            
        Returns:
            Algorithm instance
            
        Raises:
            ValueError: If algorithm not found
        """
        algorithms = self.get_available_algorithms()
        
        if name not in algorithms:
            raise ValueError(f"Algorithm not found: {name}")
        
        return algorithms[name](problem, **kwargs)
    
    def get_algorithm_info(self, name: str) -> Dict[str, Any]:
        """Get algorithm information."""
        # Check if it's a plugin
        plugin_info = PluginRegistry.get_plugin_info(name)
        if plugin_info:
            return plugin_info
        
        # Base algorithm
        if name in self.base_algorithms:
            algo_class = self.base_algorithms[name]
            return {
                'name': name,
                'class': algo_class.__name__,
                'module': algo_class.__module__,
                'is_plugin': False
            }
        
        raise ValueError(f"Algorithm not found: {name}")


# Global instance for convenience
_global_loader = PluginAlgorithmLoader()


def get_algorithm_loader() -> PluginAlgorithmLoader:
    """Get global algorithm loader."""
    return _global_loader


def update_base_algorithms(algorithms: Dict[str, Type[MetaheuristicAlgorithm]]) -> None:
    """Update base algorithms in global loader."""
    _global_loader.base_algorithms.update(algorithms)