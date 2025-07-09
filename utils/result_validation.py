"""
Sistema de validación de resultados para BioAlgoCompare.

Este módulo proporciona validación exhaustiva de resultados experimentales,
asegurando integridad, consistencia y calidad de los datos generados por
los algoritmos metaheurísticos.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
import logging
from pathlib import Path
from enum import Enum
import warnings

from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics,
    ProblemInfo, AlgorithmInfo, ExecutionInfo, ResultType
)
from utils.error_handling import (
    ValidationError, check_numeric_stability,
    NumericError
)


logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Niveles de validación disponibles."""
    BASIC = "basic"          # Validación básica de estructura
    STANDARD = "standard"    # Validación estándar con chequeos numéricos
    STRICT = "strict"        # Validación estricta con todas las verificaciones
    SCIENTIFIC = "scientific" # Validación científica con análisis estadístico


class ValidationStatus(Enum):
    """Estado de validación."""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Representa un problema encontrado durante la validación."""
    level: ValidationStatus
    category: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'level': self.level.value,
            'category': self.category,
            'message': self.message,
            'field': self.field,
            'value': str(self.value) if self.value is not None else None,
            'suggestion': self.suggestion
        }


@dataclass 
class ValidationReport:
    """Reporte completo de validación."""
    result_id: str
    validation_level: ValidationLevel
    timestamp: datetime = field(default_factory=datetime.now)
    issues: List[ValidationIssue] = field(default_factory=list)
    passed: bool = True
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """Añade un problema al reporte."""
        self.issues.append(issue)
        if issue.level in [ValidationStatus.ERROR, ValidationStatus.CRITICAL]:
            self.passed = False
    
    def get_issues_by_level(self, level: ValidationStatus) -> List[ValidationIssue]:
        """Obtiene problemas por nivel."""
        return [i for i in self.issues if i.level == level]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'result_id': self.result_id,
            'validation_level': self.validation_level.value,
            'timestamp': self.timestamp.isoformat(),
            'passed': self.passed,
            'issues': [i.to_dict() for i in self.issues],
            'summary': self.summary,
            'statistics': {
                'total_issues': len(self.issues),
                'errors': len(self.get_issues_by_level(ValidationStatus.ERROR)),
                'warnings': len(self.get_issues_by_level(ValidationStatus.WARNING)),
                'critical': len(self.get_issues_by_level(ValidationStatus.CRITICAL))
            }
        }


class ResultValidator:
    """
    Validador principal de resultados experimentales.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """
        Inicializa el validador.
        
        Args:
            validation_level: Nivel de validación por defecto
        """
        self.validation_level = validation_level
        self.custom_validators: Dict[str, Callable] = {}
        
        # Límites de validación
        self.limits = {
            'min_fitness': 0.0,
            'max_fitness': float('inf'),
            'min_time': 0.0,
            'max_time': 3600.0,  # 1 hora máximo por run
            'min_iterations': 1,
            'max_iterations': 1000000,
            'fitness_tolerance': 1e-10,
            'time_tolerance': 1e-6
        }
        
    def validate_result(self, result: StandardResult, 
                       level: Optional[ValidationLevel] = None) -> ValidationReport:
        """
        Valida un resultado completo.
        
        Args:
            result: Resultado a validar
            level: Nivel de validación (usa el por defecto si no se especifica)
            
        Returns:
            Reporte de validación
        """
        level = level or self.validation_level
        report = ValidationReport(
            result_id=result.result_id,
            validation_level=level
        )
        
        # Validación básica siempre se ejecuta
        self._validate_structure(result, report)
        self._validate_metadata(result, report)
        
        # Validación estándar
        if level.value in [ValidationLevel.STANDARD.value, 
                          ValidationLevel.STRICT.value,
                          ValidationLevel.SCIENTIFIC.value]:
            self._validate_numeric_values(result, report)
            self._validate_consistency(result, report)
            
        # Validación estricta
        if level.value in [ValidationLevel.STRICT.value,
                          ValidationLevel.SCIENTIFIC.value]:
            self._validate_constraints(result, report)
            self._validate_solution_quality(result, report)
            
        # Validación científica
        if level == ValidationLevel.SCIENTIFIC:
            self._validate_statistical_properties(result, report)
            self._validate_reproducibility(result, report)
        
        # Ejecutar validadores personalizados
        for name, validator in self.custom_validators.items():
            try:
                validator(result, report)
            except Exception as e:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='custom_validator',
                    message=f"Custom validator '{name}' failed: {str(e)}"
                ))
        
        # Generar resumen
        self._generate_summary(result, report)
        
        return report
    
    def _validate_structure(self, result: StandardResult, 
                           report: ValidationReport) -> None:
        """Valida la estructura básica del resultado."""
        # Verificar campos requeridos
        required_fields = ['result_id', 'result_type', 'timestamp', 
                          'problem_info', 'algorithm_info', 'execution_info']
        
        for field in required_fields:
            if not hasattr(result, field) or getattr(result, field) is None:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='structure',
                    field=field,
                    message=f"Required field '{field}' is missing or None"
                ))
        
        # Verificar tipo de resultado
        if result.result_type == ResultType.SINGLE_RUN:
            if not isinstance(result.data, SingleRunResult):
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='structure',
                    field='data',
                    message="Data type mismatch for SINGLE_RUN result"
                ))
        elif result.result_type == ResultType.MULTI_RUN:
            if not isinstance(result.data, MultiRunStatistics):
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='structure', 
                    field='data',
                    message="Data type mismatch for MULTI_RUN result"
                ))
    
    def _validate_metadata(self, result: StandardResult,
                          report: ValidationReport) -> None:
        """Valida los metadatos del resultado."""
        # Validar información del problema
        if result.problem_info:
            if not result.problem_info.name:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='metadata',
                    field='problem_info.name',
                    message="Problem name is empty"
                ))
            
            if result.problem_info.dimension <= 0:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='metadata',
                    field='problem_info.dimension',
                    value=result.problem_info.dimension,
                    message="Problem dimension must be positive"
                ))
        
        # Validar información del algoritmo
        if result.algorithm_info:
            if not result.algorithm_info.name:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='metadata',
                    field='algorithm_info.name',
                    message="Algorithm name is empty"
                ))
            
            # Validar parámetros
            if result.algorithm_info.parameters:
                for param, value in result.algorithm_info.parameters.items():
                    if value is None:
                        report.add_issue(ValidationIssue(
                            level=ValidationStatus.WARNING,
                            category='metadata',
                            field=f'algorithm_info.parameters.{param}',
                            message=f"Parameter '{param}' has None value"
                        ))
    
    def _validate_numeric_values(self, result: StandardResult,
                                report: ValidationReport) -> None:
        """Valida valores numéricos."""
        if result.result_type == ResultType.SINGLE_RUN:
            data = result.data
            
            # Validar fitness
            try:
                check_numeric_stability(data.best_fitness, "best_fitness")
                
                if data.best_fitness < self.limits['min_fitness']:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.ERROR,
                        category='numeric',
                        field='best_fitness',
                        value=data.best_fitness,
                        message=f"Fitness below minimum allowed ({self.limits['min_fitness']})"
                    ))
                    
                if data.best_fitness > self.limits['max_fitness']:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.WARNING,
                        category='numeric',
                        field='best_fitness',
                        value=data.best_fitness,
                        message="Extremely large fitness value"
                    ))
                    
            except NumericError as e:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.CRITICAL,
                    category='numeric',
                    field='best_fitness',
                    value=data.best_fitness,
                    message=str(e)
                ))
            
            # Validar tiempo de ejecución
            if data.execution_time < self.limits['min_time']:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='numeric',
                    field='execution_time',
                    value=data.execution_time,
                    message="Execution time is suspiciously low"
                ))
                
            if data.execution_time > self.limits['max_time']:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='numeric',
                    field='execution_time',
                    value=data.execution_time,
                    message="Execution time exceeds maximum expected"
                ))
            
            # Validar curva de convergencia
            if data.convergence_curve:
                self._validate_convergence_curve(data.convergence_curve, report)
                
        elif result.result_type == ResultType.MULTI_RUN:
            data = result.data
            
            # Validar estadísticas
            if data.mean_fitness < data.best_fitness:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='consistency',
                    message="Mean fitness is less than best fitness",
                    value=f"mean={data.mean_fitness}, best={data.best_fitness}"
                ))
            
            if data.std_fitness < 0:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='numeric',
                    field='std_fitness',
                    value=data.std_fitness,
                    message="Standard deviation cannot be negative"
                ))
    
    def _validate_convergence_curve(self, curve: List[float],
                                   report: ValidationReport) -> None:
        """Valida la curva de convergencia."""
        if not curve:
            report.add_issue(ValidationIssue(
                level=ValidationStatus.WARNING,
                category='convergence',
                message="Empty convergence curve"
            ))
            return
        
        # Verificar valores numéricos
        for i, value in enumerate(curve):
            try:
                check_numeric_stability(value, f"convergence[{i}]")
            except NumericError as e:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='convergence',
                    field=f'convergence_curve[{i}]',
                    value=value,
                    message=str(e)
                ))
        
        # Verificar monotonicidad (para minimización)
        if len(curve) > 1:
            improvements = 0
            deteriorations = 0
            
            for i in range(1, len(curve)):
                if curve[i] < curve[i-1] - self.limits['fitness_tolerance']:
                    improvements += 1
                elif curve[i] > curve[i-1] + self.limits['fitness_tolerance']:
                    deteriorations += 1
            
            if deteriorations > len(curve) * 0.1:  # Más del 10% deteriora
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='convergence',
                    message=f"Convergence curve shows {deteriorations} deteriorations",
                    suggestion="Check if algorithm maintains best solution correctly"
                ))
    
    def _validate_consistency(self, result: StandardResult,
                             report: ValidationReport) -> None:
        """Valida la consistencia interna de los datos."""
        if result.result_type == ResultType.MULTI_RUN:
            data = result.data
            
            # Verificar consistencia de runs
            if data.total_runs != len(data.all_fitness_values):
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='consistency',
                    message=f"Run count mismatch: total_runs={data.total_runs}, "
                           f"fitness_values={len(data.all_fitness_values)}"
                ))
            
            # Verificar cálculos estadísticos
            if data.all_fitness_values:
                calculated_mean = np.mean(data.all_fitness_values)
                if abs(calculated_mean - data.mean_fitness) > self.limits['fitness_tolerance']:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.ERROR,
                        category='consistency',
                        field='mean_fitness',
                        message=f"Mean fitness mismatch: stored={data.mean_fitness}, "
                               f"calculated={calculated_mean}"
                    ))
                
                calculated_std = np.std(data.all_fitness_values)
                if abs(calculated_std - data.std_fitness) > self.limits['fitness_tolerance']:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.ERROR,
                        category='consistency',
                        field='std_fitness',
                        message=f"Std fitness mismatch: stored={data.std_fitness}, "
                               f"calculated={calculated_std}"
                    ))
    
    def _validate_constraints(self, result: StandardResult,
                             report: ValidationReport) -> None:
        """Valida restricciones específicas del problema."""
        # Para VRP, validar soluciones
        if 'vrp' in result.problem_info.name.lower():
            if result.result_type == ResultType.SINGLE_RUN:
                solution = result.data.best_solution
                if solution:
                    self._validate_vrp_solution(solution, result.problem_info, report)
    
    def _validate_vrp_solution(self, solution: Any, problem_info: ProblemInfo,
                              report: ValidationReport) -> None:
        """Valida una solución VRP."""
        try:
            # Verificar que es una lista de rutas
            if not isinstance(solution, list):
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='solution',
                    message="VRP solution must be a list of routes"
                ))
                return
            
            visited_nodes = set()
            depot_count = 0
            
            for route_idx, route in enumerate(solution):
                if not isinstance(route, list):
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.ERROR,
                        category='solution',
                        field=f'route[{route_idx}]',
                        message="Each route must be a list"
                    ))
                    continue
                
                # Verificar depósito al inicio y final
                if route and (route[0] != 0 or route[-1] != 0):
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.ERROR,
                        category='solution',
                        field=f'route[{route_idx}]',
                        message="Route must start and end at depot (node 0)"
                    ))
                
                # Contar visitas a nodos
                for node in route[1:-1]:  # Excluir depósito
                    if node in visited_nodes:
                        report.add_issue(ValidationIssue(
                            level=ValidationStatus.ERROR,
                            category='solution',
                            message=f"Node {node} visited multiple times"
                        ))
                    visited_nodes.add(node)
                
                depot_count += route.count(0)
            
            # Verificar cobertura de nodos
            expected_nodes = set(range(1, problem_info.dimension))
            missing_nodes = expected_nodes - visited_nodes
            if missing_nodes:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='solution',
                    message=f"Missing nodes: {missing_nodes}"
                ))
                
        except Exception as e:
            report.add_issue(ValidationIssue(
                level=ValidationStatus.WARNING,
                category='solution',
                message=f"Error validating VRP solution: {str(e)}"
            ))
    
    def _validate_solution_quality(self, result: StandardResult,
                                  report: ValidationReport) -> None:
        """Valida la calidad de la solución."""
        if result.problem_info.optimal_value:
            if result.result_type == ResultType.SINGLE_RUN:
                gap = ((result.data.best_fitness - result.problem_info.optimal_value) / 
                       result.problem_info.optimal_value * 100)
                
                if gap < -self.limits['fitness_tolerance']:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.CRITICAL,
                        category='quality',
                        message=f"Solution better than optimal! Gap: {gap:.2f}%",
                        suggestion="Check optimal value or solution evaluation"
                    ))
                elif gap > 100:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.WARNING,
                        category='quality',
                        message=f"Very poor solution quality. Gap: {gap:.2f}%"
                    ))
    
    def _validate_statistical_properties(self, result: StandardResult,
                                        report: ValidationReport) -> None:
        """Valida propiedades estadísticas para validación científica."""
        if result.result_type == ResultType.MULTI_RUN:
            data = result.data
            
            # Verificar número mínimo de runs
            if data.total_runs < 30:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='statistical',
                    message=f"Only {data.total_runs} runs. Recommended minimum is 30 for statistical validity"
                ))
            
            # Verificar distribución de resultados
            if data.all_fitness_values and len(data.all_fitness_values) >= 10:
                # Test de normalidad básico
                cv = data.std_fitness / data.mean_fitness if data.mean_fitness > 0 else 0
                if cv > 0.5:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.WARNING,
                        category='statistical',
                        message=f"High coefficient of variation ({cv:.2f}). Results may be unstable"
                    ))
                
                # Verificar outliers
                q1 = np.percentile(data.all_fitness_values, 25)
                q3 = np.percentile(data.all_fitness_values, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = [v for v in data.all_fitness_values 
                           if v < lower_bound or v > upper_bound]
                
                if outliers:
                    report.add_issue(ValidationIssue(
                        level=ValidationStatus.WARNING,
                        category='statistical',
                        message=f"Found {len(outliers)} outliers in results",
                        value=outliers[:5]  # Mostrar primeros 5
                    ))
    
    def _validate_reproducibility(self, result: StandardResult,
                                 report: ValidationReport) -> None:
        """Valida aspectos de reproducibilidad."""
        # Verificar semillas
        if result.execution_info:
            seeds = result.execution_info.metadata.get('seeds', [])
            if not seeds:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='reproducibility',
                    message="No random seeds recorded. Results may not be reproducible"
                ))
            elif len(set(seeds)) != len(seeds):
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='reproducibility',
                    message="Duplicate seeds found. Results are not independent"
                ))
        
        # Verificar información de versión
        if result.algorithm_info and not result.algorithm_info.version:
            report.add_issue(ValidationIssue(
                level=ValidationStatus.WARNING,
                category='reproducibility',
                field='algorithm_info.version',
                message="Algorithm version not specified"
            ))
    
    def _generate_summary(self, result: StandardResult,
                         report: ValidationReport) -> None:
        """Genera un resumen del reporte de validación."""
        report.summary = {
            'algorithm': result.algorithm_info.name if result.algorithm_info else 'Unknown',
            'problem': result.problem_info.name if result.problem_info else 'Unknown',
            'result_type': result.result_type.value,
            'validation_level': report.validation_level.value,
            'total_issues': len(report.issues),
            'critical_issues': len(report.get_issues_by_level(ValidationStatus.CRITICAL)),
            'error_issues': len(report.get_issues_by_level(ValidationStatus.ERROR)),
            'warning_issues': len(report.get_issues_by_level(ValidationStatus.WARNING)),
            'categories_affected': list(set(i.category for i in report.issues))
        }
        
        # Añadir métricas específicas
        if result.result_type == ResultType.SINGLE_RUN:
            report.summary['best_fitness'] = result.data.best_fitness
            report.summary['execution_time'] = result.data.execution_time
        elif result.result_type == ResultType.MULTI_RUN:
            report.summary['mean_fitness'] = result.data.mean_fitness
            report.summary['std_fitness'] = result.data.std_fitness
            report.summary['total_runs'] = result.data.total_runs
    
    def add_custom_validator(self, name: str, validator: Callable) -> None:
        """
        Añade un validador personalizado.
        
        Args:
            name: Nombre del validador
            validator: Función que recibe (result, report) y añade issues
        """
        self.custom_validators[name] = validator
    
    def validate_batch(self, results: List[StandardResult],
                      level: Optional[ValidationLevel] = None,
                      parallel: bool = False) -> Dict[str, ValidationReport]:
        """
        Valida un lote de resultados.
        
        Args:
            results: Lista de resultados a validar
            level: Nivel de validación
            parallel: Si ejecutar en paralelo
            
        Returns:
            Diccionario con reportes por result_id
        """
        reports = {}
        
        if parallel and len(results) > 1:
            import multiprocessing as mp
            
            def validate_single(result):
                return result.result_id, self.validate_result(result, level)
            
            with mp.Pool() as pool:
                for result_id, report in pool.map(validate_single, results):
                    reports[result_id] = report
        else:
            for result in results:
                reports[result.result_id] = self.validate_result(result, level)
        
        return reports
    
    def save_report(self, report: ValidationReport, 
                   output_path: Union[str, Path]) -> None:
        """Guarda un reporte de validación."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"Validation report saved to {output_path}")
    
    def load_report(self, report_path: Union[str, Path]) -> ValidationReport:
        """Carga un reporte de validación."""
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruir reporte
        report = ValidationReport(
            result_id=data['result_id'],
            validation_level=ValidationLevel(data['validation_level']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            passed=data['passed'],
            summary=data['summary']
        )
        
        # Reconstruir issues
        for issue_data in data['issues']:
            issue = ValidationIssue(
                level=ValidationStatus(issue_data['level']),
                category=issue_data['category'],
                message=issue_data['message'],
                field=issue_data.get('field'),
                value=issue_data.get('value'),
                suggestion=issue_data.get('suggestion')
            )
            report.issues.append(issue)
        
        return report


# Validadores predefinidos para problemas específicos

def create_vrp_validator(capacity_check: bool = True,
                        distance_check: bool = True) -> Callable:
    """
    Crea un validador específico para VRP.
    
    Args:
        capacity_check: Si verificar restricciones de capacidad
        distance_check: Si verificar cálculos de distancia
        
    Returns:
        Función validadora
    """
    def vrp_validator(result: StandardResult, report: ValidationReport) -> None:
        """Validador específico para VRP."""
        if 'vrp' not in result.problem_info.name.lower():
            return
        
        # Aquí se pueden añadir validaciones específicas de VRP
        # como verificación de capacidad, cálculo de distancias, etc.
        
        if capacity_check:
            # Verificar que metadata contenga información de capacidad
            if not result.problem_info.metadata.get('capacity'):
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='vrp_specific',
                    message="VRP problem missing capacity information"
                ))
        
        if distance_check and result.result_type == ResultType.SINGLE_RUN:
            # Verificar que el fitness corresponda a una distancia válida
            if result.data.best_fitness <= 0:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.ERROR,
                    category='vrp_specific',
                    field='best_fitness',
                    value=result.data.best_fitness,
                    message="VRP distance must be positive"
                ))
    
    return vrp_validator


def create_convergence_validator(min_improvement: float = 0.01,
                                max_stagnation: int = 50) -> Callable:
    """
    Crea un validador de convergencia.
    
    Args:
        min_improvement: Mejora mínima esperada
        max_stagnation: Máximo de iteraciones sin mejora
        
    Returns:
        Función validadora
    """
    def convergence_validator(result: StandardResult, report: ValidationReport) -> None:
        """Valida propiedades de convergencia."""
        if result.result_type != ResultType.SINGLE_RUN:
            return
        
        curve = result.data.convergence_curve
        if not curve or len(curve) < 2:
            return
        
        # Calcular mejora total
        initial = curve[0]
        final = curve[-1]
        improvement = (initial - final) / initial if initial > 0 else 0
        
        if improvement < min_improvement:
            report.add_issue(ValidationIssue(
                level=ValidationStatus.WARNING,
                category='convergence_quality',
                message=f"Low improvement: {improvement:.2%}",
                suggestion="Consider increasing iterations or tuning parameters"
            ))
        
        # Detectar estancamiento
        stagnation_count = 0
        max_stagnation_found = 0
        
        for i in range(1, len(curve)):
            if abs(curve[i] - curve[i-1]) < 1e-10:
                stagnation_count += 1
                max_stagnation_found = max(max_stagnation_found, stagnation_count)
            else:
                stagnation_count = 0
        
        if max_stagnation_found > max_stagnation:
            report.add_issue(ValidationIssue(
                level=ValidationStatus.WARNING,
                category='convergence_quality',
                message=f"Long stagnation period: {max_stagnation_found} iterations",
                suggestion="Algorithm may have converged early"
            ))
    
    return convergence_validator


# Función de utilidad para validación rápida

def quick_validate(result: StandardResult, 
                  level: ValidationLevel = ValidationLevel.STANDARD) -> bool:
    """
    Validación rápida que retorna solo si pasó o no.
    
    Args:
        result: Resultado a validar
        level: Nivel de validación
        
    Returns:
        True si la validación pasó
    """
    validator = ResultValidator(level)
    report = validator.validate_result(result)
    return report.passed