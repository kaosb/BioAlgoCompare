#!/usr/bin/env python3
"""
Simple example of using the plugin system.
"""

from pathlib import Path
from plugins import PluginManager
from plugins.plugin_loader import create_plugin_template
from problems.vrp_v2 import VRPProblemV2


def main():
    """Run simple plugin example."""
    
    # Step 1: Create a plugin manager
    print("=== Creating Plugin Manager ===")
    manager = PluginManager()
    
    # Step 2: List available plugins
    print("\n=== Available Plugins ===")
    plugins = manager.list_plugins()
    if plugins:
        for plugin_info in plugins:
            metadata = plugin_info['metadata']
            print(f"- {metadata['name']} v{metadata['version']}: {metadata['description']}")
    else:
        print("No plugins loaded yet.")
    
    # Step 3: Create a simple plugin template
    print("\n=== Creating Plugin Template ===")
    template_dir = Path("examples/my_custom_plugin")
    if not template_dir.exists():
        create_plugin_template(
            output_dir=template_dir,
            plugin_name="MyCustomAlgorithm",
            algorithm_name="MyCustomOptimizer"
        )
        print(f"Plugin template created in: {template_dir}")
    
    # Step 4: Load and use a plugin
    print("\n=== Using a Plugin ===")
    
    # Load a VRP problem
    problem = VRPProblemV2("data/vrp/E-n22-k4.vrp")
    print(f"Loaded problem: {problem.name}")
    print(f"  Customers: {problem.dimension - 1}")
    print(f"  Vehicles: {problem.n_vehicles}")
    
    # Check if we have the HybridGA plugin
    hybrid_ga = manager.get_plugin("HybridGA")
    if hybrid_ga:
        print("\nUsing HybridGA plugin...")
        
        # Create algorithm from plugin
        algorithm = manager.create_algorithm(
            "HybridGA",
            problem,
            population_size=20,
            max_iterations=50,
            seed=42
        )
        
        print(f"Created algorithm: {algorithm.__class__.__name__}")
        print("Running algorithm...")
        
        # Run for a few iterations
        for i in range(10):
            algorithm.iterate()
            if i % 5 == 0:
                print(f"  Iteration {i}: Best fitness = {algorithm.best_solution.fitness():.2f}")
        
        print(f"\nFinal best fitness: {algorithm.best_solution.fitness():.2f}")
    else:
        print("\nHybridGA plugin not found. Creating a simple plugin...")
        
        # Create inline plugin code
        simple_plugin = Path("examples/simple_demo_plugin.py")
        plugin_code = '''"""
Plugin: name: SimpleDemo
Plugin: version: 1.0
Plugin: author: Demo
Plugin: description: Simple demonstration algorithm
Plugin: problem_types: vrp, optimization
"""

import numpy as np
from algorithms.base_v2 import MetaheuristicAlgorithm, Individual

class SimpleDemoIndividual(Individual):
    def __init__(self, problem, position=None):
        super().__init__(problem, position)
    
    def move(self):
        # Simple random perturbation
        self.position += np.random.normal(0, 0.05, size=self.position.shape)
        self.position = np.clip(self.position, 0, 1)
        self._fitness = None

class SimpleDemoAlgorithm(MetaheuristicAlgorithm):
    def __init__(self, problem, population_size=10, max_iterations=100, seed=None):
        super().__init__(problem, population_size, max_iterations, seed)
        self.initialize_population()
    
    def _create_individual(self):
        return SimpleDemoIndividual(self.problem)
    
    def initialize_population(self):
        self.population = [self._create_individual() for _ in range(self.population_size)]
    
    def iterate(self):
        # Simple evolution: move all individuals
        for individual in self.population:
            individual.move()
        
        # Update best
        for individual in self.population:
            if self.is_better(individual, self.best_solution):
                self.best_solution = individual.copy()
        
        self.current_iteration += 1
    
    def _create_move_context(self):
        return {"iteration": self.current_iteration}
'''
        
        simple_plugin.write_text(plugin_code)
        
        # Install the plugin
        success = manager.install_plugin(simple_plugin)
        if success:
            print("Plugin installed successfully!")
            
            # Use the plugin
            algorithm = manager.create_algorithm(
                "SimpleDemo",
                problem,
                population_size=10,
                max_iterations=20,
                seed=42
            )
            
            print(f"Running {algorithm.__class__.__name__}...")
            for i in range(10):
                algorithm.iterate()
                print(f"  Iteration {i}: Best = {algorithm.best_solution.fitness():.2f}")
    
    print("\n=== Complete ===")


if __name__ == "__main__":
    main()