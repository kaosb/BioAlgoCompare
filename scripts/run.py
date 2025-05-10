#!/usr/bin/env python3
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

# Importar algoritmos
from algorithms.sho import SHO  # Spotted Hyena Optimizer (anteriormente HOA)
from algorithms.apo import APO  # Artificial Protozoa Optimizer
from algorithms.egto import EGTO  # Enhanced Gorilla Troops Optimizer
from algorithms.fsa import FSA  # Flamingo Search Algorithm (anteriormente FGO)
from algorithms.foa import FOA  # Fossa Optimization Algorithm
from algorithms.woa import WOA  # Whale Optimization Algorithm
from algorithms.hho import HHO  # Harris Hawks Optimization
from algorithms.mrfo import MRFO  # Manta Ray Foraging Optimization
from algorithms.sma import SMA  # Slime Mould Algorithm
from algorithms.gto import GTO  # Gorilla Troops Optimizer
from algorithms.ewa import EWA  # Earthworm Algorithm
from algorithms.aha import AHA  # Artificial Hummingbird Algorithm
from algorithms.rro import RRO  # Raven Roosting Optimization
from algorithms.gvoa import GVOA  # Griffon Vultures Optimization Algorithm
from algorithms.smo import SMO  # Starling Murmuration Optimizer
from algorithms.opa import OPA  # Orca Predator Algorithm

# Aliases para mantener la compatibilidad con código antiguo
HOA = SHO  # Spotted Hyena Optimizer (anteriormente Hyena Optimization Algorithm)
FGO = FSA  # Flamingo Search Algorithm (anteriormente Flamingo Optimization Algorithm)

# Importar problema
from problems.vrp import VRPProblem

# Importar utilidades
from utils.visualization import plot_vrp_solution, plot_convergence, compare_algorithms

# Función para ejecutar un algoritmo en paralelo
def run_algorithm(algo_name, problem, population, iterations, run_seed, run_id):
    try:
        # Inicializar algoritmo
        if algo_name == 'hoa' or algo_name == 'sho':
            algo = SHO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'apo':
            algo = APO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'egto':
            algo = EGTO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'fgo' or algo_name == 'fsa':
            algo = FSA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'foa':
            algo = FOA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'woa':
            algo = WOA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'hho':
            algo = HHO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'mrfo':
            algo = MRFO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'sma':
            algo = SMA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'gto':
            algo = GTO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'ewa':
            algo = EWA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'aha':
            algo = AHA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'rro':
            algo = RRO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'gvoa':
            algo = GVOA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'smo':
            algo = SMO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
        elif algo_name == 'opa':
            algo = OPA(problem, population_size=population, max_iterations=iterations, seed=run_seed)

        # Ejecutar algoritmo
        start_time = time.time()
        best_solution = algo.execute()
        execution_time = time.time() - start_time
        
        return {
            'algorithm': algo_name.upper(),
            'run': run_id,
            'best_fitness': best_solution.fitness(),
            'execution_time': execution_time,
            'convergence': algo.get_convergence_curve(),
            'best_solution': best_solution
        }
    except Exception as e:
        return {
            'algorithm': algo_name.upper(),
            'run': run_id,
            'error': str(e)
        }

# Función auxiliar para la ejecución paralela
def run_algo_wrapper(args):
    return run_algorithm(*args)
@click.command()
@click.option('--algorithm', '-a', type=click.Choice(['hoa', 'apo', 'egto', 'fgo', 'foa', 'woa', 'hho', 'mrfo', 'sma', 'gto', 'ewa', 'aha', 'rro', 'gvoa', 'smo', 'opa', 'all']),
              required=True, help='Algoritmo a ejecutar')
@click.option('--instance', '-i', required=True, help='Nombre de la instancia VRP')
@click.option('--iterations', '-n', default=100, help='Número de iteraciones')
@click.option('--population', '-p', default=30, help='Tamaño de la población')
@click.option('--runs', '-r', default=1, help='Número de ejecuciones independientes')
@click.option('--seed', '-s', default=None, type=int, help='Semilla para reproducibilidad')
@click.option('--visualize/--no-visualize', default=True, help='Visualizar resultados')
@click.option('--save/--no-save', default=True, help='Guardar resultados')
@click.option('--parallel/--no-parallel', default=False, help='Ejecutar en paralelo')
def main(algorithm, instance, iterations, population, runs, seed, visualize, save, parallel):
    """
    Ejecuta algoritmos de optimización para resolver problemas VRP con soporte para ejecución paralela.
    
    Nota científica: Para análisis estadísticos rigurosos, se recomienda:
    - Ejecutar al menos 5 ejecuciones independientes (--runs 5 o más)
    - Incluir varios algoritmos para comparación (--algorithm all)
    - Usar semillas fijas para reproducibilidad (--seed <número>)
    - Guardar resultados para análisis posterior (--save)
    """
    
    # Verificar que la instancia exista
    instance_path = f"data/vrp/{instance}.vrp"
    if not os.path.exists(instance_path):
        click.echo(f"Error: La instancia {instance} no existe en data/vrp")
        return
    
    # Cargar el problema
    problem = VRPProblem(instance_path)
    click.echo(f"Instancia cargada: {problem.name}")
    click.echo(f"Dimensión: {problem.dimension}, Capacidad: {problem.capacity}")
    
    # Determinar qué algoritmos ejecutar
    algorithms_to_run = []
    if algorithm == 'all':
        algorithms_to_run = ['hoa', 'apo', 'egto', 'fgo', 'foa', 'woa', 'hho', 'mrfo', 'sma', 'gto', 'ewa', 'aha', 'rro', 'gvoa', 'smo', 'opa']
    else:
        algorithms_to_run = [algorithm]
    
    # Determinar número de procesos para paralelización
    num_processes = min(mp.cpu_count(), runs * len(algorithms_to_run)) if parallel else 1
    
    if parallel:
        click.echo(f"Modo paralelo activado. Usando {num_processes} procesos.")
    
    # Preparar tareas para ejecución paralela o secuencial
    all_tasks = []
    for algo_name in algorithms_to_run:
        for run in range(1, runs + 1):
            run_seed = seed + run - 1 if seed is not None else None
            all_tasks.append((algo_name, problem, population, iterations, run_seed, run))
    
    # Ejecutar algoritmos
    all_results = []
    
    if parallel and num_processes > 1:
        # Ejecución paralela
        try:
            with Pool(processes=num_processes) as pool:
                # Ejecutar tareas y mostrar progreso con barra de progreso
                click.echo(f"Ejecutando {len(all_tasks)} tareas en paralelo...")
                for result in tqdm(pool.imap_unordered(run_algo_wrapper, all_tasks), total=len(all_tasks)):
                    if 'error' in result:
                        click.echo(f"Error en {result['algorithm']}, ejecución {result['run']}: {result['error']}")
                    all_results.append(result)
        except Exception as e:
            click.echo(f"Error en la ejecución paralela: {str(e)}")
            return
    else:
        # Ejecución secuencial
        for algo_name, problem, population, iterations, run_seed, run in all_tasks:
            click.echo(f"\nEjecutando {algo_name.upper()}, ejecución {run}/{runs}...")
            result = run_algorithm(algo_name, problem, population, iterations, run_seed, run)
            
            if 'error' in result:
                click.echo(f"Error: {result['error']}")
            else:
                click.echo(f"  Mejor fitness = {result['best_fitness']:.2f}, Tiempo = {result['execution_time']:.2f}s")
            
            all_results.append(result)
    
    # Filtrar resultados exitosos
    successful_results = [r for r in all_results if 'error' not in r]
    
    if not successful_results:
        click.echo("No se obtuvieron resultados exitosos.")
        return
    
    # Preparar resultados para análisis
    results = {
        'algorithm': [],
        'run': [],
        'best_fitness': [],
        'execution_time': [],
        'convergence': [],
        'best_solution': []
    }
    
    for result in successful_results:
        results['algorithm'].append(result['algorithm'])
        results['run'].append(result['run'])
        results['best_fitness'].append(result['best_fitness'])
        results['execution_time'].append(result['execution_time'])
        results['convergence'].append(result['convergence'])
        results['best_solution'].append(result['best_solution'])
    
    # Visualizar soluciones
    if visualize:
        # Agrupar resultados por algoritmo
        algo_results = {}
        for i, algo in enumerate(results['algorithm']):
            if algo not in algo_results:
                algo_results[algo] = []
            algo_results[algo].append(i)
        
        # Para cada algoritmo, visualizar la mejor solución
        for algo, indices in algo_results.items():
            # Encontrar la mejor solución para este algoritmo
            best_idx = indices[np.argmin([results['best_fitness'][i] for i in indices])]
            best_solution = results['best_solution'][best_idx]
            
            # Visualizar solución
            routes, total_distance, _ = problem.decode_solution(best_solution.position)
            plt = plot_vrp_solution(problem, routes, f"{algo} - {instance} - Distancia: {total_distance:.2f}")
            
            if save:
                # Crear directorio si no existe
                os.makedirs("results", exist_ok=True)
                plt.savefig(f"results/{algo.lower()}_{instance}_solution.png")
            
            plt.show()
            
            # Visualizar convergencia
            plt = plot_convergence(results['convergence'][best_idx], f"{algo} - Curva de Convergencia")
            
            if save:
                plt.savefig(f"results/{algo.lower()}_{instance}_convergence.png")
            
            plt.show()
    
    # Comparar algoritmos si se ejecutaron varios
    if len(algorithms_to_run) > 1 and visualize:
        # Calcular promedio de convergencia para cada algoritmo
        avg_convergence = {}
        for algo_name in algorithms_to_run:
            algo_upper = algo_name.upper()
            algo_convergence = [results['convergence'][i] for i in range(len(results['algorithm'])) 
                               if results['algorithm'][i] == algo_upper]
            
            # Asegurar que todas las curvas tengan la misma longitud
            min_length = min(len(curve) for curve in algo_convergence)
            algo_convergence = [curve[:min_length] for curve in algo_convergence]
            
            # Calcular promedio
            avg_convergence[algo_upper] = np.mean(algo_convergence, axis=0)
        
        # Visualizar comparación
        plt = compare_algorithms(avg_convergence, f"Comparación de Algoritmos - {instance}")
        
        if save:
            plt.savefig(f"results/comparison_{instance}.png")
        
        plt.show()
    
    # Guardar resultados en CSV
    if save:
        # Crear directorio si no existe
        os.makedirs("results", exist_ok=True)
        
        # Preparar DataFrame
        df_results = pd.DataFrame({
            'Algorithm': results['algorithm'],
            'Run': results['run'],
            'Best Fitness': results['best_fitness'],
            'Execution Time (s)': results['execution_time']
        })
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df_results.to_csv(f"results/{instance}_{timestamp}.csv", index=False)
        
        # Guardar resumen
        df_summary = df_results.groupby('Algorithm').agg({
            'Best Fitness': ['min', 'mean', 'std'],
            'Execution Time (s)': ['mean', 'std']
        })
        
        df_summary.to_csv(f"results/{instance}_{timestamp}_summary.csv")
        
        click.echo(f"\nResultados guardados en results/{instance}_{timestamp}.csv")
        click.echo(f"Resumen guardado en results/{instance}_{timestamp}_summary.csv")
        
        # Guardar información sobre ejecución paralela
        if parallel:
            # Calcular métricas de paralelización
            total_runtime = sum(results['execution_time'])
            max_runtime = max(results['execution_time'])
            theoretical_speedup = total_runtime / max(1, max_runtime)
            efficiency = theoretical_speedup / num_processes
            
            parallel_info = {
                "num_processes": num_processes,
                "total_execution_time": total_runtime,
                "theoretical_sequential_time": total_runtime,
                "parallel_execution_time": max_runtime,
                "theoretical_speedup": theoretical_speedup,
                "parallel_efficiency": efficiency
            }
            
            with open(f"results/{instance}_{timestamp}_parallel_info.json", "w") as f:
                json.dump(parallel_info, f, indent=2)
            
            click.echo(f"Información de paralelización guardada en results/{instance}_{timestamp}_parallel_info.json")

if __name__ == '__main__':
    main()