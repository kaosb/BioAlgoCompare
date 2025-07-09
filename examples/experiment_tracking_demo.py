#!/usr/bin/env python3
"""
Demostración del sistema de registro de experimentos.

Este script muestra cómo usar el ExperimentTracker para registrar
y analizar experimentos de manera profesional y reproducible.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.experiment_tracker import (
    ExperimentTracker, ExperimentConfig, ExperimentResult,
    create_experiment_result
)
from algorithms.woa_v2 import WOAV2
from algorithms.sma_v2 import SMAV2
from problems.vrp_v2 import VRPProblemV2
import time


def run_demo():
    """Ejecuta una demostración del sistema de tracking."""
    
    print("🔬 Demostración del Sistema de Registro de Experimentos")
    print("=" * 60)
    
    # 1. Crear tracker
    tracker = ExperimentTracker(base_dir="demo_experiments", auto_save=True)
    print("\n✅ Tracker creado en: demo_experiments/")
    
    # 2. Cargar problema
    problem_path = "data/vrp/P-n16-k8.vrp"
    if not os.path.exists(problem_path):
        print(f"❌ Error: No se encuentra {problem_path}")
        print("   Por favor, ejecuta desde el directorio raíz del proyecto")
        return
    
    problem = VRPProblemV2(problem_path)
    print(f"✅ Problema cargado: P-n16-k8 (dimensión: {problem.dimension})")
    
    # 3. Experimento 1: WOA con diferentes tamaños de población
    print("\n📊 Experimento 1: Análisis de tamaño de población en WOA")
    print("-" * 40)
    
    population_sizes = [20, 30, 50]
    woa_experiments = []
    
    for pop_size in population_sizes:
        # Configurar experimento
        config = ExperimentConfig(
            algorithm="woa",
            problem_instance="P-n16-k8.vrp",
            population_size=pop_size,
            max_iterations=50,
            algorithm_params={"a": 2.0, "b": 1.0}
        )
        
        # Iniciar experimento
        exp_id = tracker.start_experiment(config, metadata={
            "experiment_type": "population_size_analysis",
            "variable": "population_size",
            "value": pop_size
        })
        woa_experiments.append(exp_id)
        
        print(f"\n  Probando población = {pop_size}")
        
        # Ejecutar 5 runs
        for run in range(5):
            seed = 42 + run
            start_time = time.time()
            
            # Ejecutar algoritmo
            woa = WOAV2(problem, population_size=pop_size, max_iterations=50, seed=seed)
            best = woa.execute()
            
            execution_time = time.time() - start_time
            
            # Crear y registrar resultado
            result = create_experiment_result(
                run_id=run,
                seed=seed,
                algorithm_result=best,
                execution_time=execution_time
            )
            result.convergence_curve = woa.get_convergence_curve()
            
            tracker.log_result(result)
            print(f"    Run {run+1}/5: fitness = {best.fitness():.2f}, tiempo = {execution_time:.2f}s")
        
        # Mostrar resumen
        stats = tracker.current_experiment.summary_stats
        print(f"  📈 Resumen: media = {stats['mean_fitness']:.2f}, std = {stats['std_fitness']:.2f}")
    
    # 4. Experimento 2: Comparación WOA vs SMA
    print("\n📊 Experimento 2: Comparación WOA vs SMA")
    print("-" * 40)
    
    algorithms = [("woa", WOAV2), ("sma", SMAV2)]
    comparison_experiments = []
    
    for algo_name, algo_class in algorithms:
        config = ExperimentConfig(
            algorithm=algo_name,
            problem_instance="P-n16-k8.vrp",
            population_size=30,
            max_iterations=50
        )
        
        exp_id = tracker.start_experiment(config, metadata={
            "experiment_type": "algorithm_comparison"
        })
        comparison_experiments.append(exp_id)
        
        print(f"\n  Ejecutando {algo_name.upper()}")
        
        # Ejecutar 3 runs
        for run in range(3):
            seed = 100 + run
            start_time = time.time()
            
            algorithm = algo_class(problem, population_size=30, max_iterations=50, seed=seed)
            best = algorithm.execute()
            
            execution_time = time.time() - start_time
            
            result = create_experiment_result(
                run_id=run,
                seed=seed,
                algorithm_result=best,
                execution_time=execution_time
            )
            result.convergence_curve = algorithm.get_convergence_curve()
            
            tracker.log_result(result)
            print(f"    Run {run+1}/3: fitness = {best.fitness():.2f}")
    
    # 5. Análisis de resultados
    print("\n📊 Análisis de Resultados")
    print("=" * 60)
    
    # Comparar experimentos de tamaño de población
    print("\n1. Efecto del tamaño de población en WOA:")
    pop_comparison = tracker.compare_experiments(woa_experiments)
    for _, row in pop_comparison.iterrows():
        pop_size = int(row['experiment_id'].split('_')[-1].split('-')[0])  # Extraer de metadata
        print(f"   Pop={tracker.load_experiment(row['experiment_id']).metadata['value']:3d}: "
              f"media={row['mean_fitness']:7.2f}, mejor={row['best_fitness']:7.2f}")
    
    # Comparar algoritmos
    print("\n2. Comparación de algoritmos:")
    algo_comparison = tracker.compare_experiments(comparison_experiments)
    for _, row in algo_comparison.iterrows():
        print(f"   {row['algorithm'].upper():3s}: "
              f"media={row['mean_fitness']:7.2f}, mejor={row['best_fitness']:7.2f}, "
              f"tiempo={row['mean_execution_time']:.2f}s")
    
    # 6. Exportar resultados
    print("\n💾 Exportando resultados...")
    
    # Seleccionar mejor experimento para exportar
    all_experiments = tracker.list_experiments()
    best_exp_id = all_experiments.loc[all_experiments['best_fitness'].idxmin()]['experiment_id']
    
    # Exportar en diferentes formatos
    json_file = tracker.export_experiment(best_exp_id, format='json')
    html_file = tracker.export_experiment(best_exp_id, format='html')
    latex_file = tracker.export_experiment(best_exp_id, format='latex')
    
    print(f"   ✅ JSON: {json_file}")
    print(f"   ✅ HTML: {html_file}")
    print(f"   ✅ LaTeX: {latex_file}")
    
    # 7. Mostrar resumen de todos los experimentos
    print("\n📋 Resumen de todos los experimentos:")
    summary = tracker.list_experiments()
    print(f"\nTotal de experimentos: {len(summary)}")
    print(f"Mejor fitness global: {summary['best_fitness'].min():.2f}")
    print(f"Algoritmo con mejor promedio: {summary.loc[summary['mean_fitness'].idxmin()]['algorithm']}")
    
    print("\n✨ ¡Demostración completada!")
    print(f"   Los resultados están en: demo_experiments/")
    print(f"   Abre {html_file} en tu navegador para ver el reporte")


if __name__ == "__main__":
    run_demo()