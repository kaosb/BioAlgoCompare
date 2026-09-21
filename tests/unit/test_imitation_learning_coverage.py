"""
Tests de cobertura para utils/imitation_learning.py.

Cubre las lineas: 304, 337-346, 408-409, 422-424, 428-444, 460.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from unittest.mock import patch, MagicMock

# Verificar si torch esta disponible
torch_available = True
try:
    import torch
except ImportError:
    torch_available = False

pytestmark = pytest.mark.skipif(not torch_available, reason="PyTorch not available")


class TestILPredictTrained:
    """Test imitation_learning.py:337-346 - predict con modelo entrenado."""

    def test_il_predict_trained(self, tmp_path):
        """Entrena un modelo y llama predict para cubrir lineas 337-346."""
        from utils.imitation_learning import HOImitationLearning

        il = HOImitationLearning(input_dim=64)

        # Crear CSV de demostraciones sintéticas
        n_samples = 200
        rng = np.random.RandomState(42)
        data = {
            "n_customers": rng.randint(10, 50, n_samples),
            "n_depots": np.ones(n_samples, dtype=int),
            "avg_demand": rng.uniform(10, 30, n_samples),
            "demand_std": rng.uniform(1, 10, n_samples),
            "capacity": rng.randint(50, 200, n_samples),
            "area_span": rng.uniform(20, 100, n_samples),
            "density": rng.uniform(0.01, 0.1, n_samples),
            "iteration": rng.randint(0, 100, n_samples),
            "progress": rng.uniform(0, 1, n_samples),
            "best_fitness": rng.uniform(100, 1000, n_samples),
            "avg_fitness": rng.uniform(100, 1000, n_samples),
            "fitness_std": rng.uniform(10, 100, n_samples),
            "convergence_rate": rng.uniform(0, 0.1, n_samples),
            "stagnation_counter": rng.randint(0, 20, n_samples),
            "population_diversity": rng.uniform(0.1, 0.9, n_samples),
            "elite_ratio": rng.uniform(0.05, 0.2, n_samples),
            "improvement_rate": rng.uniform(0, 0.1, n_samples),
            "dynamic_orders": np.zeros(n_samples),
            "avg_delay": np.zeros(n_samples),
            "load_imbalance": rng.uniform(0, 0.5, n_samples),
            "alpha": rng.uniform(0.1, 0.9, n_samples),
            "beta": rng.uniform(0.2, 0.8, n_samples),
            "gamma": rng.uniform(0.3, 1.0, n_samples),
        }
        df = pd.DataFrame(data)
        csv_path = str(tmp_path / "demos.csv")
        df.to_csv(csv_path, index=False)

        # Entrenar con pocas epocas
        il.train(csv_path, epochs=5, batch_size=32, seed=42)
        assert il.is_trained is True

        # Predecir (cubre lineas 337-346)
        state = {
            "n_customers": 20,
            "n_depots": 1,
            "avg_demand": 15.0,
            "demand_std": 5.0,
            "capacity": 100,
            "area_span": 50,
            "density": 0.02,
            "iteration": 10,
            "progress": 0.1,
            "best_fitness": 500,
            "avg_fitness": 550,
            "fitness_std": 30,
            "convergence_rate": 0.05,
            "stagnation_counter": 2,
            "population_diversity": 0.7,
            "elite_ratio": 0.1,
            "improvement_rate": 0.03,
            "dynamic_orders": 0,
            "avg_delay": 0,
            "load_imbalance": 0.15,
        }
        alpha, beta, gamma = il.predict(state)

        assert isinstance(alpha, float)
        assert isinstance(beta, float)
        assert isinstance(gamma, float)


class TestTrainingProgress:
    """Test imitation_learning.py:304 - progreso de entrenamiento cada 10 epocas."""

    def test_training_progress(self, tmp_path, capsys):
        """Entrena con epochs=10 y verifica salida de progreso."""
        from utils.imitation_learning import HOImitationLearning

        il = HOImitationLearning(input_dim=64)

        # Crear CSV de demostraciones
        n_samples = 200
        rng = np.random.RandomState(42)
        data = {
            "n_customers": rng.randint(10, 50, n_samples),
            "n_depots": np.ones(n_samples, dtype=int),
            "avg_demand": rng.uniform(10, 30, n_samples),
            "demand_std": rng.uniform(1, 10, n_samples),
            "capacity": rng.randint(50, 200, n_samples),
            "area_span": rng.uniform(20, 100, n_samples),
            "density": rng.uniform(0.01, 0.1, n_samples),
            "iteration": rng.randint(0, 100, n_samples),
            "progress": rng.uniform(0, 1, n_samples),
            "best_fitness": rng.uniform(100, 1000, n_samples),
            "avg_fitness": rng.uniform(100, 1000, n_samples),
            "fitness_std": rng.uniform(10, 100, n_samples),
            "convergence_rate": rng.uniform(0, 0.1, n_samples),
            "stagnation_counter": rng.randint(0, 20, n_samples),
            "population_diversity": rng.uniform(0.1, 0.9, n_samples),
            "elite_ratio": rng.uniform(0.05, 0.2, n_samples),
            "improvement_rate": rng.uniform(0, 0.1, n_samples),
            "dynamic_orders": np.zeros(n_samples),
            "avg_delay": np.zeros(n_samples),
            "load_imbalance": rng.uniform(0, 0.5, n_samples),
            "alpha": rng.uniform(0.1, 0.9, n_samples),
            "beta": rng.uniform(0.2, 0.8, n_samples),
            "gamma": rng.uniform(0.3, 1.0, n_samples),
        }
        df = pd.DataFrame(data)
        csv_path = str(tmp_path / "demos.csv")
        df.to_csv(csv_path, index=False)

        history = il.train(csv_path, epochs=10, batch_size=32, seed=42)
        captured = capsys.readouterr()

        # Linea 304: imprime cada 10 epocas, con epochs=10 debe imprimir en epoca 10
        assert "10/10" in captured.out
        assert "Loss Train" in captured.out
        assert "Loss Val" in captured.out
        assert isinstance(history, dict)
        assert "train_losses" in history
        assert len(history["train_losses"]) == 10


class TestCreateStateFromProblem:
    """Tests para create_state_from_problem cubriendo ramas condicionales."""

    def test_state_no_nodes(self):
        """Test lineas 408-409: problema sin atributo nodes."""
        from utils.imitation_learning import create_state_from_problem

        problem = MagicMock()
        problem.dimension = 21
        problem.demands = np.array([0] + [10] * 20)
        problem.capacity = 100
        # Sin atributo 'nodes'
        del problem.nodes
        # Sin atributo 'depots'
        del problem.depots

        algorithm = MagicMock()
        algorithm.population = []
        algorithm.convergence_curve = []
        del algorithm.population
        del algorithm.convergence_curve

        state = create_state_from_problem(problem, algorithm, 10, 100)

        # Sin nodes, debe usar valores default (lineas 408-409)
        assert state["area_span"] == 100
        assert state["density"] == 0.01

    def test_state_no_population(self):
        """Test lineas 422-424: algoritmo sin poblacion."""
        from utils.imitation_learning import create_state_from_problem

        problem = MagicMock()
        problem.dimension = 21
        problem.demands = np.array([0] + [10] * 20)
        problem.capacity = 100
        problem.nodes = [(0, 0)] + [(i * 5, i * 3) for i in range(1, 21)]

        algorithm = MagicMock()
        # population es lista vacia (falsy)
        algorithm.population = []
        algorithm.convergence_curve = [500, 490]

        state = create_state_from_problem(problem, algorithm, 10, 100)

        # Sin poblacion, debe usar defaults (lineas 422-424)
        assert state["best_fitness"] == 1000
        assert state["avg_fitness"] == 1000
        assert state["fitness_std"] == 0

    def test_state_convergence(self):
        """Test lineas 428-444: convergence_curve con mas de 10 elementos."""
        from utils.imitation_learning import create_state_from_problem

        problem = MagicMock()
        problem.dimension = 21
        problem.demands = np.array([0] + [10] * 20)
        problem.capacity = 100
        problem.nodes = [(0, 0)] + [(i * 5, i * 3) for i in range(1, 21)]

        # Crear individuos mock
        ind1 = MagicMock()
        ind1.fitness.return_value = 500
        ind1.position = np.array([1.0, 2.0, 3.0])

        ind2 = MagicMock()
        ind2.fitness.return_value = 600
        ind2.position = np.array([4.0, 5.0, 6.0])

        algorithm = MagicMock()
        algorithm.population = [ind1, ind2]
        # Convergence curve con mas de 10 elementos (cubre linea 428-444)
        algorithm.convergence_curve = [
            1000, 950, 900, 850, 800, 750, 700, 650, 600, 550, 500, 500
        ]

        state = create_state_from_problem(problem, algorithm, 50, 100)

        # Con convergence_curve > 10, debe calcular convergence_rate
        assert state["convergence_rate"] > 0
        # Stagnation counter: ultimos 2 valores son iguales (500, 500)
        assert state["stagnation_counter"] >= 1

    def test_state_single_pop(self):
        """Test linea 460: poblacion con un solo individuo."""
        from utils.imitation_learning import create_state_from_problem

        problem = MagicMock()
        problem.dimension = 21
        problem.demands = np.array([0] + [10] * 20)
        problem.capacity = 100
        problem.nodes = [(0, 0)] + [(i * 5, i * 3) for i in range(1, 21)]

        # Solo 1 individuo -> len(population) > 1 es False
        ind1 = MagicMock()
        ind1.fitness.return_value = 500
        ind1.position = np.array([1.0, 2.0, 3.0])

        algorithm = MagicMock()
        algorithm.population = [ind1]
        algorithm.convergence_curve = [600, 550, 500]

        state = create_state_from_problem(problem, algorithm, 10, 100)

        # Con un solo individuo, population_diversity debe ser 0.5 (default, linea 460)
        assert state["population_diversity"] == 0.5
        # Pero fitness se calcula de la poblacion (1 individuo = funciona)
        assert state["best_fitness"] == 500
