#!/usr/bin/env python3
"""
Módulo para medir tiempos por iteración en algoritmos metaheurísticos.
Diseñado para ser compatible con ejecución paralela mediante multiprocessing.
"""

import os
import time
import json
import pandas as pd
import logging
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

# Configurar logging
logger = logging.getLogger("iteration_timer")

# Crear un manager global al nivel del módulo
_manager = None
_shared_data = None

def initialize_shared_data():
    """Inicializa estructuras de datos compartidas para todos los procesos"""
    global _manager, _shared_data
    
    # Solo inicializar en el proceso principal
    if mp.current_process().name == 'MainProcess':
        _manager = mp.Manager()
        _shared_data = {
            'iteration_times': _manager.list(),
            'lock': _manager.Lock()
        }
    
    return _shared_data

def get_shared_data():
    """Obtiene acceso a las estructuras de datos compartidas"""
    global _manager, _shared_data
    
    # Inicializar si no existe
    if _shared_data is None:
        initialize_shared_data()
        
    return _shared_data

def record_iteration_time(algorithm, instance, run_id, total_time, iterations):
    """
    Registra tiempo por iteración en la estructura de datos compartida.
    
    Args:
        algorithm: Nombre del algoritmo
        instance: Nombre de la instancia
        run_id: ID de la ejecución
        total_time: Tiempo total de ejecución
        iterations: Número de iteraciones realizadas
    """
    shared = get_shared_data()
    
    # Si estamos en un proceso hijo sin acceso a _shared_data, simplemente retornamos
    if shared is None:
        return
    
    # Calcular tiempo promedio por iteración
    avg_iter_time = total_time / iterations
    
    # Crear registro de tiempo
    time_entry = {
        "algorithm": algorithm,
        "instance": instance,
        "run_id": run_id,
        "avg_iter_time": avg_iter_time,
        "total_time": total_time,
        "iterations": iterations,
        "timestamp": datetime.now().isoformat()
    }
    
    # Usar lock para acceso seguro a la lista compartida
    with shared['lock']:
        shared['iteration_times'].append(time_entry)

def wrap_algorithm_task(original_func):
    """
    Decorador para envolver la función de ejecución y medir tiempos por iteración.
    
    Args:
        original_func: Función original a envolver
        
    Returns:
        Función envuelta que mide tiempos
    """
    def wrapped_func(args):
        """Envuelve la función original para medir tiempos por iteración"""
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
        
        # Ejecutamos el algoritmo y medimos el tiempo
        start_time = time.time()
        result = original_func(args)
        total_time = time.time() - start_time
        
        # Si los primeros 5 runs o con run_id entre 1 y 5, medimos tiempo promedio por iteración
        if 1 <= run_id <= 5 and "error" not in result:
            record_iteration_time(
                result["algorithm"],
                result["instance"],
                run_id,
                total_time,
                iterations
            )
        
        return result
    
    return wrapped_func

def get_recorded_times():
    """
    Obtiene los tiempos por iteración registrados.
    
    Returns:
        Lista de registros de tiempos por iteración
    """
    shared = get_shared_data()
    
    # Si estamos en un proceso hijo sin acceso a _shared_data, retornamos lista vacía
    if shared is None:
        return []
    
    # Convertir a lista Python normal (ya que shared['iteration_times'] es un proxy)
    with shared['lock']:
        return list(shared['iteration_times'])

def calculate_avg_iteration_times():
    """
    Calcula tiempos promedio por iteración agrupados por algoritmo e instancia.
    
    Returns:
        Lista de diccionarios con promedios por algoritmo e instancia
    """
    times = get_recorded_times()
    
    if not times:
        return []
    
    # Agrupar por algoritmo e instancia
    avg_iter_times = {}
    for entry in times:
        key = (entry["algorithm"], entry["instance"])
        if key not in avg_iter_times:
            avg_iter_times[key] = []
        avg_iter_times[key].append(entry["avg_iter_time"])
    
    # Calcular promedio final
    avg_summary = []
    for (algo, inst), time_values in avg_iter_times.items():
        avg_summary.append({
            "algorithm": algo,
            "instance": inst,
            "avg_iter_time": sum(time_values) / len(time_values),
            "samples": len(time_values)
        })
    
    return avg_summary

def update_csv_with_iteration_times(csv_path):
    """
    Actualiza un archivo CSV con los tiempos promedio por iteración.
    
    Args:
        csv_path: Ruta al archivo CSV a actualizar
        
    Returns:
        True si la actualización fue exitosa, False en caso contrario
    """
    if not os.path.exists(csv_path):
        logger.warning(f"CSV no encontrado: {csv_path}")
        return False
    
    try:
        # Obtener tiempos promedio
        avg_summary = calculate_avg_iteration_times()
        
        if not avg_summary:
            logger.warning("No hay datos de tiempos por iteración disponibles")
            return False
        
        # Leer CSV existente
        df = pd.read_csv(csv_path)
        
        # Añadir columna de tiempo promedio por iteración
        for entry in avg_summary:
            mask = (df["Algorithm"] == entry["algorithm"]) & (df["Instance"] == entry["instance"])
            if mask.any():
                df.loc[mask, "avg_iter_time"] = entry["avg_iter_time"]
        
        # Guardar CSV actualizado
        df.to_csv(csv_path, index=False)
        logger.info(f"CSV actualizado con tiempos promedio por iteración: {csv_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error al actualizar CSV con tiempos por iteración: {str(e)}")
        return False

def update_manifest_with_iteration_times(manifest_path):
    """
    Actualiza un archivo manifest.json con los tiempos promedio por iteración.
    
    Args:
        manifest_path: Ruta al archivo manifest.json a actualizar
        
    Returns:
        True si la actualización fue exitosa, False en caso contrario
    """
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest no encontrado: {manifest_path}")
        return False
    
    try:
        # Obtener tiempos promedio
        avg_summary = calculate_avg_iteration_times()
        
        # Leer manifest existente
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
        
        # Añadir o actualizar tiempos promedio por iteración
        manifest_data["avg_iter_times"] = avg_summary if avg_summary else []
        
        # Guardar manifest actualizado
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Manifest actualizado con datos de tiempos por iteración")
        return True
        
    except Exception as e:
        logger.error(f"Error al actualizar manifest con tiempos por iteración: {str(e)}")
        return False

def patch_algorithm_task():
    """
    Aplica el monkey patch a la función _run_algorithm_task en enhanced_benchmarking.
    Esta función debe llamarse desde el proceso principal antes de iniciar procesos hijos.

    Returns:
        La función original antes del patching (para restauración si es necesario)
    """
    # Inicializar datos compartidos
    initialize_shared_data()

    # Importar módulo enhanced_benchmarking
    from utils.improved import enhanced_benchmarking

    # Guardar referencia a la función original
    original_func = enhanced_benchmarking._run_algorithm_task

    # Reemplazar con nuestra versión instrumentada
    enhanced_benchmarking._run_algorithm_task = wrap_algorithm_task(original_func)

    logger.info("Función _run_algorithm_task modificada para medir tiempos por iteración")

    return original_func

def restore_algorithm_task(original_func):
    """
    Restaura la función original _run_algorithm_task.

    Args:
        original_func: La función original a restaurar
    """
    from utils.improved import enhanced_benchmarking
    enhanced_benchmarking._run_algorithm_task = original_func
    logger.info("Función _run_algorithm_task restaurada a su implementación original")
