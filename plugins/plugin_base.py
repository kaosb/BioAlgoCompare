"""
Base classes and interfaces for the plugin system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path

from algorithms.base_v2 import MetaheuristicAlgorithm, Individual
from problems.base import AbstractProblem as Problem


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    author: str
    description: str
    algorithm_class: str
    problem_types: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'algorithm_class': self.algorithm_class,
            'problem_types': self.problem_types,
            'dependencies': self.dependencies,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat(),
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary."""
        data = data.copy()
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class Plugin(ABC):
    """
    Abstract base class for algorithm plugins.
    """
    
    def __init__(self):
        """Initialize plugin."""
        self._metadata: Optional[PluginMetadata] = None
        self._loaded = False
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Get plugin metadata.
        
        Returns:
            Plugin metadata
        """
        pass
    
    @abstractmethod
    def get_algorithm_class(self) -> Type[MetaheuristicAlgorithm]:
        """
        Get the algorithm class provided by this plugin.
        
        Returns:
            Algorithm class
        """
        pass
    
    @abstractmethod
    def validate_environment(self) -> bool:
        """
        Validate that the plugin can run in the current environment.
        
        Returns:
            True if environment is valid
        """
        pass
    
    def get_individual_class(self) -> Optional[Type[Individual]]:
        """
        Get custom individual class if provided.
        
        Returns:
            Individual class or None
        """
        return None
    
    def get_custom_operators(self) -> Dict[str, Callable]:
        """
        Get custom operators provided by the plugin.
        
        Returns:
            Dictionary of operator name to function
        """
        return {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for algorithm parameters.
        
        Returns:
            Parameter schema
        """
        return {
            'type': 'object',
            'properties': {},
            'required': []
        }
    
    def setup(self) -> None:
        """
        Perform any necessary setup operations.
        Called once when the plugin is loaded.
        """
        pass
    
    def teardown(self) -> None:
        """
        Perform cleanup operations.
        Called when the plugin is unloaded.
        """
        pass
    
    def is_compatible_with_problem(self, problem: Problem) -> bool:
        """
        Check if the plugin is compatible with a given problem.
        
        Args:
            problem: Problem instance
            
        Returns:
            True if compatible
        """
        metadata = self.get_metadata()
        if not metadata.problem_types:
            return True  # Compatible with all if not specified
        
        # Check problem type
        problem_type = getattr(problem, 'problem_type', 'unknown')
        return problem_type in metadata.problem_types


class AlgorithmPlugin(Plugin):
    """
    Standard plugin implementation for algorithm integration.
    """
    
    def __init__(self, 
                 name: str,
                 version: str,
                 author: str,
                 description: str,
                 algorithm_class: Type[MetaheuristicAlgorithm],
                 problem_types: Optional[List[str]] = None,
                 dependencies: Optional[List[str]] = None,
                 parameter_schema: Optional[Dict[str, Any]] = None):
        """
        Initialize algorithm plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
            author: Plugin author
            description: Plugin description
            algorithm_class: Algorithm class to provide
            problem_types: Compatible problem types
            dependencies: Required dependencies
            parameter_schema: JSON schema for parameters
        """
        super().__init__()
        
        self._algorithm_class = algorithm_class
        self._parameter_schema = parameter_schema or {}
        
        self._metadata = PluginMetadata(
            name=name,
            version=version,
            author=author,
            description=description,
            algorithm_class=algorithm_class.__name__,
            problem_types=problem_types or [],
            dependencies=dependencies or [],
            parameters=self._extract_default_parameters()
        )
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self._metadata
    
    def get_algorithm_class(self) -> Type[MetaheuristicAlgorithm]:
        """Get algorithm class."""
        return self._algorithm_class
    
    def validate_environment(self) -> bool:
        """Validate environment."""
        # Check dependencies
        for dep in self._metadata.dependencies:
            try:
                __import__(dep)
            except ImportError:
                return False
        return True
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema."""
        if self._parameter_schema:
            return self._parameter_schema
        
        # Generate basic schema from algorithm __init__
        return self._generate_parameter_schema()
    
    def _extract_default_parameters(self) -> Dict[str, Any]:
        """Extract default parameters from algorithm class."""
        import inspect
        
        try:
            sig = inspect.signature(self._algorithm_class.__init__)
            params = {}
            
            for name, param in sig.parameters.items():
                if name in ['self', 'problem']:
                    continue
                    
                if param.default != inspect.Parameter.empty:
                    params[name] = param.default
                    
            return params
        except:
            return {}
    
    def _generate_parameter_schema(self) -> Dict[str, Any]:
        """Generate parameter schema from algorithm signature."""
        import inspect
        
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        try:
            sig = inspect.signature(self._algorithm_class.__init__)
            
            for name, param in sig.parameters.items():
                if name in ['self', 'problem']:
                    continue
                
                # Infer type from annotation or default value
                param_schema = {'title': name}
                
                if param.annotation != inspect.Parameter.empty:
                    # Use annotation to determine type
                    if param.annotation == int:
                        param_schema['type'] = 'integer'
                    elif param.annotation == float:
                        param_schema['type'] = 'number'
                    elif param.annotation == str:
                        param_schema['type'] = 'string'
                    elif param.annotation == bool:
                        param_schema['type'] = 'boolean'
                elif param.default != inspect.Parameter.empty:
                    # Infer from default value
                    if isinstance(param.default, int):
                        param_schema['type'] = 'integer'
                    elif isinstance(param.default, float):
                        param_schema['type'] = 'number'
                    elif isinstance(param.default, str):
                        param_schema['type'] = 'string'
                    elif isinstance(param.default, bool):
                        param_schema['type'] = 'boolean'
                
                if param.default != inspect.Parameter.empty:
                    param_schema['default'] = param.default
                else:
                    schema['required'].append(name)
                
                schema['properties'][name] = param_schema
                
        except:
            pass
        
        return schema


class PluginInterface:
    """
    Interface for plugin communication with the main system.
    """
    
    def __init__(self, plugin: Plugin):
        """
        Initialize plugin interface.
        
        Args:
            plugin: Plugin instance
        """
        self.plugin = plugin
        self.metadata = plugin.get_metadata()
        self._algorithm_cache: Optional[Type[MetaheuristicAlgorithm]] = None
    
    def create_algorithm(self, problem: Problem, **kwargs) -> MetaheuristicAlgorithm:
        """
        Create algorithm instance.
        
        Args:
            problem: Problem instance
            **kwargs: Algorithm parameters
            
        Returns:
            Algorithm instance
        """
        if not self.plugin.is_compatible_with_problem(problem):
            raise ValueError(f"Plugin {self.metadata.name} is not compatible with problem type")
        
        algorithm_class = self.get_algorithm_class()
        
        # Merge with default parameters
        params = self.metadata.parameters.copy()
        params.update(kwargs)
        
        # Create instance
        return algorithm_class(problem, **params)
    
    def get_algorithm_class(self) -> Type[MetaheuristicAlgorithm]:
        """Get cached algorithm class."""
        if self._algorithm_cache is None:
            self._algorithm_cache = self.plugin.get_algorithm_class()
        return self._algorithm_cache
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate algorithm parameters against schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if valid
        """
        schema = self.plugin.get_parameter_schema()
        
        # Basic validation
        if 'required' in schema:
            for req in schema['required']:
                if req not in parameters:
                    return False
        
        # Type validation
        if 'properties' in schema:
            for name, value in parameters.items():
                if name in schema['properties']:
                    prop_schema = schema['properties'][name]
                    if 'type' in prop_schema:
                        expected_type = prop_schema['type']
                        if expected_type == 'integer' and not isinstance(value, int):
                            return False
                        elif expected_type == 'number' and not isinstance(value, (int, float)):
                            return False
                        elif expected_type == 'string' and not isinstance(value, str):
                            return False
                        elif expected_type == 'boolean' and not isinstance(value, bool):
                            return False
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            'metadata': self.metadata.to_dict(),
            'parameter_schema': self.plugin.get_parameter_schema(),
            'custom_operators': list(self.plugin.get_custom_operators().keys()),
            'environment_valid': self.plugin.validate_environment()
        }