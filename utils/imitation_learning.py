"""
Imitation Learning Module for Dynamic HO Parameters — LEGACY / DEPRECATED

*** ADVERTENCIA DE INTEGRIDAD (saneado 8 Jul 2026) ***
Este módulo pertenece al enfoque HO+IL original, REFUTADO y auditado. NO usar
para nuevo trabajo; el estudio riguroso vive en algorithms/hindsight_oracle.py
y utils/bc_policy.py (ver tesis-mia/gestion_proyecto/AUDITORIA_IMPLEMENTACION_IL.md).
Problemas conocidos de este enfoque:
  - La referencia que antes se citaba aquí ("Barros & Everett 2023, Imitation
    Learning for Metaheuristic Optimization") NO EXISTE — era fabricada. Eliminada.
  - HO (Amiri et al. 2024, Sci. Rep. 14:5032) es PARAMETER-FREE: los parámetros
    (α, β, γ) y sus rangos son una augmentación INVENTADA, no están en el paper
    (esos rangos corresponden a otros algoritmos, p.ej. Firefly, en la tabla
    comparativa de Amiri 2024).
  - El "experto" de las demostraciones (utils/generate_simple_demos.py) son
    fórmulas analíticas escritas a mano, no un experto real → no es imitation
    learning legítimo.
Referencias reales verificadas: tesis-mia/gestion_proyecto/REFERENCIAS_IL_VERIFICADAS.bib

Arquitectura (histórica): red de 3 capas (64 → 128 → 64 → 3); input = estado de
instancia; output = α, β, γ normalizados.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
import os
import json
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


class HO_PolicyNet(nn.Module):
    """
    Red neuronal para política de parámetros HO.

    Arquitectura de 3 capas fully connected con activaciones ReLU
    y capa de salida con sigmoid para normalizar parámetros.
    """

    def __init__(self, input_dim: int = 64, hidden_dim: int = 128):
        """
        Inicializa la red de política.

        Args:
            input_dim: Dimensión del estado de entrada (default: 64)
            hidden_dim: Dimensión de capas ocultas (default: 128)
        """
        super(HO_PolicyNet, self).__init__()

        # Arquitectura de 3 capas
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 64)
        self.fc3 = nn.Linear(64, 3)  # Output: α, β, γ

        # Activaciones
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

        # Rangos de parámetros según Amiri et al. 2024
        self.param_ranges = {
            "alpha": (0.1, 0.9),
            "beta": (0.2, 0.8),
            "gamma": (0.3, 1.0),
        }

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass de la red.

        Args:
            x: Tensor de entrada con estado de la instancia

        Returns:
            Tensor con parámetros α, β, γ normalizados
        """
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.sigmoid(self.fc3(x))  # Output en [0, 1]

        # Escalar a rangos específicos de cada parámetro
        alpha = (
            x[:, 0] * (self.param_ranges["alpha"][1] - self.param_ranges["alpha"][0])
            + self.param_ranges["alpha"][0]
        )
        beta = (
            x[:, 1] * (self.param_ranges["beta"][1] - self.param_ranges["beta"][0])
            + self.param_ranges["beta"][0]
        )
        gamma = (
            x[:, 2] * (self.param_ranges["gamma"][1] - self.param_ranges["gamma"][0])
            + self.param_ranges["gamma"][0]
        )

        return torch.stack([alpha, beta, gamma], dim=1)


class HOImitationLearning:
    """
    Sistema de Imitation Learning para HO.

    Entrena una política para predecir parámetros óptimos basándose
    en el estado actual de la optimización.
    """

    def __init__(self, input_dim: int = 64, device: str = None):
        """
        Inicializa el sistema de IL.

        Args:
            input_dim: Dimensión del estado
            device: Dispositivo para cómputo ('cuda' o 'cpu')
        """
        self.input_dim = input_dim
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Modelo y escalador
        self.model = HO_PolicyNet(input_dim).to(self.device)
        self.scaler = StandardScaler()

        # Estado del entrenamiento
        self.is_trained = False
        self.training_history = []

    def extract_features(self, state: Dict) -> np.ndarray:
        """
        Extrae características del estado actual.

        Args:
            state: Diccionario con información del estado:
                - n_customers: número de clientes
                - n_depots: número de depósitos
                - avg_demand: demanda promedio
                - demand_std: desviación estándar de demanda
                - capacity: capacidad del vehículo
                - area_span: área de cobertura
                - density: densidad de clientes
                - iteration: iteración actual
                - progress: progreso (iteration/max_iterations)
                - best_fitness: mejor fitness actual
                - avg_fitness: fitness promedio población
                - fitness_std: desviación estándar fitness
                - convergence_rate: tasa de convergencia
                - stagnation_counter: iteraciones sin mejora

        Returns:
            Vector de características de dimensión 64
        """
        # Características básicas de la instancia
        features = [
            state.get("n_customers", 0) / 100.0,  # Normalizado
            state.get("n_depots", 1) / 10.0,
            state.get("avg_demand", 0) / 50.0,
            state.get("demand_std", 0) / 20.0,
            state.get("capacity", 100) / 200.0,
            state.get("area_span", 100) / 200.0,
            state.get("density", 0.5),
        ]

        # Características del progreso de optimización
        features.extend(
            [
                state.get("iteration", 0) / 1000.0,
                state.get("progress", 0.0),
                state.get("best_fitness", 1000) / 2000.0,
                state.get("avg_fitness", 1000) / 2000.0,
                state.get("fitness_std", 100) / 500.0,
                state.get("convergence_rate", 0.0),
                state.get("stagnation_counter", 0) / 50.0,
            ]
        )

        # Características de diversidad poblacional
        features.extend(
            [
                state.get("population_diversity", 0.5),
                state.get("elite_ratio", 0.1),
                state.get("improvement_rate", 0.0),
            ]
        )

        # Características dinámicas (para DVRP)
        features.extend(
            [
                state.get("dynamic_orders", 0) / 20.0,
                state.get("avg_delay", 0) / 100.0,
                state.get("load_imbalance", 0.0),
            ]
        )

        # Padding con características derivadas hasta 64 dimensiones
        while len(features) < self.input_dim:
            # Agregar características no lineales
            if len(features) < self.input_dim - 10:
                features.append(
                    features[-1] * features[-2] if len(features) > 1 else 0
                )  # Interacciones
            else:
                features.append(0.0)  # Padding con ceros

        return np.array(features[: self.input_dim], dtype=np.float32)

    def train(
        self,
        demos_csv: str,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
        seed: int = 42,
    ) -> Dict:
        """
        Entrena el modelo con demostraciones.

        Args:
            demos_csv: Ruta al archivo CSV con demostraciones
            epochs: Número de épocas de entrenamiento
            batch_size: Tamaño del batch
            validation_split: Proporción para validación
            seed: Semilla para reproducibilidad

        Returns:
            Diccionario con métricas de entrenamiento
        """
        # Fijar semillas para reproducibilidad
        torch.manual_seed(seed)
        np.random.seed(seed)

        # Cargar datos
        print(f"Cargando demostraciones desde {demos_csv}...")
        df = pd.read_csv(demos_csv)

        # Preparar features y targets
        X = []
        y = []

        for _, row in df.iterrows():
            # Construir estado desde el CSV
            state = {
                col: row[col]
                for col in df.columns
                if col not in ["alpha", "beta", "gamma"]
            }
            features = self.extract_features(state)
            X.append(features)

            # Targets son los parámetros óptimos
            y.append([row["alpha"], row["beta"], row["gamma"]])

        X = np.array(X)
        y = np.array(y)

        # Normalizar features
        X = self.scaler.fit_transform(X)

        # Split train/validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=seed
        )

        # Convertir a tensores
        X_train = torch.FloatTensor(X_train).to(self.device)
        y_train = torch.FloatTensor(y_train).to(self.device)
        X_val = torch.FloatTensor(X_val).to(self.device)
        y_val = torch.FloatTensor(y_val).to(self.device)

        # Configurar optimizador y loss
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        # Entrenamiento
        print(f"Entrenando por {epochs} épocas...")
        train_losses = []
        val_losses = []

        for epoch in range(epochs):
            # Training
            self.model.train()
            epoch_loss = 0.0

            # Mini-batches
            n_batches = len(X_train) // batch_size
            for i in range(n_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(X_train))

                batch_X = X_train[start_idx:end_idx]
                batch_y = y_train[start_idx:end_idx]

                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val)
                val_loss = criterion(val_outputs, y_val).item()

            train_losses.append(epoch_loss / n_batches)
            val_losses.append(val_loss)

            if (epoch + 1) % 10 == 0:
                print(
                    f"Época {epoch+1}/{epochs} - Loss Train: {train_losses[-1]:.4f}, Loss Val: {val_losses[-1]:.4f}"
                )

        self.is_trained = True
        self.training_history = {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "final_train_loss": train_losses[-1],
            "final_val_loss": val_losses[-1],
        }

        print(
            f"Entrenamiento completado. Loss final: Train={train_losses[-1]:.4f}, Val={val_losses[-1]:.4f}"
        )

        return self.training_history

    def predict(self, state: Dict) -> Tuple[float, float, float]:
        """
        Predice parámetros óptimos para el estado actual.

        Args:
            state: Estado actual de la optimización

        Returns:
            Tupla (α, β, γ) con parámetros predichos
        """
        if not self.is_trained:
            # Si no está entrenado, devolver valores por defecto
            return 0.5, 0.5, 0.65

        # Extraer y normalizar features
        features = self.extract_features(state)
        features = self.scaler.transform(features.reshape(1, -1))
        features_tensor = torch.FloatTensor(features).to(self.device)

        # Predicción
        self.model.eval()
        with torch.no_grad():
            params = self.model(features_tensor).cpu().numpy()[0]

        return float(params[0]), float(params[1]), float(params[2])

    def save(self, filepath: str):
        """Guarda el modelo entrenado."""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "scaler": self.scaler,
                "training_history": self.training_history,
                "is_trained": self.is_trained,
            },
            filepath,
        )
        print(f"Modelo guardado en {filepath}")

    def load(self, filepath: str):
        """Carga un modelo entrenado."""
        checkpoint = torch.load(filepath, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.scaler = checkpoint["scaler"]
        self.training_history = checkpoint["training_history"]
        self.is_trained = checkpoint["is_trained"]
        print(f"Modelo cargado desde {filepath}")


def create_state_from_problem(
    problem, algorithm, iteration: int, max_iterations: int
) -> Dict:
    """
    Crea un estado desde el problema VRP y el algoritmo actual.

    Args:
        problem: Instancia de VRPProblem
        algorithm: Instancia del algoritmo (HO)
        iteration: Iteración actual
        max_iterations: Máximo de iteraciones

    Returns:
        Diccionario con el estado actual
    """
    # Características de la instancia
    state = {
        "n_customers": problem.dimension - 1 if hasattr(problem, "dimension") else 0,
        "n_depots": len(problem.depots) if hasattr(problem, "depots") else 1,
        "avg_demand": np.mean(problem.demands[1:])
        if hasattr(problem, "demands")
        else 0,
        "demand_std": np.std(problem.demands[1:]) if hasattr(problem, "demands") else 0,
        "capacity": problem.capacity if hasattr(problem, "capacity") else 100,
    }

    # Área de cobertura
    if hasattr(problem, "nodes") and problem.nodes:
        xs = [node[0] for node in problem.nodes]
        ys = [node[1] for node in problem.nodes]
        state["area_span"] = max(max(xs) - min(xs), max(ys) - min(ys))
        state["density"] = (
            len(problem.nodes) / (state["area_span"] ** 2)
            if state["area_span"] > 0
            else 0
        )
    else:
        state["area_span"] = 100
        state["density"] = 0.01

    # Estado de optimización
    state["iteration"] = iteration
    state["progress"] = iteration / max_iterations

    # Fitness de la población
    if hasattr(algorithm, "population") and algorithm.population:
        fitness_values = [ind.fitness() for ind in algorithm.population]
        state["best_fitness"] = min(fitness_values)
        state["avg_fitness"] = np.mean(fitness_values)
        state["fitness_std"] = np.std(fitness_values)
    else:
        state["best_fitness"] = 1000
        state["avg_fitness"] = 1000
        state["fitness_std"] = 0

    # Convergencia
    if hasattr(algorithm, "convergence_curve") and len(algorithm.convergence_curve) > 1:
        if len(algorithm.convergence_curve) > 10:
            recent_improvement = (
                algorithm.convergence_curve[-10] - algorithm.convergence_curve[-1]
            )
            state["convergence_rate"] = recent_improvement / (
                algorithm.convergence_curve[-10] + 1e-10
            )
        else:
            state["convergence_rate"] = 0

        # Estancamiento
        state["stagnation_counter"] = 0
        for i in range(1, min(20, len(algorithm.convergence_curve))):
            if algorithm.convergence_curve[-i] == algorithm.convergence_curve[-i - 1]:
                state["stagnation_counter"] += 1
            else:
                break
    else:
        state["convergence_rate"] = 0
        state["stagnation_counter"] = 0

    # Diversidad poblacional (vectorizado para eficiencia)
    if hasattr(algorithm, "population") and len(algorithm.population) > 1:
        positions = np.array([ind.position for ind in algorithm.population])
        # Sample-based diversity for large populations (avoid O(n^2))
        n_pop = len(positions)
        if n_pop > 30:
            # Sample 30 individuals for diversity estimation
            sample_idx = np.random.choice(n_pop, size=30, replace=False)
            positions_sample = positions[sample_idx]
        else:
            positions_sample = positions
        # Vectorized pairwise distances
        diffs = positions_sample[:, None, :] - positions_sample[None, :, :]
        distances = np.linalg.norm(diffs, axis=2)
        triu_idx = np.triu_indices(len(positions_sample), k=1)
        state["population_diversity"] = float(np.mean(distances[triu_idx])) if len(triu_idx[0]) > 0 else 0
    else:
        state["population_diversity"] = 0.5

    # Características dinámicas (real values when available)
    state["dynamic_orders"] = (
        len(problem.dynamic_orders) if hasattr(problem, "dynamic_orders") else 0
    )
    state["avg_delay"] = (
        float(np.mean(problem.delays)) if hasattr(problem, "delays") and len(getattr(problem, "delays", [])) > 0 else 0
    )
    state["load_imbalance"] = (
        float(np.std(problem.vehicle_loads)) if hasattr(problem, "vehicle_loads") and len(getattr(problem, "vehicle_loads", [])) > 0 else 0
    )

    # Elite ratio: fraction of population within 10% of best fitness
    if hasattr(algorithm, "population") and algorithm.population:
        fitness_values = [ind.fitness() for ind in algorithm.population]
        best = min(fitness_values)
        threshold = best * 1.10 if best > 0 else best - abs(best) * 0.10
        elite_count = sum(1 for f in fitness_values if f <= threshold)
        state["elite_ratio"] = elite_count / len(fitness_values)
    else:
        state["elite_ratio"] = 0.1

    # Improvement rate: relative improvement over last 5 iterations
    if hasattr(algorithm, "convergence_curve") and len(algorithm.convergence_curve) > 5:
        old_fit = algorithm.convergence_curve[-5]
        new_fit = algorithm.convergence_curve[-1]
        state["improvement_rate"] = (old_fit - new_fit) / (old_fit + 1e-10)
    else:
        state["improvement_rate"] = state.get("convergence_rate", 0)

    return state
