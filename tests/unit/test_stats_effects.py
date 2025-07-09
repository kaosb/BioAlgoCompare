#!/usr/bin/env python3
"""
Unit tests for statistical effect size calculations.
"""

import pytest
import numpy as np
import pandas as pd
from utils.stats_effects import (
    vargha_delaney_a12,
    cliff_delta,
    interpret_a12,
    interpret_cliff_delta,
    calculate_pairwise_effect_sizes,
    effect_size_vs_best,
)


class TestVarghaDelaneyA12:
    """Test Vargha-Delaney A12 effect size calculation."""

    def test_identical_samples(self):
        """Test A12 for identical samples should be 0.5."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 2, 3, 4, 5])
        assert vargha_delaney_a12(x, y) == 0.5

    def test_x_always_smaller(self):
        """Test A12 when x is always smaller than y."""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        assert vargha_delaney_a12(x, y) == 1.0

    def test_y_always_smaller(self):
        """Test A12 when y is always smaller than x."""
        x = np.array([4, 5, 6])
        y = np.array([1, 2, 3])
        assert vargha_delaney_a12(x, y) == 0.0

    def test_overlapping_samples(self):
        """Test A12 for overlapping samples."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([3, 4, 5, 6, 7])
        a12 = vargha_delaney_a12(x, y)
        assert 0.0 < a12 < 1.0
        # x tends to be smaller, so A12 should be > 0.5
        assert a12 > 0.5

    def test_with_ties(self):
        """Test A12 with tied values."""
        x = np.array([1, 2, 3, 3, 4])
        y = np.array([2, 3, 3, 4, 5])
        a12 = vargha_delaney_a12(x, y)
        # Should handle ties correctly
        assert 0.3 < a12 < 0.7


class TestCliffDelta:
    """Test Cliff's delta effect size calculation."""

    def test_identical_samples(self):
        """Test Cliff's delta for identical samples should be 0."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 2, 3, 4, 5])
        assert cliff_delta(x, y) == 0.0

    def test_x_dominates(self):
        """Test Cliff's delta when x dominates (all x < y)."""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        # For minimization, x < y means positive delta
        assert cliff_delta(x, y) == 1.0

    def test_y_dominates(self):
        """Test Cliff's delta when y dominates (all y < x)."""
        x = np.array([4, 5, 6])
        y = np.array([1, 2, 3])
        # For minimization, y < x means negative delta
        assert cliff_delta(x, y) == -1.0

    def test_partial_overlap(self):
        """Test Cliff's delta with partial overlap."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([3, 4, 5, 6, 7])
        delta = cliff_delta(x, y)
        # x tends to be smaller, so delta should be positive
        assert 0 < delta < 1


class TestInterpretations:
    """Test effect size interpretation functions."""

    def test_interpret_a12_negligible(self):
        """Test A12 interpretation for negligible effect."""
        assert interpret_a12(0.5) == "negligible"
        assert interpret_a12(0.52) == "negligible"
        assert interpret_a12(0.48) == "negligible"

    def test_interpret_a12_small(self):
        """Test A12 interpretation for small effect."""
        assert interpret_a12(0.58) == "small"
        assert interpret_a12(0.42) == "small"

    def test_interpret_a12_medium(self):
        """Test A12 interpretation for medium effect."""
        assert interpret_a12(0.65) == "medium"
        assert interpret_a12(0.35) == "medium"

    def test_interpret_a12_large(self):
        """Test A12 interpretation for large effect."""
        assert interpret_a12(0.75) == "large"
        assert interpret_a12(0.25) == "large"

    def test_interpret_cliff_negligible(self):
        """Test Cliff's delta interpretation for negligible effect."""
        assert interpret_cliff_delta(0.0) == "negligible"
        assert interpret_cliff_delta(0.1) == "negligible"
        assert interpret_cliff_delta(-0.1) == "negligible"

    def test_interpret_cliff_small(self):
        """Test Cliff's delta interpretation for small effect."""
        assert interpret_cliff_delta(0.2) == "small"
        assert interpret_cliff_delta(-0.2) == "small"

    def test_interpret_cliff_medium(self):
        """Test Cliff's delta interpretation for medium effect."""
        assert interpret_cliff_delta(0.4) == "medium"
        assert interpret_cliff_delta(-0.4) == "medium"

    def test_interpret_cliff_large(self):
        """Test Cliff's delta interpretation for large effect."""
        assert interpret_cliff_delta(0.6) == "large"
        assert interpret_cliff_delta(-0.6) == "large"


class TestPairwiseEffectSizes:
    """Test pairwise effect size calculations."""

    @pytest.fixture
    def sample_data(self):
        """Create sample benchmark data."""
        data = []
        np.random.seed(42)

        # Create data for 3 algorithms on 5 instances
        algorithms = ["A", "B", "C"]
        instances = ["inst1", "inst2", "inst3", "inst4", "inst5"]

        # Algorithm A: best performance (values around 100)
        for inst in instances:
            for _ in range(5):  # 5 runs per instance
                data.append(
                    {
                        "Algorithm": "A",
                        "Instance": inst,
                        "Value": np.random.normal(100, 5),
                    }
                )

        # Algorithm B: medium performance (values around 120)
        for inst in instances:
            for _ in range(5):
                data.append(
                    {
                        "Algorithm": "B",
                        "Instance": inst,
                        "Value": np.random.normal(120, 8),
                    }
                )

        # Algorithm C: worst performance (values around 150)
        for inst in instances:
            for _ in range(5):
                data.append(
                    {
                        "Algorithm": "C",
                        "Instance": inst,
                        "Value": np.random.normal(150, 10),
                    }
                )

        return pd.DataFrame(data)

    def test_calculate_pairwise_effect_sizes(self, sample_data):
        """Test pairwise effect size calculation."""
        results = calculate_pairwise_effect_sizes(sample_data)

        # Check structure
        assert "a12" in results
        assert "cliff" in results

        # Check diagonal (self-comparison)
        for algo in ["A", "B", "C"]:
            assert results["a12"].loc[algo, algo] == 0.5
            assert results["cliff"].loc[algo, algo] == 0.0

        # Check that A dominates B and C
        assert results["a12"].loc["A", "B"] > 0.5
        assert results["a12"].loc["A", "C"] > 0.5
        assert results["cliff"].loc["A", "B"] > 0
        assert results["cliff"].loc["A", "C"] > 0

        # Check symmetry properties
        # A12(X,Y) + A12(Y,X) should equal 1
        assert (
            abs(results["a12"].loc["A", "B"] + results["a12"].loc["B", "A"] - 1.0)
            < 0.001
        )

        # Cliff(X,Y) should equal -Cliff(Y,X)
        assert (
            abs(results["cliff"].loc["A", "B"] + results["cliff"].loc["B", "A"]) < 0.001
        )

    def test_effect_size_vs_best(self, sample_data):
        """Test effect size calculation vs best algorithm."""
        results = effect_size_vs_best(sample_data)

        # Check structure
        assert "Algorithm" in results.columns
        assert "A12" in results.columns
        assert "Cliff_delta" in results.columns
        assert "Is_best" in results.columns

        # Algorithm A should be best
        best_row = results[results["Is_best"]]
        assert len(best_row) == 1
        assert best_row["Algorithm"].iloc[0] == "A"

        # Effect sizes for best algorithm should be 0.5/0.0
        assert best_row["A12"].iloc[0] == 0.5
        assert best_row["Cliff_delta"].iloc[0] == 0.0

        # Other algorithms should have A12 > 0.5 (best dominates them)
        other_algos = results[~results["Is_best"]]
        assert all(other_algos["A12"] > 0.5)
        assert all(other_algos["Cliff_delta"] > 0)


class TestEffectSizeEdgeCases:
    """Test edge cases in effect size calculations."""

    def test_empty_samples(self):
        """Test handling of empty samples."""
        x = np.array([])
        y = np.array([1, 2, 3])

        # Should handle gracefully (return 0.5 or raise)
        with pytest.raises(ZeroDivisionError):
            vargha_delaney_a12(x, y)

    def test_single_value_samples(self):
        """Test with single-value samples."""
        x = np.array([5])
        y = np.array([10])

        assert vargha_delaney_a12(x, y) == 1.0
        assert cliff_delta(x, y) == 1.0

    def test_large_samples(self):
        """Test with large samples for performance."""
        np.random.seed(42)
        x = np.random.normal(100, 10, 1000)
        y = np.random.normal(110, 10, 1000)

        # Should complete in reasonable time
        a12 = vargha_delaney_a12(x, y)
        delta = cliff_delta(x, y)

        # x should tend to be smaller than y
        assert a12 > 0.5
        assert delta > 0
