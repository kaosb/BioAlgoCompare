#!/usr/bin/env python3
"""
Generate Demonstrations for Imitation Learning
=============================================

Generates expert demonstrations by evaluating many (α, β, γ) parameter
combinations at different optimization stages, recording which combinations
produce the best fitness improvement.

Method:
    1. For each VRP instance, run HO to reach different progress stages
    2. At each stage, snapshot the optimization state
    3. Try N_CANDIDATES random (α, β, γ) combinations from that state
    4. Run EVAL_ITERS more iterations with each combination
    5. Record the combination that gave the best fitness as the expert demo

This avoids meta-optimization overhead (no GA/PSO over HO) and produces
demonstrations that reflect the actual multiplicative IL integration.

Usage:
    python utils/generate_demos.py --instances P-n16-k8,E-n22-k4 --num 200
    python utils/generate_demos.py --instances all --num 500 --candidates 50
"""

import argparse
import hashlib
import os
import sys
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms.ho import HO, Hippopotamus  # noqa: E402
from problems.vrp import VRPProblem  # noqa: E402
from utils.imitation_learning import create_state_from_problem  # noqa: E402

# Parameter bounds (same as SimpleILModel)
PARAM_BOUNDS = {
    "alpha": (0.1, 0.9),
    "beta": (0.2, 0.8),
    "gamma": (0.3, 1.0),
}

# Available real instances
AVAILABLE_INSTANCES = [
    "P-n16-k8", "E-n22-k4", "A-n32-k5", "E-n51-k5",
]

PROGRESS_STAGES = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def _clone_ho_state(ho):
    """Deep-copy HO population, RNG state, and optimizer state for rollback."""
    state = {
        'positions': [ind.position.copy() for ind in ho.population],
        'fitnesses': [ind._fitness for ind in ho.population],
        'dominant_pos': ho.dominant.position.copy(),
        'dominant_fit': ho.dominant._fitness,
        'curve': ho.convergence_curve.copy(),
        'rng_state': ho.rng.bit_generator.state,  # Preserve RNG for reproducibility
    }
    return state


def _restore_ho_state(ho, state):
    """Restore HO to a previously saved state including RNG."""
    for i, ind in enumerate(ho.population):
        ind.position = state['positions'][i].copy()
        ind._fitness = state['fitnesses'][i]
    ho.dominant.position = state['dominant_pos'].copy()
    ho.dominant._fitness = state['dominant_fit']
    ho.convergence_curve = state['curve'].copy()
    ho.rng.bit_generator.state = state['rng_state']  # Restore RNG state


def _evaluate_params(ho, alpha, beta, gamma, eval_iters):
    """Run HO for eval_iters with fixed (α, β, γ), return final best fitness.

    Replaces _get_il_params entirely with a lambda that returns fixed params,
    bypassing the use_il check. This ensures the candidate params are actually
    applied during update_population().
    """
    # Save original method (bound to instance)
    original_get = ho._get_il_params

    # Replace method entirely — do NOT touch use_il, as the lambda bypasses it
    fixed = (float(alpha), float(beta), float(gamma))
    ho._get_il_params = lambda iteration: fixed

    for _ in range(eval_iters):
        ho.update_population()

    best_fitness = ho.dominant.fitness()

    # Restore original method
    ho._get_il_params = original_get

    return best_fitness


def generate_demonstrations(
    instances: List[str],
    num_demos: int,
    n_candidates: int = 30,
    eval_iters: int = 10,
    ho_pop: int = 20,
    ho_max_iter: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate expert demonstrations via random parameter search.

    Args:
        instances: List of VRP instance names
        num_demos: Total demonstrations to generate
        n_candidates: Random (α,β,γ) combinations to try per state
        eval_iters: Iterations to run with each candidate
        ho_pop: HO population size for state generation
        ho_max_iter: HO max iterations for state generation
        seed: Random seed

    Returns:
        DataFrame with columns: state features + instance, algorithm, alpha, beta, gamma, fitness
    """
    rng = np.random.default_rng(seed)
    demonstrations = []
    demos_per_instance = max(1, num_demos // len(instances))

    for inst_name in instances:
        instance_path = f"data/vrp/{inst_name}.vrp"
        if not os.path.exists(instance_path):
            print(f"  Skipping {inst_name}: file not found")
            continue

        problem = VRPProblem(instance_path)
        print(f"\n[{inst_name}] {demos_per_instance} demos, {problem.dimension} customers")

        demo_count = 0
        for demo_idx in range(demos_per_instance):
            stage = rng.choice(PROGRESS_STAGES)
            target_iter = max(1, int(stage * ho_max_iter))
            # Deterministic seed: hashlib is consistent across Python versions
            inst_hash = int(hashlib.md5(inst_name.encode()).hexdigest()[:8], 16)
            demo_seed = seed + demo_idx * 7 + inst_hash % 10000

            # Run HO to reach the target stage
            ho = HO(problem, population_size=ho_pop, max_iterations=ho_max_iter,
                     seed=demo_seed)
            ho.initialize_population()
            for _ in range(target_iter):
                ho.update_population()

            # Snapshot state for IL features
            state = create_state_from_problem(problem, ho, target_iter, ho_max_iter)
            # Add improvement_rate (expected by trained model)
            if 'improvement_rate' not in state:
                state['improvement_rate'] = state.get('convergence_rate', 0)

            baseline_fitness = ho.dominant.fitness()
            saved_state = _clone_ho_state(ho)

            # Try n_candidates random parameter combinations
            best_alpha, best_beta, best_gamma = 0.5, 0.5, 0.65
            best_fitness = float('inf')

            for _ in range(n_candidates):
                alpha = rng.uniform(*PARAM_BOUNDS["alpha"])
                beta = rng.uniform(*PARAM_BOUNDS["beta"])
                gamma = rng.uniform(*PARAM_BOUNDS["gamma"])

                _restore_ho_state(ho, saved_state)
                fitness = _evaluate_params(ho, alpha, beta, gamma, eval_iters)

                if fitness < best_fitness:
                    best_fitness = fitness
                    best_alpha, best_beta, best_gamma = alpha, beta, gamma

            # Record demonstration
            demo = state.copy()
            demo["instance"] = inst_name
            demo["algorithm"] = "random_search"
            demo["demo_id"] = demo_idx
            demo["alpha"] = best_alpha
            demo["beta"] = best_beta
            demo["gamma"] = best_gamma
            demo["fitness_after"] = best_fitness
            demo["improvement"] = baseline_fitness - best_fitness
            demonstrations.append(demo)
            demo_count += 1

            if (demo_count % 10) == 0:
                print(f"  {demo_count}/{demos_per_instance} "
                      f"stage={stage:.1f} "
                      f"α={best_alpha:.2f} β={best_beta:.2f} γ={best_gamma:.2f} "
                      f"improve={demo['improvement']:.2f}")

    return pd.DataFrame(demonstrations)


def main():
    parser = argparse.ArgumentParser(
        description="Generate IL demonstrations for HO parameter adaptation"
    )
    parser.add_argument(
        "--instances", type=str, default="all",
        help="VRP instances (comma-separated, or 'all')",
    )
    parser.add_argument("--num", type=int, default=200, help="Total demonstrations")
    parser.add_argument("--candidates", type=int, default=30,
                        help="Random candidates per state")
    parser.add_argument("--eval-iters", type=int, default=10,
                        help="Iterations per candidate evaluation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")

    args = parser.parse_args()

    if args.instances == "all":
        instances = AVAILABLE_INSTANCES
    else:
        instances = [i.strip() for i in args.instances.split(",")]

    output_path = args.output or os.path.join(
        "data", "demos",
        f"ho_demos_real_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Generating {args.num} demonstrations...")
    print(f"Instances: {instances}")
    print(f"Candidates per state: {args.candidates}")
    print(f"Eval iterations: {args.eval_iters}")
    print(f"Seed: {args.seed}")

    start = datetime.now()
    demos_df = generate_demonstrations(
        instances, args.num,
        n_candidates=args.candidates,
        eval_iters=args.eval_iters,
        seed=args.seed,
    )
    elapsed = (datetime.now() - start).total_seconds()

    demos_df.to_csv(output_path, index=False)

    print(f"\nGenerated {len(demos_df)} demonstrations in {elapsed:.1f}s")
    print(f"Saved to: {output_path}")
    print(f"\nOptimal parameter statistics:")
    for p in ['alpha', 'beta', 'gamma']:
        print(f"  {p}: {demos_df[p].mean():.3f} +/- {demos_df[p].std():.3f} "
              f"[{demos_df[p].min():.3f}, {demos_df[p].max():.3f}]")
    print(f"\nAvg improvement: {demos_df['improvement'].mean():.4f}")


if __name__ == "__main__":
    main()
