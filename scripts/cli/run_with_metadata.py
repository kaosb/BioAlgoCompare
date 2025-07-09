#!/usr/bin/env python3
"""
Enhanced run script with complete metadata capture for scientific reproducibility.

This script extends the standard run functionality to automatically capture:
- System information (platform, CPU, memory)
- Git information (commit, branch, dirty state)
- Execution information (start/end time, resource usage)
- Dependencies (all installed packages with versions)
"""

import click
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
from multiprocessing import Pool
from functools import partial
from tqdm import tqdm
from pathlib import Path
import pickle
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import enhanced algorithms with metadata capture
from utils.result_metadata_integration import (
    wrap_algorithm_with_metadata,
    ensure_metadata_in_result
)

# Import v2 algorithms
from algorithms.sho_v2 import SHOV2
from algorithms.apo_v2 import APOV2
from algorithms.egto_v2 import EGTOV2
from algorithms.fsa_v2 import FSAV2
from algorithms.foa_v2 import FOAV2
from algorithms.woa_v2 import WOAV2
from algorithms.hho_v2 import HHOV2
from algorithms.mrfo_v2 import MRFOV2
from algorithms.sma_v2 import SMAV2
from algorithms.gto_v2 import GTOV2
from algorithms.ewa_v2 import EWAV2
from algorithms.aha_v2 import AHAV2
from algorithms.rro_v2 import RROV2
from algorithms.gvoa_v2 import GVOAV2
from algorithms.smo_v2 import SMOV2
from algorithms.opa_v2 import OPAV2
from algorithms.hoa_v2 import HOAV2
from algorithms.fgo_v2 import FGOV2

# Algorithm mapping
ALGORITHMS_V2 = {
    "sho": SHOV2,
    "apo": APOV2,
    "egto": EGTOV2,
    "fsa": FSAV2,
    "foa": FOAV2,
    "woa": WOAV2,
    "hho": HHOV2,
    "mrfo": MRFOV2,
    "sma": SMAV2,
    "gto": GTOV2,
    "ewa": EWAV2,
    "aha": AHAV2,
    "rro": RROV2,
    "gvoa": GVOAV2,
    "smo": SMOV2,
    "opa": OPAV2,
    "hoa": HOAV2,
    "fgo": FGOV2,
}

# Import problem and utilities
from problems.vrp_v2 import VRPProblemV2
from utils.visualization import plot_vrp_solution, plot_convergence, compare_algorithms
from utils.result_schema_v2 import StandardResultV2


def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = ["results", "results/metadata", "checkpoints", "plots", "experiments"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def run_algorithm_with_metadata(algo_name, problem, population, iterations, run_seed, run_id, 
                               capture_metadata=True, monitor_resources=True):
    """
    Run an algorithm with complete metadata capture.
    
    Args:
        algo_name: Algorithm name
        problem: Problem instance
        population: Population size
        iterations: Number of iterations
        run_seed: Seed for this run
        run_id: Run ID
        capture_metadata: Whether to capture system metadata
        monitor_resources: Whether to monitor resource usage
    
    Returns:
        Dictionary with results and metadata
    """
    try:
        # Get algorithm class
        if algo_name not in ALGORITHMS_V2:
            click.echo(f"❌ Algorithm {algo_name} not found", err=True)
            return None
        
        # Wrap algorithm with metadata capture
        AlgoClass = ALGORITHMS_V2[algo_name]
        MetadataAlgoClass = wrap_algorithm_with_metadata(
            AlgoClass,
            capture_metadata=capture_metadata,
            monitor_resources=monitor_resources
        )
        
        # Initialize and run algorithm
        algo = MetadataAlgoClass(
            problem,
            population_size=population,
            max_iterations=iterations,
            seed=run_seed,
        )
        
        start_time = time.time()
        best_solution = algo.execute()
        execution_time = time.time() - start_time
        
        # Get complete result with metadata
        complete_result = algo.get_complete_result()
        
        # Convert to dictionary for compatibility
        result_dict = complete_result.to_dict()
        
        # Add run-specific information
        result_dict['run_id'] = run_id
        result_dict['algorithm'] = algo_name
        result_dict['instance'] = problem.name
        
        return result_dict
        
    except Exception as e:
        click.echo(f"❌ Error in {algo_name} run {run_id}: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        return None


def save_results_with_metadata(results, algorithm, instance, output_dir, timestamp):
    """Save results with complete metadata."""
    # Create metadata directory
    metadata_dir = Path(output_dir) / 'metadata'
    metadata_dir.mkdir(exist_ok=True)
    
    # Save individual results
    filename = f"{algorithm}_{instance}_{timestamp}_metadata.json"
    filepath = metadata_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    click.echo(f"💾 Results saved with metadata: {filepath}")
    
    # Create summary report
    summary_file = metadata_dir / f"{algorithm}_{instance}_{timestamp}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Algorithm: {algorithm}\n")
        f.write(f"Instance: {instance}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total runs: {len(results)}\n")
        
        if results:
            # Extract fitness values
            fitness_values = []
            for r in results:
                if r and 'runs' in r and len(r['runs']) > 0:
                    fitness_values.append(r['runs'][0]['best_fitness'])
            
            if fitness_values:
                f.write(f"\nFitness Statistics:\n")
                f.write(f"  Best: {min(fitness_values):.2f}\n")
                f.write(f"  Mean: {np.mean(fitness_values):.2f}\n")
                f.write(f"  Std: {np.std(fitness_values):.2f}\n")
                f.write(f"  Median: {np.median(fitness_values):.2f}\n")
            
            # System info from first result
            if 'system_info' in results[0]:
                f.write(f"\nSystem Information:\n")
                sys_info = results[0]['system_info']
                f.write(f"  Platform: {sys_info.get('platform', 'N/A')}\n")
                f.write(f"  CPU: {sys_info.get('processor', 'N/A')}\n")
                f.write(f"  Memory: {sys_info.get('memory_total_gb', 0):.1f} GB\n")
            
            # Git info if available
            if 'git_info' in results[0] and results[0]['git_info']:
                f.write(f"\nGit Information:\n")
                git_info = results[0]['git_info']
                f.write(f"  Branch: {git_info.get('branch', 'N/A')}\n")
                f.write(f"  Commit: {git_info.get('commit_hash', 'N/A')[:8]}\n")
                f.write(f"  Dirty: {git_info.get('is_dirty', False)}\n")
    
    click.echo(f"📊 Summary saved: {summary_file}")


@click.command()
@click.option('--algorithm', '-a', type=click.Choice(list(ALGORITHMS_V2.keys())), 
              required=True, help='Algorithm to run')
@click.option('--instance', '-i', type=str, required=True, 
              help='VRP instance to solve')
@click.option('--population', '-p', default=30, type=int, 
              help='Population size')
@click.option('--iterations', '-n', default=100, type=int, 
              help='Number of iterations')
@click.option('--runs', '-r', default=30, type=int, 
              help='Number of independent runs')
@click.option('--seed', '-s', type=int, help='Initial seed')
@click.option('--parallel/--no-parallel', default=True, 
              help='Run in parallel')
@click.option('--workers', '-w', type=int, 
              help='Number of parallel workers')
@click.option('--capture-metadata/--no-capture-metadata', default=True,
              help='Capture system metadata')
@click.option('--monitor-resources/--no-monitor-resources', default=True,
              help='Monitor resource usage')
@click.option('--output-dir', '-o', type=str, default='results',
              help='Directory to save results')
@click.option('--plot/--no-plot', default=False,
              help='Generate result plots')
def main(algorithm, instance, population, iterations, runs, seed, parallel, workers,
         capture_metadata, monitor_resources, output_dir, plot):
    """
    Run algorithms with complete metadata capture for scientific reproducibility.
    
    Examples:
    
    # Run with full metadata capture
    python run_with_metadata.py -a hoa -i A-n32-k5.vrp -r 30
    
    # Run without resource monitoring (faster)
    python run_with_metadata.py -a egto -i P-n16-k8.vrp --no-monitor-resources
    
    # Run with custom output directory
    python run_with_metadata.py -a foa -i E-n22-k4.vrp -o results/experiment1
    """
    
    # Create directories
    ensure_directories()
    
    # Configure workers
    if workers is None:
        workers = mp.cpu_count() - 1 if parallel else 1
    
    # Load problem
    instance_path = f"data/vrp/{instance}"
    if not instance.endswith('.vrp'):
        instance_path = f"data/vrp/{instance}.vrp"
    
    if not os.path.exists(instance_path):
        click.echo(f"❌ Error: Instance not found {instance_path}", err=True)
        return
    
    try:
        problem = VRPProblemV2(instance_path)
    except Exception as e:
        click.echo(f"❌ Error loading instance: {str(e)}", err=True)
        return
    
    click.echo(f"🚀 Running {algorithm.upper()} on {instance}")
    click.echo(f"📊 Configuration:")
    click.echo(f"  Population: {population}")
    click.echo(f"  Iterations: {iterations}")
    click.echo(f"  Runs: {runs}")
    click.echo(f"  Metadata capture: {capture_metadata}")
    click.echo(f"  Resource monitoring: {monitor_resources}")
    
    # Configure seeds
    base_seed = seed if seed else 42
    seeds = list(range(base_seed, base_seed + runs))
    
    # Prepare timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run algorithm
    results = []
    
    if parallel and runs > 1:
        click.echo(f"🔧 Running in parallel with {workers} workers")
        
        # Create partial function with fixed parameters
        run_func = partial(
            run_algorithm_with_metadata,
            algorithm,
            problem,
            population,
            iterations,
            capture_metadata=capture_metadata,
            monitor_resources=monitor_resources
        )
        
        # Run in parallel
        with Pool(workers) as pool:
            tasks = [(seed, i) for i, seed in enumerate(seeds)]
            
            with tqdm(total=runs, desc=f"Running {algorithm}") as pbar:
                for result in pool.starmap(run_func, tasks):
                    if result:
                        results.append(result)
                    pbar.update(1)
    else:
        # Sequential execution
        click.echo("🔧 Running sequentially")
        
        for i, seed in enumerate(tqdm(seeds, desc=f"Running {algorithm}")):
            result = run_algorithm_with_metadata(
                algorithm, problem, population, iterations, seed, i,
                capture_metadata, monitor_resources
            )
            if result:
                results.append(result)
    
    # Save results
    if results:
        save_results_with_metadata(results, algorithm, problem.name, output_dir, timestamp)
        
        # Generate plots if requested
        if plot:
            plot_dir = Path(output_dir) / 'plots'
            plot_dir.mkdir(exist_ok=True)
            
            # Extract data for plotting
            fitness_values = []
            convergence_curves = []
            
            for r in results:
                if 'runs' in r and len(r['runs']) > 0:
                    run_data = r['runs'][0]
                    fitness_values.append(run_data['best_fitness'])
                    if 'convergence_curve' in run_data:
                        convergence_curves.append(run_data['convergence_curve'])
            
            if convergence_curves:
                # Plot average convergence
                avg_curve = np.mean(convergence_curves, axis=0)
                plot_convergence(
                    {algorithm: avg_curve},
                    save_path=str(plot_dir / f"{algorithm}_convergence_{timestamp}.png")
                )
                click.echo(f"📈 Convergence plot saved")
        
        click.echo(f"✅ Completed {len(results)} successful runs")
    else:
        click.echo("❌ No successful runs completed")


if __name__ == '__main__':
    main()