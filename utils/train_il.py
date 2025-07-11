#!/usr/bin/env python3
"""
Script para entrenar el modelo de Imitation Learning para HO.

Entrena una red neuronal para predecir parámetros óptimos de HO
basándose en el estado actual de la optimización.

Uso:
    python utils/train_il.py --dataset demos.csv --epochs 100
"""

import argparse
import os
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.imitation_learning import HOImitationLearning  # noqa: E402


def plot_training_history(history: dict, output_path: str):
    """Genera gráficos del historial de entrenamiento."""
    plt.figure(figsize=(10, 6))

    epochs = range(1, len(history["train_losses"]) + 1)

    plt.plot(epochs, history["train_losses"], "b-", label="Train Loss")
    plt.plot(epochs, history["val_losses"], "r-", label="Validation Loss")

    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.title("Training History - HO Imitation Learning")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f"Gráfico guardado en: {output_path}")


def analyze_predictions(model: HOImitationLearning, test_data: pd.DataFrame):
    """Analiza las predicciones del modelo en datos de prueba."""
    print("\nAnálisis de predicciones en datos de prueba:")

    errors = {"alpha": [], "beta": [], "gamma": []}

    for _, row in test_data.iterrows():
        # Crear estado
        state = {
            col: row[col]
            for col in test_data.columns
            if col not in ["alpha", "beta", "gamma"]
        }

        # Predecir
        pred_alpha, pred_beta, pred_gamma = model.predict(state)

        # Calcular errores
        errors["alpha"].append(abs(pred_alpha - row["alpha"]))
        errors["beta"].append(abs(pred_beta - row["beta"]))
        errors["gamma"].append(abs(pred_gamma - row["gamma"]))

    # Estadísticas
    for param in ["alpha", "beta", "gamma"]:
        mae = np.mean(errors[param])
        std = np.std(errors[param])
        print(f"  {param}: MAE = {mae:.4f} ± {std:.4f}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Entrenar modelo IL para HO")
    parser.add_argument(
        "--dataset",
        type=str,
        default="results/demos_ho_il.csv",
        help="Archivo CSV con demostraciones",
    )
    parser.add_argument(
        "--epochs", type=int, default=100, help="Número de épocas de entrenamiento"
    )
    parser.add_argument("--batch-size", type=int, default=32, help="Tamaño del batch")
    parser.add_argument(
        "--val-split", type=float, default=0.2, help="Proporción para validación"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Semilla para reproducibilidad"
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="ho_il_model.pth",
        help="Archivo para guardar el modelo",
    )

    args = parser.parse_args()

    print("Configuración de entrenamiento:")
    print(f"  Dataset: {args.dataset}")
    print(f"  Épocas: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Validación: {args.val_split*100:.0f}%")
    print(f"  Semilla: {args.seed}")

    # Verificar que existe el dataset
    if not os.path.exists(args.dataset):
        print(f"\nError: No se encontró el dataset {args.dataset}")
        print("Ejecuta primero: python utils/generate_demos.py")
        return

    # Crear modelo
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nDispositivo: {device}")

    model = HOImitationLearning(input_dim=64, device=device)

    # Entrenar
    print("\nIniciando entrenamiento...")
    start_time = datetime.now()

    history = model.train(
        demos_csv=args.dataset,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=args.val_split,
        seed=args.seed,
    )

    end_time = datetime.now()
    training_time = (end_time - start_time).total_seconds()

    print(f"\nTiempo de entrenamiento: {training_time:.2f} segundos")

    # Guardar modelo
    model_path = os.path.join("models", args.model_output)
    os.makedirs("models", exist_ok=True)
    model.save(model_path)

    # Generar gráfico
    plot_path = os.path.join("results", "ho_il_training_history.png")
    plot_training_history(history, plot_path)

    # Análisis adicional con hold-out test set
    print("\nCargando datos para análisis...")
    full_data = pd.read_csv(args.dataset)
    test_size = int(len(full_data) * args.val_split)
    test_data = full_data.iloc[-test_size:]

    analyze_predictions(model, test_data)

    # Ejemplo de predicción
    print("\nEjemplo de predicción:")
    example_state = {
        "n_customers": 50,
        "n_depots": 1,
        "avg_demand": 15,
        "demand_std": 5,
        "capacity": 100,
        "area_span": 100,
        "density": 0.05,
        "iteration": 50,
        "progress": 0.5,
        "best_fitness": 800,
        "avg_fitness": 900,
        "fitness_std": 50,
        "convergence_rate": 0.05,
        "stagnation_counter": 5,
        "population_diversity": 0.4,
        "elite_ratio": 0.1,
        "improvement_rate": 0.03,
        "dynamic_orders": 0,
        "avg_delay": 0,
        "load_imbalance": 0.1,
    }

    alpha, beta, gamma = model.predict(example_state)
    print(
        f"  Estado: progress={example_state['progress']}, stagnation={example_state['stagnation_counter']}"
    )
    print(f"  Parámetros predichos: α={alpha:.3f}, β={beta:.3f}, γ={gamma:.3f}")

    print("\n✓ Entrenamiento completado exitosamente")


if __name__ == "__main__":
    main()
