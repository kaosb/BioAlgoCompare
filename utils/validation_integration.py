"""
Integración del sistema de validación con tracker y base de datos.

Este módulo conecta el sistema de validación con los componentes
existentes para proporcionar validación automática y reporte.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from datetime import datetime
import json

from utils.result_validation import (
    ResultValidator, ValidationLevel, ValidationReport,
    create_vrp_validator, create_convergence_validator,
    quick_validate
)
from utils.result_schema import StandardResult
from utils.experiment_tracker import ExperimentTracker, ExperimentRecord
from utils.results_database import ResultsDatabase
from utils.result_integration import ResultIntegration
from utils.benchmarking import BenchmarkResult


logger = logging.getLogger(__name__)


class ValidatedExperimentTracker(ExperimentTracker):
    """
    Tracker de experimentos con validación automática integrada.
    """
    
    def __init__(self, base_dir: str = "experiments", 
                 auto_save: bool = True,
                 auto_validate: bool = True,
                 validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """
        Inicializa tracker con validación.
        
        Args:
            base_dir: Directorio base para experimentos
            auto_save: Si guardar automáticamente
            auto_validate: Si validar automáticamente
            validation_level: Nivel de validación por defecto
        """
        super().__init__(base_dir, auto_save)
        
        self.auto_validate = auto_validate
        self.validator = ResultValidator(validation_level)
        self.validation_reports: Dict[str, ValidationReport] = {}
        
        # Crear directorio para reportes de validación
        self.validation_dir = self.base_dir / "validation"
        self.validation_dir.mkdir(exist_ok=True)
        
        # Configurar validadores específicos
        self._setup_validators()
    
    def _setup_validators(self) -> None:
        """Configura validadores específicos del dominio."""
        # Validador VRP
        self.validator.add_custom_validator(
            'vrp', 
            create_vrp_validator(capacity_check=True, distance_check=True)
        )
        
        # Validador de convergencia
        self.validator.add_custom_validator(
            'convergence',
            create_convergence_validator(min_improvement=0.01, max_stagnation=100)
        )
    
    def save_current(self) -> None:
        """Guarda el experimento actual con validación."""
        if not self.current_experiment:
            return
        
        # Guardar normalmente
        super().save_current()
        
        # Validar si está habilitado
        if self.auto_validate:
            self._validate_current()
    
    def _validate_current(self) -> None:
        """Valida el experimento actual."""
        if not self.current_experiment:
            return
        
        try:
            # Convertir a formato estándar
            standard_result = ResultIntegration.experiment_to_standard(
                self.current_experiment
            )
            
            # Validar
            report = self.validator.validate_result(standard_result)
            
            # Guardar reporte
            self.validation_reports[self.current_experiment.experiment_id] = report
            
            # Guardar en archivo
            report_file = self.validation_dir / f"{self.current_experiment.experiment_id}_validation.json"
            self.validator.save_report(report, report_file)
            
            # Log resultado
            if report.passed:
                self.logger.info(f"Validation passed for {self.current_experiment.experiment_id}")
            else:
                self.logger.warning(
                    f"Validation failed for {self.current_experiment.experiment_id}: "
                    f"{len(report.issues)} issues found"
                )
                
        except Exception as e:
            self.logger.error(f"Error validating experiment: {e}")
    
    def get_validation_report(self, experiment_id: str) -> Optional[ValidationReport]:
        """
        Obtiene el reporte de validación de un experimento.
        
        Args:
            experiment_id: ID del experimento
            
        Returns:
            Reporte de validación o None
        """
        # Buscar en memoria
        if experiment_id in self.validation_reports:
            return self.validation_reports[experiment_id]
        
        # Buscar en disco
        report_file = self.validation_dir / f"{experiment_id}_validation.json"
        if report_file.exists():
            return self.validator.load_report(report_file)
        
        return None
    
    def validate_all_experiments(self, level: Optional[ValidationLevel] = None) -> Dict[str, ValidationReport]:
        """
        Valida todos los experimentos guardados.
        
        Args:
            level: Nivel de validación (usa el por defecto si no se especifica)
            
        Returns:
            Diccionario con reportes por experiment_id
        """
        reports = {}
        
        for record_file in self.records_dir.glob("*.json"):
            try:
                # Cargar experimento
                experiment = self.load_experiment(record_file.stem)
                
                # Convertir y validar
                standard_result = ResultIntegration.experiment_to_standard(experiment)
                report = self.validator.validate_result(standard_result, level)
                
                reports[experiment.experiment_id] = report
                
                # Guardar reporte
                report_file = self.validation_dir / f"{experiment.experiment_id}_validation.json"
                self.validator.save_report(report, report_file)
                
            except Exception as e:
                self.logger.error(f"Error validating {record_file}: {e}")
        
        return reports
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de validación de todos los experimentos.
        
        Returns:
            Resumen con estadísticas de validación
        """
        total_experiments = 0
        passed_experiments = 0
        total_issues = 0
        issues_by_category = {}
        issues_by_level = {
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        
        for report_file in self.validation_dir.glob("*_validation.json"):
            try:
                report = self.validator.load_report(report_file)
                total_experiments += 1
                
                if report.passed:
                    passed_experiments += 1
                
                total_issues += len(report.issues)
                
                for issue in report.issues:
                    # Por categoría
                    if issue.category not in issues_by_category:
                        issues_by_category[issue.category] = 0
                    issues_by_category[issue.category] += 1
                    
                    # Por nivel
                    if issue.level.value in issues_by_level:
                        issues_by_level[issue.level.value] += 1
                        
            except Exception as e:
                self.logger.error(f"Error loading report {report_file}: {e}")
        
        return {
            'total_experiments': total_experiments,
            'passed_experiments': passed_experiments,
            'pass_rate': passed_experiments / total_experiments if total_experiments > 0 else 0,
            'total_issues': total_issues,
            'avg_issues_per_experiment': total_issues / total_experiments if total_experiments > 0 else 0,
            'issues_by_category': issues_by_category,
            'issues_by_level': issues_by_level
        }


class ValidatedResultsDatabase(ResultsDatabase):
    """
    Base de datos de resultados con validación integrada.
    """
    
    def __init__(self, db_path: Union[str, Path] = "results.db",
                 auto_validate: bool = True,
                 validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """
        Inicializa base de datos con validación.
        
        Args:
            db_path: Ruta de la base de datos
            auto_validate: Si validar antes de insertar
            validation_level: Nivel de validación
        """
        super().__init__(db_path)
        
        self.auto_validate = auto_validate
        self.validator = ResultValidator(validation_level)
        
        # Añadir tabla de validación
        self._add_validation_table()
    
    def _add_validation_table(self) -> None:
        """Añade tabla para almacenar reportes de validación."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_reports (
                    result_id TEXT PRIMARY KEY,
                    validation_level TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    passed BOOLEAN NOT NULL,
                    total_issues INTEGER NOT NULL,
                    critical_issues INTEGER NOT NULL,
                    error_issues INTEGER NOT NULL,
                    warning_issues INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    FOREIGN KEY (result_id) REFERENCES results(result_id)
                )
            """)
            conn.commit()
    
    def insert_result(self, result: StandardResult) -> bool:
        """
        Inserta resultado con validación opcional.
        
        Args:
            result: Resultado a insertar
            
        Returns:
            True si se insertó correctamente
        """
        # Validar si está habilitado
        if self.auto_validate:
            report = self.validator.validate_result(result)
            
            if not report.passed:
                logger.warning(
                    f"Result {result.result_id} failed validation with "
                    f"{len(report.issues)} issues"
                )
                # Podemos decidir si rechazar o solo advertir
                # Por ahora solo advertimos pero insertamos igual
            
            # Guardar reporte de validación
            self._save_validation_report(report)
        
        # Insertar normalmente
        return super().insert_result(result)
    
    def _save_validation_report(self, report: ValidationReport) -> None:
        """Guarda reporte de validación en la base de datos."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO validation_reports 
                (result_id, validation_level, timestamp, passed, 
                 total_issues, critical_issues, error_issues, warning_issues,
                 report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.result_id,
                report.validation_level.value,
                report.timestamp,
                report.passed,
                len(report.issues),
                len(report.get_issues_by_level(ValidationStatus.CRITICAL)),
                len(report.get_issues_by_level(ValidationStatus.ERROR)),
                len(report.get_issues_by_level(ValidationStatus.WARNING)),
                json.dumps(report.to_dict())
            ))
            conn.commit()
    
    def get_validation_report(self, result_id: str) -> Optional[ValidationReport]:
        """
        Obtiene reporte de validación de un resultado.
        
        Args:
            result_id: ID del resultado
            
        Returns:
            Reporte de validación o None
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT report_json FROM validation_reports WHERE result_id = ?",
                (result_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row['report_json'])
                # Reconstruir reporte
                return self._reconstruct_report(data)
            
        return None
    
    def _reconstruct_report(self, data: Dict[str, Any]) -> ValidationReport:
        """Reconstruye un reporte desde datos JSON."""
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
    
    def get_failed_validations(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los resultados que fallaron validación.
        
        Returns:
            Lista de resultados con información de validación
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT r.*, v.total_issues, v.critical_issues, v.error_issues
                FROM results r
                JOIN validation_reports v ON r.result_id = v.result_id
                WHERE v.passed = 0
                ORDER BY v.timestamp DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de validación.
        
        Returns:
            Diccionario con estadísticas
        """
        with self._get_connection() as conn:
            # Total de resultados con validación
            total = conn.execute(
                "SELECT COUNT(*) as count FROM validation_reports"
            ).fetchone()['count']
            
            # Resultados que pasaron
            passed = conn.execute(
                "SELECT COUNT(*) as count FROM validation_reports WHERE passed = 1"
            ).fetchone()['count']
            
            # Estadísticas de issues
            stats = conn.execute("""
                SELECT 
                    AVG(total_issues) as avg_issues,
                    MAX(total_issues) as max_issues,
                    SUM(critical_issues) as total_critical,
                    SUM(error_issues) as total_errors,
                    SUM(warning_issues) as total_warnings
                FROM validation_reports
            """).fetchone()
            
            return {
                'total_validated': total,
                'total_passed': passed,
                'pass_rate': passed / total if total > 0 else 0,
                'avg_issues_per_result': stats['avg_issues'] or 0,
                'max_issues_in_result': stats['max_issues'] or 0,
                'total_critical_issues': stats['total_critical'] or 0,
                'total_error_issues': stats['total_errors'] or 0,
                'total_warning_issues': stats['total_warnings'] or 0
            }


def validate_benchmark_results(
    results: List[BenchmarkResult],
    level: ValidationLevel = ValidationLevel.STANDARD,
    save_reports: bool = True,
    output_dir: Optional[Path] = None
) -> Dict[str, ValidationReport]:
    """
    Valida resultados de benchmark.
    
    Args:
        results: Lista de resultados de benchmark
        level: Nivel de validación
        save_reports: Si guardar reportes en archivos
        output_dir: Directorio para reportes
        
    Returns:
        Diccionario con reportes de validación
    """
    validator = ResultValidator(level)
    reports = {}
    
    if save_reports and output_dir is None:
        output_dir = Path("validation_reports") / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        try:
            # Convertir BenchmarkResult a StandardResult
            # (esto requeriría un método de conversión apropiado)
            # Por ahora asumimos que existe un método de conversión
            
            # Validar
            # report = validator.validate_result(standard_result)
            # reports[result.algorithm_name + "_" + result.instance_name] = report
            
            # if save_reports:
            #     report_file = output_dir / f"{result.algorithm_name}_{result.instance_name}_validation.json"
            #     validator.save_report(report, report_file)
            
            pass  # Implementar conversión real
            
        except Exception as e:
            logger.error(f"Error validating benchmark result: {e}")
    
    return reports


def create_validation_middleware(
    validation_level: ValidationLevel = ValidationLevel.STANDARD
) -> Callable:
    """
    Crea middleware de validación para decorar funciones.
    
    Args:
        validation_level: Nivel de validación
        
    Returns:
        Decorador de validación
    """
    def validation_decorator(func: Callable) -> Callable:
        """Decorador que valida resultados."""
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Si el resultado es un StandardResult, validar
            if isinstance(result, StandardResult):
                if not quick_validate(result, validation_level):
                    logger.warning(f"Result from {func.__name__} failed validation")
            
            return result
        
        return wrapper
    
    return validation_decorator


# Configuración por defecto para validación automática

def setup_auto_validation(
    tracker: Optional[ExperimentTracker] = None,
    database: Optional[ResultsDatabase] = None,
    level: ValidationLevel = ValidationLevel.STANDARD
) -> Tuple[ExperimentTracker, ResultsDatabase]:
    """
    Configura validación automática en tracker y base de datos.
    
    Args:
        tracker: Tracker existente o None para crear uno nuevo
        database: Base de datos existente o None para crear una nueva
        level: Nivel de validación
        
    Returns:
        Tupla con (tracker_validado, database_validada)
    """
    # Crear o envolver tracker
    if tracker is None:
        validated_tracker = ValidatedExperimentTracker(
            auto_validate=True,
            validation_level=level
        )
    else:
        # Aquí podríamos envolver un tracker existente
        # Por simplicidad, creamos uno nuevo
        validated_tracker = ValidatedExperimentTracker(
            base_dir=tracker.base_dir,
            auto_validate=True,
            validation_level=level
        )
    
    # Crear o envolver base de datos
    if database is None:
        validated_db = ValidatedResultsDatabase(
            auto_validate=True,
            validation_level=level
        )
    else:
        # Similar al tracker
        validated_db = ValidatedResultsDatabase(
            db_path=database.db_path,
            auto_validate=True,
            validation_level=level
        )
    
    return validated_tracker, validated_db