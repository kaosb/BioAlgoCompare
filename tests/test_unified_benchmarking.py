"""
Test for unified benchmarking module.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from utils.benchmarking import (
    BenchmarkResult,
    BenchmarkRunner,
    BenchmarkVisualizer,
    save_benchmark_results,
    load_benchmark_results,
    OPTIMAL_VALUES
)


def test_benchmark_result_basic():
    """Test BenchmarkResult basic functionality."""
    result = BenchmarkResult(
        algorithm_name="TestAlgo",
        instance_name="E-n22-k4"
    )
    
    # Check optimal value is loaded
    assert result.optimal_value == OPTIMAL_VALUES["E-n22-k4"]
    
    # Add some runs
    for i in range(5):
        result.add_run(
            fitness=380 + i,
            execution_time=1.0 + i * 0.1,
            convergence_curve=[400 - j for j in range(10)],
            solution=f"solution_{i}"
        )
    
    # Compute metrics
    result.compute_metrics()
    
    assert result.runs == 5
    assert result.best_fitness == 380
    assert result.worst_fitness == 384
    assert result.mean_fitness == 382
    assert result.median_fitness == 382
    assert abs(result.std_fitness - 1.414) < 0.01
    assert result.gap_to_optimal == (380 - 375) / 375 * 100


def test_benchmark_result_serialization():
    """Test BenchmarkResult serialization/deserialization."""
    result = BenchmarkResult(
        algorithm_name="TestAlgo",
        instance_name="P-n16-k8"
    )
    
    # Add data
    result.add_run(455, 1.5, [500, 480, 460, 455])
    result.compute_metrics()
    
    # Convert to dict and back
    data = result.to_dict()
    restored = BenchmarkResult.from_dict(data)
    
    assert restored.algorithm_name == result.algorithm_name
    assert restored.instance_name == result.instance_name
    assert restored.best_fitness == result.best_fitness
    assert restored.fitness_values == result.fitness_values


def test_benchmark_runner_initialization():
    """Test BenchmarkRunner initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(
            output_dir=tmpdir,
            parallel=False,
            checkpoint_interval=10
        )
        
        assert runner.output_dir == Path(tmpdir)
        assert not runner.parallel
        assert runner.checkpoint_interval == 10
        
        # Check log file was created
        assert (runner.output_dir / "benchmark.log").exists()


def test_save_load_results():
    """Test saving and loading benchmark results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test results
        results = []
        for algo in ["Algo1", "Algo2"]:
            result = BenchmarkResult(algo, "Test-Instance")
            result.add_run(100 + np.random.rand(), 1.0, [])
            result.compute_metrics()
            results.append(result)
        
        # Save results
        filename = Path(tmpdir) / "test_results.json"
        save_benchmark_results(results, str(filename))
        
        # Load results
        loaded = load_benchmark_results(str(filename))
        
        assert len(loaded) == 2
        assert loaded[0].algorithm_name == "Algo1"
        assert loaded[1].algorithm_name == "Algo2"


def test_summary_dataframe_creation():
    """Test creation of summary DataFrame."""
    results = []
    
    # Create some test results
    for algo in ["HOA", "FOA", "EWA"]:
        result = BenchmarkResult(algo, "E-n22-k4")
        
        # Add some runs with different fitness values
        base_fitness = {"HOA": 380, "FOA": 390, "EWA": 385}[algo]
        for i in range(10):
            result.add_run(
                fitness=base_fitness + np.random.normal(0, 2),
                execution_time=1.0 + np.random.normal(0, 0.1),
                convergence_curve=[]
            )
        
        result.compute_metrics()
        results.append(result)
    
    # Create summary DataFrame
    df = BenchmarkRunner.create_summary_dataframe(results)
    
    # Check structure
    assert len(df) == 3
    assert set(df.columns) >= {'Algorithm', 'Instance', 'Best', 'Mean', 'Std'}
    assert list(df['Algorithm']) == ["HOA", "FOA", "EWA"]
    assert all(df['Instance'] == "E-n22-k4")


if __name__ == "__main__":
    test_benchmark_result_basic()
    test_benchmark_result_serialization()
    test_benchmark_runner_initialization()
    test_save_load_results()
    test_summary_dataframe_creation()
    print("All tests passed!")