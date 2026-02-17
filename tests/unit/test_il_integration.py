#!/usr/bin/env python3
"""
Test IL Integration with HO
===========================

Tests whether HO with IL performs better than standard HO.
"""

import sys
from pathlib import Path
import pickle

sys.path.append(str(Path(__file__).parent.parent))

import numpy as np

from problems.vrp import VRPProblem
from algorithms.ho import HO
from utils.train_il_simple import SimpleILModel


def create_state_dict(problem, iteration, max_iterations, convergence_curve):
    """Create state dictionary for IL model."""
    progress = iteration / max_iterations
    
    state = {
        'n_customers': problem.dimension - 1,
        'n_depots': 1,
        'avg_demand': np.mean(problem.demands[1:]) if len(problem.demands) > 1 else 10,
        'demand_std': np.std(problem.demands[1:]) if len(problem.demands) > 1 else 5,
        'capacity': problem.capacity,
        'area_span': 100,
        'density': 0.01,
        'iteration': iteration,
        'progress': progress,
        'best_fitness': min(convergence_curve) if convergence_curve else 1000,
        'avg_fitness': np.mean(convergence_curve[-10:]) if convergence_curve else 1000,
        'fitness_std': np.std(convergence_curve[-10:]) if len(convergence_curve) > 10 else 100,
        'convergence_rate': 0,
        'stagnation_counter': 0,
        'population_diversity': 0.5,
        'elite_ratio': 0.1,
        'improvement_rate': 0,
        'dynamic_orders': 0,
        'avg_delay': 0,
        'load_imbalance': 0
    }
    
    # Calculate convergence metrics
    if len(convergence_curve) > 10:
        recent_improvement = convergence_curve[-10] - convergence_curve[-1]
        state['convergence_rate'] = recent_improvement / (convergence_curve[-10] + 1e-10)
        
        # Count stagnation
        for i in range(1, min(20, len(convergence_curve))):
            if convergence_curve[-i] == convergence_curve[-i-1]:
                state['stagnation_counter'] += 1
            else:
                break
    
    return state


def run_ho_with_il(problem, il_model_path, iterations=100, population=30, seed=42):
    """Run HO with IL guidance."""
    # Load IL model
    il_model = SimpleILModel()
    il_model.load(il_model_path)
    
    # Create HO instance
    ho = HO(problem, population_size=population, max_iterations=iterations, seed=seed)
    ho.initialize_population()
    
    # Track performance
    convergence = []
    param_history = []
    
    # Run with IL guidance
    for iteration in range(iterations):
        # Get current state
        state = create_state_dict(problem, iteration, iterations, ho.convergence_curve)
        
        # Get IL-predicted parameters
        alpha, beta, gamma = il_model.predict(state)
        
        # Apply parameters to HO
        ho.alpha_min = ho.alpha_max = alpha
        ho.beta_min = ho.beta_max = beta
        ho.gamma_min = ho.gamma_max = gamma
        
        # Update population
        ho.update_population()
        
        # Track
        convergence.append(ho.best_solution.fitness())
        param_history.append({'iteration': iteration, 'alpha': alpha, 'beta': beta, 'gamma': gamma})
    
    return ho.best_solution, convergence, param_history


def run_ho_standard(problem, iterations=100, population=30, seed=42):
    """Run standard HO without IL."""
    ho = HO(problem, population_size=population, max_iterations=iterations, seed=seed)
    best_sol = ho.execute()
    return best_sol, ho.get_convergence_curve()


def main():
    print("🧪 Testing IL Integration with HO\n")
    
    # Test instance
    instance = "P-n16-k8"
    problem = VRPProblem(f"data/vrp/{instance}.vrp")
    print(f"Instance: {instance}")
    print(f"Customers: {problem.dimension - 1}")
    print(f"Capacity: {problem.capacity}\n")
    
    # Run standard HO
    print("Running standard HO...")
    std_sol, std_conv = run_ho_standard(problem, iterations=100, population=30)
    print(f"  Final fitness: {std_sol.fitness():.2f}")
    print(f"  Convergence at 50%: {std_conv[50]:.2f}")
    
    # Run HO with IL
    print("\nRunning HO with IL...")
    il_model_path = "models/ho_il_model.pkl"
    
    if not Path(il_model_path).exists():
        print("❌ IL model not found. Please train it first.")
        return
    
    il_sol, il_conv, params = run_ho_with_il(problem, il_model_path, iterations=100, population=30)
    print(f"  Final fitness: {il_sol.fitness():.2f}")
    print(f"  Convergence at 50%: {il_conv[50]:.2f}")
    
    # Compare
    print("\n📊 Comparison:")
    improvement = (std_sol.fitness() - il_sol.fitness()) / std_sol.fitness() * 100
    print(f"  Improvement: {improvement:.2f}%")
    
    if il_sol.fitness() < std_sol.fitness():
        print("  ✅ IL-enhanced HO performs better!")
    else:
        print("  ❌ Standard HO performs better")
    
    # Parameter evolution
    print("\n📈 IL Parameter Evolution (samples):")
    for i in [0, 25, 50, 75, 99]:
        p = params[i]
        print(f"  Iter {p['iteration']:3d}: α={p['alpha']:.3f}, β={p['beta']:.3f}, γ={p['gamma']:.3f}")


if __name__ == "__main__":
    main()