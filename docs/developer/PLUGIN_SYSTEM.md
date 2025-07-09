# Plugin System Documentation

## Overview

The BioAlgoCompare plugin system allows you to extend the framework with custom algorithms without modifying the core codebase. This enables easy integration of external algorithms, custom implementations, and experimental approaches.

## Architecture

### Core Components

1. **Plugin Base Classes** (`plugins/plugin_base.py`)
   - `Plugin`: Abstract base class for all plugins
   - `AlgorithmPlugin`: Standard implementation for algorithm plugins
   - `PluginInterface`: Communication interface between plugins and the system
   - `PluginMetadata`: Structured metadata for plugins

2. **Plugin Manager** (`plugins/plugin_manager.py`)
   - Central management of plugins
   - Auto-discovery and loading
   - Installation/uninstallation
   - Configuration management
   - Caching support

3. **Plugin Loader** (`plugins/plugin_loader.py`)
   - Dynamic loading from various sources
   - Support for files, packages, and zip archives
   - URL-based loading with caching
   - Metadata extraction

4. **Plugin Registry** (`plugins/plugin_registry.py`)
   - Global registration system
   - Algorithm factory functions
   - Hook system for events
   - Integration with existing algorithm loader

## Quick Start

### Using Existing Plugins

```python
from plugins import PluginManager
from problems.vrp import VRPProblem

# Create manager and discover plugins
manager = PluginManager()
plugins = manager.discover_plugins()

# List available plugins
for plugin_info in manager.list_plugins():
    print(f"{plugin_info['metadata']['name']}")

# Create algorithm from plugin
problem = VRPProblem("instance.vrp")
algorithm = manager.create_algorithm(
    "HybridGA",  # Plugin name
    problem,
    population_size=50,
    max_iterations=100
)

# Run algorithm
algorithm.run()
print(f"Best: {algorithm.best_solution.fitness()}")
```

### Creating a Simple Plugin

1. **Create a Python file** with plugin metadata in docstring:

```python
"""
Plugin: name: MyAlgorithm
Plugin: version: 1.0
Plugin: author: Your Name
Plugin: description: My custom algorithm
Plugin: problem_types: vrp, optimization
Plugin: dependencies: numpy
"""

import numpy as np
from algorithms.base import MetaheuristicAlgorithm, Individual

class MyAlgorithmIndividual(Individual):
    def move(self):
        # Implement movement logic
        self.position += np.random.normal(0, 0.1, size=self.position.shape)
        self.position = np.clip(self.position, 0, 1)

class MyAlgorithm(MetaheuristicAlgorithm):
    def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        self.initialize_population()
    
    def _create_individual(self):
        return MyAlgorithmIndividual(self.problem)
    
    def initialize_population(self):
        self.population = [self._create_individual() for _ in range(self.population_size)]
    
    def iterate(self):
        # Implement algorithm logic
        for individual in self.population:
            individual.move()
        
        # Update best solution
        for individual in self.population:
            if self.is_better(individual, self.best_solution):
                self.best_solution = individual.copy()
        
        self.current_iteration += 1
```

2. **Install the plugin**:

```bash
# Using CLI
bioalgo-plugins install my_algorithm.py

# Or programmatically
manager = PluginManager()
manager.install_plugin("my_algorithm.py")
```

## Advanced Plugin Development

### Package-Based Plugin

For more complex plugins, use a package structure:

```
my_plugin/
├── __init__.py
├── plugin.json
├── algorithm.py
├── operators.py
└── README.md
```

**plugin.json**:
```json
{
    "name": "AdvancedPlugin",
    "version": "2.0",
    "author": "Your Name",
    "description": "Advanced algorithm implementation",
    "algorithm_class": "AdvancedAlgorithm",
    "problem_types": ["vrp", "tsp"],
    "dependencies": ["numpy", "scipy"],
    "entry_point": "algorithm.py"
}
```

### Using the Plugin Base Classes

```python
from plugins.plugin_base import AlgorithmPlugin
from my_algorithm import MyAlgorithm

# Create plugin programmatically
plugin = AlgorithmPlugin(
    name="MyPlugin",
    version="1.0",
    author="Me",
    description="My algorithm plugin",
    algorithm_class=MyAlgorithm,
    problem_types=["vrp"],
    parameter_schema={
        "type": "object",
        "properties": {
            "custom_param": {
                "type": "number",
                "default": 0.5,
                "description": "Custom parameter"
            }
        }
    }
)

# Register with the system
from plugins import PluginRegistry
PluginRegistry.register_plugin(plugin)
```

### Custom Operators and Extensions

Plugins can provide custom operators:

```python
class AdvancedPlugin(Plugin):
    def get_custom_operators(self):
        return {
            'crossover': self.custom_crossover,
            'mutation': self.custom_mutation,
            'local_search': self.custom_local_search
        }
    
    def custom_crossover(self, parent1, parent2):
        # Implement custom crossover
        pass
    
    def custom_mutation(self, individual):
        # Implement custom mutation
        pass
```

## CLI Tool Usage

The `bioalgo-plugins` command provides plugin management:

### List plugins
```bash
bioalgo-plugins list
```

### Install a plugin
```bash
bioalgo-plugins install path/to/plugin.py
bioalgo-plugins install path/to/plugin_package/
bioalgo-plugins install plugin.zip
```

### Get plugin information
```bash
bioalgo-plugins info PluginName
```

### Validate before installing
```bash
bioalgo-plugins validate path/to/plugin.py
```

### Create plugin template
```bash
bioalgo-plugins create --plugin-name MyPlugin --algorithm-name MyAlgorithm
```

### Export plugin report
```bash
bioalgo-plugins export plugins_report.json
```

## Plugin Development Guidelines

### 1. Metadata Requirements

Every plugin must provide:
- `name`: Unique identifier
- `version`: Semantic version (e.g., "1.0.0")
- `author`: Author name
- `description`: Brief description
- `algorithm_class`: Name of the algorithm class

Optional metadata:
- `problem_types`: List of compatible problem types
- `dependencies`: Required Python packages
- `parameters`: Default parameter values

### 2. Algorithm Requirements

Your algorithm class must:
- Inherit from `MetaheuristicAlgorithm`
- Implement `_create_individual()`
- Implement `initialize_population()`
- Implement `iterate()`
- Call `super().__init__()` in constructor

### 3. Individual Requirements

If using custom individuals:
- Inherit from `Individual`
- Implement required methods (e.g., `move()`)
- Handle problem-specific constraints

### 4. Best Practices

1. **Error Handling**: Use proper exception handling
2. **Documentation**: Document parameters and behavior
3. **Testing**: Test with various problem instances
4. **Performance**: Profile and optimize critical sections
5. **Compatibility**: Test with different Python versions

## Integration Examples

### With Benchmarking System

```python
from plugins import PluginManager
from utils.benchmarking import run_benchmark

# Get algorithms including plugins
manager = PluginManager()
algorithms = manager.get_algorithms()

# Add to benchmark
results = run_benchmark(
    algorithms=algorithms,
    instances=["E-n22-k4.vrp"],
    runs=30
)
```

### With Experiment Tracking

```python
from plugins import PluginManager
from utils.experiment_tracker import ExperimentTracker

manager = PluginManager()
tracker = ExperimentTracker()

# Track plugin algorithm
algorithm = manager.create_algorithm("MyPlugin", problem)
tracker.start_run(algorithm="MyPlugin", parameters={...})
algorithm.run()
tracker.end_run(results=algorithm.get_results())
```

### Dynamic Algorithm Selection

```python
from plugins import PluginManager
from problems.vrp import VRPProblem

manager = PluginManager()
problem = VRPProblem("instance.vrp")

# Get compatible plugins
compatible = manager.get_compatible_plugins(problem)

# Select based on problem characteristics
if problem.dimension > 100:
    # Use plugin optimized for large instances
    algorithm = manager.create_algorithm("LargeScalePlugin", problem)
else:
    # Use standard plugin
    algorithm = manager.create_algorithm("StandardPlugin", problem)
```

## Troubleshooting

### Common Issues

1. **Plugin not loading**
   - Check metadata format in docstring
   - Verify all imports are available
   - Use `validate` command to check issues

2. **Import errors**
   - Ensure dependencies are installed
   - Check Python path configuration
   - Verify relative imports

3. **Algorithm not working**
   - Implement all required methods
   - Check problem compatibility
   - Verify parameter types

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('plugins').setLevel(logging.DEBUG)

manager = PluginManager()
# Debug messages will show loading process
```

## Security Considerations

1. **Validate plugins** before installation
2. **Review code** from untrusted sources
3. **Use virtual environments** for isolation
4. **Limit file system access** in production

## Future Enhancements

Planned features:
- Plugin marketplace/repository
- Automatic dependency installation
- Performance profiling integration
- GUI plugin manager
- Plugin versioning and updates
- Distributed plugin execution