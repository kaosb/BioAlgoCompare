#!/usr/bin/env python3
import click
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Importar algoritmos
from algorithms.hoa import HOA
from algorithms.apo import APO
from algorithms.egto import EGTO
from algorithms.fgo import FGO
from algorithms.foa import FOA

# Importar problema
from problems.vrp import VRPProblem

# Importar utilidades
from utils.visualization import plot_vrp_solution, plot_convergence, compare_algorithms

@click.command()
@click.option('--algorithm', '-a', type=click.Choice(['hoa', 'apo', 'egto', 'fgo', 'foa', 'all']), 
              required=True, help='Algoritmo a ejecutar')
@click.option('--instance', '-i', required=True, help='Nombre de la instancia VRP')
@click.option('--iterations', '-n', default=100, help='Número de iteraciones')
@click.option('--population', '-p', default=30, help='Tamaño de la población')
@click.option('--runs', '-r', default=1, help='Número de ejecuciones independientes')
@click.option('--seed', '-s', default=None, type=int, help='Semilla para reproducibilidad')
@click.option('--visualize/--no-visualize', default=True, help='Visualizar resultados')
@click.option('--save/--no-save', default=True, help='Guardar resultados')
def main(algorithm, instance, iterations, population, runs, seed, visualize, save):
    """Ejecuta algoritmos de optimización para resolver problemas VRP."""
    
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
        algorithms_to_run = ['hoa', 'apo', 'egto', 'fgo', 'foa']
    else:
        algorithms_to_run = [algorithm]
    
    # Preparar resultados
    results = {
        'algorithm': [],
        'run': [],
        'best_fitness': [],
        'execution_time': [],
        'convergence': []
    }
    
    # Ejecutar algoritmos
    for algo_name in algorithms_to_run:
        click.echo(f"\nEjecutando {algo_name.upper()}...")
        
        for run in range(1, runs + 1):
            # Establecer semilla para reproducibilidad
            run_seed = seed + run - 1 if seed is not None else None
            
            # Inicializar algoritmo
            if algo_name == 'hoa':
                algo = HOA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
            elif algo_name == 'apo':
                algo = APO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
            elif algo_name == 'egto':
                algo = EGTO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
            elif algo_name == 'fgo':
                algo = FGO(problem, population_size=population, max_iterations=iterations, seed=run_seed)
            elif algo_name == 'foa':
                algo = FOA(problem, population_size=population, max_iterations=iterations, seed=run_seed)
            
            # Ejecutar algoritmo
            start_time = time.time()
            best_solution = algo.execute()
            execution_time = time.time() - start_time
            
            # Guardar resultados
            results['algorithm'].append(algo_name.upper())
            results['run'].append(run)
            results['best_fitness'].append(best_solution.fitness())
            results['execution_time'].append(execution_time)
            results['convergence'].append(algo.get_convergence_curve())
            
            click.echo(f"  Ejecución {run}/{runs}: Mejor fitness = {best_solution.fitness():.2f}, Tiempo = {execution_time:.2f}s")
            
            # Visualizar solución
            if visualize and run == runs:  # Solo visualizar la última ejecución
                routes, total_distance, _ = problem.decode_solution(best_solution.position)
                plt = plot_vrp_solution(problem, routes, f"{algo_name.upper()} - {instance} - Distancia: {total_distance:.2f}")
                
                if save:
                    # Crear directorio si no existe
                    os.makedirs("results", exist_ok=True)
                    plt.savefig(f"results/{algo_name}_{instance}_solution.png")
                
                plt.show()
                
                # Visualizar convergencia
                plt = plot_convergence(algo.get_convergence_curve(), f"{algo_name.upper()} - Curva de Convergencia")
                
                if save:
                    plt.savefig(f"results/{algo_name}_{instance}_convergence.png")
                
                plt.show()
    
    # Comparar algoritmos si se ejecutaron varios
    if len(algorithms_to_run) > 1 and visualize:
        # Calcular promedio de convergencia para cada algoritmo
        avg_convergence = {}
        for algo_name in algorithms_to_run:
            algo_convergence = [results['convergence'][i] for i in range(len(results['algorithm'])) 
                               if results['algorithm'][i] == algo_name.upper()]
            
            # Asegurar que todas las curvas tengan la misma longitud
            min_length = min(len(curve) for curve in algo_convergence)
            algo_convergence = [curve[:min_length] for curve in algo_convergence]
            
            # Calcular promedio
            avg_convergence[algo_name.upper()] = np.mean(algo_convergence, axis=0)
        
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

if __name__ == '__main__':
    main()
