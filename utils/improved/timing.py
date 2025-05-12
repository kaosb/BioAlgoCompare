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

def initialize_timing():
    """Inicializa las estructuras de datos compartidas para medición de tiempos."""
    global _manager, _iteration_times, _time_lock, _is_active
    
    # Solo inicializar una vez
    if _manager is not None:
        return
    
    # Crear manager para datos compartidos entre procesos
    _manager = mp.Manager() if mp.current_process().name == 'MainProcess' else None
    
    # Lista compartida para almacenar tiempos
    _iteration_times = _manager.list() if _manager else []
    
    # Lock para acceso sincronizado
    _time_lock = _manager.Lock() if _manager else None
    
    # Marcar como inicializado
    _is_active = True
    
    logger.debug("Sistema de medición de tiempos inicializado")

def get_iteration_times() -> List[Dict[str, Any]]:
    """Retorna una copia de los tiempos de iteración recolectados."""
    global _iteration_times, _is_active
    
    if not _is_active:
        return []
    
    # Convertir la lista compartida a una lista Python normal
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
        
        # Solo registrar para las primeras 5 ejecuciones, si no hay errores
        if run_id <= 5 and "error" not in result:
            # Calcular tiempo promedio por iteración
            avg_iter_time = total_time / iterations
            
            # Crear entrada con los datos
            new_entry = {
                "algorithm": result["algorithm"],
                "instance": result["instance"],
                "run_id": run_id,
                "avg_iter_time": avg_iter_time,
                "total_time": total_time,
                "iterations": iterations
            }
            
            # Usar lock para acceso seguro a la lista compartida
            if _time_lock:
                with _time_lock:
                    _iteration_times.append(new_entry)
            else:
                _iteration_times.append(new_entry)
        
        return result
    
    return instrumented_run_algorithm_task

def cleanup_timing():
    """Limpia y restaura el estado original después de la medición."""
    global _manager, _iteration_times, _time_lock, _is_active, _original_function
    
    # Solo limpiar si está activo
    if not _is_active:
        return
    
    # Restaurar variables
    _is_active = False
    _manager = None
    _iteration_times = None
    _time_lock = None
    _original_function = None
    
    logger.debug("Sistema de medición de tiempos limpiado")

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