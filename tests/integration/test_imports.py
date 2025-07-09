"""Integration tests for module imports and exports.

This module tests that all algorithms and utilities can be properly imported
as documented in the package.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestModuleImports:
    """Test suite for module import functionality."""

    def test_import_base_classes(self):
        """Test importing base classes."""
        from algorithms import Individual, MetaheuristicAlgorithm

        assert Individual is not None
        assert MetaheuristicAlgorithm is not None

    def test_import_individual_algorithms(self):
        """Test importing individual algorithm classes."""
        # Test direct imports
        from algorithms import AHA, APO, EGTO, EWA, FGO, FOA, FSA, GTO, GVOA
        from algorithms import HHO, HOA, MRFO, OPA, RRO, SHO, SMA, SMO, WOA

        # Verify all imports succeeded
        algorithms = [
            AHA,
            APO,
            EGTO,
            EWA,
            FGO,
            FOA,
            FSA,
            GTO,
            GVOA,
            HHO,
            HOA,
            MRFO,
            OPA,
            RRO,
            SHO,
            SMA,
            SMO,
            WOA,
        ]

        for algo in algorithms:
            assert algo is not None
            assert hasattr(algo, "__name__")

    def test_import_individual_classes(self):
        """Test importing Individual classes."""
        from algorithms import (
            Hummingbird,
            Protozoa,
            EnhancedGorilla,
            Earthworm,
            Fossa,
            Gorilla,
            Vulture,
            Hawk,
            MantaRay,
            Orca,
            Raven,
            SlimeMould,
            Starling,
            Whale,
        )

        # Note: Flamingo and Hyena have multiple versions
        from algorithms import FlamingoFGO, FlamingoFSA, HyenaHOA, HyenaSHO

        individuals = [
            Hummingbird,
            Protozoa,
            EnhancedGorilla,
            Earthworm,
            Fossa,
            Gorilla,
            Vulture,
            Hawk,
            MantaRay,
            Orca,
            Raven,
            SlimeMould,
            Starling,
            Whale,
            FlamingoFGO,
            FlamingoFSA,
            HyenaHOA,
            HyenaSHO,
        ]

        for ind_class in individuals:
            assert ind_class is not None
            assert hasattr(ind_class, "__name__")

    def test_import_utilities(self):
        """Test importing utility functions and constants."""
        from algorithms import ALGORITHMS, get_algorithm

        assert ALGORITHMS is not None
        assert isinstance(ALGORITHMS, dict)
        assert len(ALGORITHMS) > 0

        assert get_algorithm is not None
        assert callable(get_algorithm)

    def test_algorithms_registry_content(self):
        """Test ALGORITHMS registry contains all expected algorithms."""
        from algorithms import ALGORITHMS

        expected_algorithms = [
            "aha",
            "apo",
            "egto",
            "ewa",
            "fgo",
            "foa",
            "fsa",
            "gto",
            "gvoa",
            "hho",
            "hoa",
            "mrfo",
            "opa",
            "rro",
            "sho",
            "sma",
            "smo",
            "woa",
            "hyena",
            "flamingo",
        ]

        for algo_name in expected_algorithms:
            assert algo_name in ALGORITHMS, f"{algo_name} not in ALGORITHMS registry"

    def test_get_algorithm_function(self):
        """Test get_algorithm utility function."""
        from algorithms import get_algorithm, ALGORITHMS

        # Test case insensitive retrieval
        test_cases = [
            ("ewa", "ewa"),
            ("EWA", "ewa"),
            ("Ewa", "ewa"),
            ("FOA", "foa"),
            ("Opa", "opa"),
        ]

        for input_name, expected_key in test_cases:
            AlgoClass = get_algorithm(input_name)
            assert (
                AlgoClass == ALGORITHMS[expected_key]
            ), f"get_algorithm('{input_name}') returned wrong class"

    def test_get_algorithm_error_handling(self):
        """Test get_algorithm error handling."""
        from algorithms import get_algorithm

        # Test invalid algorithm name
        with pytest.raises(ValueError) as excinfo:
            get_algorithm("nonexistent")

        error_msg = str(excinfo.value)
        assert "Algorithm 'nonexistent' not found" in error_msg
        assert "Available:" in error_msg

        # Should list available algorithms
        assert "ewa" in error_msg.lower()
        assert "foa" in error_msg.lower()

    def test_algorithm_aliases(self):
        """Test algorithm aliases work correctly."""
        from algorithms import ALGORITHMS

        # Test aliases
        assert ALGORITHMS["hyena"] == ALGORITHMS["sho"]
        assert ALGORITHMS["flamingo"] == ALGORITHMS["fsa"]

    def test_import_from_submodules(self):
        """Test importing directly from algorithm submodules."""
        # Test a few representative algorithms
        from algorithms.ewa import EWA, Earthworm
        from algorithms.opa import OPA, Orca
        from algorithms.sma import SMA, SlimeMould

        assert EWA is not None
        assert Earthworm is not None
        assert OPA is not None
        assert Orca is not None
        assert SMA is not None
        assert SlimeMould is not None

    def test_all_exports(self):
        """Test __all__ exports are correct."""
        import algorithms

        # Check __all__ exists
        assert hasattr(algorithms, "__all__")

        # Check all items in __all__ can be imported
        for item_name in algorithms.__all__:
            assert hasattr(
                algorithms, item_name
            ), f"{item_name} in __all__ but not importable"

    def test_problem_imports(self):
        """Test importing problem classes."""
        from problems.vrp import VRPProblem

        assert VRPProblem is not None
        assert hasattr(VRPProblem, "load_instance")
        assert hasattr(VRPProblem, "evaluate")

    def test_utility_imports(self):
        """Test importing utility modules."""
        # Test statistical analysis
        from utils.statistical_analysis import StatisticalAnalysis

        assert StatisticalAnalysis is not None

        # Test benchmarking
        from utils.benchmarking import BenchmarkResult, create_benchmark_report

        assert BenchmarkResult is not None
        assert create_benchmark_report is not None

        # Test visualization
        from utils.visualization import plot_vrp_solution, plot_convergence

        assert plot_vrp_solution is not None
        assert plot_convergence is not None

    def test_circular_imports(self):
        """Test for circular import issues."""
        # This should not raise any errors
        import algorithms
        import algorithms.base
        import algorithms.ewa
        import algorithms.opa

        # Re-import should work
        import algorithms
        from algorithms import EWA, OPA

        assert True  # If we get here, no circular import issues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
