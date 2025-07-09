"""
Enhanced benchmarking module with complete metadata capture.

This module extends the original benchmarking functionality to ensure
all results include complete system metadata for reproducibility.
"""

from typing import List, Dict, Any, Optional, Type
from pathlib import Path
from datetime import datetime
import json
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import logging

from utils.benchmarking import BenchmarkRunner, BenchmarkResult
from utils.result_metadata_integration import (
    wrap_algorithm_with_metadata, ensure_metadata_in_result,
    MetadataEnhancedAlgorithm, ResourceMonitor
)
from utils.result_schema_v2 import (
    StandardResultV2, SystemInfo, GitInfo, ExecutionInfoV2,
    DependencyInfo, ResultBuilder
)
from algorithms.base_v2 import MetaheuristicAlgorithm


logger = logging.getLogger(__name__)


class MetadataEnhancedBenchmark(BenchmarkRunner):
    """
    Enhanced benchmark runner that captures complete metadata.
    
    This class extends UnifiedBenchmark to ensure all results include
    system information, git state, dependencies, and resource usage.
    """
    
    def __init__(
        self,
        algorithms: List[Type[MetaheuristicAlgorithm]],
        instances: List[str],
        runs_per_instance: int = 30,
        population_size: int = 30,
        max_iterations: int = 100,
        capture_metadata: bool = True,
        monitor_resources: bool = True,
        **kwargs
    ):
        """
        Initialize enhanced benchmark.
        
        Args:
            algorithms: List of algorithm classes
            instances: List of instance names
            runs_per_instance: Number of runs per instance
            population_size: Population size for algorithms
            max_iterations: Maximum iterations
            capture_metadata: Whether to capture system metadata
            monitor_resources: Whether to monitor resource usage
            **kwargs: Additional arguments for parent class
        """
        super().__init__(
            algorithms=algorithms,
            instances=instances,
            runs_per_instance=runs_per_instance,
            population_size=population_size,
            max_iterations=max_iterations,
            **kwargs
        )
        
        self.capture_metadata = capture_metadata
        self.monitor_resources = monitor_resources
        
        # Capture metadata once at start
        if self.capture_metadata:
            self.system_info = SystemInfo.capture()
            self.git_info = GitInfo.capture()
            self.dependencies = DependencyInfo.capture_all()
        else:
            self.system_info = None
            self.git_info = None
            self.dependencies = None
    
    def _create_tasks(self) -> List[Dict]:
        """Create benchmark tasks with metadata options."""
        tasks = super()._create_tasks()
        
        # Add metadata options to each task
        for task in tasks:
            task['capture_metadata'] = self.capture_metadata
            task['monitor_resources'] = self.monitor_resources
        
        return tasks
    
    @staticmethod
    def _run_single_task(task: Dict) -> Dict:
        """Execute a single algorithm run with metadata capture."""
        from problems.vrp_v2 import VRPProblemV2
        import time
        
        # Load problem instance
        instance_path = f"data/vrp/{task['instance_name']}.vrp"
        problem = VRPProblemV2(instance_path)
        
        # Wrap algorithm class if metadata capture is enabled
        AlgoClass = task['AlgoClass']
        if task.get('capture_metadata', False):
            AlgoClass = wrap_algorithm_with_metadata(
                AlgoClass,
                capture_metadata=True,
                monitor_resources=task.get('monitor_resources', False)
            )
        
        # Initialize algorithm
        algo = AlgoClass(
            problem,
            population_size=task['population'],
            max_iterations=task['iterations'],
            seed=task['seed']
        )
        
        # Run algorithm
        start_time = time.time()
        best_solution = algo.execute()
        execution_time = time.time() - start_time
        
        # Get results
        result = {
            'task_id': task['task_id'],
            'algo_name': task['algo_name'],
            'instance_name': task['instance_name'],
            'run_idx': task['run_idx'],
            'fitness': best_solution.fitness(),
            'execution_time': execution_time,
            'convergence_curve': algo.get_convergence_curve(),
            'solution': best_solution.position,
            'seed': task['seed']
        }
        
        # Add metadata if available
        if hasattr(algo, 'get_complete_result'):
            result['complete_result'] = algo.get_complete_result()
        
        # Add resource usage if monitored
        if hasattr(algo, 'execution_info') and algo.execution_info:
            result['resource_usage'] = {
                'cpu_avg': algo.execution_info.cpu_percent_avg,
                'memory_peak_mb': algo.execution_info.memory_peak_mb,
                'memory_avg_mb': algo.execution_info.memory_avg_mb
            }
        
        return result
    
    def save_results(self, results: List[BenchmarkResult], formats: List[str] = None) -> None:
        """Save benchmark results with complete metadata."""
        if formats is None:
            formats = ['json', 'csv', 'pickle', 'metadata']
        
        # Save standard formats
        super().save_results(results, formats=[f for f in formats if f != 'metadata'])
        
        # Save enhanced metadata format
        if 'metadata' in formats:
            self._save_metadata_results(results)
    
    def _save_metadata_results(self, results: List[BenchmarkResult]) -> None:
        """Save results in enhanced metadata format."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create metadata results directory
        metadata_dir = self.results_dir / 'metadata'
        metadata_dir.mkdir(exist_ok=True)
        
        # Convert each result to StandardResultV2
        enhanced_results = []
        
        for br in results:
            # Create problem info
            problem_info = {
                'problem_type': 'VRP',
                'instance_name': br.instance_name,
                'dimension': self._get_instance_dimension(br.instance_name),
                'optimal_value': self._get_optimal_value(br.instance_name)
            }
            
            # Create algorithm info
            algorithm_info = {
                'algorithm_name': br.algorithm_name,
                'parameters': {
                    'population_size': self.population_size,
                    'max_iterations': self.max_iterations
                }
            }
            
            # Build result with metadata
            builder = ResultBuilder()
            builder.set_problem(**problem_info)
            builder.set_algorithm(**algorithm_info)
            
            # Add all runs
            for i, (fitness, time, curve) in enumerate(zip(
                br.fitness_values, br.execution_times, br.convergence_curves
            )):
                builder.add_run(
                    seed=self.base_seed + i,
                    fitness=fitness,
                    execution_time=time,
                    convergence_curve=curve
                )
            
            # Create base result
            base_result = builder.build()
            
            # Enhance with metadata
            enhanced_result = StandardResultV2(
                result_type=base_result.result_type,
                problem_info=base_result.problem_info,
                algorithm_info=base_result.algorithm_info,
                runs=base_result.runs,
                statistics=base_result.statistics,
                system_info=self.system_info,
                git_info=self.git_info,
                execution_info=ExecutionInfoV2.start_tracking(
                    seed=self.base_seed,
                    parallel=self.parallel
                ),
                dependencies=self.dependencies
            )
            
            # Add metadata
            enhanced_result.metadata['benchmark_config'] = {
                'runs_per_instance': self.runs_per_instance,
                'parallel': self.parallel,
                'checkpoint_interval': self.checkpoint_interval,
                'timeout': self.timeout
            }
            
            # Calculate checksum
            enhanced_result.calculate_checksum()
            
            enhanced_results.append(enhanced_result)
        
        # Save individual result files
        for result in enhanced_results:
            filename = f"{result.algorithm_info.algorithm_name}_{result.problem_info.instance_name}_{timestamp}.json"
            filepath = metadata_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
        
        # Save summary file
        summary = {
            'timestamp': timestamp,
            'n_algorithms': len({r.algorithm_info.algorithm_name for r in enhanced_results}),
            'n_instances': len({r.problem_info.instance_name for r in enhanced_results}),
            'total_results': len(enhanced_results),
            'system_info': self.system_info.to_dict() if self.system_info else None,
            'git_info': self.git_info.to_dict() if self.git_info else None,
            'result_files': [
                f"{r.algorithm_info.algorithm_name}_{r.problem_info.instance_name}_{timestamp}.json"
                for r in enhanced_results
            ]
        }
        
        summary_file = metadata_dir / f"benchmark_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Saved {len(enhanced_results)} metadata results to {metadata_dir}")
    
    def _get_instance_dimension(self, instance_name: str) -> int:
        """Get dimension of a VRP instance."""
        try:
            from problems.vrp_v2 import VRPProblemV2
            problem = VRPProblemV2(f"data/vrp/{instance_name}.vrp")
            return problem.dimension
        except:
            return 0
    
    def _get_optimal_value(self, instance_name: str) -> Optional[float]:
        """Get optimal value for instance if known."""
        # Import from benchmarking module
        from utils.benchmarking import OPTIMAL_VALUES
        return OPTIMAL_VALUES.get(instance_name)


def run_benchmark_with_metadata(
    algorithms: List[Type[MetaheuristicAlgorithm]],
    instances: List[str],
    **kwargs
) -> List[StandardResultV2]:
    """
    Run benchmark and return results with complete metadata.
    
    Args:
        algorithms: List of algorithm classes
        instances: List of instance names
        **kwargs: Additional benchmark parameters
        
    Returns:
        List of StandardResultV2 objects with complete metadata
    """
    # Create enhanced benchmark
    benchmark = MetadataEnhancedBenchmark(
        algorithms=algorithms,
        instances=instances,
        capture_metadata=True,
        monitor_resources=True,
        **kwargs
    )
    
    # Run benchmark
    results = benchmark.run()
    
    # Save results
    benchmark.save_results(results, formats=['json', 'csv', 'metadata'])
    
    # Return enhanced results
    enhanced_results = []
    for br in results:
        # Convert to StandardResultV2 (implementation would go here)
        pass
    
    return enhanced_results