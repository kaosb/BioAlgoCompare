#!/usr/bin/env python3
"""Run QC-DVRP experiments for the IWINAC 2026 paper.

Executes 6 metaheuristic algorithms on the Quick Commerce Dynamic VRP
simulation with rolling horizon re-optimization.

Algorithms (as per paper Section 4):
    - HO: Hippopotamus Optimization (alpha=0.5, beta=0.2, no IL)
    - PSO: Particle Swarm Optimization
    - GA: Genetic Algorithm
    - SSA: Salp Swarm Algorithm
    - GTO: Gorilla Troops Optimizer
    - GWO: Grey Wolf Optimizer

Usage:
    python scripts/run_dvrp_experiments.py --test     # Quick verification (1 run)
    python scripts/run_dvrp_experiments.py --full     # Full experiment (30 runs)
    python scripts/run_dvrp_experiments.py --analyze results/dvrp_*/results.json
"""
import click
import json
import os
import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from problems.qc_dvrp import QCDVRPSimulator
from utils.algorithm_factory import create_algorithm, get_algorithm_class
from utils.benchmarking import DVRPBenchmarkResult

# Paper configuration (Section 4)
ALGORITHMS = {
    "HO": {
        "class": "ho",
        "params": {"alpha_fixed": 0.5, "beta_fixed": 0.2, "use_il": False},
    },
    "PSO": {"class": "pso", "params": {}},
    "GA": {"class": "ga", "params": {}},
    "SSA": {"class": "ssa", "params": {}},
    "GTO": {"class": "gto", "params": {}},
    "GWO": {"class": "gwo", "params": {}},
}

# Simulation parameters (Section 4)
SIM_CONFIG = {
    "zone_size": 10.0,
    "n_dark_stores": 3,
    "n_vehicles": 25,
    "vehicle_capacity": 50,
    "poisson_lambda": 5.0,
    "time_window_min": 15.0,
    "time_window_max": 45.0,
    "rolling_horizon_window": 300.0,
    "simulation_horizon": 240.0,
    "service_time": 5.0,
    "avg_speed": 40.0,
    "omega_weights": (0.4, 0.4, 0.2),
    "max_fes": 50000,
    "population_size": 100,
}

POPULATION = 100
MAX_FES = 50000
N_RUNS_FULL = 30


def run_experiment(algo_name, algo_config, n_runs, seeds, sim_config):
    """Run DVRP experiment for a single algorithm.

    Args:
        algo_name: Display name of the algorithm
        algo_config: Dict with 'class' and 'params' keys
        n_runs: Number of independent runs
        seeds: List of random seeds
        sim_config: Simulation configuration dict

    Returns:
        DVRPBenchmarkResult with all runs
    """
    algo_class = get_algorithm_class(algo_config["class"])
    algo_params = algo_config["params"]
    result = DVRPBenchmarkResult(algo_name, n_runs)

    for run in range(n_runs):
        seed = seeds[run]
        print(f"  Run {run + 1}/{n_runs} (seed={seed})...", end=" ", flush=True)

        sim = QCDVRPSimulator(seed=seed, **sim_config)
        run_result = sim.run_simulation(algo_class, algo_params)

        result.add_run(run_result)

        print(
            f"ADT={run_result['adt']:.2f}min, "
            f"DSR={run_result['dsr']:.1f}%, "
            f"WBI={run_result['wbi']:.2f}, "
            f"Time={run_result['execution_time']:.1f}s"
        )

    return result


def save_results(results, output_dir):
    """Save experiment results to JSON and CSV.

    Args:
        results: Dict of {algo_name: DVRPBenchmarkResult}
        output_dir: Output directory path
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save full results as JSON
    json_data = {name: r.to_dict() for name, r in results.items()}
    json_path = os.path.join(output_dir, "results.json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    # Save summary CSV
    rows = []
    for name, r in results.items():
        metrics = r.compute_metrics()
        rows.append({
            "Algorithm": name,
            "ADT_mean": metrics["adt"]["mean"],
            "ADT_std": metrics["adt"]["std"],
            "DSR_mean": metrics["dsr"]["mean"],
            "DSR_std": metrics["dsr"]["std"],
            "WBI_mean": metrics["wbi"]["mean"],
            "WBI_std": metrics["wbi"]["std"],
            "Fitness_mean": metrics["fitness"]["mean"],
            "Fitness_std": metrics["fitness"]["std"],
            "Time_mean": metrics["execution_time"]["mean"],
            "Time_std": metrics["execution_time"]["std"],
            "Runs": metrics["runs"],
        })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(output_dir, "results.csv")
    df.to_csv(csv_path, index=False)

    # Save detailed per-run CSV
    detail_rows = []
    for name, r in results.items():
        for i in range(len(r.adt_values)):
            detail_rows.append({
                "Algorithm": name,
                "Run": i + 1,
                "ADT": r.adt_values[i],
                "DSR": r.dsr_values[i],
                "WBI": r.wbi_values[i],
                "Fitness": r.fitness_values[i],
                "Time": r.execution_times[i],
            })

    df_detail = pd.DataFrame(detail_rows)
    detail_path = os.path.join(output_dir, "results_detailed.csv")
    df_detail.to_csv(detail_path, index=False)

    print("\nResults saved to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print(f"  Detailed: {detail_path}")

    return json_path, csv_path


@click.command()
@click.option("--test", is_flag=True, help="Quick test (1 run per algorithm)")
@click.option("--full", is_flag=True, help="Full experiment (30 runs per algorithm)")
@click.option("--runs", "-r", default=None, type=int, help="Custom number of runs")
@click.option("--algorithms", "-a", default=None, help="Comma-separated algorithm names")
@click.option("--output-dir", "-o", default=None, help="Output directory")
@click.option("--analyze", type=click.Path(exists=True), help="Analyze existing results JSON")
def main(test, full, runs, algorithms, output_dir, analyze):
    """Run QC-DVRP experiments for IWINAC 2026 paper."""
    if analyze:
        _analyze_results(analyze)
        return

    # Determine number of runs
    if test:
        n_runs = 1
    elif full:
        n_runs = N_RUNS_FULL
    elif runs:
        n_runs = runs
    else:
        print("Specify --test, --full, or --runs N")
        return

    # Determine algorithms
    if algorithms:
        algo_names = [a.strip().upper() for a in algorithms.split(",")]
        algo_dict = {name: ALGORITHMS[name] for name in algo_names if name in ALGORITHMS}
    else:
        algo_dict = ALGORITHMS

    # Determine output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/dvrp_{timestamp}"

    # Generate seeds
    seeds = list(range(42, 42 + n_runs))

    print("=" * 60)
    print("QC-DVRP Experiment - IWINAC 2026")
    print("=" * 60)
    print(f"Algorithms: {', '.join(algo_dict.keys())}")
    print(f"Runs per algorithm: {n_runs}")
    print(f"Population: {SIM_CONFIG['population_size']}")
    print(f"Max FES: {SIM_CONFIG['max_fes']}")
    print(f"Simulation: {SIM_CONFIG['simulation_horizon']}min, "
          f"RH={SIM_CONFIG['rolling_horizon_window']}s")
    print(f"Output: {output_dir}")
    print("=" * 60)

    # Run experiments
    all_results = {}
    total_start = time.time()

    for algo_name, algo_config in algo_dict.items():
        print(f"\n--- {algo_name} ---")
        result = run_experiment(algo_name, algo_config, n_runs, seeds, SIM_CONFIG)
        all_results[algo_name] = result

        # Print summary
        metrics = result.compute_metrics()
        print(f"  Summary: ADT={metrics['adt']['mean']:.2f} +/- {metrics['adt']['std']:.2f}, "
              f"DSR={metrics['dsr']['mean']:.1f} +/- {metrics['dsr']['std']:.1f}%, "
              f"WBI={metrics['wbi']['mean']:.2f} +/- {metrics['wbi']['std']:.2f}")

    total_time = time.time() - total_start
    print(f"\nTotal experiment time: {total_time:.1f}s")

    # Save results
    save_results(all_results, output_dir)

    # Save simulation config
    config_path = os.path.join(output_dir, "config.json")
    with open(config_path, "w") as f:
        config = SIM_CONFIG.copy()
        config["omega_weights"] = list(config["omega_weights"])
        config["n_runs"] = n_runs
        config["seeds"] = seeds
        config["algorithms"] = list(algo_dict.keys())
        json.dump(config, f, indent=2)


def _analyze_results(json_path):
    """Analyze and display existing results."""
    with open(json_path) as f:
        data = json.load(f)

    print("\n" + "=" * 70)
    print("QC-DVRP Results Analysis")
    print("=" * 70)

    # Reconstruct DVRPBenchmarkResult objects
    results = {}
    for name, d in data.items():
        results[name] = DVRPBenchmarkResult.from_dict(d)

    # Print comparison table
    print(f"\n{'Algorithm':<10} {'ADT (min)':<18} {'DSR (%)':<18} {'WBI':<18} {'Fitness':<18}")
    print("-" * 82)

    for name, r in results.items():
        m = r.compute_metrics()
        print(
            f"{name:<10} "
            f"{m['adt']['mean']:>7.2f} +/- {m['adt']['std']:<6.2f} "
            f"{m['dsr']['mean']:>7.1f} +/- {m['dsr']['std']:<6.1f} "
            f"{m['wbi']['mean']:>7.2f} +/- {m['wbi']['std']:<6.2f} "
            f"{m['fitness']['mean']:>7.1f} +/- {m['fitness']['std']:<6.1f}"
        )

    # Rank algorithms per metric
    print("\nRankings:")
    for metric_name, key, reverse in [
        ("ADT (lower=better)", "adt", False),
        ("DSR (higher=better)", "dsr", True),
        ("WBI (lower=better)", "wbi", False),
    ]:
        ranked = sorted(
            results.items(),
            key=lambda x: x[1].compute_metrics()[key]["mean"],
            reverse=reverse,
        )
        ranking = ", ".join(f"{i+1}.{name}" for i, (name, _) in enumerate(ranked))
        print(f"  {metric_name}: {ranking}")


if __name__ == "__main__":
    main()
