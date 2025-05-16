#!/usr/bin/env python3
"""
Test para verificar que se captura correctamente el tiempo promedio por iteración (avg_iter_time).
"""

import os
import json
import tempfile
import pandas as pd
import subprocess
import sys
import pytest
import shutil
from pathlib import Path


def test_avg_iter_time_capture():
    """
    Verifica que run_massive.py capture correctamente el tiempo promedio por
    iteración y lo incluya en el CSV y en el manifest.json.
    """
    # Usar directorio temporal para la salida
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Ejecutar run_massive.py con parámetros específicos para test rápido
        cmd = [
            sys.executable,
            "scripts/run_massive.py",
            "--runs",
            "1",
            "--iterations",
            "5",
            "--population",
            "5",
            "--algorithm",
            "hho",
            "--instances",
            "P-n16-k8",
            "--no-parallel",
            "--no-profile",
            "--output-dir",
            tmp_dir,
        ]

        # Configurar el entorno para añadir el proyecto a PYTHONPATH
        env = os.environ.copy()
        # Usar el separador de ruta correcto según el sistema operativo
        separator = os.pathsep
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = project_root + (separator + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")

        # Ejecutar el script con el entorno modificado
        process = subprocess.run(
            cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )

        # Verificar que el proceso terminó correctamente
        assert process.returncode == 0, f"Error al ejecutar run_massive.py: {process.stderr.decode()}"

        # Verificar que se creó el CSV de resultados
        csv_path = Path(tmp_dir) / "massive_benchmark_summary.csv"
        assert csv_path.exists(), "No se encontró el CSV de resumen"

        # Leer el CSV y verificar que contiene la columna avg_iter_time
        df = pd.read_csv(csv_path)
        assert "avg_iter_time" in df.columns, "El CSV no contiene la columna 'avg_iter_time'"

        # Verificar que el valor de avg_iter_time es mayor que cero
        assert df["avg_iter_time"].iloc[0] > 0, "El valor de avg_iter_time no es positivo"

        # Verificar que el manifest.json contiene el tiempo promedio global por iteración
        manifest_path = Path(tmp_dir) / "manifest.json"
        assert manifest_path.exists(), "No se encontró el manifest.json"

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert "avg_iter_time_overall" in manifest, "El manifest.json no contiene 'avg_iter_time_overall'"
        assert manifest["avg_iter_time_overall"] > 0, "El valor de avg_iter_time_overall no es positivo"


if __name__ == "__main__":
    test_avg_iter_time_capture()
