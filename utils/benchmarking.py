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


@dataclass
class BenchmarkResult:
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
            
        self.best_fitness = min(self.fitness_values)
        self.worst_fitness = max(self.fitness_values)
        self.mean_fitness = np.mean(self.fitness_values)
        self.std_fitness = np.std(self.fitness_values)
        self.median_fitness = np.median(self.fitness_values)
        
        self.mean_time = np.mean(self.execution_times)
        self.std_time = np.std(self.execution_times)
        
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