#!/usr/bin/env python3
"""
Simple Demo Generation for IL Training — LEGACY / DEPRECATED (NO USAR)

*** ADVERTENCIA DE INTEGRIDAD (saneado 8 Jul 2026) ***
Las "demostraciones expertas" que produce extract_optimal_params() son FÓRMULAS
ANALÍTICAS ESCRITAS A MANO (rampas/triángulos/senos etiquetadas "PSO-inspired"/
"GA-inspired"), NO derivadas de ejecutar PSO ni GA. Por tanto NO constituyen un
experto legítimo de imitation learning (ver
tesis-mia/gestion_proyecto/AUDITORIA_IMPLEMENTACION_IL.md). Este script pertenece
al enfoque HO+IL refutado y NO es usado por el estudio CEC actual. El experto
legítimo (oráculo por hindsight/optimal-control) está en
algorithms/hindsight_oracle.py. Conservado solo por trazabilidad histórica.

(Original) Generates demonstrations without PyTorch dependency.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from problems.vrp import VRPProblem
from algorithms.pso import PSO
from algorithms.ga import GA


def generate_simple_state(problem, iteration, max_iterations, fitness_history):
    """Create a simplified state representation."""
    progress = iteration / max_iterations
    
    state = {
        'n_customers': problem.dimension - 1,
        'n_depots': 1,
        'avg_demand': np.mean(problem.demands[1:]) if len(problem.demands) > 1 else 10,
        'demand_std': np.std(problem.demands[1:]) if len(problem.demands) > 1 else 5,
        'capacity': problem.capacity,
        'area_span': 100,  # Simplified
        'density': 0.01,
        'iteration': iteration,
        'progress': progress,
        'best_fitness': min(fitness_history) if fitness_history else 1000,
        'avg_fitness': np.mean(fitness_history[-10:]) if len(fitness_history) > 0 else 1000,
        'fitness_std': np.std(fitness_history[-10:]) if len(fitness_history) > 10 else 100,
        'convergence_rate': 0,
        'stagnation_counter': 0,
        'population_diversity': 0.5,
        'elite_ratio': 0.1,
        'improvement_rate': 0,
        'dynamic_orders': 0,
        'avg_delay': 0,
        'load_imbalance': 0
    }
    
    # Calculate convergence rate
    if len(fitness_history) > 10:
        recent_improvement = fitness_history[-10] - fitness_history[-1]
        state['convergence_rate'] = recent_improvement / (fitness_history[-10] + 1e-10)
        
        # Count stagnation
        for i in range(1, min(20, len(fitness_history))):
            if fitness_history[-i] == fitness_history[-i-1]:
                state['stagnation_counter'] += 1
            else:
                break
    
    return state


def extract_optimal_params(algorithm_name, iteration, max_iterations):
    """Extract HO parameters based on algorithm behavior."""
    progress = iteration / max_iterations
    
    if algorithm_name == 'pso':
        # PSO-inspired: High exploration early, high exploitation late
        alpha = 0.1 + 0.8 * progress  # 0.1 -> 0.9
        beta = 0.8 - 0.6 * progress   # 0.8 -> 0.2
        gamma = 0.3 + 0.4 * (1 - abs(2*progress - 1))  # Peak at middle
        
    elif algorithm_name == 'ga':
        # GA-inspired: Gradual increase in selection pressure
        alpha = 0.3 + 0.5 * progress  # 0.3 -> 0.8
        beta = 0.5 - 0.2 * progress   # 0.5 -> 0.3
        gamma = 0.4 + 0.3 * np.sin(np.pi * progress)  # Oscillating
        
    else:
        # Default balanced
        alpha = 0.5
        beta = 0.5
        gamma = 0.65
    
    return {
        'alpha': np.clip(alpha, 0.1, 0.9),
        'beta': np.clip(beta, 0.2, 0.8),
        'gamma': np.clip(gamma, 0.3, 1.0)
    }


def generate_demonstrations(instances, num_demos=100, seed=42):
    """Generate demonstrations from PSO and GA."""
    np.random.seed(seed)
    demonstrations = []
    
    algorithms = ['pso', 'ga']
    demos_per_combo = num_demos // (len(instances) * len(algorithms))
    
    for instance_name in instances:
        print(f"\n📍 Processing instance: {instance_name}")
        
        # Load instance
        instance_path = f"data/vrp/{instance_name}.vrp"
        try:
            problem = VRPProblem(instance_path=instance_path)
            print(f"   Customers: {problem.dimension - 1}, Capacity: {problem.capacity}")
        except Exception as e:
            print(f"   ❌ Error loading: {e}")
            continue
        
        for algo_name in algorithms:
            print(f"   🔧 Running {algo_name.upper()}...")
            
            for demo_idx in range(demos_per_combo):
                # Create algorithm
                if algo_name == 'pso':
                    algo = PSO(problem, population_size=20, max_iterations=50, seed=seed + demo_idx)
                else:  # ga
                    algo = GA(problem, population_size=20, max_iterations=50, seed=seed + demo_idx)
                
                # Initialize
                if algo_name == 'pso':
                    algo.population = algo.initialize_population()
                    fitness_history = []
                else:  # ga
                    algo.population = algo.initialize_population()
                    fitness_history = []
                
                # Run and collect data
                for iteration in range(algo.max_iterations):
                    # Get state
                    state = generate_simple_state(problem, iteration, algo.max_iterations, fitness_history)
                    
                    # Get "optimal" parameters
                    params = extract_optimal_params(algo_name, iteration, algo.max_iterations)
                    
                    # Update algorithm
                    algo.update_population()
                    
                    # Track fitness
                    if algo_name == 'pso':
                        current_fitness = algo.gbest_fitness
                    else:  # ga
                        current_fitness = min(ind.fitness() for ind in algo.population)
                    
                    fitness_history.append(current_fitness)
                    
                    # Calculate improvement
                    improvement = fitness_history[-2] - fitness_history[-1] if len(fitness_history) > 1 else 0
                    
                    # Record demonstration
                    demo = {
                        'instance': instance_name,
                        'algorithm': algo_name,
                        'demo_id': demo_idx,
                        'iteration': iteration,
                        **state,
                        'alpha': params['alpha'],
                        'beta': params['beta'],
                        'gamma': params['gamma'],
                        'improvement': improvement,
                        'fitness_after': current_fitness
                    }
                    demonstrations.append(demo)
                
                if demo_idx % 5 == 0:
                    print(f"      Demo {demo_idx}/{demos_per_combo}: Final fitness = {current_fitness:.2f}")
    
    return pd.DataFrame(demonstrations)


def main():
    parser = argparse.ArgumentParser(description='Generate IL demonstrations')
    parser.add_argument('--instances', type=str, default='P-n16-k8,E-n22-k4',
                       help='Comma-separated list of instances')
    parser.add_argument('--num_demos', type=int, default=100,
                       help='Total number of demonstrations')
    parser.add_argument('--output', type=str, default='data/demos/ho_demos.csv',
                       help='Output file path')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    
    args = parser.parse_args()
    
    # Parse instances
    instances = [inst.strip() for inst in args.instances.split(',')]
    
    print("🚀 Generating IL Demonstrations")
    print(f"   Instances: {instances}")
    print(f"   Total demos: {args.num_demos}")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate
    df = generate_demonstrations(instances, args.num_demos, args.seed)
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Demonstrations saved to {output_path}")
    print(f"   Total records: {len(df)}")
    print(f"   Features: {len(df.columns)}")
    
    # Statistics
    print("\n📊 Parameter Statistics:")
    for param in ['alpha', 'beta', 'gamma']:
        print(f"   {param}: mean={df[param].mean():.3f}, std={df[param].std():.3f}")
    
    print(f"\n   Average improvement: {df['improvement'].mean():.3f}")
    print(f"   Best fitness achieved: {df['fitness_after'].min():.2f}")
    print(f"\n✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()