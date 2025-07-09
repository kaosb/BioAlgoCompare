#!/usr/bin/env python3
"""
Test para verificar generación de manifest.json y columna avg_iter_time en run_massive.py
"""

import os
import tempfile
import json
import pytest
import sys
import pandas as pd
import subprocess
from pathlib import Path


def test_run_massive_manifest_and_avg_time():
    """
    Verifica que run_massive.py genere correctamente el manifest.json y
    añada la columna avg_iter_time al CSV de resultados.
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
            "1",
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

        try:
            # Configurar el entorno para añadir el proyecto a PYTHONPATH
            env = os.environ.copy()
            # Usar el separador de ruta correcto según el sistema operativo
            separator = os.pathsep
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env["PYTHONPATH"] = project_root + (
                separator + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else ""
            )

            # Ejecutar el script con el entorno modificado
            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )

            # Verificar que se creó el manifest.json
            manifest_path = Path(tmp_dir) / "manifest.json"
            assert manifest_path.exists(), "No se encontró manifest.json"

            # Verificar contenido del manifest
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            # Comprobar campos requeridos
            assert "params" in manifest, "El manifest no contiene sección 'params'"
            assert "git_commit" in manifest, "El manifest no contiene 'git_commit'"
            assert (
                "python_version" in manifest
            ), "El manifest no contiene 'python_version'"
            assert "cpu_count" in manifest, "El manifest no contiene 'cpu_count'"

            # Verificar que se creó el CSV de resultados
            csv_path = Path(tmp_dir) / "massive_benchmark_summary.csv"
            assert csv_path.exists(), "No se encontró el CSV de resumen"

            # Verificar que el CSV contiene la columna avg_iter_time
            df = pd.read_csv(csv_path)
            assert (
                "avg_iter_time" in df.columns
            ), "El CSV no contiene la columna 'avg_iter_time'"

            # Verificar que hay al menos una fila con algoritmo HHO
            hho_rows = df[df["Algorithm"] == "HHO"]
            assert not hho_rows.empty, "No se encontraron resultados para HHO"

            # Verificar que el tiempo por iteración es un número positivo
            assert all(
                hho_rows["avg_iter_time"] > 0
            ), "El tiempo por iteración no es positivo"

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Error al ejecutar run_massive.py: {e.stderr.decode()}")
        except AssertionError as e:
            pytest.fail(str(e))
        except Exception as e:
            pytest.fail(f"Error inesperado: {str(e)}")


if __name__ == "__main__":
    test_run_massive_manifest_and_avg_time()
