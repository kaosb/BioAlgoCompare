"""
Unified benchmarking module for BioAlgoCompare.
Consolidates functionality from benchmarking.py and enhanced_benchmarking.py
into a single, well-organized module.

This module provides comprehensive benchmarking capabilities for comparing
algorithm performance including:
- Single and parallel execution
- Checkpoint/resume functionality for massive runs
- Result storage and loading (JSON, CSV, pickle)
- Performance visualization and reporting
- Statistical analysis integration
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import os
import json
import time
import pickle
import gzip
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any, Callable
import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
from matplotlib.patches import Polygon
from matplotlib.table import Table
<<<<<<< HEAD
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)

# Optimal values for standard VRP instances
OPTIMAL_VALUES = {
    # A instances
    "A-n32-k5": 784,
    "A-n33-k5": 661,
    "A-n33-k6": 742,
    "A-n34-k5": 778,
    "A-n36-k5": 799,
    "A-n37-k5": 669,
    "A-n37-k6": 949,
    "A-n38-k5": 730,
    "A-n39-k5": 822,
    "A-n39-k6": 831,
    "A-n44-k6": 937,
    "A-n45-k6": 944,
    "A-n45-k7": 1146,
    "A-n46-k7": 914,
    "A-n48-k7": 1073,
    "A-n53-k7": 1010,
    "A-n54-k7": 1167,
    "A-n55-k9": 1073,
    "A-n60-k9": 1354,
    "A-n61-k9": 1034,
    "A-n62-k8": 1288,
    "A-n63-k9": 1616,
    "A-n63-k10": 1314,
    "A-n64-k9": 1401,
    "A-n65-k9": 1174,
    "A-n69-k9": 1159,
    "A-n80-k10": 1763,
    # B instances
    "B-n31-k5": 672,
    "B-n34-k5": 788,
    "B-n35-k5": 955,
    "B-n38-k6": 805,
    "B-n39-k5": 549,
    "B-n41-k6": 829,
    "B-n43-k6": 742,
    "B-n44-k7": 909,
    "B-n45-k5": 751,
    "B-n45-k6": 678,
    "B-n50-k7": 741,
    "B-n50-k8": 1312,
    "B-n51-k7": 1032,
    "B-n52-k7": 747,
    "B-n56-k7": 707,
    "B-n57-k7": 1153,
    "B-n57-k9": 1598,
    "B-n63-k10": 1496,
    "B-n64-k9": 861,
    "B-n66-k9": 1316,
    "B-n67-k10": 1032,
    "B-n68-k9": 1272,
    "B-n78-k10": 1221,
    # E instances
    "E-n22-k4": 375,
    "E-n23-k3": 569,
    "E-n30-k3": 534,
    "E-n33-k4": 835,
    "E-n51-k5": 521,
    "E-n76-k7": 682,
    "E-n76-k8": 735,
    "E-n76-k10": 830,
    "E-n76-k14": 1021,
    "E-n101-k8": 815,
    "E-n101-k14": 1067,
    # F instances
    "F-n45-k4": 724,
    "F-n72-k4": 237,
    "F-n135-k7": 1162,
    # M instances
    "M-n101-k10": 820,
    "M-n121-k7": 1034,
    "M-n151-k12": 1015,
    "M-n200-k16": 1274,
    "M-n200-k17": 1275,
    # P instances
    "P-n16-k8": 450,
    "P-n19-k2": 212,
    "P-n20-k2": 216,
    "P-n21-k2": 211,
    "P-n22-k2": 216,
    "P-n22-k8": 603,
    "P-n23-k8": 529,
    "P-n40-k5": 458,
    "P-n45-k5": 510,
    "P-n50-k7": 554,
    "P-n50-k8": 631,
    "P-n50-k10": 696,
    "P-n51-k10": 741,
    "P-n55-k7": 568,
    "P-n55-k8": 576,
    "P-n55-k10": 694,
    "P-n55-k15": 989,
    "P-n60-k10": 744,
    "P-n60-k15": 968,
    "P-n65-k10": 792,
    "P-n70-k10": 827,
    "P-n76-k4": 593,
    "P-n76-k5": 627,
    "P-n101-k4": 681,
}
=======
import matplotlib.gridspec as gridspec
from scipy.stats import friedmanchisquare, wilcoxon
import multiprocessing as mp
import logging
from tqdm import tqdm
import pickle
import gzip
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)


def create_summary_dataframe(benchmark_results):
    """
    Create a summary DataFrame from benchmark results.

    Args:
        benchmark_results: List of BenchmarkResult objects

    Returns:
        DataFrame with all individual run data
    """
    data = []

    for result in benchmark_results:
        # For each run
        for i in range(len(result.fitness_values)):
            data.append(
                {
                    "Algorithm": result.algorithm_name,
                    "Instance": result.instance_name,
                    "Run": i + 1,
                    "Best Fitness": result.fitness_values[i],
                    "Execution Time (s)": result.execution_times[i],
                    "Best_Cost": result.fitness_values[i],  # For compatibility
                    "Time": result.execution_times[i],  # For compatibility
                }
            )

    return pd.DataFrame(data)


# Helper function for parallel algorithm execution
# Defined at module level to avoid pickle issues
def _run_algo_task(params):
    AlgoClass, problem, population, iterations, run_seed, _ = params
    algo = AlgoClass(
        problem, population_size=population, max_iterations=iterations, seed=run_seed
    )

    start_time = time.time()
    best_solution = algo.execute()
    execution_time = time.time() - start_time

    # Handle both object-based and tuple-based returns
    if hasattr(best_solution, 'fitness'):
        # Object with fitness() method (HO, HHO, etc.)
        fitness_value = best_solution.fitness()
        convergence_curve = algo.get_convergence_curve()
    else:
        # Tuple return (PSO, GA)
        if isinstance(best_solution, tuple):
            _, fitness_value, convergence_curve = best_solution
        else:
            raise ValueError("Unexpected return type from algorithm")
    
    return fitness_value, execution_time, convergence_curve
>>>>>>> develop


@dataclass
class BenchmarkResult:
<<<<<<< HEAD
    """Enhanced container for benchmark results with all functionality."""
    
    algorithm_name: str
    instance_name: str
    runs: int = 0
    optimal_value: Optional[float] = None
    
    # Results storage
    fitness_values: List[float] = field(default_factory=list)
    execution_times: List[float] = field(default_factory=list)
    convergence_curves: List[List[float]] = field(default_factory=list)
    solutions: List[Any] = field(default_factory=list)
    
    # Computed metrics
    best_fitness: Optional[float] = None
    worst_fitness: Optional[float] = None
    mean_fitness: Optional[float] = None
    std_fitness: Optional[float] = None
    median_fitness: Optional[float] = None
    mean_time: Optional[float] = None
    std_time: Optional[float] = None
    gap_to_optimal: Optional[float] = None
    success_rate: Optional[float] = None
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    metadata: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Initialize optimal value from global dictionary."""
        if self.optimal_value is None:
            self.optimal_value = OPTIMAL_VALUES.get(self.instance_name)
            
    def add_run(self, fitness: float, execution_time: float, 
                convergence_curve: List[float], solution: Any = None) -> None:
        """Add a single run result."""
        self.fitness_values.append(fitness)
        self.execution_times.append(execution_time)
        self.convergence_curves.append(convergence_curve)
        if solution is not None:
            self.solutions.append(solution)
        self.runs = len(self.fitness_values)
        
    def compute_metrics(self) -> None:
        """Compute all statistical metrics from the stored results."""
        if not self.fitness_values:
            return
            
=======
    """Class to store and analyze benchmarking results."""

    def __init__(self, algorithm_name, instance_name, runs=None):
        """
        Initialize a benchmark result.

        Args:
            algorithm_name: Algorithm name
            instance_name: Instance name
            runs: Number of independent executions (if None, determined by data)
        """
        self.algorithm_name = algorithm_name
        self.instance_name = instance_name
        self.optimal_value = OPTIMAL_VALUES.get(instance_name, None)

        # Results per execution
        self.fitness_values = []
        self.execution_times = []
        self.convergence_curves = []

        # Derived metrics
        self.best_fitness = None
        self.worst_fitness = None
        self.mean_fitness = None
        self.std_fitness = None
        self.mean_time = None
        self.std_time = None
        self.gap_to_optimal = None
        self.success_rate = None
        self.avg_convergence = None

        # If number of executions is not specified, it's determined by data
        self.runs = runs

    def add_run(self, fitness, execution_time, convergence_curve):
        """Add the results of an execution."""
        self.fitness_values.append(fitness)
        self.execution_times.append(execution_time)
        self.convergence_curves.append(convergence_curve)

    def compute_metrics(self):
        """Calculate derived metrics from results."""
        if not self.fitness_values:
            return

        # Basic metrics
>>>>>>> develop
        self.best_fitness = min(self.fitness_values)
        self.worst_fitness = max(self.fitness_values)
        self.mean_fitness = np.mean(self.fitness_values)
        self.std_fitness = np.std(self.fitness_values)
        self.median_fitness = np.median(self.fitness_values)
        
        self.mean_time = np.mean(self.execution_times)
        self.std_time = np.std(self.execution_times)
<<<<<<< HEAD
        
        # Calculate gap to optimal if known
        if self.optimal_value:
            self.gap_to_optimal = ((self.best_fitness - self.optimal_value) / 
                                   self.optimal_value * 100)
            # Success rate: percentage of runs within 5% of optimal
            threshold = self.optimal_value * 1.05
            self.success_rate = sum(1 for f in self.fitness_values if f <= threshold) / self.runs * 100
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'algorithm_name': self.algorithm_name,
            'instance_name': self.instance_name,
            'runs': self.runs,
            'optimal_value': self.optimal_value,
            'fitness_values': self.fitness_values,
            'execution_times': self.execution_times,
            'convergence_curves': self.convergence_curves,
            'solutions': self.solutions,
            'best_fitness': self.best_fitness,
            'worst_fitness': self.worst_fitness,
            'mean_fitness': self.mean_fitness,
            'std_fitness': self.std_fitness,
            'median_fitness': self.median_fitness,
            'mean_time': self.mean_time,
            'std_time': self.std_time,
            'gap_to_optimal': self.gap_to_optimal,
            'success_rate': self.success_rate,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'checkpoints': self.checkpoints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """Create from dictionary."""
        result = cls(
            algorithm_name=data['algorithm_name'],
            instance_name=data['instance_name'],
            runs=data.get('runs', 0),
            optimal_value=data.get('optimal_value')
        )
        
        # Restore data
        result.fitness_values = data.get('fitness_values', [])
        result.execution_times = data.get('execution_times', [])
        result.convergence_curves = data.get('convergence_curves', [])
        result.solutions = data.get('solutions', [])
        
        # Restore metrics
        result.best_fitness = data.get('best_fitness')
        result.worst_fitness = data.get('worst_fitness')
        result.mean_fitness = data.get('mean_fitness')
        result.std_fitness = data.get('std_fitness')
        result.median_fitness = data.get('median_fitness')
        result.mean_time = data.get('mean_time')
        result.std_time = data.get('std_time')
        result.gap_to_optimal = data.get('gap_to_optimal')
        result.success_rate = data.get('success_rate')
        
        # Restore metadata
        result.timestamp = data.get('timestamp', result.timestamp)
        result.metadata = data.get('metadata', {})
        result.checkpoints = data.get('checkpoints', [])
        
        return result


class BenchmarkRunner:
    """Main class for running benchmarks with all features."""
    
    def __init__(self, output_dir: Optional[str] = None, parallel: bool = True,
                 checkpoint_interval: int = 100, verbose: bool = True):
        """
        Initialize benchmark runner.
        
        Args:
            output_dir: Directory for outputs (auto-generated if None)
            parallel: Use parallel execution
            checkpoint_interval: Save checkpoint every N runs
            verbose: Show progress bars and detailed logs
        """
        self.parallel = parallel
        self.checkpoint_interval = checkpoint_interval
        self.verbose = verbose
        
        # Setup output directory
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"results/benchmark_{timestamp}"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize timing data
        self.timing_data = {}
        
    def _setup_logging(self) -> None:
        """Configure logging for the benchmark."""
        log_file = self.output_dir / "benchmark.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
        
    def run_benchmark(
        self,
        algorithms: Dict[str, Any],
        instances: List[str],
        runs: int = 30,
        iterations: int = 100,
        population: int = 30,
        seed: int = 42,
        resume: bool = True
    ) -> List[BenchmarkResult]:
        """
        Run complete benchmark with all algorithms and instances.
        
        Args:
            algorithms: Dictionary mapping algorithm names to classes
            instances: List of instance names
            runs: Number of independent runs per algorithm/instance
            iterations: Maximum iterations per run
            population: Population size
            seed: Random seed for reproducibility
            resume: Whether to resume from checkpoint if available
            
        Returns:
            List of BenchmarkResult objects
        """
        # Generate benchmark ID for checkpointing
        benchmark_id = self._generate_benchmark_id(algorithms, instances, seed, iterations, population)
        checkpoint_file = self.output_dir / f"checkpoint_{benchmark_id}.pkl.gz"
        
        # Try to resume from checkpoint
        results = []
        completed_tasks = set()
        
        if resume and checkpoint_file.exists():
            try:
                results, completed_tasks = self._load_checkpoint(checkpoint_file)
                logger.info(f"Resumed from checkpoint with {len(completed_tasks)} completed tasks")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
                results = []
                completed_tasks = set()
        
        # Generate all tasks
        all_tasks = []
        for algo_name, AlgoClass in algorithms.items():
            for instance_name in instances:
                for run_idx in range(runs):
                    task_id = f"{algo_name}_{instance_name}_{run_idx}"
                    if task_id not in completed_tasks:
                        all_tasks.append({
                            'task_id': task_id,
                            'algo_name': algo_name,
                            'AlgoClass': AlgoClass,
                            'instance_name': instance_name,
                            'run_idx': run_idx,
                            'iterations': iterations,
                            'population': population,
                            'seed': seed + run_idx
                        })
        
        logger.info(f"Total tasks: {len(all_tasks) + len(completed_tasks)}, Remaining: {len(all_tasks)}")
        
        if not all_tasks:
            logger.info("All tasks already completed!")
            return self._organize_results(results)
        
        # Execute tasks
        if self.parallel:
            results.extend(self._run_parallel(all_tasks, checkpoint_file, completed_tasks))
        else:
            results.extend(self._run_sequential(all_tasks, checkpoint_file, completed_tasks))
        
        # Organize and compute final metrics
        final_results = self._organize_results(results)
        
        # Save final results
        self.save_results(final_results)
        
        return final_results
    
    def _run_parallel(self, tasks: List[Dict], checkpoint_file: Path, 
                      completed_tasks: set) -> List[Dict]:
        """Run tasks in parallel with checkpointing."""
        results = []
        n_workers = min(cpu_count(), len(tasks))
        
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._run_single_task, task): task 
                for task in tasks
            }
            
            # Process completed tasks with progress bar
            pbar = tqdm(total=len(tasks), desc="Running benchmark") if self.verbose else None
            
            for i, future in enumerate(as_completed(future_to_task)):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_tasks.add(task['task_id'])
                    
                    if pbar:
                        pbar.update(1)
                    
                    # Checkpoint periodically
                    if (i + 1) % self.checkpoint_interval == 0:
                        self._save_checkpoint(results, completed_tasks, checkpoint_file)
                        
                except Exception as e:
                    logger.error(f"Task {task['task_id']} failed: {e}")
                    
            if pbar:
                pbar.close()
                
        return results
    
    def _run_sequential(self, tasks: List[Dict], checkpoint_file: Path,
                        completed_tasks: set) -> List[Dict]:
        """Run tasks sequentially with checkpointing."""
        results = []
        
        pbar = tqdm(tasks, desc="Running benchmark") if self.verbose else tasks
        
        for i, task in enumerate(pbar):
            try:
                result = self._run_single_task(task)
                results.append(result)
                completed_tasks.add(task['task_id'])
                
                # Checkpoint periodically
                if (i + 1) % self.checkpoint_interval == 0:
                    self._save_checkpoint(results, completed_tasks, checkpoint_file)
                    
            except Exception as e:
                logger.error(f"Task {task['task_id']} failed: {e}")
                
        return results
    
    @staticmethod
    def _run_single_task(task: Dict) -> Dict:
        """Execute a single algorithm run."""
        # Import here to avoid issues with multiprocessing
        from problems.vrp_v2 import VRPProblemV2
        
        # Load problem instance
        instance_path = f"data/vrp/{task['instance_name']}.vrp"
        problem = VRPProblemV2(instance_path)
        
        # Initialize algorithm
        algo = task['AlgoClass'](
            problem,
            population_size=task['population'],
            max_iterations=task['iterations'],
            seed=task['seed']
        )
        
        # Run algorithm
        start_time = time.time()
        best_solution = algo.execute()
        execution_time = time.time() - start_time
        
        # Get convergence curve
        convergence_curve = algo.get_convergence_curve()
        
        return {
            'task_id': task['task_id'],
            'algo_name': task['algo_name'],
            'instance_name': task['instance_name'],
            'run_idx': task['run_idx'],
            'fitness': best_solution.fitness(),
            'execution_time': execution_time,
            'convergence_curve': convergence_curve,
            'solution': best_solution.position
        }
    
    def _organize_results(self, raw_results: List[Dict]) -> List[BenchmarkResult]:
        """Organize raw results into BenchmarkResult objects."""
        # Group by algorithm and instance
        organized = {}
        
        for result in raw_results:
            key = (result['algo_name'], result['instance_name'])
            if key not in organized:
                organized[key] = BenchmarkResult(
                    algorithm_name=result['algo_name'],
                    instance_name=result['instance_name']
                )
            
            organized[key].add_run(
                fitness=result['fitness'],
                execution_time=result['execution_time'],
                convergence_curve=result['convergence_curve'],
                solution=result.get('solution')
            )
        
        # Compute metrics for all results
        final_results = []
        for result in organized.values():
            result.compute_metrics()
            final_results.append(result)
            
        return final_results
    
    def save_results(self, results: List[BenchmarkResult], formats: List[str] = None) -> None:
        """Save benchmark results in multiple formats."""
        if formats is None:
            formats = ['json', 'csv', 'pickle']
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if 'json' in formats:
            json_file = self.output_dir / f"results_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump([r.to_dict() for r in results], f, indent=2)
            logger.info(f"Results saved to {json_file}")
            
        if 'csv' in formats:
            df = self.create_summary_dataframe(results)
            csv_file = self.output_dir / f"summary_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            logger.info(f"Summary saved to {csv_file}")
            
        if 'pickle' in formats:
            pkl_file = self.output_dir / f"results_{timestamp}.pkl.gz"
            with gzip.open(pkl_file, 'wb') as f:
                pickle.dump(results, f)
            logger.info(f"Pickle saved to {pkl_file}")
            
    @staticmethod
    def create_summary_dataframe(results: List[BenchmarkResult]) -> pd.DataFrame:
        """Create summary DataFrame from results."""
        data = []
        for result in results:
            data.append({
                'Algorithm': result.algorithm_name,
                'Instance': result.instance_name,
                'Runs': result.runs,
                'Best': result.best_fitness,
                'Worst': result.worst_fitness,
                'Mean': result.mean_fitness,
                'Std': result.std_fitness,
                'Median': result.median_fitness,
                'Time_Mean': result.mean_time,
                'Time_Std': result.std_time,
                'Gap%': result.gap_to_optimal,
                'Success%': result.success_rate
            })
        
        return pd.DataFrame(data)
    
    def _generate_benchmark_id(self, algorithms: Dict, instances: List[str],
                               seed: int, iterations: int, population: int) -> str:
        """Generate unique ID for benchmark configuration."""
        config_str = f"{sorted(algorithms.keys())}_{sorted(instances)}_{seed}_{iterations}_{population}"
        return hashlib.md5(config_str.encode()).hexdigest()[:8]
    
    def _save_checkpoint(self, results: List[Dict], completed_tasks: set, checkpoint_file: Path) -> None:
        """Save checkpoint to disk."""
        try:
            with gzip.open(checkpoint_file, 'wb') as f:
                pickle.dump((results, completed_tasks), f)
            logger.debug(f"Checkpoint saved with {len(completed_tasks)} completed tasks")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            
    def _load_checkpoint(self, checkpoint_file: Path) -> Tuple[List[Dict], set]:
        """Load checkpoint from disk."""
        with gzip.open(checkpoint_file, 'rb') as f:
            return pickle.load(f)


class BenchmarkVisualizer:
    """Class for creating benchmark visualizations and reports."""
    
    @staticmethod
    def plot_solution_quality(results: List[BenchmarkResult], 
                              title: Optional[str] = None,
                              save_path: Optional[Path] = None) -> plt.Figure:
        """Create comprehensive solution quality plot."""
        # Prepare data
        data = []
        for result in results:
            for fitness in result.fitness_values:
                data.append({
                    'Algorithm': result.algorithm_name,
                    'Instance': result.instance_name,
                    'Fitness': fitness
                })
        
        df = pd.DataFrame(data)
        
        # Create figure
        n_instances = len(df['Instance'].unique())
        fig, axes = plt.subplots(1, n_instances, figsize=(6*n_instances, 6), sharey=True)
        
        if n_instances == 1:
            axes = [axes]
            
        # Plot for each instance
        for idx, (instance, group) in enumerate(df.groupby('Instance')):
            ax = axes[idx]
            
            # Box plot
            group.boxplot(column='Fitness', by='Algorithm', ax=ax)
            
            # Add optimal value line if available
            if instance in OPTIMAL_VALUES:
                ax.axhline(y=OPTIMAL_VALUES[instance], color='red', 
                          linestyle='--', label='Optimal')
                
            ax.set_title(f'{instance}')
            ax.set_xlabel('Algorithm')
            if idx == 0:
                ax.set_ylabel('Fitness')
            ax.legend()
            
        plt.suptitle(title or 'Solution Quality Comparison')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        return fig
    
    @staticmethod
    def plot_convergence_comparison(results: List[BenchmarkResult],
                                    instance: str,
                                    save_path: Optional[Path] = None) -> plt.Figure:
        """Plot convergence curves for different algorithms on same instance."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Filter results for specific instance
        instance_results = [r for r in results if r.instance_name == instance]
        
        for result in instance_results:
            # Average convergence across runs
            curves = np.array(result.convergence_curves)
            mean_curve = np.mean(curves, axis=0)
            std_curve = np.std(curves, axis=0)
            
            iterations = np.arange(len(mean_curve))
            
            # Plot mean with confidence interval
            ax.plot(iterations, mean_curve, label=result.algorithm_name, linewidth=2)
            ax.fill_between(iterations, 
                           mean_curve - std_curve,
                           mean_curve + std_curve,
                           alpha=0.3)
        
        # Add optimal value if available
        if instance in OPTIMAL_VALUES:
            ax.axhline(y=OPTIMAL_VALUES[instance], color='red',
                      linestyle='--', label='Optimal', linewidth=2)
        
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Fitness')
        ax.set_title(f'Convergence Comparison - {instance}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        return fig
    
    @staticmethod
    def create_comprehensive_report(results: List[BenchmarkResult],
                                    output_dir: Path,
                                    include_stats: bool = True) -> Path:
        """Create comprehensive HTML report with all visualizations."""
        from utils.statistics import UnifiedStatisticalAnalysis
        
        report_path = output_dir / "benchmark_report.html"
        
        # Create visualizations
        figs_dir = output_dir / "figures"
        figs_dir.mkdir(exist_ok=True)
        
        # Solution quality plot
        quality_fig = BenchmarkVisualizer.plot_solution_quality(
            results, save_path=figs_dir / "solution_quality.png"
        )
        plt.close(quality_fig)
        
        # Convergence plots for each instance
        instances = list(set(r.instance_name for r in results))
        for instance in instances[:3]:  # Limit to first 3 instances
            conv_fig = BenchmarkVisualizer.plot_convergence_comparison(
                results, instance, save_path=figs_dir / f"convergence_{instance}.png"
            )
            plt.close(conv_fig)
        
        # Statistical analysis if requested
        stats_html = ""
        if include_stats and len(results) >= 2:
            # Prepare data for statistical analysis
            summary_df = BenchmarkRunner.create_summary_dataframe(results)
            pivot_df = summary_df.pivot(index='Instance', columns='Algorithm', values='Mean')
            
            # Run statistical analysis
            analyzer = UnifiedStatisticalAnalysis()
            analysis_result = analyzer.run_comprehensive_analysis(pivot_df)
            
            # Generate statistical report section
            stats_html = f"""
            <h2>Statistical Analysis</h2>
            <h3>Friedman Test</h3>
            <p>p-value: {analysis_result.friedman_result.p_value:.4f}</p>
            <p>Significant: {analysis_result.friedman_result.significant}</p>
            
            <h3>Algorithm Rankings</h3>
            {analysis_result.rankings.to_html()}
            """
        
        # Generate HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Benchmark Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333366; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Benchmark Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Algorithms: {len(set(r.algorithm_name for r in results))}</p>
                <p>Instances: {len(set(r.instance_name for r in results))}</p>
                <p>Total runs: {sum(r.runs for r in results)}</p>
            </div>
            
            <h2>Results Table</h2>
            {BenchmarkRunner.create_summary_dataframe(results).to_html(index=False)}
            
            <h2>Visualizations</h2>
            <h3>Solution Quality</h3>
            <img src="figures/solution_quality.png" alt="Solution Quality">
            
            <h3>Convergence Analysis</h3>
            {"".join(f'<img src="figures/convergence_{inst}.png" alt="Convergence {inst}">' 
                    for inst in instances[:3])}
            
            {stats_html}
        </body>
        </html>
        """
        
        report_path.write_text(html_content)
        logger.info(f"Report generated at {report_path}")
        
        return report_path


# Convenience functions for backward compatibility

def run_benchmark(algorithms: Dict[str, Any], instances: List[str], **kwargs) -> List[BenchmarkResult]:
    """Backward compatible benchmark function."""
    runner = BenchmarkRunner()
    return runner.run_benchmark(algorithms, instances, **kwargs)


def save_benchmark_results(results: List[BenchmarkResult], filename: Optional[str] = None) -> None:
    """Backward compatible save function."""
    if filename is None:
        filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)


def load_benchmark_results(filename: str) -> List[BenchmarkResult]:
    """Backward compatible load function."""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return [BenchmarkResult.from_dict(d) for d in data]


def create_benchmark_report(results: List[BenchmarkResult], filename: Optional[str] = None) -> str:
    """Backward compatible report function."""
    output_dir = Path("results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    visualizer = BenchmarkVisualizer()
    report_path = visualizer.create_comprehensive_report(results, output_dir)
    
    if filename:
        # Copy to requested filename
        import shutil
        shutil.copy(report_path, filename)
        return filename
    
    return str(report_path)


# Export main classes and functions
__all__ = [
    'BenchmarkResult',
    'BenchmarkRunner', 
    'BenchmarkVisualizer',
    'run_benchmark',
    'save_benchmark_results',
    'load_benchmark_results',
    'create_benchmark_report',
    'OPTIMAL_VALUES'
]
=======

        # Gap with respect to known optimum
        if self.optimal_value:
            self.gap_to_optimal = (
                (self.best_fitness - self.optimal_value) / self.optimal_value * 100
            )

            # Success rate (solutions within 1% of optimum)
            threshold = self.optimal_value * 1.01
            successful_runs = sum(
                1 for fitness in self.fitness_values if fitness <= threshold
            )
            self.success_rate = successful_runs / len(self.fitness_values) * 100

        # Calculate average convergence curve
        # First ensure all curves have the same length
        if self.convergence_curves:
            min_length = min(len(curve) for curve in self.convergence_curves)
            standardized_curves = [
                curve[:min_length] for curve in self.convergence_curves
            ]
            self.avg_convergence = np.mean(standardized_curves, axis=0)

    def to_dict(self):
        """Convert results to dictionary for storage/serialization."""
        self.compute_metrics()

        result = {
            "algorithm": self.algorithm_name,
            "instance": self.instance_name,
            "optimal_value": self.optimal_value,
            "runs": len(self.fitness_values),
            "metrics": {
                "best_fitness": self.best_fitness,
                "worst_fitness": self.worst_fitness,
                "mean_fitness": self.mean_fitness,
                "std_fitness": self.std_fitness,
                "mean_time": self.mean_time,
                "std_time": self.std_time,
                "gap_to_optimal": self.gap_to_optimal,
                "success_rate": self.success_rate,
            },
            "detailed_results": {
                "fitness_values": self.fitness_values,
                "execution_times": self.execution_times,
            },
        }

        # We don't include convergence curves in the dictionary to avoid very large objects
        return result

    @classmethod
    def from_dict(cls, data):
        """Create a BenchmarkResult object from a dictionary."""
        result = cls(data["algorithm"], data["instance"])

        for i in range(data["runs"]):
            result.add_run(
                data["detailed_results"]["fitness_values"][i],
                data["detailed_results"]["execution_times"][i],
                [],  # Convergence curves are not stored in the dictionary
            )

        # Calculate metrics
        result.compute_metrics()
        return result


# Known optimal values for standard VRP instances
OPTIMAL_VALUES = {
    "A-n32-k5": 784,
    "P-n16-k8": 450,
    "E-n22-k4": 375,
    "B-n31-k5": 672,
    "E-n51-k5": 521,
}


def save_benchmark_results(results, filename=None):
    """
    Save benchmarking results to a JSON file.

    Args:
        results: List of BenchmarkResult objects
        filename: File name (if None, generated automatically)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/benchmark_{timestamp}.json"

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Convert results to dictionaries
    data = [result.to_dict() for result in results]

    # Save in JSON format
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    return filename


def load_benchmark_results(filename):
    """
    Load benchmarking results from a JSON file.

    Args:
        filename: Path to JSON file

    Returns:
        List of BenchmarkResult objects
    """
    with open(filename, "r") as f:
        data = json.load(f)

    # Convert dictionaries to BenchmarkResult objects
    results = [BenchmarkResult.from_dict(item) for item in data]
    return results


def run_benchmark(
    algorithms,
    problem_instances,
    runs=10,
    iterations=100,
    population=30,
    seed=None,
    parallel=False,
):
    """
    Execute a comparative benchmark of algorithms on problem instances.

    Args:
        algorithms: Dictionary of algorithms {name: class}
        problem_instances: List of VRP instances
        runs: Number of independent executions per combination
        iterations: Number of iterations per execution
        population: Population size for algorithms
        seed: Initial seed for reproducibility
        parallel: If True, execute in parallel

    Returns:
        List of BenchmarkResult objects
    """
    from problems.vrp import VRPProblem

    results = []

    # Configure parallel processing if enabled
    if parallel:
        pool = mp.Pool(
            processes=min(mp.cpu_count(), len(algorithms) * len(problem_instances))
        )
        tasks = []

    for instance_name in problem_instances:
        instance_path = f"data/vrp/{instance_name}.vrp"
        if not os.path.exists(instance_path):
            print(f"Error: Instance {instance_name} doesn't exist in data/vrp")
            continue

        problem = VRPProblem(instance_path)
        print(f"Benchmark for instance: {instance_name}")

        for algo_name, AlgoClass in algorithms.items():
            print(f"  Running {algo_name}...")
            benchmark_result = BenchmarkResult(algo_name, instance_name, runs)

            if parallel:
                # Add task to list for parallel execution
                for run in range(runs):
                    run_seed = seed + run if seed is not None else None
                    tasks.append(
                        (
                            AlgoClass,
                            problem,
                            population,
                            iterations,
                            run_seed,
                            benchmark_result,
                        )
                    )
            else:
                # Sequential execution
                for run in range(runs):
                    run_seed = seed + run if seed is not None else None
                    algo = AlgoClass(
                        problem,
                        population_size=population,
                        max_iterations=iterations,
                        seed=run_seed,
                    )

                    start_time = time.time()
                    best_solution = algo.execute()
                    execution_time = time.time() - start_time

                    # Handle both object-based and tuple-based returns
                    if hasattr(best_solution, 'fitness'):
                        # Object with fitness() method (HO, HHO, etc.)
                        fitness_value = best_solution.fitness()
                        convergence_curve = algo.get_convergence_curve()
                    else:
                        # Tuple return (PSO, GA)
                        if isinstance(best_solution, tuple):
                            _, fitness_value, convergence_curve = best_solution
                        else:
                            raise ValueError(f"Unexpected return type from {algo_name}")

                    benchmark_result.add_run(
                        fitness_value,
                        execution_time,
                        convergence_curve,
                    )

                    print(
                        f"    Run {run+1}/{runs}: Fitness = {fitness_value:.2f}, Time = {execution_time:.2f}s"
                    )

                benchmark_result.compute_metrics()
                results.append(benchmark_result)

                print(
                    f"  Best: {benchmark_result.best_fitness:.2f}, Average: {benchmark_result.mean_fitness:.2f}, "
                    + f"Time: {benchmark_result.mean_time:.2f}s"
                )
                if benchmark_result.optimal_value:
                    print(
                        f"  Gap to optimum: {benchmark_result.gap_to_optimal:.2f}%, "
                        + f"Success rate: {benchmark_result.success_rate:.2f}%"
                    )
                print()

    # Execute tasks in parallel if enabled
    if parallel and tasks:
        # Execute tasks in parallel using the module-level _run_algo_task function
        parallel_results = pool.map(_run_algo_task, tasks)
        pool.close()
        pool.join()

        # Agrupar los resultados por algoritmo e instancia
        task_index = 0
        for instance_name in problem_instances:
            for algo_name in algorithms:
                benchmark_result = BenchmarkResult(algo_name, instance_name, runs)

                for _ in range(runs):
                    fitness, exec_time, convergence = parallel_results[task_index]
                    benchmark_result.add_run(fitness, exec_time, convergence)
                    task_index += 1

                benchmark_result.compute_metrics()
                results.append(benchmark_result)

    return results


def plot_solution_quality(benchmark_results, title=None, show_optimal=True):
    """
    Visualiza la calidad de las soluciones obtenidas por diferentes algoritmos.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        title: Título para el gráfico
        show_optimal: Si es True, muestra el valor óptimo como línea de referencia
    """
    # Agrupar por instancia
    instances = {}
    for result in benchmark_results:
        if result.instance_name not in instances:
            instances[result.instance_name] = []
        instances[result.instance_name].append(result)

    # Crear gráficos para cada instancia
    n_instances = len(instances)
    fig, axes = plt.subplots(n_instances, 1, figsize=(12, 5 * n_instances))

    if n_instances == 1:
        axes = [axes]

    for i, (instance_name, results) in enumerate(instances.items()):
        ax = axes[i]

        # Datos para el boxplot
        data = []
        labels = []

        for result in results:
            data.append(result.fitness_values)
            labels.append(result.algorithm_name)

        # Crear boxplot
        bp = ax.boxplot(data, patch_artist=True, labels=labels)

        # Colorear cajas
        colors = list(mcolors.TABLEAU_COLORS.values())
        for j, box in enumerate(bp["boxes"]):
            box.set(facecolor=colors[j % len(colors)])

        # Mostrar valor óptimo si está disponible
        optimal = OPTIMAL_VALUES.get(instance_name)
        if show_optimal and optimal is not None:
            ax.axhline(y=optimal, color="r", linestyle="--", label=f"Óptimo: {optimal}")
            ax.legend()

        ax.set_title(f"Calidad de solución - {instance_name}")
        ax.set_ylabel("Fitness (Distancia)")
        ax.grid(True, linestyle="--", alpha=0.7)

    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)

    return plt


def plot_execution_time(benchmark_results, title=None):
    """
    Visualiza el tiempo de ejecución de diferentes algoritmos.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        title: Título para el gráfico
    """
    # Agrupar por instancia
    instances = {}
    for result in benchmark_results:
        if result.instance_name not in instances:
            instances[result.instance_name] = []
        instances[result.instance_name].append(result)

    # Crear gráficos para cada instancia
    n_instances = len(instances)
    fig, axes = plt.subplots(n_instances, 1, figsize=(12, 4 * n_instances))

    if n_instances == 1:
        axes = [axes]

    for i, (instance_name, results) in enumerate(instances.items()):
        ax = axes[i]

        # Datos para el gráfico de barras
        algorithms = []
        mean_times = []
        std_times = []

        for result in results:
            algorithms.append(result.algorithm_name)
            mean_times.append(result.mean_time)
            std_times.append(result.std_time)

        # Crear gráfico de barras
        x = np.arange(len(algorithms))
        bars = ax.bar(x, mean_times, yerr=std_times, alpha=0.7, capsize=5)

        # Colorear barras
        colors = list(mcolors.TABLEAU_COLORS.values())
        for j, bar in enumerate(bars):
            bar.set_color(colors[j % len(colors)])

        ax.set_title(f"Tiempo de ejecución - {instance_name}")
        ax.set_ylabel("Tiempo (segundos)")
        ax.set_xticks(x)
        ax.set_xticklabels(algorithms)
        ax.grid(True, linestyle="--", alpha=0.7, axis="y")

    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)

    return plt


def plot_convergence_comparison(benchmark_results, title=None):
    """
    Compara las curvas de convergencia de diferentes algoritmos.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        title: Título para el gráfico
    """
    # Agrupar por instancia
    instances = {}
    for result in benchmark_results:
        if result.instance_name not in instances:
            instances[result.instance_name] = []
        instances[result.instance_name].append(result)

    # Crear gráficos para cada instancia
    n_instances = len(instances)
    fig, axes = plt.subplots(n_instances, 1, figsize=(12, 5 * n_instances))

    if n_instances == 1:
        axes = [axes]

    for i, (instance_name, results) in enumerate(instances.items()):
        ax = axes[i]

        # Dibujar curvas de convergencia
        for result in results:
            if result.avg_convergence is not None:
                iterations = list(range(1, len(result.avg_convergence) + 1))
                ax.plot(
                    iterations,
                    result.avg_convergence,
                    linewidth=2,
                    label=result.algorithm_name,
                )

        # Mostrar valor óptimo si está disponible
        optimal = OPTIMAL_VALUES.get(instance_name)
        if optimal is not None:
            ax.axhline(y=optimal, color="r", linestyle="--", label=f"Óptimo: {optimal}")

        ax.set_title(f"Curvas de convergencia - {instance_name}")
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Fitness (Distancia)")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

    plt.tight_layout()

    if title:
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)

    return plt


def plot_performance_radar(benchmark_results, instance_name, metrics=None, title=None):
    """
    Crea un gráfico radar que compara el rendimiento de los algoritmos en varias métricas.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        instance_name: Nombre de la instancia a comparar
        metrics: Lista de métricas a comparar (por defecto: calidad, tiempo, estabilidad)
        title: Título para el gráfico
    """
    # Filtrar resultados por instancia
    results = [r for r in benchmark_results if r.instance_name == instance_name]
    if not results:
        return None

    if metrics is None:
        metrics = ["quality", "time", "stability", "success"]

    # Obtener datos normalizados para cada métrica
    n_metrics = len(metrics)

    # Ángulos para el gráfico radar
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el polígono

    # Crear figura
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Preparar datos para cada algoritmo
    for i, result in enumerate(results):
        values = []

        for metric in metrics:
            if metric == "quality":
                # Mejor fitness normalizado (menor es mejor, invertir la normalización)
                if result.optimal_value:
                    # Normalizar respecto al óptimo
                    value = result.optimal_value / result.best_fitness
                else:
                    # Normalizar respecto al mejor entre los algoritmos
                    best_fitness = min(r.best_fitness for r in results)
                    value = best_fitness / result.best_fitness
            elif metric == "time":
                # Tiempo normalizado (menor es mejor, invertir la normalización)
                min_time = min(r.mean_time for r in results)
                value = min_time / result.mean_time
            elif metric == "stability":
                # Estabilidad normalizada (menor desviación es mejor, invertir la normalización)
                if result.std_fitness == 0:
                    value = 1.0  # Perfecta estabilidad
                else:
                    min_std = min(max(0.001, r.std_fitness) for r in results)
                    value = min_std / max(0.001, result.std_fitness)
            elif metric == "success":
                # Tasa de éxito normalizada (mayor es mejor)
                if result.success_rate is not None:
                    value = result.success_rate / 100.0
                else:
                    value = 0.0
            else:
                value = 0.5  # Valor por defecto

            values.append(max(0, min(1, value)))  # Limitar entre 0 y 1

        # Cerrar el polígono
        values += values[:1]

        # Dibujar el polígono
        ax.plot(angles, values, linewidth=2, label=result.algorithm_name)
        ax.fill(angles, values, alpha=0.1)

    # Configurar el gráfico
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.capitalize() for m in metrics])
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])
    ax.set_ylim(0, 1)

    if title:
        ax.set_title(title)
    else:
        ax.set_title(f"Comparación de rendimiento - {instance_name}")

    ax.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))

    return plt


class BenchmarkReportBuilder:
    """Build benchmark reports with proper separation of concerns."""

    def __init__(self, benchmark_results):
        """Initialize with benchmark results."""
        self.results = benchmark_results
        self.instances = self._group_by_instance()

    def create_report(self, filename=None):
        """Create the benchmark report."""
        filename = self._prepare_filename(filename)

        # Create summary
        summary_df = self._create_summary_dataframe()

        # Generate visualizations
        figures_dir = self._prepare_figures_directory(filename)
        visualizations = self._generate_all_visualizations(figures_dir)

        # Build HTML
        html_content = self._build_html_report(summary_df, visualizations)

        # Save report
        self._save_report(filename, html_content)

        return filename

    def _prepare_filename(self, filename):
        """Prepare output filename."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results/benchmark_report_{timestamp}.html"

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        return filename

    def _group_by_instance(self):
        """Group results by instance name."""
        instances = {}
        for result in self.results:
            if result.instance_name not in instances:
                instances[result.instance_name] = []
            instances[result.instance_name].append(result)
        return instances

    def _create_summary_dataframe(self):
        """Create summary DataFrame from results."""
        summary_data = []

        for instance_name, results in self.instances.items():
            for result in results:
                summary_data.append(
                    {
                        "Instance": result.instance_name,
                        "Algorithm": result.algorithm_name,
                        "Best": f"{result.best_fitness:.2f}",
                        "Mean": f"{result.mean_fitness:.2f} ± {result.std_fitness:.2f}",
                        "Time (s)": f"{result.mean_time:.2f} ± {result.std_time:.2f}",
                        "Gap (%)": f"{result.gap_to_optimal:.2f}"
                        if result.gap_to_optimal is not None
                        else "N/A",
                        "Success (%)": f"{result.success_rate:.2f}"
                        if result.success_rate is not None
                        else "N/A",
                    }
                )

        return pd.DataFrame(summary_data)

    def _prepare_figures_directory(self, filename):
        """Prepare directory for figures."""
        figures_dir = os.path.join(os.path.dirname(filename), "figures")
        os.makedirs(figures_dir, exist_ok=True)
        return figures_dir

    def _generate_all_visualizations(self, figures_dir):
        """Generate all visualizations for the report."""
        visualizations = {}

        for instance_name, results in self.instances.items():
            instance_results = [
                r for r in self.results if r.instance_name == instance_name
            ]

            visualizations[instance_name] = self._generate_instance_visualizations(
                instance_name, instance_results, figures_dir
            )

        return visualizations

    def _generate_instance_visualizations(self, instance_name, results, figures_dir):
        """Generate visualizations for a single instance."""
        viz = {}

        # Solution quality
        viz["quality"] = self._save_plot(
            plot_solution_quality(results), figures_dir, f"{instance_name}_quality.png"
        )

        # Execution time
        viz["time"] = self._save_plot(
            plot_execution_time(results), figures_dir, f"{instance_name}_time.png"
        )

        # Convergence
        viz["convergence"] = self._save_plot(
            plot_convergence_comparison(results),
            figures_dir,
            f"{instance_name}_convergence.png",
        )

        # Performance radar
        plt_radar = plot_performance_radar(results, instance_name)
        if plt_radar:
            viz["radar"] = self._save_plot(
                plt_radar, figures_dir, f"{instance_name}_radar.png"
            )

        return viz

    def _save_plot(self, plt_obj, figures_dir, filename):
        """Save a plot and return the filename."""
        path = os.path.join(figures_dir, filename)
        plt_obj.savefig(path)
        plt_obj.close()
        return filename

    def _build_html_report(self, summary_df, visualizations):
        """Build the HTML report content."""
        html = self._get_html_header()
        html += self._get_summary_section(summary_df)

        # Add instance sections
        for instance_name in self.instances:
            html += self._get_instance_section(
                instance_name, visualizations.get(instance_name, {})
            )

        # Add statistical analysis
        html += self._get_statistical_analysis_section()

        html += "</body>\n</html>"
        return html

    def _get_html_header(self):
        """Get HTML header with CSS."""
        css = self._get_css_styles()
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <style>
{css}
    </style>
</head>
<body>
    <h1>Benchmark Report</h1>
    <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

    def _get_css_styles(self):
        """Get CSS styles for the report."""
        return """body {
    font-family: "Arial", sans-serif;
    margin: 20px;
    line-height: 1.6;
}
h1, h2, h3 {
    color: #2c3e50;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 20px;
}
th, td {
    text-align: left;
    padding: 8px;
    border: 1px solid #ddd;
}
th {
    background-color: #f2f2f2;
}
tr:nth-child(even) {
    background-color: #f9f9f9;
}
.section {
    margin-bottom: 30px;
}
.figure {
    margin: 20px 0;
    text-align: center;
}
.figure img {
    max-width: 100%;
    height: auto;
}
.caption {
    margin-top: 10px;
    font-style: italic;
    color: #666;
}
.highlight {
    font-weight: bold;
    color: #e74c3c;
}"""

    def _get_summary_section(self, summary_df):
        """Get HTML for summary section."""
        return f"""
    <div class="section">
        <h2>Summary</h2>
        {summary_df.to_html(index=False)}
    </div>
"""

    def _get_instance_section(self, instance_name, visualizations):
        """Get HTML for instance section."""
        html = f"""
    <div class="section">
        <h2>Instance: {instance_name}</h2>
        <p>Optimal value: {OPTIMAL_VALUES.get(instance_name, 'Unknown')}</p>
"""

        # Add visualizations
        if "quality" in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['quality']}" alt="Solution Quality">
            <div class="caption">Figure: Solution quality comparison for {instance_name}</div>
        </div>
"""

        if "time" in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['time']}" alt="Execution Time">
            <div class="caption">Figure: Execution time comparison for {instance_name}</div>
        </div>
"""

        if "convergence" in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['convergence']}" alt="Convergence Curves">
            <div class="caption">Figure: Convergence curve comparison for {instance_name}</div>
        </div>
"""

        if "radar" in visualizations:
            html += f"""
        <div class="figure">
            <img src="figures/{visualizations['radar']}" alt="Performance Radar">
            <div class="caption">Figure: Performance radar chart for {instance_name}</div>
        </div>
"""

        html += "    </div>"
        return html

    def _get_statistical_analysis_section(self):
        """Get HTML for statistical analysis section."""
        if len(self.results) == 0:
            return ""

        html = """
    <div class="section">
        <h2>Statistical Analysis</h2>
"""

        # Perform statistical tests for each instance
        for instance_name, results in self.instances.items():
            if len(results) >= 2:
                html += self._perform_statistical_tests(instance_name, results)

        html += "    </div>"
        return html

    def _perform_statistical_tests(self, instance_name, results):
        """Perform statistical tests for an instance."""
        html = f"<h3>Statistical tests for {instance_name}</h3>"

        # Prepare data
        algorithm_names = [r.algorithm_name for r in results]
        samples = [r.fitness_values for r in results]

        # Ensure equal sample sizes
        min_samples = min(len(s) for s in samples)
        samples = [s[:min_samples] for s in samples]

        if min_samples >= 5 and len(samples) >= 2:
            # Friedman test
            friedman_html = self._perform_friedman_test(samples, algorithm_names)
            if friedman_html:
                html += friedman_html

        return html

    def _perform_friedman_test(self, samples, algorithm_names):
        """Perform Friedman test and return HTML."""
        try:
            friedman_samples = [list(s) for s in samples]
            statistic, p_value = friedmanchisquare(*friedman_samples)

            html = f"""<p>Friedman Test</p>
<table>
    <tr><th>Statistic</th><th>p-value</th><th>Interpretation</th></tr>
    <tr>
        <td>{statistic:.4f}</td>
        <td>{p_value:.4f}</td>
        <td>{"Significant differences exist" if p_value < 0.05 else "No significant differences"}</td>
    </tr>
</table>
"""

            # Post-hoc tests if significant
            if p_value < 0.05 and len(samples) > 2:
                html += self._perform_posthoc_tests(samples, algorithm_names)

            return html

        except Exception as e:
            return f"<p>Error performing Friedman test: {str(e)}</p>"

    def _perform_posthoc_tests(self, samples, algorithm_names):
        """Perform post-hoc tests."""
        html = "<p>Post-hoc Wilcoxon Signed-Rank Tests</p>"
        html += """<table>
    <tr><th>Algorithm A</th><th>Algorithm B</th><th>p-value</th><th>Interpretation</th></tr>
"""

        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                try:
                    stat, p = wilcoxon(samples[i], samples[j])
                    html += f"""    <tr>
        <td>{algorithm_names[i]}</td>
        <td>{algorithm_names[j]}</td>
        <td>{p:.4f}</td>
        <td>{"Significant difference" if p < 0.05 else "No significant difference"}</td>
    </tr>
"""
                except Exception:
                    pass

        html += "</table>"
        return html

    def _save_report(self, filename, html_content):
        """Save the HTML report."""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)


# Note: create_summary_dataframe is defined at the top of the file


def create_benchmark_report(benchmark_results, filename=None):
    """
    Crea un informe detallado de los resultados del benchmark.

    Versión refactorizada que utiliza BenchmarkReportBuilder para reducir
    la complejidad ciclomática de 17 a menos de 10.

    Args:
        benchmark_results: Lista de objetos BenchmarkResult
        filename: Ruta donde guardar el informe (si es None, se genera automáticamente)
    """
    builder = BenchmarkReportBuilder(benchmark_results)
    return builder.create_report(filename)


def run_massive_benchmark(
    algorithms,
    instances,
    runs=1000,
    iterations=100,
    population_size=40,
    output_dir="massive_benchmark",
    num_workers=None,
    checkpoint_interval=50,
    resume=True,
    optimize_instances=None,
):
    """
    Execute massive benchmark with checkpoint support.

    Args:
        algorithms: List of algorithm classes or names
        instances: List of instance names
        runs: Number of runs per algorithm-instance pair
        iterations: Number of iterations per run
        population_size: Population size
        output_dir: Output directory
        num_workers: Number of parallel workers
        checkpoint_interval: Save checkpoint every N runs
        resume: Resume from checkpoint if available
        optimize_instances: Optional list of instances to optimize

    Returns:
        List of BenchmarkResult objects
    """
    # Imports ya realizados al inicio del archivo
    from datetime import datetime

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_path / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)

    # Checkpoint file
    checkpoint_file = output_path / "benchmark_state.pkl.gz"

    # Initialize results and completed tasks
    all_results = []
    completed_tasks = set()

    # Load checkpoint if resuming
    if resume and checkpoint_file.exists():
        try:
            logger.info(f"Loading checkpoint from {checkpoint_file}")
            with gzip.open(checkpoint_file, "rb") as f:
                checkpoint_data = pickle.load(f)
            all_results = checkpoint_data["results"]
            completed_tasks = set(checkpoint_data["completed_tasks"])
            logger.info(f"Resumed {len(completed_tasks)} completed tasks")
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")

    # Prepare tasks
    tasks = []
    for algo_name, algo_class in algorithms.items():
        for instance in instances:
            for run_id in range(runs):
                task_id = f"{algo_name}_{instance}_run{run_id}"
                if task_id not in completed_tasks:
                    tasks.append((algo_name, algo_class, instance, run_id, task_id))

    logger.info(f"Total tasks to run: {len(tasks)}")

    if not tasks:
        logger.info("All tasks already completed!")
        return all_results

    # Run tasks
    num_workers = num_workers or mp.cpu_count()
    checkpoint_counter = 0

    def save_checkpoint():
        """Save current state to checkpoint file."""
        checkpoint_data = {
            "results": all_results,
            "completed_tasks": list(completed_tasks),
            "timestamp": datetime.now().isoformat(),
            "total_runs": runs,
            "algorithms": [
                a.__name__ if hasattr(a, "__name__") else a for a in algorithms
            ],
            "instances": instances,
        }
        with gzip.open(checkpoint_file, "wb") as f:
            pickle.dump(checkpoint_data, f)
        logger.debug(f"Checkpoint saved: {len(completed_tasks)} tasks completed")

    # Initial checkpoint
    save_checkpoint()

    # Process tasks
    checkpoint_counter = 0
    with tqdm(total=len(tasks), desc="Running massive benchmark") as pbar:
        for algo_name, algo_class, instance, run_id, task_id in tasks:
            try:
                # Run single benchmark
                result = run_benchmark(
                    algorithms={algo_name: algo_class},
                    problem_instances=[instance],
                    runs=1,  # Single run at a time
                    iterations=iterations,
                    population=population_size,
                    seed=None,  # Will be randomized for each run
                    parallel=False,
                )

                if result:
                    all_results.extend(result)
                    completed_tasks.add(task_id)

                    # Save individual result
                    result_file = checkpoint_dir / f"{task_id}.pkl"
                    with open(result_file, "wb") as f:
                        pickle.dump(result[0], f)

            except Exception as e:
                logger.error(f"Error in task {task_id}: {e}")

            pbar.update(1)
            checkpoint_counter += 1

            # Save checkpoint periodically
            if checkpoint_counter >= checkpoint_interval:
                save_checkpoint()
                checkpoint_counter = 0

    # Final checkpoint
    save_checkpoint()

    # Create summary CSV
    summary_path = output_path / "massive_benchmark_summary.csv"
    create_summary_dataframe(all_results).to_csv(summary_path, index=False)

    logger.info(f"Massive benchmark completed. Results saved to {output_path}")
    return all_results


# QC-DVRP Extensions (migrated from qc_dvrp_benchmarking.py)
# =========================================================

# Extended optimal values including Solomon instances
QC_OPTIMAL_VALUES = OPTIMAL_VALUES.copy()
QC_OPTIMAL_VALUES.update(
    {
        "Solomon-RC101": 1696.94,  # Best known solution
        "Solomon-RC102": 1554.75,
        "Solomon-RC103": 1261.67,
        "Solomon-RC104": 1135.48,
        "Solomon-RC105": 1629.44,
        "Solomon-RC106": 1424.73,
        "Solomon-RC107": 1230.48,
        "Solomon-RC108": 1139.82,
    }
)
>>>>>>> develop
