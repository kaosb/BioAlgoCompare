#!/usr/bin/env python3
"""
Test end-to-end para verificar que el tiempo promedio por iteración se propaga al CSV.
"""

import os
import subprocess
import pandas as pd
import pytest
from pathlib import Path


def test_avg_iter_time_in_summary_csv():
    """Verifica que avg_iter_time se propaga correctamente al CSV de resumen."""
    # Definir ruta de resultados
    output_dir = "results/timing_smoke"

    # Eliminar directorio si existe
    if os.path.exists(output_dir):
        import shutil

        shutil.rmtree(output_dir)

    # Ejecutar benchmark con pocas iteraciones
    cmd = [
        "python",
        "scripts/run_massive.py",
        "-a",
        "hho",
        "-i",
        "P-n16-k8",
        "-r",
        "1",
        "-n",
        "5",
        "--no-parallel",
        "-o",
        output_dir,
    ]

    # Ejecutar en el entorno actual
    python_path = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = (
        f"{python_path}:{os.getcwd()}" if python_path else os.getcwd()
    )

    # Ejecutar el script como subproceso
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Verificar que el comando se ejecutó correctamente
    assert result.returncode == 0, f"Error en ejecución: {result.stderr}"

    # Ruta al CSV de resumen
    summary_csv = Path(output_dir) / "massive_benchmark_summary.csv"

    # Verificar que el CSV existe
    assert summary_csv.exists(), f"No se encontró el CSV de resumen en {summary_csv}"

    # Cargar el CSV
    df = pd.read_csv(summary_csv)

    # Verificar que existe la columna avg_iter_time
    assert (
        "avg_iter_time" in df.columns
    ), "La columna avg_iter_time no está presente en el CSV"

    # Verificar que el valor es mayor que 0
    assert (
        df["avg_iter_time"].iloc[0] > 0
    ), "El tiempo promedio por iteración debe ser mayor que 0"

    print(f"Tiempo promedio por iteración: {df['avg_iter_time'].iloc[0]:.6f} segundos")


if __name__ == "__main__":
    test_avg_iter_time_in_summary_csv()
