"""
Validador de reproducibilidad para algoritmos y experimentos.

Verifica que los algoritmos y experimentos cumplan con los
estándares de reproducibilidad del proyecto.
"""

import numpy as np
import inspect
import ast
from typing import Type, List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import logging

from algorithms.core.base import MetaheuristicAlgorithm, Individual
from problems.vrp import VRPProblem

logger = logging.getLogger(__name__)


class ReproducibilityViolation:
    """Representa una violación de los estándares de reproducibilidad."""
    
    def __init__(self, 
                 severity: str,
                 component: str,
                 issue: str,
                 location: Optional[str] = None,
                 suggestion: Optional[str] = None):
        """
        Inicializa una violación.
        
        Args:
            severity: 'error', 'warning', 'info'
            component: Componente afectado
            issue: Descripción del problema
            location: Ubicación del problema (archivo:línea)
            suggestion: Sugerencia para resolver
        """
        self.severity = severity
        self.component = component
        self.issue = issue
        self.location = location
        self.suggestion = suggestion
    
    def __str__(self):
        msg = f"[{self.severity.upper()}] {self.component}: {self.issue}"
        if self.location:
            msg += f" (at {self.location})"
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


class AlgorithmReproducibilityValidator:
    """
    Validador de reproducibilidad para algoritmos.
    
    Verifica que los algoritmos cumplan con los estándares
    necesarios para garantizar reproducibilidad.
    """
    
    def __init__(self):
        """Inicializa el validador."""
        self.violations = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def validate_algorithm_class(self, algorithm_class: Type[MetaheuristicAlgorithm]) -> List[ReproducibilityViolation]:
        """
        Valida una clase de algoritmo.
        
        Args:
            algorithm_class: Clase del algoritmo a validar
            
        Returns:
            Lista de violaciones encontradas
        """
        self.violations = []
        self.checks_passed = 0
        self.checks_failed = 0
        
        logger.info(f"Validating algorithm class: {algorithm_class.__name__}")
        
        # Ejecutar todas las validaciones
        self._check_seed_parameter(algorithm_class)
        self._check_random_usage(algorithm_class)
        self._check_initialization(algorithm_class)
        self._check_determinism(algorithm_class)
        self._check_state_isolation(algorithm_class)
        
        logger.info(f"Validation complete: {self.checks_passed} passed, {self.checks_failed} failed")
        
        return self.violations
    
    def _check_seed_parameter(self, algorithm_class: Type[MetaheuristicAlgorithm]):
        """Verifica que el algoritmo acepte parámetro seed."""
        try:
            # Verificar __init__
            init_signature = inspect.signature(algorithm_class.__init__)
            if 'seed' not in init_signature.parameters:
                self._add_violation(
                    'error',
                    f'{algorithm_class.__name__}.__init__',
                    'Missing seed parameter in constructor',
                    suggestion='Add seed parameter: def __init__(self, ..., seed=None)'
                )
                self.checks_failed += 1
            else:
                # Verificar que se pase a la clase base
                source = inspect.getsource(algorithm_class.__init__)
                if 'super().__init__' in source and 'seed=' not in source:
                    self._add_violation(
                        'warning',
                        f'{algorithm_class.__name__}.__init__',
                        'Seed parameter not passed to parent class',
                        suggestion='Pass seed to super().__init__(..., seed=seed)'
                    )
                    self.checks_failed += 1
                else:
                    self.checks_passed += 1
        except Exception as e:
            self._add_violation(
                'error',
                algorithm_class.__name__,
                f'Could not analyze __init__: {e}'
            )
            self.checks_failed += 1
    
    def _check_random_usage(self, algorithm_class: Type[MetaheuristicAlgorithm]):
        """Verifica el uso correcto de generadores aleatorios."""
        try:
            # Obtener todos los métodos
            for name, method in inspect.getmembers(algorithm_class, inspect.isfunction):
                if name.startswith('_'):  # Skip private methods for now
                    continue
                
                try:
                    source = inspect.getsource(method)
                    
                    # Buscar usos incorrectos de random
                    bad_patterns = [
                        ('random.random()', 'Use self.random_state.random()'),
                        ('random.randint', 'Use self.random_state.randint()'),
                        ('random.choice', 'Use self.random_state.choice()'),
                        ('np.random.random()', 'Use self.random_state.random()'),
                        ('np.random.randint', 'Use self.random_state.randint()'),
                        ('np.random.choice', 'Use self.random_state.choice()'),
                        ('np.random.seed', 'Do not set seeds inside methods')
                    ]
                    
                    for pattern, suggestion in bad_patterns:
                        if pattern in source:
                            self._add_violation(
                                'error',
                                f'{algorithm_class.__name__}.{name}',
                                f'Direct use of {pattern}',
                                suggestion=suggestion
                            )
                            self.checks_failed += 1
                            break
                    else:
                        # Check for correct usage
                        if 'random' in source.lower() and 'self.random_state' in source:
                            self.checks_passed += 1
                
                except OSError:
                    # Built-in method, skip
                    pass
                    
        except Exception as e:
            self._add_violation(
                'warning',
                algorithm_class.__name__,
                f'Could not analyze random usage: {e}'
            )
    
    def _check_initialization(self, algorithm_class: Type[MetaheuristicAlgorithm]):
        """Verifica que la inicialización sea determinística."""
        try:
            # Verificar initialize_population
            if hasattr(algorithm_class, 'initialize_population'):
                source = inspect.getsource(algorithm_class.initialize_population)
                
                # Debe usar random_state
                if 'self.random_state' not in source and 'random' in source.lower():
                    self._add_violation(
                        'error',
                        f'{algorithm_class.__name__}.initialize_population',
                        'Initialization may not be deterministic',
                        suggestion='Use self.random_state for all random operations'
                    )
                    self.checks_failed += 1
                else:
                    self.checks_passed += 1
            
            # Verificar _create_individual
            if hasattr(algorithm_class, '_create_individual'):
                source = inspect.getsource(algorithm_class._create_individual)
                
                # Debe pasar random_state a Individual
                if 'Individual' in source and 'self.random_state' not in source:
                    self._add_violation(
                        'warning',
                        f'{algorithm_class.__name__}._create_individual',
                        'Individual creation may not use consistent random state',
                        suggestion='Pass self.random_state to Individual.initialize()'
                    )
                    self.checks_failed += 1
                else:
                    self.checks_passed += 1
                    
        except Exception as e:
            self._add_violation(
                'warning',
                algorithm_class.__name__,
                f'Could not analyze initialization: {e}'
            )
    
    def _check_determinism(self, algorithm_class: Type[MetaheuristicAlgorithm]):
        """Verifica que el algoritmo sea determinístico con la misma semilla."""
        try:
            # Crear instancia de prueba
            problem = VRPProblem('E-n22-k4')
            
            # Ejecutar con misma semilla
            results = []
            for i in range(3):
                algo = algorithm_class(
                    problem=problem,
                    population_size=10,
                    max_iterations=5,
                    seed=42
                )
                result = algo.run()
                results.append(result['best_fitness'])
            
            # Verificar que todos los resultados sean idénticos
            if len(set(results)) > 1:
                self._add_violation(
                    'error',
                    algorithm_class.__name__,
                    f'Non-deterministic results with same seed: {results}',
                    suggestion='Ensure all random operations use self.random_state'
                )
                self.checks_failed += 1
            else:
                self.checks_passed += 1
                
        except Exception as e:
            self._add_violation(
                'warning',
                algorithm_class.__name__,
                f'Could not test determinism: {e}'
            )
    
    def _check_state_isolation(self, algorithm_class: Type[MetaheuristicAlgorithm]):
        """Verifica que el algoritmo no contamine el estado global."""
        try:
            # Guardar estado global
            numpy_state_before = np.random.get_state()
            
            # Ejecutar algoritmo
            problem = VRPProblem('E-n22-k4')
            algo = algorithm_class(
                problem=problem,
                population_size=5,
                max_iterations=2,
                seed=42
            )
            algo.run()
            
            # Verificar estado global
            numpy_state_after = np.random.get_state()
            
            # El estado no debería cambiar (comparar primeros elementos)
            if not np.array_equal(numpy_state_before[1][:10], numpy_state_after[1][:10]):
                self._add_violation(
                    'warning',
                    algorithm_class.__name__,
                    'Algorithm modifies global random state',
                    suggestion='Use only self.random_state, not global np.random'
                )
                self.checks_failed += 1
            else:
                self.checks_passed += 1
                
        except Exception as e:
            self._add_violation(
                'info',
                algorithm_class.__name__,
                f'Could not test state isolation: {e}'
            )
    
    def _add_violation(self, severity: str, component: str, issue: str, 
                      location: Optional[str] = None, suggestion: Optional[str] = None):
        """Añade una violación a la lista."""
        violation = ReproducibilityViolation(severity, component, issue, location, suggestion)
        self.violations.append(violation)
        logger.debug(str(violation))


class ExperimentReproducibilityValidator:
    """
    Validador de reproducibilidad para experimentos completos.
    
    Verifica que los experimentos se ejecuten de forma reproducible.
    """
    
    def __init__(self):
        """Inicializa el validador."""
        self.violations = []
    
    def validate_experiment_setup(self, 
                                 algorithm_name: str,
                                 problem_name: str,
                                 parameters: Dict[str, Any]) -> List[ReproducibilityViolation]:
        """
        Valida la configuración de un experimento.
        
        Args:
            algorithm_name: Nombre del algoritmo
            problem_name: Nombre del problema
            parameters: Parámetros del experimento
            
        Returns:
            Lista de violaciones encontradas
        """
        self.violations = []
        
        # Verificar presencia de seed
        if 'seed' not in parameters:
            self.violations.append(ReproducibilityViolation(
                'error',
                'experiment_setup',
                'Missing seed parameter',
                suggestion='Always specify seed parameter for reproducibility'
            ))
        
        # Verificar parámetros críticos
        critical_params = ['population_size', 'max_iterations']
        for param in critical_params:
            if param not in parameters:
                self.violations.append(ReproducibilityViolation(
                    'warning',
                    'experiment_setup',
                    f'Missing {param} parameter',
                    suggestion=f'Specify {param} explicitly'
                ))
        
        # Verificar tipos de datos
        if 'seed' in parameters and not isinstance(parameters['seed'], (int, type(None))):
            self.violations.append(ReproducibilityViolation(
                'error',
                'experiment_setup',
                f'Invalid seed type: {type(parameters["seed"])}',
                suggestion='Seed must be an integer or None'
            ))
        
        return self.violations
    
    def validate_results_consistency(self, 
                                   results: List[Dict[str, Any]],
                                   expected_variance: float = 0.0) -> List[ReproducibilityViolation]:
        """
        Valida la consistencia de resultados con misma semilla.
        
        Args:
            results: Lista de resultados de ejecuciones
            expected_variance: Varianza esperada (0 para determinismo total)
            
        Returns:
            Lista de violaciones encontradas
        """
        self.violations = []
        
        if len(results) < 2:
            self.violations.append(ReproducibilityViolation(
                'info',
                'results_validation',
                'Not enough results to validate consistency'
            ))
            return self.violations
        
        # Agrupar por semilla
        by_seed = {}
        for result in results:
            seed = result.get('seed', 'unknown')
            if seed not in by_seed:
                by_seed[seed] = []
            by_seed[seed].append(result.get('best_fitness', float('inf')))
        
        # Verificar consistencia por semilla
        for seed, fitness_values in by_seed.items():
            if len(fitness_values) > 1:
                variance = np.var(fitness_values)
                if variance > expected_variance:
                    self.violations.append(ReproducibilityViolation(
                        'error',
                        'results_consistency',
                        f'Inconsistent results for seed {seed}: variance={variance:.6f}',
                        suggestion='Check random state usage in algorithm'
                    ))
        
        return self.violations


def validate_all_algorithms() -> Dict[str, List[ReproducibilityViolation]]:
    """
    Valida todos los algoritmos del proyecto.
    
    Returns:
        Dict con violaciones por algoritmo
    """
    from algorithms import ALGORITHMS
    
    validator = AlgorithmReproducibilityValidator()
    all_violations = {}
    
    for name, algorithm_class in ALGORITHMS.items():
        logger.info(f"\nValidating {name}...")
        violations = validator.validate_algorithm_class(algorithm_class)
        if violations:
            all_violations[name] = violations
    
    return all_violations


def generate_reproducibility_report(output_path: Optional[Path] = None) -> str:
    """
    Genera un reporte completo de reproducibilidad.
    
    Args:
        output_path: Ruta para guardar el reporte (opcional)
        
    Returns:
        Contenido del reporte
    """
    violations = validate_all_algorithms()
    
    report = "# BioAlgoCompare Reproducibility Report\n\n"
    report += f"Generated: {np.datetime64('now')}\n\n"
    
    if not violations:
        report += "✅ **All algorithms pass reproducibility validation!**\n"
    else:
        report += f"⚠️  **Found issues in {len(violations)} algorithms**\n\n"
        
        # Resumen
        total_errors = sum(
            1 for alg_violations in violations.values() 
            for v in alg_violations if v.severity == 'error'
        )
        total_warnings = sum(
            1 for alg_violations in violations.values() 
            for v in alg_violations if v.severity == 'warning'
        )
        
        report += f"## Summary\n\n"
        report += f"- Errors: {total_errors}\n"
        report += f"- Warnings: {total_warnings}\n\n"
        
        # Detalles por algoritmo
        report += "## Details by Algorithm\n\n"
        
        for algorithm, alg_violations in sorted(violations.items()):
            report += f"### {algorithm}\n\n"
            
            for violation in alg_violations:
                icon = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[violation.severity]
                report += f"{icon} **{violation.issue}**\n"
                if violation.location:
                    report += f"   - Location: `{violation.location}`\n"
                if violation.suggestion:
                    report += f"   - Suggestion: {violation.suggestion}\n"
                report += "\n"
    
    # Guardar si se especifica ruta
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)
        logger.info(f"Report saved to {output_path}")
    
    return report


if __name__ == "__main__":
    # Generar reporte si se ejecuta directamente
    report = generate_reproducibility_report(Path("reproducibility_validation_report.md"))
    print(report)