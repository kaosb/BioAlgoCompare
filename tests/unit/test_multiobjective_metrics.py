"""
Tests for multi-objective optimization metrics.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from utils.multiobjective_metrics import (
    calculate_hypervolume,
    calculate_igd,
    get_non_dominated_solutions,
    calculate_spacing,
    calculate_spread,
    simulate_dynamic_demands,
    calculate_qc_metrics,
    DEAP_AVAILABLE
)


class TestCalculateHypervolume:
    """Tests for hypervolume calculation."""
    
    def test_empty_pareto_front(self):
        """Test hypervolume with empty Pareto front."""
        assert calculate_hypervolume([]) == 0.0
    
    def test_single_solution(self):
        """Test hypervolume with single solution."""
        pareto_front = [(10.0, 20.0, 30.0)]
        reference_point = (15.0, 25.0, 35.0)
        hv = calculate_hypervolume(pareto_front, reference_point)
        # Volume should be (15-10) * (25-20) * (35-30) = 5 * 5 * 5 = 125
        if not DEAP_AVAILABLE:
            assert hv == 125.0
    
    def test_multiple_solutions(self):
        """Test hypervolume with multiple solutions."""
        pareto_front = [(10.0, 20.0, 30.0), (12.0, 18.0, 28.0)]
        hv = calculate_hypervolume(pareto_front)
        assert hv > 0
    
    def test_auto_reference_point(self):
        """Test automatic reference point calculation."""
        pareto_front = [(10.0, 20.0, 30.0), (15.0, 15.0, 25.0)]
        hv = calculate_hypervolume(pareto_front)
        assert hv > 0
    
    def test_solution_beyond_reference(self):
        """Test solution beyond reference point (simplified implementation)."""
        if not DEAP_AVAILABLE:
            pareto_front = [(10.0, 20.0, 30.0)]
            reference_point = (5.0, 15.0, 25.0)  # Smaller than solution
            hv = calculate_hypervolume(pareto_front, reference_point)
            assert hv == 0.0  # No dominated volume
    
    def test_deap_not_available(self):
        """Test hypervolume when DEAP is not available."""
        # Already tested implicitly in other tests when DEAP_AVAILABLE is False
        # but let's make it explicit
        with patch('utils.multiobjective_metrics.DEAP_AVAILABLE', False):
            pareto_front = [(10.0, 20.0, 30.0)]
            reference_point = (15.0, 25.0, 35.0)
            hv = calculate_hypervolume(pareto_front, reference_point)
            # Should use simplified calculation
            assert hv == 125.0  # (15-10) * (25-20) * (35-30) = 125
    
    def test_hypervolume_with_deap(self):
        """Test lineas 44-52: rama DEAP_AVAILABLE=True con mock de deap."""
        mock_hv_instance = MagicMock()
        mock_hv_instance.compute.return_value = 999.0

        mock_hypervolume = MagicMock()
        mock_hypervolume.Hypervolume.return_value = mock_hv_instance

        with patch('utils.multiobjective_metrics.DEAP_AVAILABLE', True), \
             patch('utils.multiobjective_metrics.deap_hypervolume', mock_hypervolume, create=True):
            pareto_front = [(10.0, 20.0, 30.0)]
            reference_point = (15.0, 25.0, 35.0)
            hv = calculate_hypervolume(pareto_front, reference_point)

            mock_hypervolume.Hypervolume.assert_called_once_with(reference_point)
            mock_hv_instance.compute.assert_called_once_with(pareto_front)
            assert hv == 999.0

    def test_hypervolume_with_deap_auto_refpoint(self):
        """Test lineas 44-52: DEAP con reference_point=None (auto-calculado)."""
        mock_hv_instance = MagicMock()
        mock_hv_instance.compute.return_value = 500.0

        mock_hypervolume = MagicMock()
        mock_hypervolume.Hypervolume.return_value = mock_hv_instance

        with patch('utils.multiobjective_metrics.DEAP_AVAILABLE', True), \
             patch('utils.multiobjective_metrics.deap_hypervolume', mock_hypervolume, create=True):
            pareto_front = [(10.0, 20.0, 30.0), (15.0, 25.0, 35.0)]
            hv = calculate_hypervolume(pareto_front)

            # reference_point debe ser auto-calculado como max * 1.1
            call_args = mock_hypervolume.Hypervolume.call_args[0][0]
            assert len(call_args) == 3
            assert hv == 500.0

    def test_deap_import_false(self):
        """Test linea 21: verificar que DEAP_AVAILABLE=False cuando import falla."""
        import sys

        original_module = sys.modules.get('utils.multiobjective_metrics')

        with patch.dict(sys.modules, {'deap': None, 'deap.tools': None, 'deap.tools.hypervolume': None}):
            if 'utils.multiobjective_metrics' in sys.modules:
                del sys.modules['utils.multiobjective_metrics']
            try:
                import utils.multiobjective_metrics as mm_reloaded
                assert mm_reloaded.DEAP_AVAILABLE is False
            finally:
                if original_module is not None:
                    sys.modules['utils.multiobjective_metrics'] = original_module

    def test_deap_import_true(self):
        """Test linea 19: verificar que DEAP_AVAILABLE=True cuando deap esta disponible."""
        import sys
        import types

        original_module = sys.modules.get('utils.multiobjective_metrics')

        # Crear un modulo fake de deap con hypervolume
        fake_deap = types.ModuleType('deap')
        fake_deap_tools = types.ModuleType('deap.tools')
        fake_hv_mod = types.ModuleType('deap.tools.hypervolume')
        fake_hv_mod.Hypervolume = MagicMock()
        fake_deap.tools = fake_deap_tools
        fake_deap_tools.hypervolume = fake_hv_mod

        with patch.dict(sys.modules, {
            'deap': fake_deap,
            'deap.tools': fake_deap_tools,
            'deap.tools.hypervolume': fake_hv_mod,
        }):
            if 'utils.multiobjective_metrics' in sys.modules:
                del sys.modules['utils.multiobjective_metrics']
            try:
                import utils.multiobjective_metrics as mm_reloaded
                assert mm_reloaded.DEAP_AVAILABLE is True
            finally:
                if original_module is not None:
                    sys.modules['utils.multiobjective_metrics'] = original_module

    def test_with_deap_behavior(self):
        """Test hypervolume behavior when DEAP would be available."""
        # Since we can't easily mock the DEAP import, let's test the logic
        # by directly testing what would happen with DEAP
        pareto_front = [(10.0, 20.0, 30.0), (12.0, 18.0, 28.0)]
        
        # Test automatic reference point calculation
        hv = calculate_hypervolume(pareto_front)
        assert hv > 0
        
        # Test with explicit reference point
        reference_point = (15.0, 25.0, 35.0)
        hv2 = calculate_hypervolume(pareto_front, reference_point)
        assert hv2 > 0


class TestCalculateIGD:
    """Tests for IGD calculation."""
    
    def test_empty_sets(self):
        """Test IGD with empty sets."""
        assert calculate_igd([], [(1, 2, 3)]) == float('inf')
        assert calculate_igd([(1, 2, 3)], []) == float('inf')
        assert calculate_igd([], []) == float('inf')
    
    def test_identical_sets(self):
        """Test IGD with identical sets."""
        reference = [(10.0, 20.0, 30.0), (15.0, 15.0, 25.0)]
        pareto = [(10.0, 20.0, 30.0), (15.0, 15.0, 25.0)]
        igd = calculate_igd(pareto, reference)
        assert igd == 0.0
    
    def test_different_sets(self):
        """Test IGD with different sets."""
        reference = [(10.0, 20.0, 30.0), (15.0, 15.0, 25.0)]
        pareto = [(11.0, 21.0, 31.0), (16.0, 16.0, 26.0)]
        igd = calculate_igd(pareto, reference)
        assert igd > 0
        # Should be approximately sqrt(3) for each point
        assert 1.5 < igd < 2.0
    
    def test_partial_coverage(self):
        """Test IGD with partial coverage."""
        reference = [(10.0, 20.0, 30.0), (15.0, 15.0, 25.0), (20.0, 10.0, 20.0)]
        pareto = [(10.0, 20.0, 30.0)]  # Only covers first reference point
        igd = calculate_igd(pareto, reference)
        assert igd > 0  # Should have distance from uncovered points


class TestGetNonDominatedSolutions:
    """Tests for non-dominated solution filtering."""
    
    def test_empty_solutions(self):
        """Test with empty solution set."""
        assert get_non_dominated_solutions([]) == []
    
    def test_single_solution(self):
        """Test with single solution."""
        solutions = [(10.0, 20.0, 30.0)]
        assert get_non_dominated_solutions(solutions) == solutions
    
    def test_dominated_solutions(self):
        """Test filtering dominated solutions."""
        solutions = [
            (10.0, 20.0, 30.0),  # Dominated by the next
            (9.0, 19.0, 29.0),   # Dominates the previous
            (15.0, 15.0, 25.0)   # Non-dominated (trade-off)
        ]
        non_dominated = get_non_dominated_solutions(solutions)
        assert len(non_dominated) == 2
        assert (9.0, 19.0, 29.0) in non_dominated
        assert (15.0, 15.0, 25.0) in non_dominated
        assert (10.0, 20.0, 30.0) not in non_dominated
    
    def test_all_non_dominated(self):
        """Test when all solutions are non-dominated."""
        solutions = [
            (10.0, 20.0, 30.0),
            (20.0, 10.0, 30.0),  # Trade-off in obj1 vs obj2
            (15.0, 15.0, 20.0)   # Trade-off in obj3
        ]
        non_dominated = get_non_dominated_solutions(solutions)
        assert len(non_dominated) == 3
    
    def test_duplicate_solutions(self):
        """Test with duplicate solutions."""
        solutions = [
            (10.0, 20.0, 30.0),
            (10.0, 20.0, 30.0),  # Duplicate
            (15.0, 15.0, 25.0)
        ]
        non_dominated = get_non_dominated_solutions(solutions)
        # Current implementation doesn't filter duplicates
        assert len(non_dominated) == 3
        assert (10.0, 20.0, 30.0) in non_dominated
        assert (15.0, 15.0, 25.0) in non_dominated


class TestCalculateSpacing:
    """Tests for spacing metric calculation."""
    
    def test_single_solution(self):
        """Test spacing with single solution."""
        assert calculate_spacing([(10.0, 20.0, 30.0)]) == 0.0
    
    def test_empty_front(self):
        """Test spacing with empty front."""
        assert calculate_spacing([]) == 0.0
    
    def test_uniform_spacing(self):
        """Test spacing with uniformly distributed solutions."""
        # Solutions equally spaced along a line
        pareto_front = [(i, i, i) for i in range(0, 11, 2)]
        spacing = calculate_spacing(pareto_front)
        # Should be close to 0 for uniform distribution
        assert spacing < 0.1
    
    def test_non_uniform_spacing(self):
        """Test spacing with non-uniform distribution."""
        pareto_front = [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0),
            (10.0, 10.0, 10.0)  # Far from others
        ]
        spacing = calculate_spacing(pareto_front)
        assert spacing > 0


class TestCalculateSpread:
    """Tests for spread metric calculation."""
    
    def test_single_solution(self):
        """Test spread with single solution."""
        assert calculate_spread([(10.0, 20.0, 30.0)]) == 0.0
    
    def test_empty_front(self):
        """Test spread with empty front."""
        assert calculate_spread([]) == 0.0
    
    def test_two_solutions(self):
        """Test spread with two solutions."""
        pareto_front = [(10.0, 20.0, 30.0), (20.0, 10.0, 20.0)]
        spread = calculate_spread(pareto_front)
        assert 0 <= spread <= 1
    
    def test_with_extreme_points(self):
        """Test spread with provided extreme points."""
        pareto_front = [(10.0, 20.0, 30.0), (15.0, 15.0, 25.0), (20.0, 10.0, 20.0)]
        extreme_points = [(5.0, 25.0, 35.0), (25.0, 5.0, 15.0)]
        spread = calculate_spread(pareto_front, extreme_points)
        assert 0 <= spread <= 1
    
    def test_spread_zero_denominator(self):
        """Test linea 218: denominador cero cuando todos los puntos son identicos."""
        # Puntos identicos -> d_sum = 0, df = 0, dl = 0 -> denominator = 0
        pareto_front = [(5.0, 5.0, 5.0), (5.0, 5.0, 5.0)]
        spread = calculate_spread(pareto_front)
        assert spread == 0.0

    def test_well_distributed_front(self):
        """Test spread with well-distributed front."""
        # Create a well-distributed Pareto front
        pareto_front = []
        for i in range(10):
            pareto_front.append((i, 10-i, 5))
        spread = calculate_spread(pareto_front)
        assert spread > 0


class TestSimulateDynamicDemands:
    """Tests for dynamic demand simulation."""
    
    def test_zero_rate(self):
        """Test with zero arrival rate."""
        mock_problem = MagicMock()
        mock_problem.dimension = 10
        orders = simulate_dynamic_demands(mock_problem, lambda_rate=0, time_horizon=60)
        assert len(orders) == 0
    
    def test_negative_rate(self):
        """Test with negative arrival rate."""
        mock_problem = MagicMock()
        mock_problem.dimension = 10
        orders = simulate_dynamic_demands(mock_problem, lambda_rate=-1, time_horizon=60)
        assert len(orders) == 0
    
    def test_basic_simulation(self):
        """Test basic demand simulation."""
        mock_problem = MagicMock()
        mock_problem.dimension = 10
        mock_problem.nodes = {i: (i*10, i*10) for i in range(10)}
        
        orders = simulate_dynamic_demands(
            mock_problem, 
            lambda_rate=10, 
            time_horizon=60, 
            seed=42
        )
        
        assert len(orders) > 0
        for order in orders:
            assert 'customer_id' in order
            assert 'demand' in order
            assert 'arrival_time' in order
            assert 'coord' in order
            assert 'time_window' in order
            assert 1 <= order['customer_id'] < 10
            assert 5 <= order['demand'] <= 19
            assert 0 <= order['arrival_time'] < 60
    
    def test_reproducibility(self):
        """Test simulation reproducibility with seed."""
        mock_problem = MagicMock()
        mock_problem.dimension = 10
        mock_problem.nodes = {i: (i*10, i*10) for i in range(10)}
        
        orders1 = simulate_dynamic_demands(mock_problem, seed=42)
        orders2 = simulate_dynamic_demands(mock_problem, seed=42)
        
        assert len(orders1) == len(orders2)
        for o1, o2 in zip(orders1, orders2):
            assert o1['customer_id'] == o2['customer_id']
            assert o1['arrival_time'] == o2['arrival_time']
    
    def test_without_nodes_attribute(self):
        """Test simulation when problem has no nodes attribute."""
        mock_problem = MagicMock()
        mock_problem.dimension = 10
        del mock_problem.nodes  # Remove nodes attribute
        
        orders = simulate_dynamic_demands(mock_problem, lambda_rate=10, time_horizon=60, seed=42)
        
        assert len(orders) > 0
        for order in orders:
            assert order['coord'] == (0, 0)  # Default coordinate


class TestCalculateQCMetrics:
    """Tests for Quick Commerce metrics calculation."""
    
    def test_empty_routes(self):
        """Test with empty routes."""
        assert calculate_qc_metrics([]) == 0.0
        assert calculate_qc_metrics([[]]) == 0.0
    
    def test_depot_only_routes(self):
        """Test with routes containing only depots."""
        routes = [[0, 0], [0, 0]]  # Only depot visits
        assert calculate_qc_metrics(routes) == 0.0
    
    def test_single_customer_routes(self):
        """Test with single customer per route."""
        routes = [
            [0, 1, 0],  # Depot -> Customer 1 -> Depot
            [0, 2, 0],  # Depot -> Customer 2 -> Depot
            [0, 3, 0]   # Depot -> Customer 3 -> Depot
        ]
        rate = calculate_qc_metrics(routes)
        assert rate > 0.9  # Should be high for single customer routes
    
    def test_multiple_customers_per_route(self):
        """Test with multiple customers per route."""
        routes = [
            [0, 1, 2, 3, 4, 5, 0],  # 5 customers
            [0, 6, 7, 8, 9, 10, 0]  # 5 customers
        ]
        rate = calculate_qc_metrics(routes)
        assert 0.5 < rate <= 0.8  # Should be moderate
    
    def test_with_dynamic_orders(self):
        """Test metrics with dynamic orders."""
        routes = [[0, 1, 2, 0], [0, 3, 4, 0]]
        dynamic_orders = [
            {'customer_id': 5, 'arrival_time': 10},
            {'customer_id': 6, 'arrival_time': 20}
        ]
        rate_without = calculate_qc_metrics(routes)
        rate_with = calculate_qc_metrics(routes, dynamic_orders)
        
        assert rate_with < rate_without  # Dynamic orders reduce efficiency
    
    def test_many_dynamic_orders(self):
        """Test with many dynamic orders."""
        routes = [[0, 1, 0]]
        dynamic_orders = [{'customer_id': i, 'arrival_time': i*5} for i in range(2, 22)]
        rate = calculate_qc_metrics(routes, dynamic_orders)
        
        assert rate < 0.9  # Should be reduced by complexity
    
    def test_qc_metrics_no_customers(self):
        """Test linea 293: rutas sin clientes (solo depot, e.g. [0,0,0])."""
        routes = [[0, 0, 0]]
        rate = calculate_qc_metrics(routes)
        # Route tiene len=3 > 2, pero clientes = 3 - 2 = 1
        # En realidad [0,0,0] tiene len=3, asi que total_customers = 1
        # Verifiquemos el resultado
        assert 0 <= rate <= 1

    def test_qc_metrics_all_short_routes(self):
        """Test linea 293 variante: rutas con len <= 2 no tienen clientes."""
        routes = [[0, 0], [0], [0, 0]]
        rate = calculate_qc_metrics(routes)
        assert rate == 0.0

    def test_mixed_route_lengths(self):
        """Test with mixed route lengths."""
        routes = [
            [0, 1, 0],           # 1 customer
            [0, 2, 3, 4, 0],     # 3 customers
            [0, 5, 6, 7, 8, 9, 0] # 5 customers
        ]
        rate = calculate_qc_metrics(routes)
        assert 0 < rate <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])