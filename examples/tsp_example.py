#!/usr/bin/env python3
"""
Example of using TSP problem with bio-inspired algorithms.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from problems import TSPProblem, ContinuousAdapter
from algorithms.woa_v2 import WOAV2
from algorithms.gto_v2 import GTOV2
from algorithms.sma_v2 import SMAV2


def main():
    """Run TSP example."""
    
    # Create a simple TSP instance with 15 cities
    print("Creating TSP instance with 15 random cities...")
    tsp = TSPProblem.generate_random(n_cities=15, seed=42)
    
    # Get initial solution using nearest neighbor heuristic
    print("\nGenerating initial solution with Nearest Neighbor heuristic:")
    nn_tour, nn_distance = tsp.nearest_neighbor_heuristic(start_city=0)
    print(f"Nearest Neighbor tour distance: {nn_distance:.2f}")
    
    # Improve with 2-opt
    print("\nImproving with 2-opt local search:")
    improved_tour, improved_distance = tsp.two_opt_improvement(nn_tour)
    print(f"2-opt improved distance: {improved_distance:.2f}")
    print(f"Improvement: {nn_distance - improved_distance:.2f} ({(nn_distance - improved_distance) / nn_distance * 100:.1f}%)")
    
    # Now solve with bio-inspired algorithms
    print("\n" + "="*60)
    print("Solving with bio-inspired algorithms...")
    print("="*60)
    
    # Adapt TSP for continuous algorithms
    adapted_tsp = ContinuousAdapter(tsp)
    
    # Test different algorithms
    algorithms = [
        ("WOA (Whale Optimization)", WOAV2),
        ("GTO (Gorilla Troops)", GTOV2),
        ("SMA (Slime Mould)", SMAV2)
    ]
    
    results = []
    
    for name, AlgoClass in algorithms:
        print(f"\n{name}:")
        print("-" * len(name))
        
        # Create and run algorithm
        algo = AlgoClass(
            adapted_tsp,
            population_size=30,
            max_iterations=50,
            seed=42
        )
        
        best_solution = algo.execute()
        
        # Convert continuous solution to tour
        best_tour = tsp.encode_continuous(best_solution.position)
        best_distance = tsp.evaluate(best_tour)
        
        print(f"Best distance found: {best_distance:.2f}")
        print(f"Improvement over NN: {nn_distance - best_distance:.2f}")
        print(f"Number of evaluations: {tsp.evaluations}")
        
        results.append((name, best_distance, best_tour))
        
        # Reset evaluation counter
        tsp.reset_evaluations()
    
    # Compare results
    print("\n" + "="*60)
    print("Summary of Results:")
    print("="*60)
    print(f"{'Algorithm':<30} {'Distance':<12} {'vs NN':<12} {'vs 2-opt':<12}")
    print("-" * 66)
    print(f"{'Nearest Neighbor':<30} {nn_distance:<12.2f} {0:<12.2f} {nn_distance - improved_distance:<12.2f}")
    print(f"{'2-opt Local Search':<30} {improved_distance:<12.2f} {nn_distance - improved_distance:<12.2f} {0:<12.2f}")
    
    for name, distance, _ in sorted(results, key=lambda x: x[1]):
        nn_diff = nn_distance - distance
        opt_diff = improved_distance - distance
        print(f"{name:<30} {distance:<12.2f} {nn_diff:<12.2f} {opt_diff:<12.2f}")
    
    # Show best tour found
    best_result = min(results, key=lambda x: x[1])
    print(f"\nBest solution found by: {best_result[0]}")
    print(f"Tour: {best_result[2]}")
    
    # Optionally visualize if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        print("\nGenerating visualization...")
        tsp.plot_tour(best_result[2], title=f"Best TSP Tour - {best_result[0]} - Distance: {best_result[1]:.2f}")
    except ImportError:
        print("\nMatplotlib not available for visualization")


if __name__ == "__main__":
    main()