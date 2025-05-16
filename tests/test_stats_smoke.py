"""
Smoke test for the advanced statistical analysis module.
Creates a minimal dataset and verifies that the analysis runs successfully.
"""
import os
import pandas as pd
import numpy as np
import pytest
from utils.advanced_statistical_analysis import run_all as run_stats

def test_statistical_analysis_smoke(tmp_path):
    """
    Create a mini test CSV with 2 algorithms and 2 instances, 
    then run the statistical analysis and verify the output files exist.
    """
    # Create a test dataset
    np.random.seed(42)  # For reproducible tests
    
    # Generate a small dataset (3 algorithms x 5 instances)
    algos = ["algo1", "algo2", "algo3"]
    instances = ["inst1", "inst2", "inst3", "inst4", "inst5"]
    
    data = []
    for algo in algos:
        # algo1 will be consistently better than algo2, which is better than algo3
        if algo == "algo1":
            base_fitness = 50   # Much better
        elif algo == "algo2":
            base_fitness = 200  # Worse
        else:  # algo3
            base_fitness = 350  # Much worse
        
        for inst in instances:
            # Add some random variation
            fitness = base_fitness + np.random.normal(0, 10, 5)
            
            for i, f in enumerate(fitness):
                data.append({
                    "Algorithm": algo,
                    "Instance": inst,
                    "Run": i + 1,
                    "Best Fitness": f,
                    "Execution Time (s)": np.random.uniform(1, 5)
                })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV in temporary directory
    csv_path = os.path.join(tmp_path, "test_benchmark.csv")
    df.to_csv(csv_path, index=False)
    
    # Create output directory
    out_dir = os.path.join(tmp_path, "stats_output")
    os.makedirs(out_dir, exist_ok=True)
    
    # Run the analysis
    results = run_stats(csv_path, out_dir)
    
    # Check that there was no error
    assert "error" not in results, f"Error in statistical analysis: {results.get('error', 'Unknown error')}"
    
    # Check that the output files exist
    assert os.path.exists(os.path.join(out_dir, "cd_diagram.png")), "CD diagram not created"
    assert os.path.exists(os.path.join(out_dir, "stats_report.md")), "Stats report not created"
    
    # Check that the results dict contains the expected keys
    expected_keys = ["friedman_p", "nemenyi", "a12", "cd_diagram", "report"]
    for key in expected_keys:
        assert key in results, f"Missing expected key in results: {key}"
    
    # Verify that the p-value is a float and critical distance exists
    assert isinstance(results["friedman_p"], float), "p-value is not a float"
    assert "critical_distance" in results, "Critical distance not in results"
    
    # Because we designed algo1 to be better than algo2, expect a significant result
    assert results["friedman_p"] < 0.05, "Expected significant p-value but got nonsignificant"
    
    # Check that the A12 effect size shows algo1 as better than algo2 and algo3
    if not results["a12"].empty:
        a12_value1vs2 = results["a12"].loc["algo1", "algo2"]
        a12_value1vs3 = results["a12"].loc["algo1", "algo3"]
        a12_value2vs3 = results["a12"].loc["algo2", "algo3"]

        assert a12_value1vs2 > 0.5, f"Expected A12 > 0.5 for algo1 vs algo2 but got {a12_value1vs2}"
        assert a12_value1vs3 > 0.5, f"Expected A12 > 0.5 for algo1 vs algo3 but got {a12_value1vs3}"
        assert a12_value2vs3 > 0.5, f"Expected A12 > 0.5 for algo2 vs algo3 but got {a12_value2vs3}"
    
    # Don't return results, assert all checks have passed

def test_commandline_integration():
    """
    Test that the stats command is properly integrated into the CLI.
    """
    # Since the @click.command decorator transforms the function signature,
    # we need to check the existence of the command in the CLI

    from scripts.analyze import cli

    # Check that the "stats" command exists in the CLI
    commands = [cmd.name for cmd in cli.commands.values()]
    assert "stats" in commands, "Stats command not found in CLI"
