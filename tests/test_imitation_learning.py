"""
Tests para el módulo de Imitation Learning de HO.

Valida:
- Arquitectura de la red neuronal
- Extracción de características
- Entrenamiento y predicción
- Integración con HO
- Mejora de performance con IL
"""

import pytest
import numpy as np
import torch
import pandas as pd
import os
import tempfile
from problems.vrp import VRPProblem
from algorithms.ho import HO
from utils.imitation_learning import (
    HO_PolicyNet,
    HOImitationLearning,
    create_state_from_problem,
)


class TestHOPolicyNet:
    """Tests para la red neuronal de política."""

    def test_network_architecture(self):
        """Test arquitectura de la red."""
        net = HO_PolicyNet(input_dim=64, hidden_dim=128)

        # Verificar capas
        assert hasattr(net, "fc1")
        assert hasattr(net, "fc2")
        assert hasattr(net, "fc3")

        # Verificar dimensiones
        assert net.fc1.in_features == 64
        assert net.fc1.out_features == 128
        assert net.fc2.in_features == 128
        assert net.fc2.out_features == 64
        assert net.fc3.in_features == 64
        assert net.fc3.out_features == 3

    def test_forward_pass(self):
        """Test forward pass de la red."""
        net = HO_PolicyNet()

        # Input batch
        batch_size = 10
        x = torch.randn(batch_size, 64)

        # Forward
        output = net(x)

        # Verificar dimensiones de salida
        assert output.shape == (batch_size, 3)

        # Verificar rangos de parámetros
        alpha = output[:, 0].detach()
        beta = output[:, 1].detach()
        gamma = output[:, 2].detach()

        # Usar torch en lugar de numpy para evitar el error
        assert torch.all((alpha >= 0.1) & (alpha <= 0.9))
        assert torch.all((beta >= 0.2) & (beta <= 0.8))
        assert torch.all((gamma >= 0.3) & (gamma <= 1.0))


class TestHOImitationLearning:
    """Tests para el sistema de IL."""

    def test_initialization(self):
        """Test inicialización del sistema IL."""
        il = HOImitationLearning(input_dim=64)

        assert il.input_dim == 64
        assert il.device in ["cpu", "cuda"]
        assert isinstance(il.model, HO_PolicyNet)
        assert il.is_trained == False

    def test_feature_extraction(self):
        """Test extracción de características."""
        il = HOImitationLearning()

        # Estado de ejemplo
        state = {
            "n_customers": 50,
            "n_depots": 2,
            "avg_demand": 15.0,
            "demand_std": 5.0,
            "capacity": 100,
            "area_span": 150,
            "density": 0.02,
            "iteration": 50,
            "progress": 0.5,
            "best_fitness": 800,
            "avg_fitness": 900,
            "fitness_std": 50,
            "convergence_rate": 0.05,
            "stagnation_counter": 3,
            "population_diversity": 0.4,
            "elite_ratio": 0.1,
            "improvement_rate": 0.03,
            "dynamic_orders": 5,
            "avg_delay": 10,
            "load_imbalance": 0.15,
        }

        features = il.extract_features(state)

        # Verificar dimensión
        assert len(features) == 64
        assert features.dtype == np.float32

        # Verificar normalización (valores en rango razonable)
        assert np.all(features >= -10) and np.all(features <= 10)

    def test_training_process(self):
        """Test proceso de entrenamiento."""
        il = HOImitationLearning()

        # Crear datos sintéticos
        n_samples = 100
        data = []

        for i in range(n_samples):
            row = {
                "n_customers": np.random.randint(10, 100),
                "n_depots": np.random.randint(1, 5),
                "avg_demand": np.random.uniform(5, 20),
                "demand_std": np.random.uniform(1, 10),
                "capacity": np.random.randint(50, 200),
                "area_span": np.random.uniform(50, 200),
                "density": np.random.uniform(0.01, 0.1),
                "iteration": np.random.randint(0, 100),
                "progress": np.random.uniform(0, 1),
                "best_fitness": np.random.uniform(500, 1500),
                "avg_fitness": np.random.uniform(600, 1600),
                "fitness_std": np.random.uniform(10, 100),
                "convergence_rate": np.random.uniform(0, 0.1),
                "stagnation_counter": np.random.randint(0, 20),
                "population_diversity": np.random.uniform(0.1, 0.9),
                "elite_ratio": 0.1,
                "improvement_rate": np.random.uniform(0, 0.1),
                "dynamic_orders": np.random.randint(0, 10),
                "avg_delay": np.random.uniform(0, 50),
                "load_imbalance": np.random.uniform(0, 0.5),
                # Parámetros objetivo (ground truth)
                "alpha": np.random.uniform(0.1, 0.9),
                "beta": np.random.uniform(0.2, 0.8),
                "gamma": np.random.uniform(0.3, 1.0),
            }
            data.append(row)

        # Guardar a CSV temporal
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df = pd.DataFrame(data)
            df.to_csv(f.name, index=False)
            temp_file = f.name

        try:
            # Entrenar
            history = il.train(temp_file, epochs=5, batch_size=32, seed=42)

            # Verificar que se entrenó
            assert il.is_trained == True
            assert "train_losses" in history
            assert "val_losses" in history
            assert len(history["train_losses"]) == 5

            # Verificar que el loss disminuye
            assert history["train_losses"][-1] < history["train_losses"][0]

        finally:
            # Limpiar archivo temporal
            os.unlink(temp_file)

    def test_prediction(self):
        """Test predicción de parámetros."""
        il = HOImitationLearning()

        # Estado de prueba
        state = {
            "n_customers": 30,
            "n_depots": 1,
            "avg_demand": 10,
            "demand_std": 3,
            "capacity": 80,
            "area_span": 100,
            "density": 0.03,
            "iteration": 25,
            "progress": 0.25,
            "best_fitness": 600,
            "avg_fitness": 700,
            "fitness_std": 30,
            "convergence_rate": 0.08,
            "stagnation_counter": 0,
            "population_diversity": 0.6,
            "elite_ratio": 0.1,
            "improvement_rate": 0.05,
            "dynamic_orders": 0,
            "avg_delay": 0,
            "load_imbalance": 0.1,
        }

        # Sin entrenar, debe devolver valores por defecto
        alpha, beta, gamma = il.predict(state)
        assert alpha == 0.5
        assert beta == 0.5
        assert gamma == 0.65

    def test_save_load_model(self):
        """Test guardar y cargar modelo."""
        il = HOImitationLearning()

        # Cambiar estado para simular entrenamiento
        il.is_trained = True
        il.training_history = {"test": "data"}

        # Guardar
        with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
            temp_file = f.name

        try:
            il.save(temp_file)

            # Crear nueva instancia y cargar
            il2 = HOImitationLearning()
            il2.load(temp_file)

            # Verificar que se cargó correctamente
            assert il2.is_trained == True
            assert il2.training_history == {"test": "data"}

        finally:
            os.unlink(temp_file)


class TestCreateStateFromProblem:
    """Tests para la función de creación de estado."""

    def test_create_state_basic(self):
        """Test creación de estado básico."""
        # Crear problema VRP simple
        problem = VRPProblem(seed=42)
        problem.nodes = [(0, 0), (10, 0), (0, 10), (10, 10)]
        problem.demands = [0, 5, 10, 15]
        problem.capacity = 30
        problem.dimension = 4
        problem.compute_distance_matrix()

        # Crear algoritmo HO
        ho = HO(problem, population_size=10, max_iterations=100, seed=42)
        ho.initialize_population()

        # Crear estado
        state = create_state_from_problem(problem, ho, 50, 100)

        # Verificar campos básicos
        assert state["n_customers"] == 3  # dimension - 1
        assert state["n_depots"] == 1
        assert state["capacity"] == 30
        assert state["iteration"] == 50
        assert state["progress"] == 0.5

        # Verificar que tiene todos los campos necesarios
        expected_fields = [
            "n_customers",
            "n_depots",
            "avg_demand",
            "demand_std",
            "capacity",
            "area_span",
            "density",
            "iteration",
            "progress",
            "best_fitness",
            "avg_fitness",
            "fitness_std",
            "convergence_rate",
            "stagnation_counter",
            "population_diversity",
            "elite_ratio",
            "improvement_rate",
            "dynamic_orders",
            "avg_delay",
            "load_imbalance",
        ]

        for field in expected_fields:
            assert field in state


class TestHOWithIL:
    """Tests para HO con IL integrado."""

    def test_ho_with_il_initialization(self):
        """Test inicialización de HO con IL."""
        problem = VRPProblem(seed=42)

        # Sin IL
        ho1 = HO(problem, use_il=False)
        assert ho1.use_il == False
        assert ho1.il_model is None

        # Con IL pero sin modelo
        ho2 = HO(problem, use_il=True)
        assert ho2.use_il == False  # Se desactiva si no hay modelo

        # Con IL y modelo válido (simulado)
        with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
            # Crear modelo dummy
            il = HOImitationLearning()
            il.save(f.name)

            ho3 = HO(problem, use_il=True, il_model_path=f.name)
            # Nota: Puede fallar la carga por compatibilidad, pero verifica el intento

            os.unlink(f.name)

    def test_ho_parameter_adaptation_with_il(self):
        """Test adaptación de parámetros con IL."""
        # Este test verifica que HO puede ejecutarse con IL habilitado
        problem = VRPProblem(seed=42)
        problem.nodes = [(0, 0), (5, 0), (0, 5), (5, 5)]
        problem.demands = [0, 5, 5, 5]
        problem.capacity = 15
        problem.dimension = 4
        problem.compute_distance_matrix()

        # Ejecutar HO estándar
        ho_standard = HO(problem, population_size=5, max_iterations=10, seed=42)
        ho_standard.execute()
        fitness_standard = ho_standard.best_solution.fitness()

        # Ejecutar HO con IL (sin modelo entrenado, usa fallback)
        ho_il = HO(problem, population_size=5, max_iterations=10, seed=42, use_il=True)
        ho_il.execute()
        fitness_il = ho_il.best_solution.fitness()

        # Ambos deberían funcionar
        assert fitness_standard > 0
        assert fitness_il > 0


def test_il_improves_convergence():
    """Test que IL mejora la convergencia (placeholder para evaluación completa)."""
    # Este test requiere un modelo IL entrenado real
    # Por ahora solo verifica que el sistema funciona

    problem = VRPProblem(seed=42)
    problem.nodes = [(0, 0)] + [
        (np.random.uniform(-10, 10), np.random.uniform(-10, 10)) for _ in range(10)
    ]
    problem.demands = [0] + [np.random.randint(1, 10) for _ in range(10)]
    problem.capacity = 30
    problem.dimension = 11
    problem.compute_distance_matrix()

    # Ejecutar varias veces y calcular estadísticas
    runs = 5
    fitness_standard = []
    fitness_il = []

    for i in range(runs):
        # HO estándar
        ho1 = HO(problem, population_size=10, max_iterations=20, seed=42 + i)
        ho1.execute()
        fitness_standard.append(ho1.best_solution.fitness())

        # HO con IL (fallback)
        ho2 = HO(
            problem, population_size=10, max_iterations=20, seed=42 + i, use_il=True
        )
        ho2.execute()
        fitness_il.append(ho2.best_solution.fitness())

    # Verificar que ambos métodos producen resultados válidos
    assert all(f > 0 for f in fitness_standard)
    assert all(f > 0 for f in fitness_il)

    # Con un modelo entrenado real, esperaríamos:
    # assert np.mean(fitness_il) < np.mean(fitness_standard)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
