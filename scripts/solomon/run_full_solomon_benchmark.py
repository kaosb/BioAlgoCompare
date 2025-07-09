#!/usr/bin/env python3
"""
Script para ejecutar benchmarks con todas las instancias Solomon (101 y 201 series)
"""

import sys
import os
import shutil
import time
import argparse
import glob
from pathlib import Path
import re

def get_solomon_instances():
    """Obtiene la lista de instancias Solomon desde el directorio data/vrp/Solomon"""
    solomon_path = Path("data/vrp/Solomon")
    if not solomon_path.exists():
        return []

    instance_files = glob.glob(str(solomon_path / "*.vrp"))
    instances = []

    for f in instance_files:
        # Extraer nombre de la instancia sin extensión ni ruta
        name = Path(f).stem
        instances.append(name)

    return sorted(instances)

def prepare_temp_files(instances):
    """Prepara archivos temporales en data/vrp para las instancias Solomon"""
    for instance in instances:
        source = f"data/vrp/Solomon/{instance}.vrp"
        dest = f"data/vrp/{instance}.vrp"
        try:
            shutil.copy(source, dest)
            print(f"Copiado: {source} → {dest}")
        except Exception as e:
            print(f"Error al copiar {source}: {str(e)}")

    return

def cleanup_temp_files(instances):
    """Elimina archivos temporales creados en data/vrp"""
    for instance in instances:
        dest = f"data/vrp/{instance}.vrp"
        try:
            if os.path.exists(dest):
                os.remove(dest)
                print(f"Eliminado: {dest}")
        except Exception as e:
            print(f"Error al eliminar {dest}: {str(e)}")

    return

def main():
    """Función principal para ejecutar el benchmark"""
    parser = argparse.ArgumentParser(description="Ejecuta benchmark con instancias Solomon")
    parser.add_argument("--runs", type=int, default=10, help="Número de ejecuciones (default: 10)")
    parser.add_argument("--iterations", type=int, default=50, help="Número de iteraciones (default: 50)")
    parser.add_argument("--algorithms", type=str, default="woa,opa",
                        help="Algoritmos a ejecutar separados por comas (default: woa,opa)")
    parser.add_argument("--series", type=str, default="201",
                        help="Series a ejecutar: 101, 201 o all (default: 201)")

    args = parser.parse_args()

    print("=== Benchmark con instancias Solomon ===")
    print("Configuración:")
    print(f"  - Ejecuciones: {args.runs}")
    print(f"  - Iteraciones: {args.iterations}")
    print(f"  - Algoritmos: {args.algorithms}")
    print(f"  - Series: {args.series}")

    # Obtener instancias Solomon
    all_instances = get_solomon_instances()
    if not all_instances:
        print("Error: No se encontraron instancias Solomon en data/vrp/Solomon/")
        return

    # Filtrar por serie
    selected_instances = []
    if args.series == "101":
        selected_instances = [i for i in all_instances if re.search(r'101$', i)]
    elif args.series == "201":
        selected_instances = [i for i in all_instances if re.search(r'201$', i)]
    else:  # all
        selected_instances = all_instances

    if not selected_instances:
        print(f"Error: No se encontraron instancias para la serie {args.series}")
        return

    print(f"\nInstancias seleccionadas ({len(selected_instances)}):")
    for i in selected_instances:
        print(f"  - {i}")

    # Preparar archivos temporales
    print("\nPreparando archivos temporales...")
    prepare_temp_files(selected_instances)

    try:
        # Construir comando de benchmark
        algo_args = []
        for algo in args.algorithms.split(','):
            algo_args.append(f"--algorithm {algo.strip()}")

        instance_args = []
        for instance in selected_instances:
            instance_args.append(f"--instances {instance}")

        cmd = f"PYTHONPATH=. python scripts/run_massive.py {' '.join(algo_args)} {' '.join(instance_args)} --runs {args.runs} --iterations {args.iterations}"

        print("\nEjecutando benchmark...")
        print(f"Comando: {cmd}")
        os.system(cmd)

    except Exception as e:
        print(f"Error durante el benchmark: {str(e)}")

    finally:
        # Limpiar archivos temporales
        print("\nLimpiando archivos temporales...")
        cleanup_temp_files(selected_instances)

    print("\nBenchmark completado.")

if __name__ == "__main__":
    main()
