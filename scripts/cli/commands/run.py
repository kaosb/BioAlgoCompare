#!/usr/bin/env python3
"""
Unified run command for BioAlgoCompare.

This command consolidates all run functionality including:
- Standard runs
- Runs with metadata capture
- Runs with experiment tracking
- Runs with result schema validation
"""

import click
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import multiprocessing as mp

# Import algorithm classes
from algorithms.hoa_v2 import HOAV2
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
from algorithms.fgo_v2 import FGOV2
from algorithms.sho_v2 import SHOV2

# Algorithm mapping
ALGORITHMS_V2 = {
    "hoa": HOAV2,
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
    "fgo": FGOV2,
    "sho": SHOV2,
}


@click.command()
@click.option('--algorithm', '-a', 
              type=click.Choice(list(ALGORITHMS_V2.keys())), 
              required=True, 
              help='Algorithm to run')
@click.option('--instance', '-i', 
              type=str, 
              required=True, 
              help='VRP instance name (e.g., A-n32-k5)')
@click.option('--population', '-p', 
              default=30, 
              type=int, 
              help='Population size')
@click.option('--iterations', '-n', 
              default=100, 
              type=int, 
              help='Number of iterations')
@click.option('--runs', '-r', 
              default=1, 
              type=int, 
              help='Number of independent runs')
@click.option('--seed', '-s', 
              type=int, 
              help='Random seed for reproducibility')
@click.option('--parallel/--no-parallel', 
              default=False, 
              help='Run multiple runs in parallel')
@click.option('--workers', '-w', 
              type=int, 
              help='Number of parallel workers (default: CPU count - 1)')
# Output options
@click.option('--output-dir', '-o', 
              type=str, 
              default='results', 
              help='Output directory')
@click.option('--save/--no-save', 
              default=True, 
              help='Save results to file')
@click.option('--format', 
              type=click.Choice(['json', 'csv', 'both']), 
              default='json', 
              help='Output format')
# Advanced options
@click.option('--metadata/--no-metadata', 
              default=True, 
              help='Capture system metadata for reproducibility')
@click.option('--monitor/--no-monitor', 
              default=False, 
              help='Monitor resource usage during execution')
@click.option('--validate/--no-validate', 
              default=True, 
              help='Validate results with schema')
@click.option('--track/--no-track', 
              default=False, 
              help='Use experiment tracking')
# Visualization options
@click.option('--plot/--no-plot', 
              default=False, 
              help='Generate visualization plots')
@click.option('--show/--no-show', 
              default=False, 
              help='Show plots interactively')
# Verbosity
@click.option('--verbose', '-v', 
              count=True, 
              help='Increase verbosity (-v, -vv, -vvv)')
@click.option('--quiet', '-q', 
              is_flag=True, 
              help='Suppress all output except errors')
def run(algorithm, instance, population, iterations, runs, seed, parallel, workers,
        output_dir, save, format, metadata, monitor, validate, track,
        plot, show, verbose, quiet):
    """
    Run bio-inspired algorithms on VRP instances.
    
    This unified command provides all run functionality with various options
    for metadata capture, monitoring, validation, and tracking.
    
    Examples:
    
        # Basic run
        bioalgo run -a hoa -i A-n32-k5
        
        # Multiple runs with full features
        bioalgo run -a egto -i P-n16-k8 -r 30 --parallel --metadata --monitor
        
        # Experiment with tracking
        bioalgo run -a foa -i E-n22-k4 --track --plot --format both
    """
    
    # Set verbosity
    if quiet:
        verbose = -1
    
    # Validate instance
    instance_path = Path(f"data/vrp/{instance}.vrp")
    if not instance_path.exists():
        instance_path = Path(f"data/vrp/{instance}")
        if not instance_path.exists():
            click.echo(f"❌ Error: Instance '{instance}' not found", err=True)
            return
    
    # Configure workers
    if workers is None:
        workers = max(1, mp.cpu_count() - 1) if parallel else 1
    
    # Show configuration
    if verbose >= 0:
        click.echo(f"🚀 Running {algorithm.upper()} on {instance}")
        if verbose >= 1:
            click.echo(f"📊 Configuration:")
            click.echo(f"  Population: {population}")
            click.echo(f"  Iterations: {iterations}")
            click.echo(f"  Runs: {runs}")
            if seed:
                click.echo(f"  Seed: {seed}")
            if parallel and runs > 1:
                click.echo(f"  Workers: {workers}")
            if metadata:
                click.echo(f"  Metadata: ✓")
            if monitor:
                click.echo(f"  Monitoring: ✓")
    
    # Import necessary modules based on options
    if metadata or monitor:
        from utils.result_metadata_integration import wrap_algorithm_with_metadata
    
    if track:
        from utils.experiment_tracker import ExperimentTracker
        tracker = ExperimentTracker()
    
    # Load problem
    try:
        from problems.vrp_v2 import VRPProblemV2
        problem = VRPProblemV2(str(instance_path))
    except Exception as e:
        click.echo(f"❌ Error loading instance: {str(e)}", err=True)
        return
    
    # Prepare algorithm class
    AlgoClass = ALGORITHMS_V2[algorithm]
    
    # Wrap with metadata if requested
    if metadata or monitor:
        AlgoClass = wrap_algorithm_with_metadata(
            AlgoClass,
            capture_metadata=metadata,
            monitor_resources=monitor
        )
    
    # Prepare output directory
    if save:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Run algorithm
    results = []
    base_seed = seed if seed else 42
    
    if runs == 1:
        # Single run
        if verbose >= 0:
            click.echo("⏳ Running algorithm...")
        
        algo = AlgoClass(
            problem,
            population_size=population,
            max_iterations=iterations,
            seed=base_seed
        )
        
        start_time = time.time()
        best_solution = algo.execute()
        execution_time = time.time() - start_time
        
        # Collect results
        result = {
            'algorithm': algorithm,
            'instance': instance,
            'run_id': 0,
            'seed': base_seed,
            'fitness': best_solution.fitness(),
            'execution_time': execution_time,
            'convergence_curve': algo.get_convergence_curve(),
        }
        
        # Add metadata if available
        if hasattr(algo, 'get_complete_result'):
            result['complete_result'] = algo.get_complete_result()
        
        results.append(result)
        
        if verbose >= 0:
            click.echo(f"✅ Best fitness: {best_solution.fitness():.2f}")
            click.echo(f"⏱️  Time: {execution_time:.2f}s")
    
    else:
        # Multiple runs
        from functools import partial
        from tqdm import tqdm
        
        def run_single(run_id, seed):
            algo = AlgoClass(
                problem,
                population_size=population,
                max_iterations=iterations,
                seed=seed
            )
            
            start_time = time.time()
            best_solution = algo.execute()
            execution_time = time.time() - start_time
            
            result = {
                'algorithm': algorithm,
                'instance': instance,
                'run_id': run_id,
                'seed': seed,
                'fitness': best_solution.fitness(),
                'execution_time': execution_time,
                'convergence_curve': algo.get_convergence_curve(),
            }
            
            if hasattr(algo, 'get_complete_result'):
                result['complete_result'] = algo.get_complete_result()
            
            return result
        
        seeds = [base_seed + i for i in range(runs)]
        
        if parallel and runs > 1:
            # Parallel execution
            if verbose >= 0:
                click.echo(f"⏳ Running {runs} runs in parallel with {workers} workers...")
            
            with mp.Pool(workers) as pool:
                tasks = [(i, seed) for i, seed in enumerate(seeds)]
                
                if verbose >= 0:
                    results = list(tqdm(
                        pool.starmap(run_single, tasks),
                        total=runs,
                        desc=f"Running {algorithm}"
                    ))
                else:
                    results = pool.starmap(run_single, tasks)
        else:
            # Sequential execution
            if verbose >= 0:
                click.echo(f"⏳ Running {runs} runs sequentially...")
                
                results = []
                for i, seed in tqdm(enumerate(seeds), total=runs, desc=f"Running {algorithm}"):
                    results.append(run_single(i, seed))
            else:
                results = [run_single(i, seed) for i, seed in enumerate(seeds)]
        
        # Show summary
        if verbose >= 0 and results:
            fitness_values = [r['fitness'] for r in results]
            import numpy as np
            
            click.echo(f"\n📊 Summary of {runs} runs:")
            click.echo(f"  Best: {min(fitness_values):.2f}")
            click.echo(f"  Mean: {np.mean(fitness_values):.2f}")
            click.echo(f"  Std: {np.std(fitness_values):.2f}")
            click.echo(f"  Worst: {max(fitness_values):.2f}")
    
    # Save results
    if save and results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format in ['json', 'both']:
            json_file = output_path / f"{algorithm}_{instance}_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            if verbose >= 0:
                click.echo(f"💾 Results saved to: {json_file}")
        
        if format in ['csv', 'both']:
            import pandas as pd
            
            # Convert to DataFrame
            df_data = []
            for r in results:
                df_data.append({
                    'algorithm': r['algorithm'],
                    'instance': r['instance'],
                    'run_id': r['run_id'],
                    'seed': r['seed'],
                    'fitness': r['fitness'],
                    'execution_time': r['execution_time'],
                })
            
            df = pd.DataFrame(df_data)
            csv_file = output_path / f"{algorithm}_{instance}_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            if verbose >= 0:
                click.echo(f"💾 Results saved to: {csv_file}")
    
    # Generate plots
    if plot and results:
        if verbose >= 0:
            click.echo("📈 Generating plots...")
        
        from utils.visualization import plot_convergence, plot_vrp_solution
        
        plot_dir = output_path / 'plots' if save else Path('plots')
        plot_dir.mkdir(exist_ok=True)
        
        # Plot convergence
        if len(results) == 1:
            # Single run
            convergence_data = {algorithm: results[0]['convergence_curve']}
        else:
            # Average convergence
            import numpy as np
            curves = [r['convergence_curve'] for r in results]
            avg_curve = np.mean(curves, axis=0).tolist()
            convergence_data = {algorithm: avg_curve}
        
        conv_plot = plot_dir / f"{algorithm}_{instance}_convergence.png"
        plot_convergence(convergence_data, save_path=str(conv_plot), show=show)
        
        if verbose >= 0:
            click.echo(f"📊 Convergence plot saved: {conv_plot}")
    
    # Track experiment
    if track and results:
        experiment_id = tracker.create_experiment(
            name=f"{algorithm}_{instance}",
            algorithm=algorithm,
            problem=instance,
            config={
                'population_size': population,
                'max_iterations': iterations,
                'runs': runs,
                'seed': base_seed
            }
        )
        
        for r in results:
            tracker.log_run(
                experiment_id=experiment_id,
                run_id=r['run_id'],
                metrics={
                    'fitness': r['fitness'],
                    'execution_time': r['execution_time']
                }
            )
        
        if verbose >= 0:
            click.echo(f"📊 Experiment tracked: ID {experiment_id}")
    
    if verbose >= 0:
        click.echo("✅ Done!")


if __name__ == '__main__':
    run()