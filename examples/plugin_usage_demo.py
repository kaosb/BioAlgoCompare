"""
Demonstration of plugin system usage.
"""

import numpy as np
from pathlib import Path
import json
import time

from plugins import PluginManager, PluginRegistry
from plugins.plugin_loader import PluginLoader, create_plugin_template
from problems.vrp_v2 import VRPProblemV2 as VRPProblem


def demo_basic_plugin_usage():
    """Demonstrate basic plugin loading and usage."""
    print("=== Basic Plugin Usage Demo ===\n")
    
    # Create plugin manager
    manager = PluginManager()
    
    # Discover and load plugins
    print("Discovering plugins...")
    loaded_plugins = manager.discover_plugins()
    print(f"Loaded {len(loaded_plugins)} plugins: {loaded_plugins}\n")
    
    # List available plugins
    print("Available plugins:")
    for plugin_info in manager.list_plugins():
        metadata = plugin_info['metadata']
        print(f"  - {metadata['name']} v{metadata['version']} by {metadata['author']}")
        print(f"    {metadata['description']}")
        print(f"    Problem types: {', '.join(metadata.get('problem_types', []))}\n")
    
    # Create a VRP problem
    print("Creating VRP problem...")
    problem = VRPProblem("data/vrp/E-n22-k4.vrp")
    
    # Get compatible plugins
    compatible = manager.get_compatible_plugins(problem)
    print(f"Plugins compatible with VRP: {compatible}\n")
    
    # Create and run algorithm from plugin
    if compatible:
        plugin_name = compatible[0]
        print(f"Creating algorithm from plugin: {plugin_name}")
        
        algorithm = manager.create_algorithm(
            plugin_name,
            problem,
            population_size=30,
            max_iterations=50
        )
        
        print(f"Running {algorithm.__class__.__name__}...")
        start_time = time.time()
        
        # Run algorithm
        algorithm.run()
        
        elapsed = time.time() - start_time
        print(f"Completed in {elapsed:.2f} seconds")
        print(f"Best fitness: {algorithm.best_solution.fitness():.2f}\n")


def demo_plugin_creation():
    """Demonstrate creating a new plugin."""
    print("=== Plugin Creation Demo ===\n")
    
    # Create plugin template
    output_dir = Path("examples/custom_plugin")
    plugin_name = "CustomGA"
    algorithm_name = "CustomGeneticAlgorithm"
    
    print(f"Creating plugin template: {plugin_name}")
    create_plugin_template(output_dir, plugin_name, algorithm_name)
    
    print(f"Plugin template created in: {output_dir}")
    print("Files created:")
    for file in output_dir.iterdir():
        print(f"  - {file.name}")
    print()
    
    # Show plugin structure
    if (output_dir / "plugin.json").exists():
        with open(output_dir / "plugin.json") as f:
            manifest = json.load(f)
        print("Plugin manifest:")
        print(json.dumps(manifest, indent=2))
    print()


def demo_plugin_from_file():
    """Demonstrate loading plugin from file."""
    print("=== Loading Plugin from File ===\n")
    
    # Path to builtin plugin
    plugin_file = Path("plugins/builtin/hybrid_ga_plugin.py")
    
    if plugin_file.exists():
        print(f"Loading plugin from: {plugin_file}")
        plugin = PluginLoader.load_from_file(plugin_file)
        
        if plugin:
            metadata = plugin.get_metadata()
            print(f"Successfully loaded: {metadata.name}")
            print(f"Algorithm class: {metadata.algorithm_class}")
            
            # Get parameter schema
            schema = plugin.get_parameter_schema()
            print("\nParameter schema:")
            for param, info in schema.get('properties', {}).items():
                print(f"  - {param}: {info.get('type', 'any')}")
                if 'default' in info:
                    print(f"    default: {info['default']}")
        else:
            print("Failed to load plugin")
    else:
        print(f"Plugin file not found: {plugin_file}")
    print()


def demo_plugin_registry():
    """Demonstrate using the plugin registry."""
    print("=== Plugin Registry Demo ===\n")
    
    # Create and register a custom plugin
    from algorithms.factories import AlgorithmFactory
    
    # Get a standard algorithm
    algo_info = AlgorithmFactory.get_algorithm("GeneticAlgorithm")
    GeneticAlgorithm = algo_info["class"]
    from plugins.plugin_base import AlgorithmPlugin
    
    custom_plugin = AlgorithmPlugin(
        name="RegistryDemoGA",
        version="1.0",
        author="Demo Author",
        description="Genetic Algorithm registered via registry",
        algorithm_class=GeneticAlgorithm,
        problem_types=["vrp", "optimization"],
        parameter_schema={
            "type": "object",
            "properties": {
                "crossover_rate": {"type": "number", "default": 0.8},
                "mutation_rate": {"type": "number", "default": 0.1}
            }
        }
    )
    
    # Register plugin
    print("Registering custom plugin...")
    success = PluginRegistry.register_plugin(custom_plugin)
    print(f"Registration {'successful' if success else 'failed'}")
    
    # List registered algorithms
    print("\nRegistered algorithms:")
    for algo_name in PluginRegistry.list_algorithms():
        print(f"  - {algo_name}")
    
    # Create algorithm using registry
    print("\nCreating algorithm from registry...")
    problem = VRPProblem("data/vrp/E-n22-k4.vrp")
    
    from plugins.plugin_registry import create_algorithm
    algorithm = create_algorithm("GeneticAlgorithm", problem, population_size=20)
    
    if algorithm:
        print(f"Created: {algorithm.__class__.__name__}")
        print(f"Population size: {algorithm.population_size}")
    
    # Unregister
    print("\nUnregistering plugin...")
    PluginRegistry.unregister_plugin("RegistryDemoGA")
    print()


def demo_advanced_plugin_features():
    """Demonstrate advanced plugin features."""
    print("=== Advanced Plugin Features ===\n")
    
    manager = PluginManager()
    
    # Export plugin information
    print("Exporting plugin information...")
    manager.export_plugin_info("examples/plugin_report.json")
    print("Plugin information exported to: examples/plugin_report.json")
    
    # Load and display report
    with open("examples/plugin_report.json") as f:
        report = json.load(f)
    
    print("\nPlugin Statistics:")
    stats = report.get('statistics', {})
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # Check individual plugin info
    if report['plugins']:
        plugin_info = report['plugins'][0]
        print(f"\nDetailed info for: {plugin_info['metadata']['name']}")
        print(f"  Status: {plugin_info.get('status', 'unknown')}")
        print(f"  Environment valid: {plugin_info.get('environment_valid', False)}")
        if 'custom_operators' in plugin_info:
            print(f"  Custom operators: {', '.join(plugin_info['custom_operators'])}")
    print()


def demo_plugin_with_vrp():
    """Demonstrate plugin solving VRP problem."""
    print("=== Plugin VRP Solution Demo ===\n")
    
    # Load VRP problem
    problem = VRPProblem("data/vrp/E-n22-k4.vrp")
    print(f"Loaded VRP instance: {problem.name}")
    print(f"Customers: {problem.dimension - 1}")
    print(f"Vehicles: {problem.n_vehicles}")
    print(f"Capacity: {problem.capacity}")
    
    # Try different plugin algorithms
    manager = PluginManager()
    
    # Look for VRP-compatible plugins
    compatible_plugins = []
    for plugin_info in manager.list_plugins():
        metadata = plugin_info['metadata']
        problem_types = metadata.get('problem_types', [])
        if 'vrp' in problem_types:
            compatible_plugins.append(metadata['name'])
    
    print(f"\nVRP-compatible plugins: {compatible_plugins}")
    
    # Run each compatible plugin
    results = []
    for plugin_name in compatible_plugins[:2]:  # Limit to first 2 for demo
        print(f"\n--- Running {plugin_name} ---")
        
        try:
            algorithm = manager.create_algorithm(
                plugin_name,
                problem,
                population_size=20,
                max_iterations=30,
                seed=42
            )
            
            start = time.time()
            algorithm.run()
            elapsed = time.time() - start
            
            results.append({
                'plugin': plugin_name,
                'fitness': algorithm.best_solution.fitness(),
                'time': elapsed,
                'iterations': algorithm.current_iteration
            })
            
            print(f"Best fitness: {algorithm.best_solution.fitness():.2f}")
            print(f"Time: {elapsed:.2f}s")
            
            # Get algorithm-specific stats if available
            if hasattr(algorithm, 'get_stats'):
                stats = algorithm.get_stats()
                print("Algorithm stats:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            print(f"Error running {plugin_name}: {e}")
    
    # Compare results
    if results:
        print("\n=== Results Comparison ===")
        print(f"{'Plugin':<20} {'Fitness':<12} {'Time (s)':<10} {'Iterations':<10}")
        print("-" * 52)
        for result in results:
            print(f"{result['plugin']:<20} {result['fitness']:<12.2f} "
                  f"{result['time']:<10.2f} {result['iterations']:<10}")


def main():
    """Run all demonstrations."""
    demos = [
        demo_basic_plugin_usage,
        demo_plugin_creation,
        demo_plugin_from_file,
        demo_plugin_registry,
        demo_advanced_plugin_features,
        demo_plugin_with_vrp
    ]
    
    for demo in demos:
        try:
            demo()
            print("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"Error in {demo.__name__}: {e}")
            print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()