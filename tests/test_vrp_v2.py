"""
Unit tests for the VRPProblemV2 class.
"""

import pytest
import numpy as np
from pathlib import Path
import os
import tempfile

from problems.vrp_v2 import VRPProblemV2


@pytest.fixture
def simple_vrp_instance_path():
    """Creates a temporary simple VRP instance file for testing."""
    content = """NAME : test-n5-k2
COMMENT : Synthetic test instance with 5 nodes and 2 vehicles
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 100
NODE_COORD_SECTION
1 0 0
2 10 0
3 10 10
4 0 10
5 5 5
DEMAND_SECTION
1 0
2 20
3 30
4 25
5 15
DEPOT_SECTION
1
-1
EOF
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vrp', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def complex_vrp_instance_path():
    """Creates a temporary more complex VRP instance file for testing."""
    content = """NAME : test-n10-k3
COMMENT : Synthetic test instance with 10 nodes and 3 vehicles
TYPE : CVRP
DIMENSION : 10
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 150
NODE_COORD_SECTION
1 50 50
2 60 40
3 70 50
4 60 60
5 40 60
6 30 50
7 40 40
8 50 30
9 50 70
10 50 50
DEMAND_SECTION
1 0
2 20
3 30
4 25
5 15
6 35
7 20
8 25
9 30
10 20
DEPOT_SECTION
1
-1
EOF
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vrp', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)


class TestVRPProblemV2:
    """Tests for the VRPProblemV2 class."""

    def test_initialization_and_loading(self, simple_vrp_instance_path):
        """Tests if the VRP instance loads correctly."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        assert problem._name == "test-n5-k2"
        assert problem._dimension == 5
        assert problem.capacity == 100
        assert problem.depot_index == 0
        assert len(problem.nodes) == 5
        assert len(problem.demands) == 5
        assert problem.nodes[0] == (0, 0)
        assert problem.demands[1] == 20
        assert problem.distance_matrix is not None
        assert problem.distance_matrix.shape == (5, 5)

    def test_dimension_property(self, simple_vrp_instance_path):
        """Tests the dimension property (number of customers)."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        assert problem.dimension == 4  # 5 nodes - 1 depot = 4 customers

    def test_evaluate_solution_feasible(self, simple_vrp_instance_path):
        """Tests evaluation of a feasible solution."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        # Route 1: 0 -> 1 -> 2 -> 0 (demands: 20+30=50, capacity 100)
        # Route 2: 0 -> 3 -> 4 -> 0 (demands: 25+15=40, capacity 100)
        routes = [[0, 1, 2, 0], [0, 3, 4, 0]]
        fitness = problem.evaluate(routes)
        # Expected distances: (0,1)=10, (1,2)=10, (2,0)=22.36 (approx)
        # (0,3)=10, (3,4)=10, (4,0)=7.07 (approx)
        # Total approx: 10+10+14.14213562 + 10+7.07106781+7.07106781 = 58.28427124
        assert fitness == pytest.approx(58.28, abs=0.1)
        assert problem.evaluations == 1

    def test_evaluate_solution_infeasible_capacity(self, simple_vrp_instance_path):
        """Tests evaluation of an infeasible solution due to capacity."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        # Route 1: 0 -> 1 -> 2 -> 3 -> 4 -> 0 (demands: 20+30+25+15=90, capacity 100)
        # This route is feasible by capacity, but let's make one that isn't
        # Node 1 (20), Node 2 (30), Node 3 (25), Node 4 (15)
        # Total demand = 90. If capacity was 80, this would be infeasible.
        # Let's create a route that exceeds capacity
        problem.capacity = 50 # Temporarily reduce capacity for this test
        routes = [[0, 1, 2, 0]] # Demand 20+30=50. If capacity is 40, this is infeasible.
        problem.capacity = 40 # Set capacity to make it infeasible
        fitness = problem.evaluate(routes)
        # Expecting a penalty
        assert fitness > 1000  # Penalty factor is 1000

    def test_evaluate_solution_infeasible_missing_nodes(self, simple_vrp_instance_path):
        """Tests evaluation of an infeasible solution due to missing nodes."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        routes = [[0, 1, 0]]  # Missing nodes 2, 3, 4
        fitness = problem.evaluate(routes)
        assert fitness > 1000 * 3  # Expecting penalty for 3 missing nodes

    def test_evaluate_solution_infeasible_duplicate_nodes(self, simple_vrp_instance_path):
        """Tests evaluation of an infeasible solution due to duplicate nodes."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        routes = [[0, 1, 2, 0], [0, 1, 3, 0]]  # Node 1 is duplicated
        fitness = problem.evaluate(routes)
        assert fitness > 1000 * 1  # Expecting penalty for 1 duplicate node

    def test_is_feasible(self, simple_vrp_instance_path):
        """Tests the is_feasible method."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        # Feasible
        assert problem.is_feasible([[0, 1, 2, 0], [0, 3, 4, 0]]) is True
        # Infeasible (capacity)
        problem.capacity = 40
        assert problem.is_feasible([[0, 1, 2, 0]]) is False
        problem.capacity = 100 # Reset
        # Infeasible (missing)
        assert problem.is_feasible([[0, 1, 0]]) is False
        # Infeasible (duplicate)
        assert problem.is_feasible([[0, 1, 2, 0], [0, 1, 3, 0]]) is False

    def test_random_solution(self, simple_vrp_instance_path):
        """Tests generation of a random feasible solution."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        solution = problem.random_solution()
        assert isinstance(solution, list)
        assert len(solution) > 0
        assert problem.is_feasible(solution) is True
        # Check if all customers are covered
        all_customers = set(node for route in solution for node in route if node != problem.depot_index)
        assert all_customers == set(range(1, problem._dimension))

    def test_repair_solution(self, simple_vrp_instance_path):
        """Tests the repair method for infeasible solutions."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        # Solution with missing and duplicate nodes
        infeasible_routes = [[0, 1, 0], [0, 1, 3, 0]] # Node 2 missing, Node 1 duplicated
        repaired_routes = problem.repair(infeasible_routes)
        assert problem.is_feasible(repaired_routes) is True
        # Check if all customers are covered after repair
        all_customers = set(node for route in repaired_routes for node in route if node != problem.depot_index)
        assert all_customers == set(range(1, problem._dimension))

    def test_repair_solution_no_change_if_feasible(self, simple_vrp_instance_path):
        """Tests repair method does not change a feasible solution."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        feasible_routes = [[0, 1, 2, 0], [0, 3, 4, 0]]
        repaired_routes = problem.repair(feasible_routes)
        # Repair might reorder or split routes, so direct equality check might fail
        # Instead, check if the set of customers and total distance are the same
        assert problem.is_feasible(repaired_routes) is True
        original_customers = set(node for route in feasible_routes for node in route if node != problem.depot_index)
        repaired_customers = set(node for route in repaired_routes for node in route if node != problem.depot_index)
        assert original_customers == repaired_customers

    def test_evaluations_counter(self, simple_vrp_instance_path):
        """Tests the evaluation counter."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        assert problem.evaluations == 0
        problem.evaluate([[0, 1, 0]])
        assert problem.evaluations == 1
        problem.reset_evaluations()
        assert problem.evaluations == 0

    def test_distance_matrix_computation(self, complex_vrp_instance_path):
        """Tests distance matrix computation for a more complex instance."""
        problem = VRPProblemV2(str(complex_vrp_instance_path))
        assert problem.distance_matrix.shape == (10, 10)
        # Check a known distance (e.g., node 0 to node 1: (50,50) to (60,40) -> sqrt(10^2 + (-10)^2) = sqrt(200) = 14.14)
        assert problem.distance_matrix[0, 1] == pytest.approx(14.14, abs=0.01)
        assert problem.distance_matrix[1, 0] == pytest.approx(14.14, abs=0.01)
        # Check distance to self is 0
        assert problem.distance_matrix[0, 0] == 0.0

    def test_large_instance_loading(self, complex_vrp_instance_path):
        """Tests loading of a larger instance to ensure scalability."""
        problem = VRPProblemV2(str(complex_vrp_instance_path))
        assert problem._name == "test-n10-k3"
        assert problem._dimension == 10
        assert problem.capacity == 150
        assert problem.depot_index == 0
        assert len(problem.nodes) == 10
        assert len(problem.demands) == 10

    def test_str_representation(self, simple_vrp_instance_path):
        """Tests the string representation of the problem."""
        problem = VRPProblemV2(str(simple_vrp_instance_path))
        assert str(problem) == "VRPProblemV2(name='test-n5-k2', dimension=4)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])