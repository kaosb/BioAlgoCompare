"""
Tests for simple demo generation module.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from utils.generate_simple_demos import (
    generate_simple_state,
    extract_optimal_params,
    generate_demonstrations
)


class TestGenerateSimpleState:
    """Tests for generate_simple_state function."""
    
    def test_generate_simple_state_basic(self):
        """Test generating simple state features."""
        # Mock problem
        mock_problem = MagicMock()
        mock_problem.dimension = 21  # 20 customers + 1 depot
        mock_problem.capacity = 100
        mock_problem.demands = np.array([0, 10, 20, 15, 25, 30])  # depot + 5 customers
        
        # Test state generation
        iteration = 10
        max_iterations = 100
        fitness_history = [1000, 900, 800, 700, 600, 500]
        
        state = generate_simple_state(mock_problem, iteration, max_iterations, fitness_history)
        
        # Check state features
        assert 'n_customers' in state
        assert state['n_customers'] == 20
        assert 'capacity' in state
        assert state['capacity'] == 100
        assert 'iteration' in state
        assert state['iteration'] == 10
        assert 'progress' in state
        assert state['progress'] == 0.1
        assert 'best_fitness' in state
        assert state['best_fitness'] == 500  # min of fitness_history


    def test_long_fitness_history(self):
        """Test con fitness_history de 15+ elementos (cubre linea 62)."""
        mock_problem = MagicMock()
        mock_problem.dimension = 21
        mock_problem.capacity = 100
        mock_problem.demands = np.array([0] + [10] * 20)

        # fitness_history con mas de 10 elementos para cubrir rama len > 10
        fitness_history = [1000 - i * 50 for i in range(16)]  # 16 elementos

        state = generate_simple_state(mock_problem, 50, 100, fitness_history)

        # Con len(fitness_history) > 10, debe calcular convergence_rate
        assert state['convergence_rate'] != 0
        # fitness_std debe usar ultimos 10 (no el default 100)
        assert state['fitness_std'] != 100
        # stagnation_counter se calcula
        assert 'stagnation_counter' in state
        # best_fitness = min(fitness_history)
        assert state['best_fitness'] == min(fitness_history)


class TestExtractOptimalParams:
    """Tests for extract_optimal_params function."""
    
    def test_extract_optimal_params_early_stage(self):
        """Test parameter extraction in early stage."""
        params = extract_optimal_params('ho', 10, 100)
        
        # Check that params are returned
        assert 'alpha' in params
        assert 'beta' in params
        assert 'gamma' in params
        
        # Check reasonable ranges
        assert 0.1 <= params['alpha'] <= 0.9
        assert 0.2 <= params['beta'] <= 0.8
        assert 0.3 <= params['gamma'] <= 1.0
    
    def test_extract_optimal_params_late_stage(self):
        """Test parameter extraction in late stage."""
        params = extract_optimal_params('ho', 90, 100)
        
        # Check that params are returned
        assert 'alpha' in params
        assert 'beta' in params
        assert 'gamma' in params
        
        # Check reasonable ranges
        assert 0.1 <= params['alpha'] <= 0.9
        assert 0.2 <= params['beta'] <= 0.8
        assert 0.3 <= params['gamma'] <= 1.0


class TestGenerateDemonstrations:
    """Tests for generate_demonstrations function."""
    
    @patch('utils.generate_simple_demos.VRPProblem')
    @patch('utils.generate_simple_demos.PSO')
    @patch('utils.generate_simple_demos.GA')
    def test_generate_demonstrations_single_instance(self, mock_ga_class, mock_pso_class, mock_vrp_class):
        """Test demo generation for single instance."""
        # Mock problem
        mock_problem = MagicMock()
        mock_problem.dimension = 11  # 10 customers + 1 depot
        mock_problem.capacity = 100
        mock_problem.demands = np.ones(11) * 10
        mock_vrp_class.return_value = mock_problem
        
        # Mock PSO algorithm
        mock_pso = MagicMock()
        mock_pso.problem = mock_problem
        mock_pso.population_size = 20
        mock_pso.max_iterations = 50
        mock_pso.gbest_fitness = 500.0  # PSO uses gbest_fitness
        mock_pso.initialize_population = MagicMock(return_value=[])
        mock_pso.update_population = MagicMock()
        mock_pso_class.return_value = mock_pso
        
        # Mock GA algorithm
        mock_ga = MagicMock()
        mock_ga.problem = mock_problem
        mock_ga.population_size = 20
        mock_ga.max_iterations = 50
        mock_ga.population = [MagicMock(fitness=MagicMock(return_value=500.0))]
        mock_ga.initialize_population = MagicMock(return_value=mock_ga.population)
        mock_ga.update_population = MagicMock()
        mock_ga_class.return_value = mock_ga
        
        # Generate demos
        demos = generate_demonstrations(['test-instance.vrp'], num_demos=2, seed=42)
        
        # Check demos dataframe
        assert isinstance(demos, pd.DataFrame)
        assert len(demos) > 0
        
        # Check columns
        expected_columns = ['instance', 'algorithm', 'demo_id', 'alpha', 'beta', 'gamma', 
                           'improvement', 'fitness_after']
        for col in expected_columns:
            assert col in demos.columns
        
        # Check data
        assert all(demos['instance'] == 'test-instance.vrp')
        assert set(demos['algorithm'].unique()) == {'pso', 'ga'}
        assert all(0.1 <= demos['alpha']) and all(demos['alpha'] <= 0.9)
        assert all(0.2 <= demos['beta']) and all(demos['beta'] <= 0.8)
        assert all(0.3 <= demos['gamma']) and all(demos['gamma'] <= 1.0)


    @patch('utils.generate_simple_demos.VRPProblem')
    @patch('utils.generate_simple_demos.PSO')
    @patch('utils.generate_simple_demos.GA')
    def test_generate_demonstrations_multiple_instances(self, mock_ga_class, mock_pso_class, mock_vrp_class):
        """Test demo generation for multiple instances."""
        # Mock problem
        def create_mock_problem(instance_path=None, **kwargs):
            mock_problem = MagicMock()
            mock_problem.dimension = 11 if 'test1' in instance_path else 16
            mock_problem.capacity = 100
            mock_problem.demands = np.ones(mock_problem.dimension) * 10
            return mock_problem
        
        mock_vrp_class.side_effect = create_mock_problem
        
        # Mock algorithm factory
        def create_mock_pso(problem, **kwargs):
            mock_pso = MagicMock()
            mock_pso.problem = problem
            mock_pso.population_size = 20
            mock_pso.max_iterations = 50
            mock_pso.gbest_fitness = 500.0 if problem.dimension == 11 else 600.0
            mock_pso.initialize_population = MagicMock(return_value=[])
            mock_pso.update_population = MagicMock()
            return mock_pso
        
        def create_mock_ga(problem, **kwargs):
            mock_ga = MagicMock()
            mock_ga.problem = problem
            mock_ga.population_size = 20
            mock_ga.max_iterations = 50
            fitness = 500.0 if problem.dimension == 11 else 600.0
            mock_ga.population = [MagicMock(fitness=MagicMock(return_value=fitness))]
            mock_ga.initialize_population = MagicMock(return_value=mock_ga.population)
            mock_ga.update_population = MagicMock()
            return mock_ga
        
        mock_pso_class.side_effect = create_mock_pso
        mock_ga_class.side_effect = create_mock_ga
        
        # Generate demos
        # With 2 instances and 2 algorithms, we need at least 4 demos to get 1 per combo
        demos = generate_demonstrations(['test1.vrp', 'test2.vrp'], num_demos=4, seed=42)
        
        # Check demos dataframe
        assert isinstance(demos, pd.DataFrame)
        assert len(demos) > 0
        
        # Check that we have data from at least one instance
        instances_in_demos = set(demos['instance'].unique())
        assert 'test1.vrp' in instances_in_demos or 'test2.vrp' in instances_in_demos
        
        # Check algorithms
        assert set(demos['algorithm'].unique()).issubset({'pso', 'ga'})


    @patch('utils.generate_simple_demos.VRPProblem')
    def test_instance_load_error(self, mock_vrp_class):
        """Test que un error al cargar instancia hace continue (lineas 112-114)."""
        mock_vrp_class.side_effect = Exception("File not found")

        demos = generate_demonstrations(['nonexistent-instance'], num_demos=10, seed=42)

        # Con error de carga, debe hacer continue y retornar DataFrame vacio
        assert isinstance(demos, pd.DataFrame)
        assert len(demos) == 0

    def test_generate_demonstrations_seed_reproducibility(self):
        """Test that seed ensures reproducibility."""
        with patch('utils.generate_simple_demos.VRPProblem') as mock_vrp, \
             patch('utils.generate_simple_demos.PSO') as mock_pso, \
             patch('utils.generate_simple_demos.GA') as mock_ga:
            
            # Setup mocks
            mock_problem = MagicMock()
            mock_problem.dimension = 11
            mock_problem.capacity = 100
            mock_problem.demands = np.ones(11) * 10
            mock_vrp.return_value = mock_problem
            
            # Mock PSO
            mock_pso_inst = MagicMock()
            mock_pso_inst.problem = mock_problem
            mock_pso_inst.population_size = 20
            mock_pso_inst.max_iterations = 50
            mock_pso_inst.gbest_fitness = 500.0
            mock_pso_inst.initialize_population = MagicMock(return_value=[])
            mock_pso_inst.update_population = MagicMock()
            mock_pso.return_value = mock_pso_inst
            
            # Mock GA
            mock_ga_inst = MagicMock()
            mock_ga_inst.problem = mock_problem
            mock_ga_inst.population_size = 20
            mock_ga_inst.max_iterations = 50
            mock_ga_inst.population = [MagicMock(fitness=MagicMock(return_value=500.0))]
            mock_ga_inst.initialize_population = MagicMock(return_value=mock_ga_inst.population)
            mock_ga_inst.update_population = MagicMock()
            mock_ga.return_value = mock_ga_inst
            
            # Generate with same seed twice
            # Need at least 2 demos (1 per algorithm)
            demos1 = generate_demonstrations(['test.vrp'], num_demos=2, seed=42)
            demos2 = generate_demonstrations(['test.vrp'], num_demos=2, seed=42)
            
            # Should produce identical results
            assert isinstance(demos1, pd.DataFrame)
            assert isinstance(demos2, pd.DataFrame)
            assert len(demos1) == len(demos2)
            # With same seed, should have same instances
            assert list(demos1['instance']) == list(demos2['instance'])


    def test_generate_demonstrations_output_format(self):
        """Test output format of demonstrations."""
        with patch('utils.generate_simple_demos.VRPProblem') as mock_vrp, \
             patch('utils.generate_simple_demos.PSO') as mock_pso, \
             patch('utils.generate_simple_demos.GA') as mock_ga:
            
            # Setup mocks
            mock_problem = MagicMock()
            mock_problem.dimension = 11
            mock_problem.capacity = 100
            mock_problem.demands = np.ones(11) * 10
            mock_vrp.return_value = mock_problem
            
            # Mock PSO
            mock_pso_inst = MagicMock()
            mock_pso_inst.problem = mock_problem
            mock_pso_inst.population_size = 20
            mock_pso_inst.max_iterations = 50
            mock_pso_inst.gbest_fitness = 500.0
            mock_pso_inst.initialize_population = MagicMock(return_value=[])
            mock_pso_inst.update_population = MagicMock()
            mock_pso.return_value = mock_pso_inst
            
            # Mock GA
            mock_ga_inst = MagicMock()
            mock_ga_inst.problem = mock_problem
            mock_ga_inst.population_size = 20
            mock_ga_inst.max_iterations = 50
            mock_ga_inst.population = [MagicMock(fitness=MagicMock(return_value=500.0))]
            mock_ga_inst.initialize_population = MagicMock(return_value=mock_ga_inst.population)
            mock_ga_inst.update_population = MagicMock()
            mock_ga.return_value = mock_ga_inst
            
            # Generate demos
            # Need at least 2 demos for 2 algorithms
            demos = generate_demonstrations(['test.vrp'], num_demos=2, seed=42)
            
            # Check output structure
            assert isinstance(demos, pd.DataFrame)
            assert len(demos) > 0
            
            # Check columns exist
            required_columns = ['instance', 'algorithm', 'demo_id', 'alpha', 'beta', 'gamma']
            for col in required_columns:
                assert col in demos.columns
            
            # Check data values
            assert all(demos['instance'] == 'test.vrp')
            assert demos['algorithm'].isin(['pso', 'ga']).all()


class TestMainFunction:
    """Tests for the main function."""
    
    @patch('utils.generate_simple_demos.generate_demonstrations')
    @patch('utils.generate_simple_demos.pd.DataFrame.to_csv')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_basic(self, mock_args, mock_to_csv, mock_generate):
        """Test main function with basic arguments."""
        # Mock arguments
        mock_args.return_value = MagicMock(
            instances='test.vrp',
            output='demos.csv',
            num_demos=5,
            seed=42
        )
        
        # Mock generate_demonstrations to return a DataFrame
        mock_generate.return_value = pd.DataFrame({
            'instance': ['test.vrp'],
            'algorithm': ['pso'],
            'demo_id': [0],
            'alpha': [0.5],
            'beta': [0.5],
            'gamma': [0.5],
            'improvement': [0.1],
            'fitness_after': [500.0]
        })
        
        # Import and run main
        from utils.generate_simple_demos import main
        
        # Run main
        main()
        
        # Check that generate_demonstrations was called correctly
        mock_generate.assert_called_once_with(
            ['test.vrp'],
            5,
            42
        )
        
        # Check that CSV was saved
        mock_to_csv.assert_called_once()
    
    @patch('utils.generate_simple_demos.generate_demonstrations')
    @patch('utils.generate_simple_demos.pd.DataFrame.to_csv')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_multiple_instances(self, mock_args, mock_to_csv, mock_generate):
        """Test main function with multiple instances."""
        # Mock arguments
        mock_args.return_value = MagicMock(
            instances='test1.vrp,test2.vrp',
            output='demos.csv',
            num_demos=10,
            seed=123
        )
        
        # Mock generate_demonstrations to return DataFrame with required columns
        mock_generate.return_value = pd.DataFrame({
            'instance': [],
            'algorithm': [],
            'demo_id': [],
            'alpha': [],
            'beta': [],
            'gamma': [],
            'improvement': [],
            'fitness_after': []
        })
        
        # Import and run main
        from utils.generate_simple_demos import main
        
        # Run main
        main()
        
        # Check that instances were split correctly
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[0]
        assert call_args[0] == ['test1.vrp', 'test2.vrp']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])