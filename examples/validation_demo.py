#!/usr/bin/env python3
"""
Demostración del sistema de validación de resultados.

Este script muestra cómo usar el sistema de validación con
diferentes niveles y configuraciones.
"""

import numpy as np
from datetime import datetime
import sys
import os

# Añadir directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.result_validation import (
    ResultValidator, ValidationLevel, ValidationStatus,
    create_vrp_validator, create_convergence_validator,
    quick_validate
)
from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics,
    ProblemInfo, AlgorithmInfo, ExecutionInfo, ResultType
)
from utils.validation_integration import (
    ValidatedExperimentTracker, ValidatedResultsDatabase,
    setup_auto_validation
)


def create_sample_results():
    """Crea resultados de ejemplo para demostración."""
    results = []
    
    # 1. Resultado válido
    valid_result = StandardResult(
        result_id='demo_valid_001',
        result_type=ResultType.SINGLE_RUN,
        timestamp=datetime.now(),
        problem_info=ProblemInfo(
            name='A-n32-k5',
            problem_type='VRP',
            dimension=32,
            optimal_value=784.0,
            metadata={'capacity': 100}
        ),
        algorithm_info=AlgorithmInfo(
            name='GeneticAlgorithm',
            version='2.0',
            parameters={
                'population_size': 50,
                'crossover_rate': 0.8,
                'mutation_rate': 0.1
            }
        ),
        execution_info=ExecutionInfo(
            platform='Linux',
            python_version='3.8.10',
            total_time=45.3,
            metadata={'seed': 42}
        ),
        data=SingleRunResult(
            run_id=1,
            seed=42,
            best_fitness=812.5,
            execution_time=45.3,
            iterations_completed=100,
            convergence_curve=[950.0, 900.0, 850.0, 830.0, 820.0, 815.0, 812.5],
            best_solution=[
                [0, 1, 2, 3, 4, 0],
                [0, 5, 6, 7, 8, 0],
                [0, 9, 10, 11, 0]
            ]
        )
    )
    results.append(('Valid Result', valid_result))
    
    # 2. Resultado con error numérico
    nan_result = StandardResult(
        result_id='demo_nan_002',
        result_type=ResultType.SINGLE_RUN,
        timestamp=datetime.now(),
        problem_info=ProblemInfo(
            name='test_problem',
            problem_type='optimization',
            dimension=10
        ),
        algorithm_info=AlgorithmInfo(
            name='BuggyAlgorithm',
            version='1.0'
        ),
        execution_info=ExecutionInfo(
            platform='Windows',
            python_version='3.9.0',
            total_time=10.0
        ),
        data=SingleRunResult(
            run_id=1,
            seed=123,
            best_fitness=float('nan'),  # Error: NaN
            execution_time=10.0,
            iterations_completed=50,
            convergence_curve=[100.0, 90.0, float('inf'), 70.0]  # Error: Inf
        )
    )
    results.append(('Result with NaN/Inf', nan_result))
    
    # 3. Resultado VRP con solución inválida
    invalid_vrp = StandardResult(
        result_id='demo_vrp_003',
        result_type=ResultType.SINGLE_RUN,
        timestamp=datetime.now(),
        problem_info=ProblemInfo(
            name='vrp_test',
            problem_type='VRP',
            dimension=6,  # 5 clientes + depósito
            optimal_value=100.0
        ),
        algorithm_info=AlgorithmInfo(
            name='VRPSolver',
            version='1.0'
        ),
        execution_info=ExecutionInfo(
            platform='Linux',
            python_version='3.8.0',
            total_time=5.0
        ),
        data=SingleRunResult(
            run_id=1,
            seed=42,
            best_fitness=120.0,
            execution_time=5.0,
            iterations_completed=20,
            best_solution=[
                [0, 1, 2, 0],
                [0, 2, 3, 0],  # Error: nodo 2 visitado dos veces
                [0, 4, 0]      # Error: falta nodo 5
            ]
        )
    )
    results.append(('Invalid VRP Solution', invalid_vrp))
    
    # 4. Resultado multi-run con inconsistencias
    inconsistent_multi = StandardResult(
        result_id='demo_multi_004',
        result_type=ResultType.MULTI_RUN,
        timestamp=datetime.now(),
        problem_info=ProblemInfo(
            name='test_problem',
            problem_type='optimization',
            dimension=20,
            optimal_value=50.0
        ),
        algorithm_info=AlgorithmInfo(
            name='MultiRunAlgo',
            version='1.0',
            parameters={'runs': 10}
        ),
        execution_info=ExecutionInfo(
            platform='MacOS',
            python_version='3.9.5',
            total_time=100.0
        ),
        data=MultiRunStatistics(
            total_runs=10,
            best_fitness=52.3,
            worst_fitness=58.7,
            mean_fitness=40.0,  # Error: mean < best
            std_fitness=-2.5,   # Error: std negativo
            median_fitness=55.0,
            all_fitness_values=[52.3, 53.1, 54.2, 55.0, 55.5, 56.1, 56.8, 57.2, 58.0, 58.7],
            all_execution_times=[10.0] * 10
        )
    )
    results.append(('Inconsistent Multi-Run', inconsistent_multi))
    
    # 5. Resultado con convergencia pobre
    poor_convergence = StandardResult(
        result_id='demo_conv_005',
        result_type=ResultType.SINGLE_RUN,
        timestamp=datetime.now(),
        problem_info=ProblemInfo(
            name='hard_problem',
            problem_type='optimization',
            dimension=50,
            optimal_value=1000.0
        ),
        algorithm_info=AlgorithmInfo(
            name='SlowConverger',
            version='1.0'
        ),
        execution_info=ExecutionInfo(
            platform='Linux',
            python_version='3.8.0',
            total_time=60.0
        ),
        data=SingleRunResult(
            run_id=1,
            seed=999,
            best_fitness=1950.0,
            execution_time=60.0,
            iterations_completed=1000,
            convergence_curve=[2000.0, 1999.0, 1998.0, 1997.0, 1996.0, 1995.0] + 
                            [1995.0] * 50 +  # Estancamiento largo
                            [1990.0, 1985.0, 1980.0, 1975.0, 1970.0, 1965.0, 1960.0, 1955.0, 1950.0]
        )
    )
    results.append(('Poor Convergence', poor_convergence))
    
    return results


def demonstrate_validation_levels():
    """Demuestra diferentes niveles de validación."""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DE NIVELES DE VALIDACIÓN")
    print("="*60)
    
    # Crear resultado con múltiples problemas
    test_result = StandardResult(
        result_id='level_test',
        result_type=ResultType.SINGLE_RUN,
        timestamp=datetime.now(),
        problem_info=ProblemInfo(
            name='vrp_test',
            problem_type='VRP',
            dimension=5,
            optimal_value=100.0
        ),
        algorithm_info=AlgorithmInfo(
            name='TestAlgo',
            version='1.0'
        ),
        execution_info=ExecutionInfo(
            platform='Test',
            python_version='3.8.0',
            total_time=10.0,
            metadata={}  # Sin semillas - problema de reproducibilidad
        ),
        data=SingleRunResult(
            run_id=1,
            seed=42,
            best_fitness=95.0,  # Mejor que óptimo!
            execution_time=10.0,
            iterations_completed=100,
            convergence_curve=[150.0, 120.0, 100.0, 95.0],
            best_solution=[[0, 1, 2, 0], [0, 3, 0]]  # Falta nodo 4
        )
    )
    
    # Probar cada nivel
    for level in ValidationLevel:
        print(f"\n{level.value.upper()} Validation:")
        print("-" * 40)
        
        validator = ResultValidator(level)
        report = validator.validate_result(test_result)
        
        print(f"Passed: {report.passed}")
        print(f"Total Issues: {len(report.issues)}")
        print(f"Critical: {len(report.get_issues_by_level(ValidationStatus.CRITICAL))}")
        print(f"Errors: {len(report.get_issues_by_level(ValidationStatus.ERROR))}")
        print(f"Warnings: {len(report.get_issues_by_level(ValidationStatus.WARNING))}")
        
        if report.issues:
            print("\nSample Issues:")
            for issue in report.issues[:3]:  # Mostrar primeras 3
                print(f"  - [{issue.level.value}] {issue.category}: {issue.message}")


def demonstrate_custom_validators():
    """Demuestra validadores personalizados."""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DE VALIDADORES PERSONALIZADOS")
    print("="*60)
    
    # Crear validador con reglas personalizadas
    validator = ResultValidator()
    
    # Añadir validador VRP
    validator.add_custom_validator('vrp', create_vrp_validator())
    
    # Añadir validador de convergencia estricto
    validator.add_custom_validator(
        'strict_convergence',
        create_convergence_validator(min_improvement=0.10, max_stagnation=20)
    )
    
    # Añadir validador personalizado
    def custom_time_validator(result, report):
        """Valida que el tiempo por iteración sea razonable."""
        if result.result_type == ResultType.SINGLE_RUN:
            time_per_iter = result.data.execution_time / result.data.iterations_completed
            if time_per_iter > 1.0:  # Más de 1 segundo por iteración
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='performance',
                    message=f'High time per iteration: {time_per_iter:.2f}s',
                    suggestion='Consider optimizing the algorithm implementation'
                ))
    
    validator.add_custom_validator('time_check', custom_time_validator)
    
    # Validar resultado de ejemplo
    _, poor_conv_result = create_sample_results()[4]  # Poor convergence
    report = validator.validate_result(poor_conv_result)
    
    print(f"Custom validation report for {poor_conv_result.result_id}:")
    print(f"Passed: {report.passed}")
    print(f"Issues found: {len(report.issues)}")
    
    for issue in report.issues:
        print(f"\n[{issue.level.value}] {issue.category}:")
        print(f"  {issue.message}")
        if issue.suggestion:
            print(f"  Suggestion: {issue.suggestion}")


def demonstrate_integration():
    """Demuestra integración con tracker y base de datos."""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DE INTEGRACIÓN")
    print("="*60)
    
    # Crear tracker validado
    tracker = ValidatedExperimentTracker(
        base_dir="demo_experiments",
        auto_validate=True,
        validation_level=ValidationLevel.STANDARD
    )
    
    print("Validating all sample results...")
    
    # Validar todos los resultados de ejemplo
    sample_results = create_sample_results()
    
    for name, result in sample_results:
        print(f"\n{name}:")
        
        # Simular guardado en tracker (normalmente vendría de un experimento real)
        # Aquí solo validamos directamente
        report = tracker.validator.validate_result(result)
        
        print(f"  - Passed: {report.passed}")
        print(f"  - Issues: {len(report.issues)}")
        
        if not report.passed:
            # Mostrar primer error/crítico
            for issue in report.issues:
                if issue.level in [ValidationStatus.ERROR, ValidationStatus.CRITICAL]:
                    print(f"  - First Error: [{issue.level.value}] {issue.message}")
                    break
    
    # Mostrar resumen
    print("\n" + "-"*40)
    print("VALIDATION SUMMARY")
    print("-"*40)
    
    total = len(sample_results)
    passed = sum(1 for _, r in sample_results if quick_validate(r))
    
    print(f"Total Results: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass Rate: {passed/total*100:.1f}%")


def demonstrate_batch_validation():
    """Demuestra validación por lotes."""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DE VALIDACIÓN POR LOTES")
    print("="*60)
    
    # Crear múltiples resultados
    results = []
    for i in range(10):
        result = StandardResult(
            result_id=f'batch_{i:03d}',
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo(
                name=f'problem_{i}',
                problem_type='optimization',
                dimension=10 + i
            ),
            algorithm_info=AlgorithmInfo(
                name='BatchAlgo',
                version='1.0'
            ),
            execution_info=ExecutionInfo(
                platform='Linux',
                python_version='3.8.0',
                total_time=5.0 + i
            ),
            data=SingleRunResult(
                run_id=i,
                seed=42 + i,
                best_fitness=100.0 + np.random.normal(0, 10),  # Añadir variabilidad
                execution_time=5.0 + i,
                iterations_completed=50,
                convergence_curve=[200.0, 150.0, 120.0, 110.0, 105.0, 100.0]
            )
        )
        results.append(result)
    
    # Validar en lote
    validator = ResultValidator(ValidationLevel.STANDARD)
    
    import time
    
    # Sin paralelización
    start = time.time()
    reports_serial = validator.validate_batch(results, parallel=False)
    time_serial = time.time() - start
    
    # Con paralelización
    start = time.time()
    reports_parallel = validator.validate_batch(results, parallel=True)
    time_parallel = time.time() - start
    
    print(f"Validated {len(results)} results")
    print(f"Serial time: {time_serial:.3f}s")
    print(f"Parallel time: {time_parallel:.3f}s")
    print(f"Speedup: {time_serial/time_parallel:.2f}x")
    
    # Mostrar estadísticas
    passed = sum(1 for r in reports_serial.values() if r.passed)
    total_issues = sum(len(r.issues) for r in reports_serial.values())
    
    print(f"\nValidation Statistics:")
    print(f"  - Passed: {passed}/{len(results)}")
    print(f"  - Total Issues: {total_issues}")
    print(f"  - Avg Issues per Result: {total_issues/len(results):.1f}")


def main():
    """Función principal de demostración."""
    print("SISTEMA DE VALIDACIÓN DE RESULTADOS - DEMOSTRACIÓN")
    print("=" * 60)
    
    # 1. Validar resultados individuales
    print("\n1. VALIDACIÓN DE RESULTADOS INDIVIDUALES")
    print("-" * 40)
    
    sample_results = create_sample_results()
    validator = ResultValidator(ValidationLevel.STANDARD)
    
    for name, result in sample_results[:3]:  # Primeros 3
        print(f"\nValidating: {name}")
        report = validator.validate_result(result)
        
        print(f"Result ID: {result.result_id}")
        print(f"Validation Passed: {report.passed}")
        print(f"Issues Found: {len(report.issues)}")
        
        if report.issues:
            print("Issues:")
            for issue in report.issues[:2]:  # Mostrar primeras 2
                print(f"  - [{issue.level.value}] {issue.category}: {issue.message}")
    
    # 2. Demostrar niveles de validación
    demonstrate_validation_levels()
    
    # 3. Demostrar validadores personalizados
    demonstrate_custom_validators()
    
    # 4. Demostrar integración
    demonstrate_integration()
    
    # 5. Demostrar validación por lotes
    demonstrate_batch_validation()
    
    print("\n" + "="*60)
    print("DEMOSTRACIÓN COMPLETADA")
    print("="*60)


if __name__ == "__main__":
    main()