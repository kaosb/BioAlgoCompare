"""
Test backward compatibility with existing code.
"""

import pytest
import numpy as np
from problems import VRPProblem, ContinuousAdapter
from algorithms.woa_v2 import WOAV2
import tempfile
import os


def test_vrp_still_works():
    """Test that VRPProblem continues to work as before."""
    # Create a temporary VRP file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vrp', delete=False) as f:
        f.write("""NAME : test
COMMENT : Test instance
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 0
3 20 0
4 30 0
5 40 0
DEMAND_SECTION
1 0
2 10
3 20
4 15
5 25
DEPOT_SECTION
1
-1
EOF""")
        temp_file = f.name
    
    try:
        # Create VRPProblem as before
        vrp = VRPProblem(temp_file)
        
        # Test properties
        assert vrp.get_dimension() > 0
        assert vrp.get_lower_bounds() is not None
        assert vrp.get_upper_bounds() is not None
        
        # Test with algorithm
        algo = WOAV2(vrp, population_size=20, max_iterations=30)
        best = algo.execute()
        
        # Should find a solution
        assert best.fitness() > 0
        
    finally:
        os.unlink(temp_file)


def test_continuous_adapter_transparency():
    """Test that ContinuousAdapter is transparent for algorithms."""
    from problems import SphereProblem
    
    # Create a continuous problem
    sphere = SphereProblem(dimension=10)
    
    # Adapt it
    adapted = ContinuousAdapter(sphere)
    
    # Both should work with algorithms
    algo1 = WOAV2(sphere, population_size=20, max_iterations=30)
    algo2 = WOAV2(adapted, population_size=20, max_iterations=30, seed=42)
    
    # Reset seed for fair comparison
    algo1 = WOAV2(sphere, population_size=20, max_iterations=30, seed=42)
    
    best1 = algo1.execute()
    best2 = algo2.execute()
    
    # Results should be identical (same seed)
    assert best1.fitness() == pytest.approx(best2.fitness())


def test_mixed_usage():
    """Test using old and new problems together."""
    from problems import SphereProblem, RastriginProblem
    
    # Create temporary VRP file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vrp', delete=False) as f:
        f.write("""NAME : test
COMMENT : Test instance
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 0
3 20 0
4 30 0
5 40 0
DEMAND_SECTION
1 0
2 10
3 20
4 15
5 25
DEPOT_SECTION
1
-1
EOF""")
        temp_file = f.name
    
    try:
        # Mix of old and new problems
        problems = [
            VRPProblem(temp_file),  # Old
            ContinuousAdapter(SphereProblem(dimension=10)),  # New adapted
            ContinuousAdapter(RastriginProblem(dimension=10))  # New adapted
        ]
        
        # All should work with algorithms
        for problem in problems:
            algo = WOAV2(problem, population_size=10, max_iterations=10)
            best = algo.execute()
            assert best.fitness() >= 0
            
    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])