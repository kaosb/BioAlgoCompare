#!/usr/bin/env python3
"""
Demostración del uso de la base de datos de resultados.

Este script muestra cómo usar la base de datos SQLite para
almacenar, consultar y analizar resultados experimentales.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.results_database import ResultsDatabase, DatabaseQuery
from utils.tracker_db_integration import (
    TrackerWithDatabase, DatabaseBackedTracker,
    setup_database_tracking, migrate_experiments_to_database
)
from utils.result_schema import ResultBuilder
from algorithms.woa_v2 import WOAV2
from algorithms.sma_v2 import SMAV2
from problems.vrp_v2 import VRPProblemV2
import time
from datetime import datetime


def demo_basic_database():
    """Demostración básica de la base de datos."""
    print("🗄️  Demostración de Base de Datos de Resultados")
    print("=" * 60)
    
    # 1. Crear base de datos
    db = ResultsDatabase("demo_results.db")
    print("✅ Base de datos creada: demo_results.db")
    
    # 2. Ejecutar un experimento simple
    print("\n📊 Ejecutando experimento...")
    
    # Cargar problema
    problem = VRPProblemV2("data/vrp/P-n16-k8.vrp")
    
    # Ejecutar WOA
    woa = WOAV2(problem, population_size=20, max_iterations=50, seed=42)
    start_time = time.time()
    best = woa.execute()
    execution_time = time.time() - start_time
    
    # Crear resultado estándar
    result = ResultBuilder.create_single_run(
        algorithm_name="woa",
        problem_name="P-n16-k8",
        run_result=best,
        execution_time=execution_time,
        dimension=problem.dimension,
        optimal_value=450.0,
        population_size=20,
        max_iterations=50,
        convergence_curve=woa.get_convergence_curve(),
        seed=42
    )
    
    # 3. Insertar en base de datos
    if db.insert_result(result):
        print(f"✅ Resultado insertado: {result.result_id}")
    else:
        print("⚠️  El resultado ya existe en la base de datos")
    
    # 4. Consultar resultado
    print("\n🔍 Consultando base de datos...")
    
    # Buscar por algoritmo
    woa_results = db.search_results(algorithm="woa")
    print(f"Encontrados {len(woa_results)} resultados de WOA")
    
    # Obtener resultado específico
    retrieved = db.get_result(result.result_id)
    if retrieved:
        print(f"Resultado recuperado: fitness = {retrieved.statistics.best_fitness:.2f}")
    
    # 5. Estadísticas
    stats = db.get_statistics()
    print(f"\n📈 Estadísticas de la BD:")
    print(f"  - Total resultados: {stats['total_results']}")
    print(f"  - Total runs: {stats['total_runs']}")
    print(f"  - Algoritmos únicos: {stats['unique_algorithms']}")
    
    return db


def demo_tracker_integration():
    """Demostración de integración con el tracker."""
    print("\n\n🔗 Demostración de Integración Tracker + BD")
    print("=" * 60)
    
    # 1. Crear tracker con base de datos
    tracker = TrackerWithDatabase(
        base_dir="demo_experiments",
        db_path="demo_experiments/tracker_results.db",
        auto_persist=True
    )
    print("✅ Tracker con BD creado")
    
    # 2. Configurar experimento
    from utils.experiment_tracker import ExperimentConfig
    
    config = ExperimentConfig(
        algorithm="sma",
        problem_instance="P-n16-k8.vrp",
        population_size=25,
        max_iterations=60,
        algorithm_params={"z": 0.03}
    )
    
    # 3. Iniciar experimento
    exp_id = tracker.start_experiment(config, metadata={
        "purpose": "demo integración DB"
    })
    print(f"✅ Experimento iniciado: {exp_id}")
    
    # 4. Ejecutar y registrar
    problem = VRPProblemV2("data/vrp/P-n16-k8.vrp")
    
    for run in range(3):
        print(f"\n  Ejecutando run {run+1}/3...")
        
        sma = SMAV2(problem, population_size=25, max_iterations=60, seed=100+run)
        start_time = time.time()
        best = sma.execute()
        execution_time = time.time() - start_time
        
        # Registrar resultado
        from utils.experiment_tracker import create_experiment_result
        
        result = create_experiment_result(
            run_id=run,
            seed=100+run,
            algorithm_result=best,
            execution_time=execution_time
        )
        result.convergence_curve = sma.get_convergence_curve()
        
        tracker.log_result(result)
        print(f"    Fitness: {best.fitness():.2f}")
    
    # 5. Guardar (persiste automáticamente en BD)
    tracker.save_current()
    print("\n✅ Experimento guardado y persistido en BD")
    
    # 6. Consultar desde la BD
    db_stats = tracker.get_database_stats()
    print(f"\n📊 Estado de la BD del tracker:")
    print(f"  - Total resultados: {db_stats['total_results']}")
    
    # 7. Buscar en BD
    sma_results = tracker.search_in_database(algorithm="sma")
    print(f"  - Resultados de SMA: {len(sma_results)}")
    
    return tracker


def demo_database_backed_tracker():
    """Demostración del tracker simplificado con BD."""
    print("\n\n💾 Demostración de DatabaseBackedTracker")
    print("=" * 60)
    
    # 1. Crear tracker respaldado por BD
    db_tracker = DatabaseBackedTracker("demo_db_tracker.db")
    print("✅ DatabaseBackedTracker creado")
    
    # 2. Ejecutar múltiples algoritmos
    algorithms = [
        ("woa", WOAV2, {"a": 2.0, "b": 1.0}),
        ("sma", SMAV2, {"z": 0.03})
    ]
    
    problem = VRPProblemV2("data/vrp/E-n22-k4.vrp")
    
    for algo_name, AlgoClass, params in algorithms:
        print(f"\n📊 Ejecutando {algo_name.upper()}...")
        
        # Ejecutar 2 runs
        run_results = []
        for i in range(2):
            algo = AlgoClass(
                problem, 
                population_size=30, 
                max_iterations=40,
                seed=200+i,
                **params
            )
            
            start = time.time()
            best = algo.execute()
            exec_time = time.time() - start
            
            run_results.append({
                'best_fitness': best.fitness(),
                'best_solution': best.position,
                'convergence_curve': algo.get_convergence_curve(),
                'execution_time': exec_time,
                'seed': 200+i
            })
            
            print(f"  Run {i+1}: {best.fitness():.2f}")
        
        # Crear resultado multi-run
        result = ResultBuilder.create_multi_run(
            algorithm_name=algo_name,
            problem_name="E-n22-k4",
            run_results=run_results,
            dimension=problem.dimension,
            optimal_value=375.0,
            population_size=30,
            max_iterations=40,
            algorithm_params=params
        )
        
        # Registrar en BD
        if db_tracker.track_result(result):
            print(f"✅ Resultado de {algo_name} registrado")
    
    # 3. Comparar algoritmos
    print("\n📊 Comparación de algoritmos:")
    comparison = db_tracker.compare_algorithms(["woa", "sma"])
    
    for problem_name, algos in comparison.items():
        print(f"\n{problem_name}:")
        for algo, metrics in algos.items():
            print(f"  {algo}: best={metrics['best_fitness']:.2f}, "
                  f"avg={metrics['avg_fitness']:.2f}")
    
    # 4. Obtener mejor resultado
    best_result = db_tracker.get_best_for_problem("E-n22-k4")
    if best_result:
        print(f"\n🏆 Mejor resultado para E-n22-k4:")
        print(f"  Algoritmo: {best_result.algorithm_info.name}")
        print(f"  Fitness: {best_result.statistics.best_fitness:.2f}")
        print(f"  Gap: {best_result.get_gap_to_optimal():.2f}%")
    
    # 5. Estadísticas
    stats = db_tracker.stats()
    print(f"\n📈 Estadísticas totales:")
    print(f"  - Resultados: {stats['total_results']}")
    print(f"  - Runs: {stats['total_runs']}")
    
    return db_tracker


def demo_migration():
    """Demostración de migración de experimentos existentes."""
    print("\n\n🔄 Demostración de Migración a BD")
    print("=" * 60)
    
    # Simular que tenemos experimentos existentes
    print("Migrando experimentos existentes a base de datos...")
    
    # Intentar migrar (si hay experimentos)
    migrated, errors = migrate_experiments_to_database(
        experiment_dir="experiments",
        db_path="migrated_results.db"
    )
    
    if migrated > 0:
        print(f"✅ Migrados {migrated} experimentos")
        if errors > 0:
            print(f"⚠️  Errores en {errors} archivos")
    else:
        print("ℹ️  No hay experimentos para migrar")
    
    # Verificar base de datos migrada
    if migrated > 0:
        db = ResultsDatabase("migrated_results.db")
        stats = db.get_statistics()
        print(f"\n📊 Base de datos migrada:")
        print(f"  - Total resultados: {stats['total_results']}")


def demo_advanced_queries():
    """Demostración de consultas avanzadas."""
    print("\n\n🔍 Demostración de Consultas Avanzadas")
    print("=" * 60)
    
    # Usar la BD de demo con algunos datos
    db = ResultsDatabase("demo_results.db")
    query = DatabaseQuery(db)
    
    # 1. Timeline de mejoras
    print("\n📈 Timeline de mejoras para WOA en P-n16-k8:")
    timeline = query.get_improvement_timeline("woa", "P-n16-k8")
    
    if not timeline.empty:
        for _, row in timeline.iterrows():
            improvement = f"+{row['improvement']:.2f}" if row['improvement'] > 0 else ""
            print(f"  {row['timestamp']}: {row['best_fitness']:.2f} {improvement}")
    else:
        print("  (No hay suficientes datos)")
    
    # 2. Parámetros óptimos
    print("\n🎯 Búsqueda de parámetros óptimos:")
    optimal = query.find_optimal_parameters("woa", "P-n16-k8")
    
    if optimal:
        print(f"  Mejor configuración encontrada:")
        print(f"  - Fitness: {optimal['metric_value']:.2f}")
        print(f"  - Parámetros: {optimal['parameters']}")
    
    # 3. Exportar a CSV
    print("\n💾 Exportando base de datos...")
    db.export_to_csv("demo_export")
    print("✅ Datos exportados a demo_export/")


def cleanup_demo_files():
    """Limpia archivos de demostración."""
    import os
    import shutil
    
    files = [
        "demo_results.db",
        "demo_db_tracker.db", 
        "migrated_results.db"
    ]
    
    dirs = [
        "demo_experiments",
        "demo_export"
    ]
    
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    
    for dir in dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)
    
    print("\n🧹 Archivos de demo limpiados")


def main():
    """Ejecuta todas las demostraciones."""
    print("🚀 DEMOSTRACIÓN COMPLETA DEL SISTEMA DE BASE DE DATOS")
    print("=" * 80)
    
    try:
        # 1. Base de datos básica
        db = demo_basic_database()
        
        # 2. Integración con tracker
        tracker = demo_tracker_integration()
        
        # 3. Tracker respaldado por BD
        db_tracker = demo_database_backed_tracker()
        
        # 4. Migración
        demo_migration()
        
        # 5. Consultas avanzadas
        demo_advanced_queries()
        
        print("\n\n✨ ¡Demostración completada exitosamente!")
        print("\nArchivos creados:")
        print("  - demo_results.db: Base de datos principal")
        print("  - demo_experiments/: Directorio de experimentos con tracker")
        print("  - demo_db_tracker.db: Base de datos del tracker simplificado")
        print("  - demo_export/: Exportación CSV de la base de datos")
        
        # Preguntar si limpiar
        response = input("\n¿Desea eliminar los archivos de demo? (s/n): ")
        if response.lower() == 's':
            cleanup_demo_files()
        else:
            print("ℹ️  Archivos de demo conservados para exploración")
            
    except Exception as e:
        print(f"\n❌ Error en la demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()