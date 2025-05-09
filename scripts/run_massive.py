#!/usr/bin/env python3
"""
Script para ejecutar benchmarks masivos (1000 runs por algoritmo) con sistema 
de checkpoint y recuperación para algoritmos metaheurísticos de optimización.
"""

import os
import click
import logging
import time
from datetime import datetime
import multiprocessing as mp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("massive_benchmark.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_massive")

# Importar módulo mejorado de benchmarking
from utils.improved.enhanced_benchmarking import run_complete_analysis, run_massive_benchmark

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

@click.command()
@click.option('--runs', '-r', default=1000, help='Número de ejecuciones por algoritmo/instancia')
@click.option('--iterations', '-n', default=100, help='Número de iteraciones por ejecución')
@click.option('--population', '-p', default=40, help='Tamaño de población')
@click.option('--seed', '-s', default=42, help='Semilla para reproducibilidad')
@click.option('--algorithm', '-a', multiple=True, 
              type=click.Choice(['hoa', 'sho', 'apo', 'egto', 'fgo', 'fsa', 'foa', 'woa', 'hho', 'mrfo', 'sma', 'gto', 'ewa', 'all']),
              default=['all'], help='Algoritmos a ejecutar')
@click.option('--instances', '-i', multiple=True, 
              help='Instancias a evaluar (sin extensión)')
@click.option('--parallel/--no-parallel', default=True, help='Ejecutar en paralelo')
@click.option('--resume/--no-resume', default=True, 
              help='Intentar reanudar benchmark interrumpido')
@click.option('--output-dir', '-o', default=None, 
              help='Directorio de salida (automático si no se especifica)')
def main(runs, iterations, population, seed, algorithm, instances, parallel, resume, output_dir):
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
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Directorio de salida: {output_dir}")
    
    # Determinar algoritmos a ejecutar
    if 'all' in algorithm:
        algo_dict = {
            'hoa': SHO,  # Previously HOA
            'sho': SHO,
            'apo': APO,
            'egto': EGTO,
            'fgo': FSA,  # Previously FGO
            'fsa': FSA,
            'foa': FOA,
            'woa': WOA,
            'hho': HHO,
            'mrfo': MRFO,
            'sma': SMA,
            'gto': GTO,
            'ewa': EWA
        }
    else:
        algo_classes = {
            'hoa': SHO,  # Previously HOA
            'sho': SHO,
            'apo': APO,
            'egto': EGTO,
            'fgo': FSA,  # Previously FGO
            'fsa': FSA,
            'foa': FOA,
            'woa': WOA,
            'hho': HHO,
            'mrfo': MRFO,
            'sma': SMA,
            'gto': GTO,
            'ewa': EWA
        }
        algo_dict = {algo: algo_classes[algo] for algo in algorithm}
    
    # Determinar instancias a evaluar
    if not instances:
        instances = ['E-n22-k4', 'P-n16-k8', 'A-n32-k5']
        logger.info(f"Usando instancias por defecto: {', '.join(instances)}")
    
    # Verificar instancias
    valid_instances = []
    for instance in instances:
        instance_path = f"data/vrp/{instance}.vrp"
        if os.path.exists(instance_path):
            valid_instances.append(instance)
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
    
    # Calcular estimación de tiempo
    avg_time_per_run = 0.3  # Segundos estimados por ejecución (ajustar según experiencia)
    total_runs = runs * len(algo_dict) * len(valid_instances)
    estimated_time = (total_runs * avg_time_per_run) / (mp.cpu_count() if parallel else 1)
    
    logger.info(f"Total de ejecuciones: {total_runs}")
    logger.info(f"Tiempo estimado: {estimated_time/60:.1f} minutos ({estimated_time/3600:.1f} horas)")
    
    # Solicitar confirmación para ejecuciones grandes
    if total_runs > 10000 and not click.confirm("¿Desea continuar con esta ejecución masiva?"):
        logger.info("Operación cancelada por el usuario")
        return
    
    try:
        # Ejecutar análisis completo
        report_path = run_complete_analysis(
            algo_dict,
            valid_instances,
            runs=runs,
            iterations=iterations,
            population=population,
            seed=seed,
            parallel=parallel,
            output_dir=output_dir,
            resume=resume
        )
        
        # Mostrar resultado
        if report_path:
            logger.info(f"Benchmark completado con éxito. Reporte: {report_path}")
            elapsed = time.time() - start_time
            logger.info(f"Tiempo total: {elapsed/60:.1f} minutos ({elapsed/3600:.1f} horas)")
        else:
            logger.error("El benchmark no generó un reporte válido")
            
    except KeyboardInterrupt:
        logger.warning("Benchmark interrumpido por el usuario")
        logger.info("Puede reanudar la ejecución usando --resume")
    except Exception as e:
        logger.error(f"Error en la ejecución del benchmark: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()