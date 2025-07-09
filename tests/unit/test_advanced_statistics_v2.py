#!/usr/bin/env python3
"""
Unit tests for advanced statistical analysis v2 with corrected CD.
"""

import pytest
import numpy as np
import pandas as pd
import os
import tempfile
from scipy.stats import friedmanchisquare
from statsmodels.stats.libqsturng import qsturng

# Import the module to test
from utils.advanced_statistical_analysis_v2 import (
    aligned_friedman_test,
    quade_test,
    create_cd_diagram,
    get_software_versions,
    run_all_v2,
)


class TestCriticalDistance:
    """Test critical distance calculation corrections."""

    def test_cd_calculation_k5_n10(self):
        """Test CD calculation for k=5 algorithms, n=10 instances."""
        # Create synthetic data
        np.random.seed(42)
        data = []

        algorithms = ["A", "B", "C", "D", "E"]
        instances = [f"inst{i}" for i in range(10)]

        # Create data with clear differences
        base_values = {"A": 100, "B": 110, "C": 120, "D": 130, "E": 140}

        for inst in instances:
            for algo in algorithms:
                data.append(
                    {
                        "Algorithm": algo,
                        "Instance": inst,
                        "Value": np.random.normal(base_values[algo], 5),
                    }
                )

        df = pd.DataFrame(data)

        # Run Friedman test
        results = aligned_friedman_test(df, alpha=0.05)

        # Check CD calculation
        k = 5  # algorithms
        n = 10  # instances
        alpha = 0.05

        # Correct formula: q_alpha/sqrt(2) * sqrt(k(k+1)/(6n))
        q_alpha_raw = qsturng(1 - alpha, k, np.inf)
        q_alpha_corrected = q_alpha_raw / np.sqrt(2)
        expected_cd = q_alpha_corrected * np.sqrt((k * (k + 1)) / (6 * n))

        assert abs(results["critical_distance"] - expected_cd) < 0.001
        assert results["q_alpha"] == q_alpha_corrected

        # CD should be around 1.51 for k=5, n=10, alpha=0.05
        assert 1.4 < results["critical_distance"] < 1.6

    def test_cd_calculation_k8_n5(self):
        """Test CD calculation for k=8 algorithms, n=5 instances."""
        # This is the case mentioned in the requirements
        np.random.seed(42)
        data = []

        algorithms = ["A", "B", "C", "D", "E", "F", "G", "H"]
        instances = [f"inst{i}" for i in range(5)]

        for inst in instances:
            for algo in algorithms:
                data.append(
                    {
                        "Algorithm": algo,
                        "Instance": inst,
                        "Value": np.random.normal(100, 10),
                    }
                )

        df = pd.DataFrame(data)
        results = aligned_friedman_test(df, alpha=0.05)

        # CD should be around 5.4 (not 6.64)
        assert 5.2 < results["critical_distance"] < 5.6


class TestAlignedFriedman:
    """Test aligned Friedman test implementation."""

    def test_aligned_friedman_basic(self):
        """Test basic functionality of aligned Friedman test."""
        # Create data with clear algorithm differences
        data = []
        algorithms = ["A", "B", "C"]
        instances = ["inst1", "inst2", "inst3", "inst4"]

        # A is best, B is medium, C is worst
        values = {"A": 10, "B": 20, "C": 30}

        for inst in instances:
            for algo in algorithms:
                data.append(
                    {
                        "Algorithm": algo,
                        "Instance": inst,
                        "Value": values[algo] + np.random.normal(0, 1),
                    }
                )

        df = pd.DataFrame(data)
        results = aligned_friedman_test(df)

        # Check results structure
        assert "friedman_p" in results
        assert "statistic" in results
        assert "mean_ranks" in results
        assert "critical_distance" in results
        assert "test_type" in results
        assert results["test_type"] == "aligned_friedman"

        # Check that we detect significant differences
        assert results["friedman_p"] < 0.05
        assert results["reject_h0"] is True

        # Check ranking order
        ranks = results["mean_ranks"]
        assert ranks["A"] < ranks["B"] < ranks["C"]

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        # Only one instance
        df = pd.DataFrame(
            [
                {"Algorithm": "A", "Instance": "inst1", "Value": 10},
                {"Algorithm": "B", "Instance": "inst1", "Value": 20},
            ]
        )

        results = aligned_friedman_test(df)
        assert "error" in results
        assert results["friedman_p"] == 1.0


class TestQuadeTest:
    """Test Quade test implementation."""

    def test_quade_basic(self):
        """Test basic Quade test functionality."""
        # Create data
        data = []
        algorithms = ["A", "B", "C"]
        instances = [f"inst{i}" for i in range(10)]

        # Create data with varying ranges per instance
        for i, inst in enumerate(instances):
            # Vary the range of values per instance
            range_mult = 1 + i * 0.5
            for algo in algorithms:
                base = {"A": 10, "B": 15, "C": 20}[algo]
                data.append(
                    {
                        "Algorithm": algo,
                        "Instance": inst,
                        "Value": base * range_mult + np.random.normal(0, 0.5),
                    }
                )

        df = pd.DataFrame(data)
        results = quade_test(df)

        # Check results structure
        assert "quade_p" in results
        assert "statistic" in results
        assert "mean_ranks" in results
        assert "critical_distance" in results
        assert "test_type" in results
        assert results["test_type"] == "quade"

        # Should detect differences
        assert results["quade_p"] < 0.05
        assert results["reject_h0"] is True


class TestCDDiagram:
    """Test critical difference diagram generation."""

    def test_cd_diagram_creation(self):
        """Test that CD diagram is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test data
            ranks = np.array([1.5, 2.8, 3.2, 4.5])
            names = ["Algo1", "Algo2", "Algo3", "Algo4"]
            cd = 1.5

            output_file = os.path.join(tmpdir, "cd_test.png")

            # Create diagram
            result = create_cd_diagram(ranks, names, cd, output_file)

            # Check file was created
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0


class TestSoftwareVersions:
    """Test software version tracking."""

    def test_get_software_versions(self):
        """Test software version information collection."""
        versions = get_software_versions()

        # Check required fields
        assert "python" in versions
        assert "numpy" in versions
        assert "pandas" in versions
        assert "scipy" in versions
        assert "platform" in versions
        assert "timestamp" in versions

        # Check format
        assert "." in versions["python"]  # Should be like "3.x.x"
        assert "." in versions["numpy"]  # Should be like "1.x.x"


class TestRunAllV2:
    """Test the complete analysis pipeline."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file for testing."""
        data = []
        np.random.seed(42)

        algorithms = ["EGTO", "FOA", "WOA", "HHO", "SMA"]
        instances = ["E-n22-k4", "P-n16-k8", "A-n32-k5", "B-n31-k5", "E-n51-k5"]

        # Create realistic data
        base_performance = {"EGTO": 100, "FOA": 105, "WOA": 110, "HHO": 108, "SMA": 115}

        for _ in range(30):  # 30 runs
            for inst in instances:
                for algo in algorithms:
                    data.append(
                        {
                            "Algorithm": algo,
                            "Instance": inst,
                            "Best": np.random.normal(base_performance[algo], 5),
                            "Time": np.random.uniform(1, 10),
                        }
                    )

        df = pd.DataFrame(data)
        csv_file = tmp_path / "test_results.csv"
        df.to_csv(csv_file, index=False)

        return str(csv_file)

    def test_run_all_basic(self, sample_csv, tmp_path):
        """Test basic run_all_v2 functionality."""
        output_dir = str(tmp_path / "results")

        results = run_all_v2(sample_csv, output_dir)

        # Check no errors
        assert "error" not in results

        # Check main results
        assert "friedman_p" in results
        assert "critical_distance" in results
        assert "mean_ranks" in results
        assert "nemenyi" in results
        assert "effect_sizes_vs_best" in results

        # Check files created
        assert os.path.exists(os.path.join(output_dir, "stats_report.md"))
        assert os.path.exists(os.path.join(output_dir, "cd_diagram.png"))
        assert os.path.exists(os.path.join(output_dir, "effect_sizes.csv"))
        assert os.path.exists(os.path.join(output_dir, "software_versions.json"))

    def test_run_all_extended(self, sample_csv, tmp_path):
        """Test run_all_v2 with extended tests."""
        output_dir = str(tmp_path / "results_extended")

        results = run_all_v2(sample_csv, output_dir, extended_tests=True)

        # Check Quade test was run
        assert "quade_results" in results
        assert "quade_p" in results["quade_results"]

    def test_run_all_no_versions(self, sample_csv, tmp_path):
        """Test run_all_v2 without saving versions."""
        output_dir = str(tmp_path / "results_no_versions")

        results = run_all_v2(sample_csv, output_dir, save_versions=False)

        # Check version file was not created
        assert not os.path.exists(os.path.join(output_dir, "software_versions.json"))


class TestReportGeneration:
    """Test report generation functionality."""

    def test_report_content(self, tmp_path):
        """Test that generated reports contain expected content."""
        # Create mock results
        results = {
            "software_versions": {"python": "3.9.0", "numpy": "1.21.0"},
            "summary_stats": pd.DataFrame(
                [
                    {
                        "Algorithm": "A",
                        "Mean": 100,
                        "SD": 5,
                        "Median": 99,
                        "Min": 90,
                        "Max": 110,
                        "IQR": 8,
                    },
                    {
                        "Algorithm": "B",
                        "Mean": 110,
                        "SD": 6,
                        "Median": 109,
                        "Min": 95,
                        "Max": 120,
                        "IQR": 10,
                    },
                ]
            ),
            "friedman_results": {
                "friedman_p": 0.001,
                "statistic": 15.2,
                "reject_h0": True,
                "critical_distance": 1.5,
                "q_alpha": 2.8,
                "alpha": 0.05,
                "n_algorithms": 2,
                "n_instances": 10,
                "test_type": "aligned_friedman",
            },
            "mean_ranks": {"A": 1.2, "B": 1.8},
            "effect_sizes_vs_best": pd.DataFrame(
                [
                    {
                        "Algorithm": "A",
                        "A12": 0.5,
                        "A12_interpretation": "negligible",
                        "Cliff_delta": 0.0,
                        "Cliff_interpretation": "negligible",
                        "Is_best": True,
                    },
                    {
                        "Algorithm": "B",
                        "A12": 0.75,
                        "A12_interpretation": "large",
                        "Cliff_delta": 0.5,
                        "Cliff_interpretation": "large",
                        "Is_best": False,
                    },
                ]
            ),
        }

        # Import function and generate report
        from utils.advanced_statistical_analysis_v2 import (
            generate_extended_stats_report,
        )

        report_file = str(tmp_path / "test_report.md")
        generate_extended_stats_report(results, report_file)

        # Check report content
        with open(report_file, "r") as f:
            content = f.read()

        # Check key sections exist
        assert "# Extended Statistical Analysis Report" in content
        assert "## Software Environment" in content
        assert "## Summary Statistics" in content
        assert "## Friedman Test Results" in content
        assert "## Algorithm Rankings" in content
        assert "## Effect Sizes vs Best Algorithm" in content
        assert "## Conclusions" in content

        # Check specific values
        assert "p-value: 0.001000" in content
        assert "Critical difference: 1.5000" in content
        assert "Best performing algorithm: A" in content
