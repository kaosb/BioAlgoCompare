#!/usr/bin/env python3
"""
Script unificado para ejecutar algoritmos bio-inspirados.
Combina las funcionalidades de run.py, run_massive.py y run_opa_experiment.py

Modos de operación:
- standard: Ejecución normal con configuración específica
- massive: Benchmark masivo con 1000 runs y sistema de checkpoint
- experiment: Experimentos específicos con semillas predefinidas
"""

import click
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
from multiprocessing import Pool
from functools import partial
from tqdm import tqdm
from pathlib import Path
import pickle
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importar todas las versiones v2 de los algoritmos
from algorithms.sho_v2 import SHOV2
from algorithms.apo_v2 import APOV2
from algorithms.egto_v2 import EGTOV2
from algorithms.fsa_v2 import FSAV2
from algorithms.foa_v2 import FOAV2
from algorithms.woa_v2 import WOAV2
from algorithms.hho_v2 import HHOV2
from algorithms.mrfo_v2 import MRFOV2
from algorithms.sma_v2 import SMAV2
from algorithms.gto_v2 import GTOV2
from algorithms.ewa_v2 import EWAV2
from algorithms.aha_v2 import AHAV2
from algorithms.rro_v2 import RROV2
from algorithms.gvoa_v2 import GVOAV2
from algorithms.smo_v2 import SMOV2
from algorithms.opa_v2 import OPAV2
from algorithms.hoa_v2 import HOAV2
from algorithms.fgo_v2 import FGOV2

# Mapeo de algoritmos v2
ALGORITHMS_V2 = {
    "sho": SHOV2,
    "apo": APOV2,
    "egto": EGTOV2,
    "fsa": FSAV2,
    "foa": FOAV2,
    "woa": WOAV2,
    "hho": HHOV2,
    "mrfo": MRFOV2,
    "sma": SMAV2,
    "gto": GTOV2,
    "ewa": EWAV2,
    "aha": AHAV2,
    "rro": RROV2,
    "gvoa": GVOAV2,
    "smo": SMOV2,
    "opa": OPAV2,
    "hoa": HOAV2,
    "fgo": FGOV2,
}

# Importar problema y utilidades
from problems.vrp_v2 import VRPProblemV2
from utils.visualization import plot_vrp_solution, plot_convergence, compare_algorithms


def ensure_directories():
    """Crea los directorios necesarios si no existen."""
    directories = ["results", "checkpoints", "plots", "experiments"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)


def run_algorithm(algo_name, problem, population, iterations, run_seed, run_id, use_v2=True):
    """
    Ejecuta un algoritmo para una semilla específica.
    
    Args:
        algo_name: Nombre del algoritmo
        problem: Instancia del problema
        population: Tamaño de población
        iterations: Número de iteraciones
        run_seed: Semilla para esta ejecución
        run_id: ID de la ejecución
        use_v2: Si usar la versión v2 del algoritmo
    
    Returns:
        Diccionario con resultados de la ejecución
    """
    try:
        # Seleccionar la clase del algoritmo
        if use_v2 and algo_name in ALGORITHMS_V2:
            algo_class = ALGORITHMS_V2[algo_name]
        else:
            # Fallback a v1 si no hay v2 o si se especifica
            click.echo(f"⚠️  Usando versión v1 de {algo_name}", err=True)
            return None
        
        # Inicializar y ejecutar algoritmo
        algo = algo_class(
            problem,
            population_size=population,
            max_iterations=iterations,
            seed=run_seed,
        )
        
        start_time = time.time()
        best_solution = algo.execute()
        execution_time = time.time() - start_time
        
        # Recopilar resultados
        return {
            "run_id": run_id,
            "seed": run_seed,
            "fitness": best_solution.fitness(),
            "solution": best_solution.position.tolist(),
            "convergence": algo.get_convergence_curve(),
            "execution_time": execution_time,
            "algorithm": algo_name,
            "instance": problem.name,
        }
        
    except Exception as e:
        click.echo(f"❌ Error en {algo_name} run {run_id}: {str(e)}", err=True)
        return None


def save_checkpoint(checkpoint_data, checkpoint_file):
    """Guarda el estado actual en un checkpoint."""
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    click.echo(f"💾 Checkpoint guardado: {checkpoint_file}")


def load_checkpoint(checkpoint_file):
    """Carga el estado desde un checkpoint."""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'rb') as f:
            return pickle.load(f)
    return None


@click.command()
@click.option('--mode', type=click.Choice(['standard', 'massive', 'experiment']), 
              default='standard', help='Modo de ejecución')
@click.option('--algorithm', '-a', type=click.Choice(list(ALGORITHMS_V2.keys())), 
              required=True, help='Algoritmo a ejecutar')
@click.option('--instance', '-i', type=str, required=True, 
              help='Instancia VRP a resolver')
@click.option('--population', '-p', default=30, type=int, 
              help='Tamaño de la población')
@click.option('--iterations', '-n', default=100, type=int, 
              help='Número de iteraciones')
@click.option('--runs', '-r', default=30, type=int, 
              help='Número de ejecuciones (standard/experiment)')
@click.option('--massive-runs', default=1000, type=int, 
              help='Número de ejecuciones para modo massive')
@click.option('--seed', '-s', type=int, help='Semilla inicial')
@click.option('--parallel/--no-parallel', default=True, 
              help='Ejecutar en paralelo')
@click.option('--workers', '-w', type=int, 
              help='Número de workers paralelos')
@click.option('--checkpoint-interval', default=100, type=int,
              help='Intervalo de checkpoint para modo massive')
@click.option('--resume', is_flag=True, 
              help='Reanudar desde checkpoint en modo massive')
@click.option('--experiment-seeds', type=str,
              help='Semillas específicas para modo experiment (separadas por coma)')
@click.option('--output-dir', '-o', type=str, default='results',
              help='Directorio para guardar resultados')
@click.option('--plot/--no-plot', default=False,
              help='Generar gráficos de resultados')
@click.option('--v2/--v1', default=True,
              help='Usar versión v2 de los algoritmos')
def main(mode, algorithm, instance, population, iterations, runs, massive_runs,
         seed, parallel, workers, checkpoint_interval, resume, experiment_seeds,
         output_dir, plot, v2):
    """
    Script unificado para ejecutar algoritmos bio-inspirados en VRP.
    
    Ejemplos:
    
    # Modo standard (30 runs)
    python run.py --mode standard -a woa -i P-n16-k8.vrp -r 30
    
    # Modo massive (1000 runs con checkpoint)
    python run.py --mode massive -a sma -i P-n16-k8.vrp --checkpoint-interval 100
    
    # Modo experiment (semillas específicas)
    python run.py --mode experiment -a opa -i P-n16-k8.vrp --experiment-seeds "42,123,456"
    """
    
    # Crear directorios necesarios
    ensure_directories()
    
    # Configurar workers
    if workers is None:
        workers = mp.cpu_count() - 1
    
    # Cargar problema
    instance_path = f"data/vrp/{instance}"
    if not os.path.exists(instance_path):
        click.echo(f"❌ Error: No se encuentra la instancia {instance_path}", err=True)
        return
    
    try:
        if v2:
            problem = VRPProblemV2(instance_path)
        else:
            problem = VRPProblem(instance_path)
    except Exception as e:
        click.echo(f"❌ Error al cargar la instancia: {str(e)}", err=True)
        return
    
    click.echo(f"🚀 Ejecutando {algorithm.upper()} en {instance}")
    click.echo(f"📊 Modo: {mode}")
    click.echo(f"👥 Población: {population}")
    click.echo(f"🔄 Iteraciones: {iterations}")
    
    # Configurar semillas según el modo
    if mode == 'massive':
        total_runs = massive_runs
        base_seed = seed if seed else 42
        seeds = list(range(base_seed, base_seed + total_runs))
    elif mode == 'experiment' and experiment_seeds:
        seeds = [int(s.strip()) for s in experiment_seeds.split(',')]
        total_runs = len(seeds)
    else:
        total_runs = runs
        base_seed = seed if seed else 42
        seeds = list(range(base_seed, base_seed + total_runs))
    
    click.echo(f"🎲 Total de ejecuciones: {total_runs}")
    
    # Configurar checkpoint para modo massive
    checkpoint_file = None
    completed_runs = []
    
    if mode == 'massive':
        checkpoint_file = f"checkpoints/{algorithm}_{instance.replace('.vrp', '')}_{massive_runs}runs.pkl"
        
        if resume and os.path.exists(checkpoint_file):
            checkpoint_data = load_checkpoint(checkpoint_file)
            if checkpoint_data:
                completed_runs = checkpoint_data.get('completed_runs', [])
                click.echo(f"♻️  Reanudando desde checkpoint: {len(completed_runs)} runs completados")
                seeds = [s for s in seeds if s not in [r['seed'] for r in completed_runs]]
    
    # Ejecutar algoritmo
    results = []
    start_time = time.time()
    
    if parallel and len(seeds) > 1:
        click.echo(f"🔧 Ejecutando en paralelo con {workers} workers")
        
        # Crear función parcial con parámetros fijos
        run_func = partial(
            run_algorithm,
            algorithm,
            problem,
            population,
            iterations,
            use_v2=v2
        )
        
        # Ejecutar en paralelo con progress bar
        with Pool(processes=workers) as pool:
            # Crear tareas
            tasks = [(seed, i) for i, seed in enumerate(seeds)]
            
            # Ejecutar con progress bar
            with tqdm(total=len(tasks), desc=f"Ejecutando {algorithm.upper()}") as pbar:
                for result in pool.starmap(run_func, tasks):
                    if result:
                        results.append(result)
                        
                        # Checkpoint en modo massive
                        if mode == 'massive' and len(results) % checkpoint_interval == 0:
                            all_results = completed_runs + results
                            checkpoint_data = {
                                'completed_runs': all_results,
                                'algorithm': algorithm,
                                'instance': instance,
                                'timestamp': datetime.now().isoformat()
                            }
                            save_checkpoint(checkpoint_data, checkpoint_file)
                    
                    pbar.update(1)
    else:
        # Ejecución secuencial
        click.echo("🔧 Ejecutando en modo secuencial")
        
        for i, seed in enumerate(tqdm(seeds, desc=f"Ejecutando {algorithm.upper()}")):
            result = run_algorithm(
                algorithm, problem, population, iterations, 
                seed, i, use_v2=v2
            )
            if result:
                results.append(result)
                
                # Checkpoint en modo massive
                if mode == 'massive' and len(results) % checkpoint_interval == 0:
                    all_results = completed_runs + results
                    checkpoint_data = {
                        'completed_runs': all_results,
                        'algorithm': algorithm,
                        'instance': instance,
                        'timestamp': datetime.now().isoformat()
                    }
                    save_checkpoint(checkpoint_data, checkpoint_file)
    
    # Combinar con runs completados anteriormente
    all_results = completed_runs + results
    
    total_time = time.time() - start_time
    click.echo(f"⏱️  Tiempo total: {total_time:.2f} segundos")
    
    if not all_results:
        click.echo("❌ No se obtuvieron resultados", err=True)
        return
    
    # Procesar resultados
    fitness_values = [r['fitness'] for r in all_results]
    best_idx = np.argmin(fitness_values)
    best_result = all_results[best_idx]
    
    # Estadísticas
    stats = {
        'algorithm': algorithm,
        'instance': instance,
        'mode': mode,
        'total_runs': len(all_results),
        'best_fitness': best_result['fitness'],
        'worst_fitness': np.max(fitness_values),
        'mean_fitness': np.mean(fitness_values),
        'std_fitness': np.std(fitness_values),
        'median_fitness': np.median(fitness_values),
        'q1_fitness': np.percentile(fitness_values, 25),
        'q3_fitness': np.percentile(fitness_values, 75),
        'best_seed': best_result['seed'],
        'total_time': total_time,
        'timestamp': datetime.now().isoformat()
    }
    
    # Mostrar resultados
    click.echo("\n📊 Resultados:")
    click.echo(f"✅ Mejor fitness: {stats['best_fitness']:.4f} (semilla: {stats['best_seed']})")
    click.echo(f"📈 Media ± Std: {stats['mean_fitness']:.4f} ± {stats['std_fitness']:.4f}")
    click.echo(f"📊 Mediana: {stats['median_fitness']:.4f}")
    click.echo(f"📊 Q1-Q3: [{stats['q1_fitness']:.4f}, {stats['q3_fitness']:.4f}]")
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{mode}_{algorithm}_{instance.replace('.vrp', '')}"
    
    # Guardar JSON detallado
    json_file = f"{output_dir}/{prefix}_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump({
            'stats': stats,
            'results': all_results
        }, f, indent=2)
    click.echo(f"💾 Resultados guardados en: {json_file}")
    
    # Guardar CSV resumido
    csv_file = f"{output_dir}/{prefix}_{timestamp}.csv"
    df = pd.DataFrame(all_results)
    df.to_csv(csv_file, index=False)
    click.echo(f"📄 CSV guardado en: {csv_file}")
    
    # Generar gráficos si se solicita
    if plot:
        click.echo("📈 Generando gráficos...")
        
        # Gráfico de convergencia del mejor run
        plot_file = f"plots/{prefix}_convergence_{timestamp}.png"
        plot_convergence(
            best_result['convergence'],
            title=f"{algorithm.upper()} - {instance} (Best Run)",
            save_path=plot_file
        )
        click.echo(f"📊 Gráfico de convergencia: {plot_file}")
        
        # Gráfico de solución VRP si es posible
        try:
            solution_to_plot = best_result['solution']
            # La v2 ya tiene la lista de rutas, la v1 necesita decodificación
            if not v2:
                # La solución en v1 es un vector continuo que necesita decodificación
                routes, _, _ = problem.decode_solution(np.array(solution_to_plot))
                solution_to_plot = routes

            solution_file = f"plots/{prefix}_solution_{timestamp}.png"
            plot_vrp_solution(
                problem,
                solution_to_plot,
                title=f"{algorithm.upper()} - {instance} (Best Solution)",
                save_path=solution_file
            )
            click.echo(f"🗺️  Gráfico de solución: {solution_file}")
        except Exception as e:
            click.echo(f"⚠️  No se pudo generar el gráfico de la solución: {e}", err=True)
    
    # Limpiar checkpoint si se completó el modo massive
    if mode == 'massive' and checkpoint_file and os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        click.echo("🧹 Checkpoint eliminado (ejecución completada)")
    
    click.echo("\n✅ Ejecución completada exitosamente")


if __name__ == "__main__":
    main()