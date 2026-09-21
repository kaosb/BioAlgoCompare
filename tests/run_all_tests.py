#!/usr/bin/env python3
"""Test runner script for BioAlgoCompare test suite.

This script runs all tests and generates a summary report.
"""
import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_test_suite():
    """Run the complete test suite."""
    print("=" * 70)
    print("BioAlgoCompare Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Test categories
    test_categories = [
        (
            "Unit Tests",
            [
                "unit/test_algorithm_initialization.py",
                "unit/test_algorithm_interface.py",
                "unit/test_algorithm_convergence_all.py",
            ],
        ),
        ("Integration Tests", ["integration/test_imports.py"]),
        ("Functional Tests", ["functional/test_reproducibility.py"]),
        ("Documentation Tests", ["documentation/test_documentation_examples.py"]),
    ]

    total_passed = 0
    total_failed = 0
    results = []

    for category_name, test_files in test_categories:
        print(f"\n{category_name}")
        print("-" * len(category_name))

        for test_file in test_files:
            test_path = os.path.join(os.path.dirname(__file__), test_file)
            if not os.path.exists(test_path):
                print(f"  ⚠️  {test_file} - NOT FOUND")
                continue

            # Run pytest on the file
            result = pytest.main(
                [
                    test_path,
                    "-v",
                    "--tb=short",
                    "-m",
                    "not slow",  # Skip slow tests by default
                    "--color=yes",
                ]
            )

            if result == 0:
                print(f"  ✅ {test_file} - PASSED")
                total_passed += 1
            else:
                print(f"  ❌ {test_file} - FAILED")
                total_failed += 1

            results.append((test_file, result))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total test modules: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")

    # Detailed results
    if total_failed > 0:
        print("\n⚠️  Failed tests:")
        for test_file, result in results:
            if result != 0:
                print(f"  - {test_file}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return total_failed == 0


def run_specific_category(category):
    """Run tests for a specific category."""
    categories = {
        "unit": "unit/",
        "integration": "integration/",
        "functional": "functional/",
        "documentation": "documentation/",
        "performance": "performance/",
        "robustness": "robustness/",
        "statistical": "statistical/",
    }

    if category not in categories:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return False

    test_dir = os.path.join(os.path.dirname(__file__), categories[category])
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        return False

    print(f"Running {category} tests...")
    result = pytest.main([test_dir, "-v", "--tb=short", "-m", "not slow"])
    return result == 0


def run_slow_tests():
    """Run tests marked as slow."""
    print("Running slow tests (this may take a while)...")
    result = pytest.main([os.path.dirname(__file__), "-v", "--tb=short", "-m", "slow"])
    return result == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "slow":
            success = run_slow_tests()
        else:
            success = run_specific_category(sys.argv[1])
    else:
        success = run_test_suite()

    sys.exit(0 if success else 1)
