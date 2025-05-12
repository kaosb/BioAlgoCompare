#!/usr/bin/env python3
"""
Script para ejecutar benchmarks masivos (1000 runs por algoritmo) con sistema
de checkpoint y recuperación para algoritmos metaheurísticos de optimización.
"""

import os
import click
import logging
import time
import json
import platform
import cProfile
import pstats
import sys
import numpy as np
from datetime import datetime
import multiprocessing as mp
from pathlib import Path
import subprocess

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("run_massive")

# ruff: noqa: E402
# Importar módulo mejorado de benchmarking
from utils.improved.enhanced_benchmarking import (
    run_complete_analysis,
    run_massive_benchmark,
    get_iteration_times,
    cleanup_timing,
    calculate_avg_summary
)
from utils.improved.timing import initialize_timing, finalize_timing

# Importar algoritmos
from algorithms.sho import SHO  # Previously HOA
from algorithms.apo import APO
from algorithms.egto import EGTO
from algorithms.fsa import FSA  # Previously FGO
from algorithms.foa import FOA
from algorithms.woa import WOA
from algorithms.hho import HHO
from algorithms.mrfo import MRFO
from algorithms.sma import SMA
from algorithms.gto import GTO
from algorithms.ewa import EWA
from algorithms.aha import AHA
from algorithms.rro import RRO
from algorithms.gvoa import GVOA
from algorithms.smo import SMO
from algorithms.opa import OPA

# Mapa de algoritmos (DRY)
ALGO_MAP = {
    "hoa": SHO,  # Previously HOA
    "sho": SHO,
    "apo": APO,
    "egto": EGTO,
    "fgo": FSA,  # Previously FGO
    "fsa": FSA,
    "foa": FOA,
    "woa": WOA,
    "hho": HHO,
    "mrfo": MRFO,
    "sma": SMA,
    "gto": GTO,
    "ewa": EWA,
    "aha": AHA,
    "rro": RRO,
    "gvoa": GVOA,
    "smo": SMO,
    "opa": OPA,
}


@click.command()
@click.option(
    "--runs", "-r", default=1000, help="Número de ejecuciones por algoritmo/instancia"
)
@click.option(
    "--iterations", "-n", default=100, help="Número de iteraciones por ejecución"
)
@click.option("--population", "-p", default=40, help="Tamaño de población")
@click.option("--seed", "-s", default=42, help="Semilla para reproducibilidad")
@click.option(
    "--algorithm",
    "-a",
    multiple=True,
    type=click.Choice(
        [
            "hoa",
            "sho",
            "apo",
            "egto",
            "fgo",
            "fsa",
            "foa",
            "woa",
            "hho",
            "mrfo",
            "sma",
            "gto",
            "ewa",
            "aha",
            "rro",
            "gvoa",
            "smo",
            "opa",
            "all",
        ]
    ),
    default=["all"],
    help="Algoritmos a ejecutar",
)
@click.option(
    "--instances", "-i", multiple=True, help="Instancias a evaluar (sin extensión)"
)
@click.option("--parallel/--no-parallel", default=True, help="Ejecutar en paralelo")
@click.option(
    "--resume/--no-resume",
    default=True,
    help="Intentar reanudar benchmark interrumpido",
)
@click.option(
    "--output-dir",
    "-o",
    default=None,
    help="Directorio de salida (automático si no se especifica)",
)
@click.option(
    "--profile/--no-profile",
    default=False,
    help="Generar perfil de rendimiento (cProfile) por algoritmo",
)
def main(
    runs,
    iterations,
    population,
    seed,
    algorithm,
    instances,
    parallel,
    resume,
    output_dir,
    profile,
):
    """
    Ejecuta un benchmark masivo con 1000 ejecuciones por algoritmo/instancia,
    con soporte de checkpoint y recuperación automática.

    Este script permite realizar un análisis estadísticamente riguroso del comportamiento
    de varios algoritmos metaheurísticos en problemas de optimización VRP.
    """
    start_time = time.time()

    # Mostrar información del sistema
    logger.info(f"Procesadores disponibles: {mp.cpu_count()}")
    logger.info(f"Paralelo: {parallel}")

    # Determinar el directorio de salida
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results/massive_benchmark_{timestamp}"

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Configurar logging específico para este benchmark
    log_file = output_path / "massive_benchmark.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    logger.info(f"Directorio de salida: {output_dir}")

    # El sistema de medición de tiempos ahora está integrado
    # directamente en el módulo enhanced_benchmarking
    # No es necesario hacer monkey patching

    # Determinar algoritmos a ejecutar usando el mapa DRY global
    if "all" in algorithm:
        algo_dict = ALGO_MAP
    else:
        algo_dict = {algo: ALGO_MAP[algo] for algo in algorithm}

    # Determinar instancias a evaluar
    if not instances:
        instances = ["E-n22-k4", "P-n16-k8", "A-n32-k5"]
        logger.info(f"Usando instancias por defecto: {', '.join(instances)}")

    # Verificar instancias
    valid_instances = []
    for instance in instances:
        # Buscar primero en la ruta principal
        instance_path = f"data/vrp/{instance}.vrp"
        # Buscar también en la carpeta Solomon si es necesario
        solomon_path = f"data/vrp/Solomon/{instance}.vrp"

        if os.path.exists(instance_path):
            valid_instances.append(instance)
        elif os.path.exists(solomon_path):
            # Usar la ruta alternativa para Solomon
            valid_instances.append(instance)
            logger.info(f"Instancia encontrada en ruta Solomon: {solomon_path}")
        else:
            logger.warning(f"Instancia no encontrada: {instance}")

    if not valid_instances:
        logger.error("No se encontraron instancias válidas")
        return

    # Mostrar resumen de la ejecución
    logger.info("=== CONFIGURACIÓN DE BENCHMARK MASIVO ===")
    logger.info(f"Algoritmos: {', '.join(algo_dict.keys())}")
    logger.info(f"Instancias: {', '.join(valid_instances)}")
    logger.info(f"Runs por algoritmo/instancia: {runs}")
    logger.info(f"Iteraciones por ejecución: {iterations}")
    logger.info(f"Tamaño de población: {population}")
    logger.info(f"Semilla base: {seed}")

    # Inicializar el sistema de medición de tiempos
    from utils.improved.timing import initialize_timing, finalize_timing
    initialize_timing()

    # Establecer semillas globales si se proporciona una semilla
    if seed is not None:
        import random
        import numpy as np

        random.seed(seed)
        np.random.seed(seed)
        logger.info(f"Semilla global establecida: {seed}")

    # Calcular estimación de tiempo
    avg_time_per_run = (
        0.3  # Segundos estimados por ejecución (ajustar según experiencia)
    )
    total_runs = runs * len(algo_dict) * len(valid_instances)
    estimated_time = (total_runs * avg_time_per_run) / (
        mp.cpu_count() if parallel else 1
    )

    logger.info(f"Total de ejecuciones: {total_runs}")
    logger.info(
        f"Tiempo estimado: {estimated_time/60:.1f} minutos ({estimated_time/3600:.1f} horas)"
    )

    # Solicitar confirmación para ejecuciones grandes
    if total_runs > 10000 and not click.confirm(
        "¿Desea continuar con esta ejecución masiva?"
    ):
        logger.info("Operación cancelada por el usuario")
        return

    # Crear manifest.json con información del entorno
    try:
        # Obtener hash del último commit
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], universal_newlines=True
            ).strip()
        except:
            git_commit = "unknown"

        # Crear manifest con parámetros y metadatos
        manifest = {
            "params": {
                "algorithms": list(algo_dict.keys()),
                "instances": valid_instances,
                "runs": runs,
                "iterations": iterations,
                "population": population,
                "seed": seed,
                "parallel": parallel,
            },
            "git_commit": git_commit,
            "python_version": platform.python_version(),
            "cpu_count": mp.cpu_count(),
            "platform": platform.platform(),
            "timestamp": datetime.now().isoformat(),
        }

        # Guardar manifest
        manifest_path = output_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Manifest creado: {manifest_path}")

        # Lista para almacenar información de tiempo por iteración
        iteration_times = []

        # Ejecutar análisis completo, utilizando hook para tiempo por iteración si es necesario
        if profile:
            logger.info("Modo perfil activado, generando perfiles por algoritmo")

            # Crear directorio para perfiles
            profile_dir = output_path / "profiles"
            profile_dir.mkdir(exist_ok=True)

            # Ejecutar cada algoritmo con perfil separado
            for algo_name, algo_class in algo_dict.items():
                algo_profile_path = profile_dir / f"{algo_name}.prof"
                logger.info(f"Generando perfil para {algo_name}: {algo_profile_path}")

                # Crear profiler
                profiler = cProfile.Profile()
                profiler.enable()

                # Ejecutar algoritmo específico
                single_algo_dict = {algo_name: algo_class}
                run_complete_analysis(
                    single_algo_dict,
                    valid_instances,
                    runs=runs,
                    iterations=iterations,
                    population=population,
                    seed=seed,
                    parallel=parallel,
                    output_dir=str(output_path / algo_name),
                    resume=resume,
                )

                # Desactivar profiler y guardar resultados
                profiler.disable()
                profiler.dump_stats(str(algo_profile_path))

                # Mostrar estadísticas básicas
                stats = pstats.Stats(str(algo_profile_path)).sort_stats('cumulative')
                stats.print_stats(10)

            # Combinar resultados
            report_path = str(output_path / "massive_benchmark_report.html")
        else:
            # Ejecutar normalmente sin perfil
            # Verificar si el CSV existe y tiene la columna Instance antes de ejecutar el análisis completo
            summary_path = Path(output_dir) / "massive_benchmark_summary.csv"
            if summary_path.exists():
                import pandas as pd
                try:
                    df = pd.read_csv(summary_path)
                    if "Instance" not in df.columns:
                        logger.warning("'Instance' missing – forcing rewrite of headers")
                        df.to_csv(summary_path, index=False, header=True)
                except Exception as e:
                    logger.error(f"Error al verificar CSV: {str(e)}")

            report_path = run_complete_analysis(
                algo_dict,
                valid_instances,
                runs=runs,
                iterations=iterations,
                population=population,
                seed=seed,
                parallel=parallel,
                output_dir=output_dir,
                resume=resume,
            )

        # Calcular y guardar tiempos promedio por iteración
        # Obtener los tiempos registrados durante la ejecución
        try:
            recorded_times = get_iteration_times()
            if recorded_times:
                logger.info(f"Se registraron {len(recorded_times)} mediciones de tiempo por iteración")

                # Calcular promedios por algoritmo e instancia
                avg_summary = calculate_avg_summary()

                # Actualizar el CSV con los tiempos promedio por iteración
                summary_path = Path(output_dir) / "massive_benchmark_summary.csv"
                if summary_path.exists():
                    try:
                        # Leer CSV existente
                        import pandas as pd
                        df = pd.read_csv(summary_path)

                        # Añadir o actualizar columna de tiempo promedio por iteración
                        for entry in avg_summary:
                            mask = (df["Algorithm"] == entry["algorithm"]) & (df["Instance"] == entry["instance"])
                            if mask.any():
                                df.loc[mask, "avg_iter_time"] = entry["avg_iter_time"]

                        # Guardar CSV actualizado
                        df.to_csv(summary_path, index=False)
                        logger.info(f"CSV actualizado con tiempos promedio por iteración: {summary_path}")
                    except Exception as e:
                        logger.warning(f"No se pudo actualizar el CSV con tiempos por iteración: {str(e)}")

                # Actualizar el manifest con los tiempos promedio por iteración
                if Path(manifest_path).exists():
                    try:
                        with open(manifest_path, "r") as f:
                            manifest_data = json.load(f)

                        # Añadir tiempos promedio por iteración
                        manifest_data["avg_iter_times"] = avg_summary

                        # Guardar manifest actualizado
                        with open(manifest_path, "w") as f:
                            json.dump(manifest_data, f, indent=2)

                        logger.info("Manifest actualizado con datos de tiempos por iteración")
                    except Exception as e:
                        logger.warning(f"No se pudo actualizar el manifest con tiempos por iteración: {str(e)}")
            else:
                logger.warning("No se registraron mediciones de tiempo por iteración")
                avg_summary = []
        except Exception as e:
            logger.error(f"Error al obtener tiempos de iteración: {str(e)}")
            recorded_times = []
            avg_summary = []

        # Mostrar resultado
        if report_path:
            logger.info(f"Benchmark completado con éxito. Reporte: {report_path}")
            elapsed = time.time() - start_time
            logger.info(
                f"Tiempo total: {elapsed/60:.1f} minutos ({elapsed/3600:.1f} horas)"
            )
        else:
            logger.error("El benchmark no generó un reporte válido")

    except KeyboardInterrupt:
        logger.warning("Benchmark interrumpido por el usuario")
        logger.info("Puede reanudar la ejecución usando --resume")
    except Exception as e:
        logger.error(f"Error en la ejecución del benchmark: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Finalizar y limpiar el sistema de medición de tiempos
        try:
            # Obtener los tiempos registrados
            times = get_iteration_times()

            # Calcular el tiempo promedio global por iteración
            avg_iter_time_overall = None
            if times:
                all_times = [entry["avg_iter_time"] for entry in times]
                if all_times:
                    avg_iter_time_overall = sum(all_times) / len(all_times)
                    logger.info(f"Tiempo promedio global por iteración: {avg_iter_time_overall:.6f} segundos")

            # Actualizar el manifest con el tiempo promedio global por iteración
            if avg_iter_time_overall and Path(manifest_path).exists():
                try:
                    with open(manifest_path, "r") as f:
                        manifest_data = json.load(f)

                    # Añadir el tiempo promedio global por iteración
                    manifest_data["avg_iter_time_overall"] = avg_iter_time_overall

                    # Guardar manifest actualizado
                    with open(manifest_path, "w") as f:
                        json.dump(manifest_data, f, indent=2)

                    logger.info(f"Manifest actualizado con tiempo promedio: {avg_iter_time_overall:.6f} segundos")
                except Exception as e:
                    logger.warning(f"No se pudo actualizar el manifest con el tiempo promedio global: {str(e)}")

            # Finalizar el sistema de medición de tiempos
            finalize_timing()
            # Ahora podemos limpiar
            cleanup_timing()
        except Exception as e:
            logger.warning(f"No se pudo limpiar el sistema de medición de tiempos: {str(e)}")


if __name__ == "__main__":
    main()
