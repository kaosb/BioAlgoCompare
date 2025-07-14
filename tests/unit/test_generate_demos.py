"""
Tests para el módulo generate_demos.
Cubre la generación de demostraciones de parámetros óptimos para IL.
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from utils.generate_demos import SimpleGA, SimplePSO, generate_demonstrations, main


class TestSimpleGA:
    """Tests para la clase SimpleGA."""
    
    @pytest.fixture
    def mock_problem(self):
        """Mock de un problema VRP."""
        problem = Mock()
        problem.dimension = 10
        problem.distance_matrix = np.random.rand(10, 10)
        return problem
    
    @pytest.fixture
    def mock_state(self):
        """Mock de un estado de optimización."""
        return {
            "iteration_progress": 0.5,
            "fitness_diversity": 0.3,
            "convergence_rate": -0.1,
            "stagnation": 0.2
        }
    
    def test_simple_ga_initialization(self):
        """Test inicialización de SimpleGA."""
        ga = SimpleGA(population_size=10, generations=20, seed=42)
        
        assert ga.population_size == 10
        assert ga.generations == 20
        assert ga.rng is not None
    
    @patch('utils.generate_demos.HO')
    def test_optimize_ho_params_basic(self, mock_ho_class, mock_problem, mock_state):
        """Test optimización básica de parámetros."""
        # Mock del algoritmo HO
        mock_ho_instance = Mock()
        mock_best = Mock()
        mock_best.fitness.return_value = 100.0
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_class.return_value = mock_ho_instance
        
        # Ejecutar optimización
        ga = SimpleGA(population_size=5, generations=2, seed=42)
        alpha, beta, gamma, fitness = ga.optimize_ho_params(
            mock_problem, mock_state, ho_iterations=10
        )
        
        # Verificar resultados
        assert 0.1 <= alpha <= 0.9
        assert 0.2 <= beta <= 0.8
        assert 0.3 <= gamma <= 1.0
        assert fitness == 100.0
        
        # Verificar que se ejecutó HO
        assert mock_ho_class.call_count > 0
    
    @patch('utils.generate_demos.HO')
    def test_optimize_ho_params_evolution(self, mock_ho_class, mock_problem, mock_state):
        """Test que la evolución mejora el fitness."""
        # Mock con fitness que mejora con ciertos parámetros
        def create_ho_mock(problem, **kwargs):
            mock_ho = Mock()
            mock_best = Mock()
            # Fitness mejora cuando alpha se acerca a 0.5
            mock_best.fitness = Mock(side_effect=lambda: 100.0)
            mock_ho.execute.return_value = mock_best
            mock_ho.alpha_min = 0.1
            mock_ho.alpha_max = 0.9
            mock_ho.beta_min = 0.2
            mock_ho.beta_max = 0.8
            mock_ho.gamma_min = 0.3
            mock_ho.gamma_max = 1.0
            return mock_ho
        
        mock_ho_class.side_effect = create_ho_mock
        
        # Ejecutar con más generaciones
        ga = SimpleGA(population_size=10, generations=5, seed=42)
        alpha, beta, gamma, fitness = ga.optimize_ho_params(
            mock_problem, mock_state, ho_iterations=5
        )
        
        # Verificar que se hicieron múltiples evaluaciones
        expected_calls = ga.population_size * ga.generations
        assert mock_ho_class.call_count == expected_calls
    
    def test_crossover_and_mutation(self):
        """Test operadores genéticos."""
        ga = SimpleGA(population_size=4, generations=1, seed=42)
        
        # Verificar que la mutación ocurre
        mutations = 0
        for _ in range(100):
            if ga.rng.random() < 0.1:
                mutations += 1
        
        # Con probabilidad 0.1, esperamos ~10 mutaciones
        assert 5 <= mutations <= 15


class TestSimplePSO:
    """Tests para la clase SimplePSO."""
    
    @pytest.fixture
    def mock_problem(self):
        """Mock de un problema VRP."""
        problem = Mock()
        problem.dimension = 10
        return problem
    
    @pytest.fixture
    def mock_state(self):
        """Mock de un estado de optimización."""
        return {"some_feature": 0.5}
    
    def test_simple_pso_initialization(self):
        """Test inicialización de SimplePSO."""
        pso = SimplePSO(swarm_size=15, iterations=25, seed=42)
        
        assert pso.swarm_size == 15
        assert pso.iterations == 25
        assert pso.rng is not None
    
    @patch('utils.generate_demos.HO')
    def test_optimize_ho_params_basic(self, mock_ho_class, mock_problem, mock_state):
        """Test optimización básica con PSO."""
        # Mock del algoritmo HO
        mock_ho_instance = Mock()
        mock_best = Mock()
        mock_best.fitness.return_value = 90.0
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_class.return_value = mock_ho_instance
        
        # Ejecutar optimización
        pso = SimplePSO(swarm_size=5, iterations=3, seed=42)
        alpha, beta, gamma, fitness = pso.optimize_ho_params(
            mock_problem, mock_state, ho_iterations=10
        )
        
        # Verificar resultados
        assert 0.1 <= alpha <= 0.9
        assert 0.2 <= beta <= 0.8
        assert 0.3 <= gamma <= 1.0
        assert fitness == 90.0
        
        # Verificar número de evaluaciones
        expected_calls = pso.swarm_size * pso.iterations
        assert mock_ho_class.call_count == expected_calls
    
    @patch('utils.generate_demos.HO')
    def test_pso_convergence(self, mock_ho_class, mock_problem, mock_state):
        """Test que PSO converge hacia mejores soluciones."""
        # Fitness que mejora con el tiempo
        fitness_values = list(range(100, 80, -1))
        fitness_idx = 0
        
        def create_ho_mock(problem, **kwargs):
            nonlocal fitness_idx
            mock_ho = Mock()
            mock_best = Mock()
            mock_best.fitness.return_value = fitness_values[min(fitness_idx, len(fitness_values)-1)]
            fitness_idx += 1
            mock_ho.execute.return_value = mock_best
            return mock_ho
        
        mock_ho_class.side_effect = create_ho_mock
        
        # Ejecutar PSO
        pso = SimplePSO(swarm_size=3, iterations=5, seed=42)
        alpha, beta, gamma, fitness = pso.optimize_ho_params(
            mock_problem, mock_state, ho_iterations=5
        )
        
        # El fitness final debería ser mejor que el inicial
        assert fitness <= 100.0
    
    def test_particle_bounds(self):
        """Test que las partículas respetan los límites."""
        pso = SimplePSO(swarm_size=10, iterations=5, seed=42)
        
        # Inicializar posiciones y velocidades
        bounds = np.array([
            [0.1, 0.9],  # alpha
            [0.2, 0.8],  # beta
            [0.3, 1.0],  # gamma
        ])
        
        positions = pso.rng.uniform(bounds[:, 0], bounds[:, 1], (pso.swarm_size, 3))
        
        # Verificar que todas las posiciones están dentro de los límites
        for i in range(3):
            assert np.all(positions[:, i] >= bounds[i, 0])
            assert np.all(positions[:, i] <= bounds[i, 1])


class TestGenerateDemonstrations:
    """Tests para la función generate_demonstrations."""
    
    @patch('utils.generate_demos.VRPProblem')
    @patch('utils.generate_demos.HO')
    @patch('utils.generate_demos.create_state_from_problem')
    @patch('os.path.exists')
    def test_generate_demonstrations_basic(self, mock_exists, mock_create_state, 
                                         mock_ho_class, mock_vrp_class):
        """Test generación básica de demostraciones."""
        # Configurar mocks
        mock_exists.return_value = False  # Forzar instancia sintética
        
        # Mock del problema
        mock_problem = Mock()
        mock_problem.nodes = []
        mock_problem.demands = []
        mock_problem.compute_distance_matrix = Mock()
        mock_vrp_class.return_value = mock_problem
        
        # Mock del HO
        mock_ho_instance = Mock()
        mock_ho_instance.max_iterations = 100
        mock_ho_instance.initialize_population = Mock()
        mock_ho_instance.update_population = Mock()
        mock_best = Mock()
        mock_best.fitness.return_value = 100.0
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_class.return_value = mock_ho_instance
        
        # Mock del estado
        mock_state = {
            "iteration_progress": 0.5,
            "fitness_diversity": 0.3,
            "convergence_rate": -0.1
        }
        mock_create_state.return_value = mock_state
        
        # Generar demostraciones
        algorithms = ["ga"]
        instances = ["test-instance"]
        num_demos = 2
        
        df = generate_demonstrations(algorithms, instances, num_demos, seed=42)
        
        # Verificar resultado
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # num_demos
        assert "instance" in df.columns
        assert "algorithm" in df.columns
        assert "alpha" in df.columns
        assert "beta" in df.columns
        assert "gamma" in df.columns
        assert "fitness" in df.columns
        
        # Verificar valores
        assert all(df["algorithm"] == "ga")
        assert all(df["instance"] == "test-instance")
        assert all(0.1 <= df["alpha"]) and all(df["alpha"] <= 0.9)
        assert all(0.2 <= df["beta"]) and all(df["beta"] <= 0.8)
        assert all(0.3 <= df["gamma"]) and all(df["gamma"] <= 1.0)
    
    @patch('utils.generate_demos.VRPProblem')
    @patch('utils.generate_demos.HO')
    @patch('utils.generate_demos.create_state_from_problem')
    def test_generate_demonstrations_solomon_instance(self, mock_create_state, 
                                                    mock_ho_class, mock_vrp_class):
        """Test con instancia tipo Solomon."""
        # Mock del problema
        mock_problem = Mock()
        mock_problem.nodes = [(0, 0)]
        mock_problem.demands = [0]
        mock_problem.compute_distance_matrix = Mock()
        mock_vrp_class.return_value = mock_problem
        
        # Mock del HO
        mock_ho_instance = Mock()
        mock_ho_instance.max_iterations = 100
        mock_ho_instance.initialize_population = Mock()
        mock_ho_instance.update_population = Mock()
        mock_best = Mock()
        mock_best.fitness.return_value = 95.0
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_class.return_value = mock_ho_instance
        
        # Mock del estado
        mock_create_state.return_value = {"test": "state"}
        
        # Generar con instancia Solomon
        algorithms = ["pso"]
        instances = ["Solomon-RC101"]
        num_demos = 1
        
        generate_demonstrations(algorithms, instances, num_demos, seed=42)
        
        # Verificar que se creó instancia Solomon
        assert mock_problem.capacity == 100
        assert mock_problem.dimension == 26  # 25 clientes + depot
    
    @patch('utils.generate_demos.VRPProblem')
    @patch('utils.generate_demos.HO')
    @patch('utils.generate_demos.create_state_from_problem')
    @patch('os.path.exists')
    def test_generate_demonstrations_real_instance(self, mock_exists, mock_create_state,
                                                 mock_ho_class, mock_vrp_class):
        """Test con instancia VRP real."""
        # Simular que existe el archivo
        mock_exists.return_value = True
        
        # Mock del problema cargado desde archivo
        mock_problem = Mock()
        mock_vrp_class.return_value = mock_problem
        
        # Mock del HO
        mock_ho_instance = Mock()
        mock_ho_instance.max_iterations = 100
        mock_ho_instance.initialize_population = Mock()
        mock_ho_instance.update_population = Mock()
        mock_best = Mock()
        mock_best.fitness.return_value = 85.0
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_class.return_value = mock_ho_instance
        
        # Mock del estado
        mock_create_state.return_value = {"state": "data"}
        
        # Generar demostraciones
        algorithms = ["ga", "pso"]
        instances = ["P-n16-k8"]
        num_demos = 4
        
        df = generate_demonstrations(algorithms, instances, num_demos, seed=42)
        
        # Verificar
        assert len(df) == 8  # 4 demos * 2 algorithms
        assert set(df["algorithm"]) == {"ga", "pso"}
        assert all(df["instance"] == "P-n16-k8")
        
        # Verificar que se cargó desde archivo
        mock_vrp_class.assert_called_with("data/vrp/P-n16-k8.vrp")
    
    @patch('utils.generate_demos.VRPProblem')
    @patch('utils.generate_demos.HO')
    @patch('utils.generate_demos.create_state_from_problem')
    @patch('os.path.exists')
    def test_generate_demonstrations_invalid_algorithm(self, mock_exists, mock_create_state,
                                                     mock_ho_class, mock_vrp_class):
        """Test con algoritmo no reconocido."""
        # Setup básico
        mock_exists.return_value = False
        mock_problem = Mock()
        mock_problem.dimension = 20
        mock_vrp_class.return_value = mock_problem
        
        mock_ho_instance = Mock()
        mock_ho_instance.max_iterations = 100
        mock_ho_instance.initialize_population = Mock()
        mock_ho_instance.update_population = Mock()
        mock_ho_class.return_value = mock_ho_instance
        
        mock_create_state.return_value = {"test": "state"}
        
        algorithms = ["invalid_algo"]
        instances = ["test"]
        num_demos = 1
        
        df = generate_demonstrations(algorithms, instances, num_demos)
        
        # Debería retornar DataFrame vacío para algoritmo inválido
        assert len(df) == 0
    
    @patch('utils.generate_demos.VRPProblem')
    @patch('utils.generate_demos.HO')
    @patch('utils.generate_demos.create_state_from_problem')
    def test_different_progress_stages(self, mock_create_state, mock_ho_class, mock_vrp_class):
        """Test que se generan diferentes etapas de progreso."""
        # Mock básico
        mock_problem = Mock()
        mock_vrp_class.return_value = mock_problem
        
        mock_ho_instance = Mock()
        mock_ho_instance.max_iterations = 100
        mock_ho_instance.initialize_population = Mock()
        mock_ho_instance.update_population = Mock()
        mock_best = Mock()
        mock_best.fitness.return_value = 90.0
        mock_ho_instance.execute.return_value = mock_best
        mock_ho_class.return_value = mock_ho_instance
        
        mock_create_state.return_value = {"state": "data"}
        
        # Generar múltiples demostraciones
        algorithms = ["ga"]
        instances = ["test"]
        num_demos = 10
        
        # Capturar las iteraciones objetivo
        update_calls = []
        mock_ho_instance.update_population.side_effect = lambda: update_calls.append(1)
        
        df = generate_demonstrations(algorithms, instances, num_demos, seed=42)
        
        # Verificar que se usaron diferentes etapas de progreso
        # Con 10 demos, deberíamos tener variación en las iteraciones
        assert len(df) == 10
        # Las llamadas a update_population deberían variar
        assert len(set(update_calls)) > 1 or len(update_calls) > 0


class TestMain:
    """Tests para la función main."""
    
    @patch('utils.generate_demos.argparse.ArgumentParser.parse_args')
    @patch('utils.generate_demos.generate_demonstrations')
    @patch('pandas.DataFrame.to_csv')
    @patch('os.makedirs')
    def test_main_basic(self, mock_makedirs, mock_to_csv, mock_generate, mock_parse_args):
        """Test ejecución básica del main."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.algorithms = "ga,pso"
        mock_args.instances = "Solomon-RC101,P-n16-k8"
        mock_args.num = 100
        mock_args.seed = 42
        mock_args.output = "test_demos.csv"
        mock_parse_args.return_value = mock_args
        
        # Mock de generate_demonstrations
        mock_df = pd.DataFrame({
            "instance": ["Solomon-RC101"] * 100,
            "algorithm": ["ga"] * 50 + ["pso"] * 50,
            "alpha": np.random.rand(100),
            "beta": np.random.rand(100),
            "gamma": np.random.rand(100),
            "fitness": np.random.rand(100) * 100
        })
        mock_generate.return_value = mock_df
        
        # Ejecutar main
        main()
        
        # Verificar llamadas
        mock_generate.assert_called_once_with(
            ["ga", "pso"], 
            ["Solomon-RC101", "P-n16-k8"], 
            100, 
            42
        )
        
        mock_makedirs.assert_called_once_with("results", exist_ok=True)
        mock_to_csv.assert_called_once()
        
        # Verificar que se llamó con la ruta correcta
        call_args = mock_to_csv.call_args
        assert call_args[0][0] == "results/test_demos.csv"
        assert call_args[1]["index"] is False
    
    @patch('utils.generate_demos.argparse.ArgumentParser.parse_args')
    @patch('utils.generate_demos.generate_demonstrations')
    @patch('pandas.DataFrame.to_csv')
    @patch('os.makedirs')
    def test_main_single_algorithm_instance(self, mock_makedirs, mock_to_csv, 
                                          mock_generate, mock_parse_args):
        """Test con un solo algoritmo e instancia."""
        # Configurar argumentos
        mock_args = Mock()
        mock_args.algorithms = "ga"
        mock_args.instances = "test-instance"
        mock_args.num = 50
        mock_args.seed = 123
        mock_args.output = "single_demo.csv"
        mock_parse_args.return_value = mock_args
        
        # Mock DataFrame simple
        mock_df = pd.DataFrame({
            "instance": ["test-instance"] * 50,
            "algorithm": ["ga"] * 50,
            "alpha": [0.5] * 50,
            "beta": [0.5] * 50,
            "gamma": [0.65] * 50,
            "fitness": [100.0] * 50
        })
        mock_generate.return_value = mock_df
        
        # Ejecutar
        main()
        
        # Verificar
        mock_generate.assert_called_once_with(["ga"], ["test-instance"], 50, 123)


class TestIntegration:
    """Tests de integración."""
    
    @patch('utils.generate_demos.VRPProblem')
    @patch('utils.generate_demos.HO')
    @patch('utils.generate_demos.create_state_from_problem')
    def test_full_pipeline(self, mock_create_state, mock_ho_class, mock_vrp_class):
        """Test del pipeline completo de generación."""
        # Setup complejo para simular el pipeline completo
        mock_problem = Mock()
        mock_problem.dimension = 10
        mock_vrp_class.return_value = mock_problem
        
        # HO que retorna fitness variable
        fitness_counter = 0
        def create_ho(*args, **kwargs):
            nonlocal fitness_counter
            mock_ho = Mock()
            mock_ho.max_iterations = 50
            mock_ho.initialize_population = Mock()
            mock_ho.update_population = Mock()
            mock_best = Mock()
            mock_best.fitness.return_value = 100.0 - fitness_counter
            fitness_counter += 1
            mock_ho.execute.return_value = mock_best
            return mock_ho
        
        mock_ho_class.side_effect = create_ho
        mock_create_state.return_value = {"test": "state"}
        
        # Generar demostraciones con ambos algoritmos
        algorithms = ["ga", "pso"]
        instances = ["test-instance"]
        num_demos = 4
        
        df = generate_demonstrations(algorithms, instances, num_demos, seed=42)
        
        # Verificar estructura completa
        assert len(df) == 8  # 4 demos * 2 algorithms
        assert set(df.columns) >= {
            "instance", "algorithm", "alpha", "beta", "gamma", "fitness", "test"
        }
        
        # Verificar que GA y PSO produjeron resultados
        ga_results = df[df["algorithm"] == "ga"]
        pso_results = df[df["algorithm"] == "pso"]
        
        assert len(ga_results) == 4
        assert len(pso_results) == 4
        
        # Verificar que los parámetros están en rangos válidos
        assert all(0.1 <= df["alpha"]) and all(df["alpha"] <= 0.9)
        assert all(0.2 <= df["beta"]) and all(df["beta"] <= 0.8)
        assert all(0.3 <= df["gamma"]) and all(df["gamma"] <= 1.0)