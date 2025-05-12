#!/usr/bin/env python3
"""
Módulo para medir tiempos de ejecución por iteración en funciones de benchmarking.
Compatible con ejecución paralela y multiprocessing.
"""

import time
import multiprocessing as mp
import numpy as np
import logging
from typing import Dict, List, Any, Callable, Tuple

# Configuración de logging
logger = logging.getLogger("timing")

# Variables globales a nivel de módulo para compartir entre procesos
_manager = None
_original_function = None
_iteration_times = None
_time_lock = None
_is_active = False
# Nueva lista compartida para tiempos usando Manager
SHARED_TIMES = None

def initialize_timing():
    """Inicializa las estructuras de datos compartidas para medición de tiempos."""
    global _manager, _iteration_times, _time_lock, _is_active, SHARED_TIMES

    # Solo inicializar una vez
    if _manager is not None:
        return

    # Crear manager para datos compartidos entre procesos
    _manager = mp.Manager() if mp.current_process().name == 'MainProcess' else None

    # Lista compartida para almacenar tiempos
    _iteration_times = _manager.list() if _manager else []

    # Crear lista compartida SHARED_TIMES usando Manager
    SHARED_TIMES = _manager.list() if _manager else []

    # Lock para acceso sincronizado
    _time_lock = _manager.Lock() if _manager else None

    # Marcar como inicializado
    _is_active = True

    logger.debug("Sistema de medición de tiempos inicializado")

def record_iter_time(algorithm: str, instance: str, run_id: int,
                  avg_iter_time: float, total_time: float, iterations: int):
    """
    Registra un tiempo de iteración en la lista compartida SHARED_TIMES.

    Args:
        algorithm: Nombre del algoritmo
        instance: Nombre de la instancia
        run_id: ID de la ejecución
        avg_iter_time: Tiempo promedio por iteración
        total_time: Tiempo total de ejecución
        iterations: Número de iteraciones
    """
    global SHARED_TIMES, _time_lock, _is_active

    if not _is_active:
        return

    # Crear entrada con los datos
    new_entry = {
        "algorithm": algorithm,
        "instance": instance,
        "run_id": run_id,
        "avg_iter_time": avg_iter_time,
        "total_time": total_time,
        "iterations": iterations
    }

    # Usar lock para acceso seguro a la lista compartida
    if _time_lock:
        with _time_lock:
            SHARED_TIMES.append(new_entry)
    else:
        SHARED_TIMES.append(new_entry)

    logger.debug(f"Tiempo registrado para {algorithm}/{instance} run {run_id}: {avg_iter_time:.6f} seg/iter")

def get_iteration_times() -> List[Dict[str, Any]]:
    """Retorna una copia de los tiempos de iteración recolectados."""
    global _iteration_times, SHARED_TIMES, _is_active

    if not _is_active:
        return []

    # Convertir la lista compartida a una lista Python normal
    # Primero intentar con SHARED_TIMES, luego con _iteration_times para compatibilidad
    if SHARED_TIMES and len(SHARED_TIMES) > 0:
        return list(SHARED_TIMES)
    return list(_iteration_times)

def instrument_run_algorithm_task(original_task_function: Callable) -> Callable:
    """
    Instrumenta la función de ejecución de algoritmos para medir tiempos por iteración.
    
    Args:
        original_task_function: La función original _run_algorithm_task
        
    Returns:
        Una función instrumentada que registra los tiempos de ejecución
    """
    global _original_function, _is_active
    
    # Guardar referencia a la función original
    _original_function = original_task_function
    
    # Inicializar sistema de medición si no está activo
    if not _is_active:
        initialize_timing()
    
    def instrumented_run_algorithm_task(args: Tuple):
        """
        Versión instrumentada que mide tiempos por iteración.
        Compatible con multiprocessing.
        """
        # Desempaquetar argumentos
        (
            algo_class,
            instance_name,
            instance_path,
            run_id,
            iterations,
            population,
            seed,
            checkpoint_dir,
        ) = args
        
        # Establecer semilla específica para este proceso
        if seed is not None:
            np.random.seed(seed + run_id)
        
        # Medir tiempo de ejecución
        start_time = time.time()
        result = _original_function(args)
        total_time = time.time() - start_time
        
        # Registrar tiempo para todas las ejecuciones (quitada la restricción de las 5 primeras)
        if "error" not in result:
            # Calcular tiempo promedio por iteración
            avg_iter_time = total_time / iterations

            # Registrar tiempo usando la nueva función
            record_iter_time(
                algorithm=result["algorithm"],
                instance=result["instance"],
                run_id=run_id,
                avg_iter_time=avg_iter_time,
                total_time=total_time,
                iterations=iterations
            )
        
        return result
    
    return instrumented_run_algorithm_task

def finalize_timing():
    """
    Finaliza la medición de tiempos y devuelve el tiempo promedio global por iteración.
    Además, escribe este valor en el manifest.json.

    Returns:
        float: Tiempo promedio global por iteración o None si no hay datos
    """
    global SHARED_TIMES, _is_active

    # Verificar si está activo
    if not _is_active:
        return None

    # Calcular el tiempo promedio global
    avg_iter_time_overall = None
    times = get_iteration_times()

    if times:
        # Extraer todos los tiempos de iteración
        all_times = [entry["avg_iter_time"] for entry in times]
        if all_times:
            avg_iter_time_overall = sum(all_times) / len(all_times)
            logger.info(f"Tiempo promedio global calculado: {avg_iter_time_overall:.6f} seg/iter de {len(all_times)} muestras")

        # Intentar actualizar manifest.json si existe
        try:
            import json
            import os
            from pathlib import Path

            # Buscar manifestos en directorios results/
            manifest_paths = []
            results_dir = Path("results")
            if results_dir.exists():
                for dir_path in results_dir.glob("**/"):
                    manifest_path = dir_path / "manifest.json"
                    if manifest_path.exists():
                        manifest_paths.append(manifest_path)

            # Tomar el manifest más reciente por su fecha de modificación
            if manifest_paths:
                newest_manifest = max(manifest_paths, key=os.path.getmtime)

                # Leer el manifest
                with open(newest_manifest, "r") as f:
                    manifest_data = json.load(f)

                # Añadir o actualizar el tiempo promedio global
                manifest_data["avg_iter_time_overall"] = avg_iter_time_overall

                # Calcular promedio por algoritmo e instancia
                avg_summary = calculate_avg_summary()
                manifest_data["avg_iter_times"] = avg_summary

                # Guardar manifest actualizado
                with open(newest_manifest, "w") as f:
                    json.dump(manifest_data, f, indent=2)

                logger.info(f"Manifest actualizado con tiempos: {newest_manifest}")
        except Exception as e:
            logger.warning(f"No se pudo actualizar el manifest: {str(e)}")

    return avg_iter_time_overall

def cleanup_timing():
    """Limpia y restaura el estado original después de la medición."""
    global _manager, _iteration_times, _time_lock, _is_active, _original_function, SHARED_TIMES

    # Solo limpiar si está activo
    if not _is_active:
        return None

    # Obtener el tiempo promedio antes de limpiar
    avg_iter_time = finalize_timing()

    # Restaurar variables
    _is_active = False
    _manager = None
    _iteration_times = None
    SHARED_TIMES = None
    _time_lock = None
    _original_function = None

    logger.debug("Sistema de medición de tiempos limpiado")

    # Devolver el tiempo promedio
    return avg_iter_time

def calculate_avg_summary():
    """
    Calcula un resumen de tiempos promedio por algoritmo e instancia.

    Returns:
        Lista de diccionarios con promedios por algoritmo e instancia
    """
    # Obtener tiempos registrados
    times = get_iteration_times()

    if not times:
        return []

    # Agrupar por algoritmo e instancia
    avg_iter_times = {}
    for entry in times:
        key = (entry["algorithm"], entry["instance"])
        if key not in avg_iter_times:
            avg_iter_times[key] = []
        avg_iter_times[key].append(entry["avg_iter_time"])

    # Calcular promedio final para cada grupo
    avg_summary = []
    for (algo, inst), time_values in avg_iter_times.items():
        avg_summary.append({
            "algorithm": algo,
            "instance": inst,
            "avg_iter_time": sum(time_values) / len(time_values),
            "samples": len(time_values)
        })

    return avg_summary


def flush_worker_times():
    """
    Llamado solo por procesos worker.
    Copia los tiempos locales a SHARED_TIMES sin vaciar la lista global
    que el maestro necesita para calcular avg_iter_time_overall.
    """
    global _iteration_times, SHARED_TIMES, _time_lock
    if not _iteration_times:
        return
    if _time_lock:
        with _time_lock:
            SHARED_TIMES.extend(_iteration_times)
            _iteration_times = []
    else:
        SHARED_TIMES.extend(_iteration_times)
        _iteration_times = []