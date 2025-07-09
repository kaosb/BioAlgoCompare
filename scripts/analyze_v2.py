#!/usr/bin/env python3
"""
Script unificado para análisis de algoritmos metaheurísticos - Version 2.
Incluye correcciones estadísticas y nuevos comandos.
"""

import click
import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
from pathlib import Path
import multiprocessing as mp
from math import sqrt
from scipy import stats
import sys

# Añadir el directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("analyze.log"), logging.StreamHandler()],
)
logger = logging.getLogger("analyze")

# Importar utilidades
from utils.benchmarking import BenchmarkResult, OPTIMAL_VALUES, create_benchmark_report
from utils.benchmarking import run_benchmark as benchmark_function
from utils.statistical_analysis import StatisticalAnalysis
from utils.vrp_operators import VRPOperators
from utils.improved.enhanced_benchmarking import (
    run_complete_analysis,
    run_massive_benchmark,
)
from utils.improved.enhanced_statistics import EnhancedStatisticalAnalysis
from utils.improved.advanced_visualization import (
    create_full_visualization_set,
    create_visual_report,
)

# Import v2 statistical analysis
from utils.advanced_statistical_analysis_v2 import run_all_v2
from utils.stats_effects import effect_size_vs_best

# Importar problema
from problems.vrp import VRPProblem

# Importar algoritmos
from algorithms.sho import SHO
from algorithms.apo import APO
from algorithms.egto import EGTO
from algorithms.fsa import FSA
from algorithms.foa import FOA
from algorithms.woa import WOA
from algorithms.hho import HHO
from algorithms.mrfo import MRFO
from algorithms.sma import SMA
from algorithms.gto import GTO
from algorithms.ewa import EWA
from algorithms.aha import AHA
from algorithms.rro import RRO
from algorithms.gvoa import GVOA
from algorithms.smo import SMO
from algorithms.opa import OPA

# Todos los algoritmos disponibles
ALGORITHMS = {
    "hoa": SHO,
    "sho": SHO,
    "apo": APO,
    "egto": EGTO,
    "fgo": FSA,
    "fsa": FSA,
    "foa": FOA,
    "woa": WOA,
    "hho": HHO,
    "mrfo": MRFO,
    "sma": SMA,
    "gto": GTO,
    "ewa": EWA,
    "aha": AHA,
    "rro": RRO,
    "gvoa": GVOA,
    "smo": SMO,
    "opa": OPA,
}


@click.group()
def cli():
    """BioAlgoCompare - Advanced Analysis Tool v2"""
    pass


@cli.command()
@click.option("--algorithm", "-a", type=click.Choice(list(ALGORITHMS.keys()) + ["all"]),
              required=True, help="Algorithm to run")
@click.option("--instance", "-i", required=True, help="VRP instance name (without extension)")
@click.option("--iterations", "-n", default=100, help="Number of iterations")
@click.option("--population", "-pop", default=30, help="Population size")
@click.option("--runs", "-r", default=1, help="Number of independent runs")
@click.option("--seed", "-s", type=int, help="Random seed for reproducibility")
@click.option("--visualize/--no-visualize", default=True, help="Generate visualizations")
@click.option("--save/--no-save", default=True, help="Save results to file")
@click.option("--parallel/--no-parallel", default=False, help="Use parallel execution")
@click.option("--optimize/--no-optimize", default=False, help="Apply local optimization")
def run(algorithm, instance, iterations, population, runs, seed, visualize, save, parallel, optimize):
    """Run algorithm(s) on a VRP instance."""
    # Implementation remains the same as original
    logger.info(f"Running {algorithm} on {instance} for {runs} runs")

    # Load instance
    try:
        problem = VRPProblem(f"data/vrp/{instance}.vrp")
    except Exception as e:
        logger.error(f"Failed to load instance {instance}: {e}")
        return

    # Select algorithms to run
    if algorithm == "all":
        algorithms_to_run = list(ALGORITHMS.keys())
    else:
        algorithms_to_run = [algorithm]

    # Run algorithms
    results = []
    for algo_name in algorithms_to_run:
        algo_class = ALGORITHMS[algo_name]
        logger.info(f"Running {algo_name}...")

        for run_idx in range(runs):
            if seed is not None:
                run_seed = seed + run_idx
                np.random.seed(run_seed)
            else:
                run_seed = None

            # Initialize and run algorithm
            algo = algo_class(
                problem=problem,
                population_size=population,
                iterations=iterations,
                seed=run_seed
            )

            result = algo.execute()

            # Create benchmark result
            br = BenchmarkResult(
                algorithm=algo_name,
                instance=instance,
                best_fitness=result['best_fitness'],
                execution_time=result.get('execution_time', 0),
                convergence=result.get('convergence', []),
                parameters={
                    'population_size': population,
                    'iterations': iterations,
                    'seed': run_seed
                }
            )
            results.append(br)

    # Save results if requested
    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/run_{instance}_{timestamp}.json"
        os.makedirs("results", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump([r.__dict__ for r in results], f, indent=2)

        logger.info(f"Results saved to {output_file}")

    # Generate visualizations if requested
    if visualize and results:
        create_benchmark_report(results, f"results/report_{instance}_{timestamp}")

    return results


@cli.command()
@click.option("--input", "-i", help="Path to existing results file")
@click.option("--run-benchmark/--no-run-benchmark", default=False,
              help="Run new benchmark instead of analyzing existing results")
@click.option("--instances", "-inst", default="P-n16-k8,E-n22-k4",
              help="Comma-separated list of instances for benchmark")
@click.option("--algorithms", "-a", default="all",
              help="Comma-separated list of algorithms or 'all'")
@click.option("--runs", "-r", default=5, help="Number of runs per algorithm")
@click.option("--iterations", "-n", default=100, help="Number of iterations")
@click.option("--population", "-p", default=30, help="Population size")
@click.option("--seed", "-s", type=int, default=42, help="Random seed")
@click.option("--parallel/--no-parallel", default=False, help="Use parallel execution")
@click.option("--optimize/--no-optimize", default=False, help="Apply local optimization")
@click.option("--output-dir", "-o", help="Output directory for results")
def benchmark(input, run_benchmark, instances, algorithms, runs, iterations, population,
              seed, parallel, optimize, output_dir):
    """Run or analyze benchmarks comparing multiple algorithms."""
    if run_benchmark:
        # Parse instances and algorithms
        instance_list = [i.strip() for i in instances.split(",")]
        if algorithms == "all":
            algo_list = list(ALGORITHMS.keys())
        else:
            algo_list = [a.strip() for a in algorithms.split(",")]

        # Set output directory
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"results/benchmark_{timestamp}"

        os.makedirs(output_dir, exist_ok=True)

        # Run benchmark
        logger.info(f"Running benchmark with {len(algo_list)} algorithms on {len(instance_list)} instances")

        results = benchmark_function(
            algorithms={name: ALGORITHMS[name] for name in algo_list},
            instances=instance_list,
            runs=runs,
            iterations=iterations,
            population_size=population,
            seed=seed,
            parallel=parallel,
            apply_optimization=optimize
        )

        # Save results
        output_file = os.path.join(output_dir, "benchmark_results.json")
        with open(output_file, 'w') as f:
            json.dump([r.__dict__ for r in results], f, indent=2)

        # Create report
        create_benchmark_report(results, output_dir)

        logger.info(f"Benchmark completed. Results saved to {output_dir}")

    else:
        # Analyze existing results
        if not input:
            logger.error("Please provide input file with --input or run new benchmark with --run-benchmark")
            return

        # Load results
        with open(input, 'r') as f:
            data = json.load(f)

        results = [BenchmarkResult(**item) for item in data]

        # Create report
        output_dir = output_dir or os.path.dirname(input)
        create_benchmark_report(results, output_dir)

        logger.info(f"Analysis completed. Report saved to {output_dir}")


@cli.command()
@click.option("--runs", "-r", default=1000, help="Number of runs per algorithm")
@click.option("--iterations", "-n", default=100, help="Number of iterations")
@click.option("--population", "-p", default=40, help="Population size")
@click.option("--seed", "-s", type=int, default=42, help="Random seed")
@click.option("--algorithm", "-a", multiple=True, default=["all"],
              help="Algorithms to run (can specify multiple)")
@click.option("--instances", "-i", multiple=True,
              default=["E-n22-k4", "P-n16-k8", "A-n32-k5"],
              help="Instances to evaluate")
@click.option("--parallel/--no-parallel", default=True, help="Use parallel execution")
@click.option("--resume/--no-resume", default=True, help="Resume interrupted benchmark")
@click.option("--output-dir", "-o", help="Output directory")
def massive(runs, iterations, population, seed, algorithm, instances, parallel, resume, output_dir):
    """Run massive benchmark with checkpoint support."""
    # Parse algorithms
    if "all" in algorithm:
        algo_list = list(ALGORITHMS.keys())
    else:
        algo_list = list(algorithm)

    # Set output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/massive_benchmark_{timestamp}"

    # Run massive benchmark
    logger.info(f"Starting massive benchmark: {runs} runs × {len(algo_list)} algorithms × {len(instances)} instances")

    run_massive_benchmark(
        algorithms={name: ALGORITHMS[name] for name in algo_list},
        instances=list(instances),
        n_runs=runs,
        n_iterations=iterations,
        population_size=population,
        base_seed=seed,
        output_dir=output_dir,
        parallel=parallel,
        checkpoint=resume
    )

    logger.info(f"Massive benchmark completed. Results in {output_dir}")


@cli.command()
@click.option("--csv", required=True, help="Path to CSV file with benchmark results")
@click.option("--out", default=None, help="Output directory (default: same as CSV)")
@click.option("--extended-tests/--no-extended-tests", default=False,
              help="Run extended tests (Quade, Friedman aligned)")
@click.option("--save-versions/--no-save-versions", default=True,
              help="Save software versions to JSON")
def stats(csv, out, extended_tests, save_versions):
    """
    Perform advanced statistical analysis with corrected CD and effect sizes.

    Includes:
    - Corrected Friedman test with proper CD calculation
    - Optional Quade test for small k relative to N
    - Vargha-Delaney A12 and Cliff's delta effect sizes
    - Extended report with software versions
    """
    # Check if CSV exists
    if not os.path.exists(csv):
        logger.error(f"CSV file not found: {csv}")
        return

    # Set output directory
    if out is None:
        out = os.path.dirname(csv)

    os.makedirs(out, exist_ok=True)

    logger.info(f"Performing statistical analysis v2 on {csv}")
    logger.info(f"Results will be saved to {out}")

    # Run analysis
    results = run_all_v2(csv, out, extended_tests=extended_tests,
                        save_versions=save_versions)

    if "error" in results:
        logger.error(f"Error in statistical analysis: {results['error']}")
        return

    # Print summary
    print("\n----- Statistical Analysis Summary (v2) -----")
    print(f"Friedman p-value: {results['friedman_p']:.6f}")
    print(f"Critical Distance: {results['critical_distance']:.4f}")

    if extended_tests and 'quade_results' in results:
        print(f"Quade p-value: {results['quade_results']['quade_p']:.6f}")

    if results['friedman_p'] < 0.05:
        print("\nResult: Statistically significant differences detected.")

        # Show rankings
        ranks = results['mean_ranks']
        sorted_algos = sorted(ranks.items(), key=lambda x: x[1])

        print("\nAlgorithm Rankings:")
        for i, (algo, rank) in enumerate(sorted_algos[:5]):
            print(f"{i+1}. {algo} (rank: {rank:.3f})")

        # Show effect sizes vs best
        if 'effect_sizes_vs_best' in results:
            print("\nEffect Sizes vs Best Algorithm:")
            es = results['effect_sizes_vs_best']
            best = es[es['Is_best']]['Algorithm'].iloc[0]
            print(f"Best algorithm: {best}")

            for _, row in es[~es['Is_best']].head(5).iterrows():
                print(f"- {row['Algorithm']}: A12={row['A12']:.3f} ({row['A12_interpretation']})")
    else:
        print("\nResult: No statistically significant differences detected.")

    print(f"\nFull report: {results.get('report', 'N/A')}")
    print(f"CD diagram: {results.get('cd_diagram', 'N/A')}")
    print(f"Effect sizes: {out}/effect_sizes.csv")

    if save_versions:
        print(f"Software versions: {out}/software_versions.json")

    print("-----------------------------------------------")

    return results


@cli.command()
@click.option("--csv", required=True, help="Path to CSV file with benchmark results")
@click.option("--out", default=None, help="Output directory (default: same as CSV)")
@click.option("--vs-best/--pairwise", default=True,
              help="Calculate effect sizes vs best or all pairwise")
def effect_size(csv, out, vs_best):
    """
    Calculate effect sizes (A12 and Cliff's delta) for algorithm comparisons.

    Options:
    - vs-best: Compare all algorithms against the best performing one
    - pairwise: Calculate effect sizes for all algorithm pairs
    """
    # Check if CSV exists
    if not os.path.exists(csv):
        logger.error(f"CSV file not found: {csv}")
        return

    # Set output directory
    if out is None:
        out = os.path.dirname(csv)

    os.makedirs(out, exist_ok=True)

    # Load data
    df = pd.read_csv(csv)

    # Find value column
    value_col = None
    for col in ['Best', 'Best Fitness', 'Value']:
        if col in df.columns:
            value_col = col
            break

    if value_col is None:
        logger.error("No suitable value column found in CSV")
        return

    # Prepare data
    data = df[['Algorithm', 'Instance', value_col]].copy()
    data.columns = ['Algorithm', 'Instance', 'Value']

    if vs_best:
        # Calculate effect sizes vs best
        logger.info("Calculating effect sizes vs best algorithm...")

        es_results = effect_size_vs_best(data)

        # Save results
        output_file = os.path.join(out, "effect_sizes_vs_best.csv")
        es_results.to_csv(output_file, index=False)

        # Print summary
        print("\n----- Effect Sizes vs Best Algorithm -----")
        best = es_results[es_results['Is_best']]['Algorithm'].iloc[0]
        print(f"Best algorithm: {best}\n")

        print("Algorithm       A12    Interpretation    Cliff's δ    Interpretation")
        print("-" * 70)

        for _, row in es_results.iterrows():
            print(f"{row['Algorithm']:<15} {row['A12']:.3f}  {row['A12_interpretation']:<15} "
                  f"{row['Cliff_delta']:+.3f}      {row['Cliff_interpretation']}")

        print(f"\nResults saved to: {output_file}")

    else:
        # Calculate all pairwise effect sizes
        from utils.stats_effects import calculate_pairwise_effect_sizes

        logger.info("Calculating pairwise effect sizes...")

        pairwise = calculate_pairwise_effect_sizes(data)

        # Save results
        a12_file = os.path.join(out, "pairwise_a12.csv")
        cliff_file = os.path.join(out, "pairwise_cliff.csv")

        pairwise['a12'].to_csv(a12_file)
        pairwise['cliff'].to_csv(cliff_file)

        print("\n----- Pairwise Effect Sizes -----")
        print(f"A12 matrix saved to: {a12_file}")
        print(f"Cliff's delta matrix saved to: {cliff_file}")

        # Show sample of results
        algorithms = list(pairwise['a12'].index)[:5]
        print("\nSample A12 values (first 5 algorithms):")
        print(pairwise['a12'].loc[algorithms, algorithms].round(3))


@cli.command()
def analyze_csv(csv_file, output_dir):
    """Analyze results from a CSV file (legacy compatibility)."""
    # This is kept for backward compatibility
    # Redirect to stats command
    ctx = click.get_current_context()
    ctx.invoke(stats, csv=csv_file, out=output_dir)


if __name__ == "__main__":
    cli()
