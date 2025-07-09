"""
Plugin loader utilities for dynamic loading of algorithm plugins.
"""

import ast
import importlib.util
import sys
import logging
from typing import Dict, List, Optional, Type, Any, Tuple
from pathlib import Path
import json
import zipfile
import tempfile
import shutil

from .plugin_base import Plugin, AlgorithmPlugin, PluginMetadata
from algorithms.base_v2 import MetaheuristicAlgorithm


logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Loader for algorithm plugins with various source formats.
    """
    
    @staticmethod
    def load_from_file(file_path: Path) -> Optional[Plugin]:
        """
        Load plugin from Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Plugin instance or None
        """
        if not file_path.exists() or not file_path.suffix == '.py':
            logger.error(f"Invalid plugin file: {file_path}")
            return None
        
        try:
            # Parse file to extract metadata
            metadata = PluginLoader._extract_metadata_from_file(file_path)
            
            # Import module
            spec = importlib.util.spec_from_file_location(
                file_path.stem, 
                file_path
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[file_path.stem] = module
                spec.loader.exec_module(module)
                
                # Find algorithm class
                algorithm_class = PluginLoader._find_algorithm_class(module)
                
                if algorithm_class:
                    # Create plugin
                    plugin = AlgorithmPlugin(
                        name=metadata.get('name', file_path.stem),
                        version=metadata.get('version', '1.0'),
                        author=metadata.get('author', 'Unknown'),
                        description=metadata.get('description', 'No description'),
                        algorithm_class=algorithm_class,
                        problem_types=metadata.get('problem_types', []),
                        dependencies=metadata.get('dependencies', [])
                    )
                    
                    return plugin
                    
        except Exception as e:
            logger.error(f"Failed to load plugin from {file_path}: {e}")
        
        return None
    
    @staticmethod
    def load_from_package(package_dir: Path) -> Optional[Plugin]:
        """
        Load plugin from package directory.
        
        Args:
            package_dir: Path to package directory
            
        Returns:
            Plugin instance or None
        """
        if not package_dir.is_dir():
            logger.error(f"Invalid package directory: {package_dir}")
            return None
        
        # Look for manifest
        manifest_file = package_dir / 'plugin.json'
        if not manifest_file.exists():
            manifest_file = package_dir / 'manifest.json'
        
        if not manifest_file.exists():
            logger.error(f"No manifest found in {package_dir}")
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            # Add package to path
            sys.path.insert(0, str(package_dir.parent))
            
            try:
                # Import package
                module_name = manifest.get('module', package_dir.name)
                module = importlib.import_module(module_name)
                
                # Get plugin class
                plugin_class_name = manifest.get('plugin_class')
                if plugin_class_name:
                    plugin_class = getattr(module, plugin_class_name)
                    if issubclass(plugin_class, Plugin):
                        return plugin_class()
                
                # Try to find algorithm class
                algorithm_class_name = manifest.get('algorithm_class')
                if algorithm_class_name:
                    algorithm_class = getattr(module, algorithm_class_name)
                    if issubclass(algorithm_class, MetaheuristicAlgorithm):
                        return AlgorithmPlugin(
                            name=manifest.get('name', package_dir.name),
                            version=manifest.get('version', '1.0'),
                            author=manifest.get('author', 'Unknown'),
                            description=manifest.get('description', ''),
                            algorithm_class=algorithm_class,
                            problem_types=manifest.get('problem_types', []),
                            dependencies=manifest.get('dependencies', [])
                        )
                        
            finally:
                sys.path.remove(str(package_dir.parent))
                
        except Exception as e:
            logger.error(f"Failed to load plugin from {package_dir}: {e}")
        
        return None
    
    @staticmethod
    def load_from_zip(zip_path: Path) -> Optional[Plugin]:
        """
        Load plugin from zip file.
        
        Args:
            zip_path: Path to zip file
            
        Returns:
            Plugin instance or None
        """
        if not zip_path.exists() or not zip_path.suffix == '.zip':
            logger.error(f"Invalid zip file: {zip_path}")
            return None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract zip
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find plugin in extracted files
                temp_path = Path(temp_dir)
                
                # Look for single Python file
                py_files = list(temp_path.glob('*.py'))
                if len(py_files) == 1:
                    return PluginLoader.load_from_file(py_files[0])
                
                # Look for package
                for item in temp_path.iterdir():
                    if item.is_dir():
                        manifest = item / 'plugin.json'
                        if manifest.exists():
                            return PluginLoader.load_from_package(item)
                
                # Look for manifest in root
                manifest = temp_path / 'plugin.json'
                if manifest.exists():
                    return PluginLoader.load_from_package(temp_path)
                    
            except Exception as e:
                logger.error(f"Failed to load plugin from {zip_path}: {e}")
        
        return None
    
    @staticmethod
    def load_from_url(url: str, cache_dir: Optional[Path] = None) -> Optional[Plugin]:
        """
        Load plugin from URL.
        
        Args:
            url: URL to plugin file
            cache_dir: Optional cache directory
            
        Returns:
            Plugin instance or None
        """
        import urllib.request
        import hashlib
        
        if cache_dir is None:
            cache_dir = Path.home() / '.bioalgocompare' / 'plugin_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Generate cache filename
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_file = cache_dir / f"plugin_{url_hash}"
            
            # Download if not cached
            if not cache_file.exists():
                logger.info(f"Downloading plugin from {url}")
                urllib.request.urlretrieve(url, cache_file)
            
            # Determine file type and load
            if url.endswith('.py'):
                cache_file = cache_file.with_suffix('.py')
                return PluginLoader.load_from_file(cache_file)
            elif url.endswith('.zip'):
                cache_file = cache_file.with_suffix('.zip')
                return PluginLoader.load_from_zip(cache_file)
            else:
                logger.error(f"Unknown plugin format from URL: {url}")
                
        except Exception as e:
            logger.error(f"Failed to load plugin from {url}: {e}")
        
        return None
    
    @staticmethod
    def _extract_metadata_from_file(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from Python file docstring or comments."""
        metadata = {}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Look for module docstring
            if (tree.body and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                
                docstring = tree.body[0].value.value
                
                # Parse metadata from docstring
                for line in docstring.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == 'plugin':
                            # Handle Plugin: prefix format
                            parts = value.split(':', 1)
                            if len(parts) == 2:
                                sub_key = parts[0].strip().lower()
                                sub_value = parts[1].strip()
                                if sub_key in ['name', 'version', 'author', 'description']:
                                    metadata[sub_key] = sub_value
                                elif sub_key == 'problem_types':
                                    metadata[sub_key] = [v.strip() for v in sub_value.split(',')]
                                elif sub_key == 'dependencies':
                                    metadata[sub_key] = [v.strip() for v in sub_value.split(',')]
                        elif key in ['name', 'version', 'author', 'description']:
                            metadata[key] = value
                        elif key == 'problem_types':
                            metadata[key] = [v.strip() for v in value.split(',')]
                        elif key == 'dependencies':
                            metadata[key] = [v.strip() for v in value.split(',')]
            
            # Look for metadata in comments
            for line in content.split('\n'):
                if line.strip().startswith('# Plugin:'):
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        key = parts[1].strip().lower()
                        value = parts[2].strip()
                        metadata[key] = value
                        
        except Exception as e:
            logger.debug(f"Could not extract metadata from {file_path}: {e}")
        
        return metadata
    
    @staticmethod
    def _find_algorithm_class(module) -> Optional[Type[MetaheuristicAlgorithm]]:
        """Find MetaheuristicAlgorithm subclass in module."""
        for name in dir(module):
            obj = getattr(module, name)
            
            if (isinstance(obj, type) and 
                issubclass(obj, MetaheuristicAlgorithm) and 
                obj != MetaheuristicAlgorithm):
                return obj
        
        return None


def discover_plugins(search_paths: List[Path]) -> List[Plugin]:
    """
    Discover plugins in given paths.
    
    Args:
        search_paths: List of paths to search
        
    Returns:
        List of discovered plugins
    """
    plugins = []
    
    for path in search_paths:
        if not path.exists():
            continue
        
        # Search for Python files
        for py_file in path.glob('**/*.py'):
            if py_file.name.startswith('_'):
                continue
                
            plugin = PluginLoader.load_from_file(py_file)
            if plugin:
                plugins.append(plugin)
        
        # Search for packages
        for item in path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                manifest = item / 'plugin.json'
                if manifest.exists():
                    plugin = PluginLoader.load_from_package(item)
                    if plugin:
                        plugins.append(plugin)
        
        # Search for zip files
        for zip_file in path.glob('*.zip'):
            plugin = PluginLoader.load_from_zip(zip_file)
            if plugin:
                plugins.append(plugin)
    
    return plugins


def validate_plugin(plugin: Plugin) -> Tuple[bool, List[str]]:
    """
    Validate a plugin.
    
    Args:
        plugin: Plugin to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        # Check metadata
        metadata = plugin.get_metadata()
        
        if not metadata.name:
            issues.append("Plugin name is required")
        if not metadata.version:
            issues.append("Plugin version is required")
        if not metadata.algorithm_class:
            issues.append("Algorithm class name is required")
        
        # Check algorithm class
        try:
            algo_class = plugin.get_algorithm_class()
            if not issubclass(algo_class, MetaheuristicAlgorithm):
                issues.append("Algorithm class must inherit from MetaheuristicAlgorithm")
        except Exception as e:
            issues.append(f"Cannot get algorithm class: {e}")
        
        # Check environment
        if not plugin.validate_environment():
            issues.append("Environment validation failed")
        
        # Check parameter schema
        try:
            schema = plugin.get_parameter_schema()
            if not isinstance(schema, dict):
                issues.append("Parameter schema must be a dictionary")
        except Exception as e:
            issues.append(f"Cannot get parameter schema: {e}")
            
    except Exception as e:
        issues.append(f"Plugin validation error: {e}")
    
    return len(issues) == 0, issues


def create_plugin_template(output_dir: Path, 
                         plugin_name: str,
                         algorithm_name: str) -> None:
    """
    Create a plugin template.
    
    Args:
        output_dir: Output directory
        plugin_name: Plugin name
        algorithm_name: Algorithm class name
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create plugin file
    plugin_file = output_dir / f"{plugin_name.lower()}_plugin.py"
    
    template = f'''"""
Plugin: name: {plugin_name}
Plugin: version: 1.0
Plugin: author: Your Name
Plugin: description: {algorithm_name} implementation
Plugin: problem_types: optimization, vrp
Plugin: dependencies: numpy
"""

import numpy as np
from algorithms.base_v2 import MetaheuristicAlgorithm, Individual
from typing import Optional


class {algorithm_name}Individual(Individual):
    """Individual for {algorithm_name}."""
    
    def __init__(self, problem, position=None):
        super().__init__(problem, position)
        # Add algorithm-specific attributes here
    
    def move(self, *args, **kwargs):
        """Implement movement logic."""
        # Implement movement behavior
        pass


class {algorithm_name}(MetaheuristicAlgorithm):
    """
    {algorithm_name} implementation.
    
    This algorithm implements...
    """
    
    def __init__(self, problem, population_size=30, max_iterations=100,
                 param1=0.5, param2=0.8, seed=None):
        """
        Initialize {algorithm_name}.
        
        Args:
            problem: Problem instance
            population_size: Size of population
            max_iterations: Maximum iterations
            param1: Description of param1
            param2: Description of param2
            seed: Random seed
        """
        super().__init__(problem, population_size, max_iterations, seed)
        
        self.param1 = param1
        self.param2 = param2
        
        # Initialize population
        self.initialize_population()
    
    def _create_individual(self):
        """Create a new individual."""
        return {algorithm_name}Individual(self.problem)
    
    def initialize_population(self):
        """Initialize the population."""
        self.population = []
        for _ in range(self.population_size):
            individual = self._create_individual()
            self.population.append(individual)
    
    def iterate(self):
        """Perform one iteration of the algorithm."""
        # Implement algorithm logic here
        
        # Update best solution
        for individual in self.population:
            if self.is_better(individual, self.best_solution):
                self.best_solution = individual.copy()
        
        self.current_iteration += 1


# Optional: Create plugin instance for automatic discovery
# from plugins.plugin_base import AlgorithmPlugin
# 
# plugin = AlgorithmPlugin(
#     name="{plugin_name}",
#     version="1.0",
#     author="Your Name",
#     description="{algorithm_name} implementation",
#     algorithm_class={algorithm_name},
#     problem_types=["optimization", "vrp"]
# )
'''
    
    with open(plugin_file, 'w') as f:
        f.write(template)
    
    # Create manifest for package-style plugin
    manifest = {
        "name": plugin_name,
        "version": "1.0",
        "author": "Your Name",
        "description": f"{algorithm_name} implementation",
        "algorithm_class": algorithm_name,
        "problem_types": ["optimization", "vrp"],
        "dependencies": ["numpy"],
        "entry_point": f"{plugin_name.lower()}_plugin.py"
    }
    
    manifest_file = output_dir / "plugin.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create README
    readme_file = output_dir / "README.md"
    readme_content = f"""# {plugin_name} Plugin

## Description

{algorithm_name} implementation for BioAlgoCompare.

## Installation

1. Copy this directory to the `external_plugins/installed/` directory
2. The plugin will be automatically discovered

Or use the plugin manager:

```python
from plugins import PluginManager

manager = PluginManager()
manager.install_plugin("path/to/this/directory")
```

## Usage

```python
from plugins import PluginManager
from problems.vrp import VRPProblem

# Load plugin
manager = PluginManager()
plugin = manager.get_plugin("{plugin_name}")

# Create algorithm
problem = VRPProblem("instance.vrp")
algorithm = plugin.create_algorithm(
    problem,
    population_size=50,
    max_iterations=100,
    param1=0.5,
    param2=0.8
)

# Run algorithm
algorithm.run()
print(f"Best solution: {{algorithm.best_solution.fitness()}}")
```

## Parameters

- `population_size`: Size of the population (default: 30)
- `max_iterations`: Maximum number of iterations (default: 100)
- `param1`: Description of param1 (default: 0.5)
- `param2`: Description of param2 (default: 0.8)

## Requirements

- numpy
- BioAlgoCompare framework

## License

Your license here
"""
    
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    logger.info(f"Plugin template created in {output_dir}")