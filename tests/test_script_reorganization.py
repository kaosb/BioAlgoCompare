"""
Test script reorganization.
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_script_structure():
    """Test that the new script structure is correct."""
    scripts_dir = project_root / "scripts"
    
    # Check main directories exist
    assert (scripts_dir / "config").exists()
    assert (scripts_dir / "core").exists()
    assert (scripts_dir / "utilities").exists()
    assert (scripts_dir / "deprecated").exists()
    
    # Check __init__.py files
    assert (scripts_dir / "__init__.py").exists()
    assert (scripts_dir / "config" / "__init__.py").exists()
    assert (scripts_dir / "core" / "__init__.py").exists()
    assert (scripts_dir / "utilities" / "__init__.py").exists()
    
    # Check key files are in correct locations
    assert (scripts_dir / "config" / "algorithms.py").exists()
    assert (scripts_dir / "core" / "analyze.py").exists()
    assert (scripts_dir / "core" / "run.py").exists()
    assert (scripts_dir / "core" / "benchmark.py").exists()
    
    # Check utilities
    assert (scripts_dir / "utilities" / "clean.py").exists()
    assert (scripts_dir / "utilities" / "inventory.py").exists()
    assert (scripts_dir / "utilities" / "manage_datasets.py").exists()
    assert (scripts_dir / "utilities" / "migrate_algorithm.py").exists()
    
    # Check deprecated
    assert (scripts_dir / "deprecated" / "run").exists()


def test_algorithm_config_import():
    """Test that algorithm config can be imported."""
    try:
        from scripts.config.algorithms import ALGORITHMS
        assert isinstance(ALGORITHMS, dict)
        assert len(ALGORITHMS) > 0
        assert "hoa" in ALGORITHMS
        assert "foa" in ALGORITHMS
    except ImportError as e:
        pytest.fail(f"Failed to import algorithm config: {e}")


def test_main_entry_point():
    """Test that main entry point exists and is executable."""
    bioalgo_path = project_root / "bioalgo"
    assert bioalgo_path.exists()
    assert os.access(bioalgo_path, os.X_OK), "bioalgo script is not executable"


def test_module_docstrings():
    """Test that all modules have proper docstrings."""
    modules_to_check = [
        "scripts",
        "scripts.config",
        "scripts.core",
        "scripts.utilities"
    ]
    
    for module_name in modules_to_check:
        module = __import__(module_name, fromlist=[''])
        assert module.__doc__ is not None, f"{module_name} missing docstring"
        assert len(module.__doc__.strip()) > 10, f"{module_name} docstring too short"


if __name__ == "__main__":
    test_script_structure()
    test_algorithm_config_import()
    test_main_entry_point()
    test_module_docstrings()
    print("All reorganization tests passed!")