"""
Tests para el sistema de validación de resultados.
"""

import pytest
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import tempfile

from utils.result_validation import (
    ResultValidator, ValidationLevel, ValidationStatus,
    ValidationIssue, ValidationReport,
    create_vrp_validator, create_convergence_validator,
    quick_validate
)
from utils.result_schema import (
    StandardResult, SingleRunResult, MultiRunStatistics,
    ProblemInfo, AlgorithmInfo, ExecutionInfo, ResultType
)


class TestValidationBasics:
    """Tests básicos de validación."""
    
    def test_validator_initialization(self):
        """Test inicialización del validador."""
        validator = ResultValidator()
        assert validator.validation_level == ValidationLevel.STANDARD
        assert len(validator.custom_validators) == 0
        assert validator.limits['min_fitness'] == 0.0
        
        # Con nivel personalizado
        validator = ResultValidator(ValidationLevel.STRICT)
        assert validator.validation_level == ValidationLevel.STRICT
    
    def test_validation_issue_creation(self):
        """Test creación de issues de validación."""
        issue = ValidationIssue(
            level=ValidationStatus.ERROR,
            category='test',
            message='Test error',
            field='test_field',
            value=42,
            suggestion='Fix it'
        )
        
        assert issue.level == ValidationStatus.ERROR
        assert issue.category == 'test'
        assert issue.message == 'Test error'
        
        # Test conversión a dict
        issue_dict = issue.to_dict()
        assert issue_dict['level'] == 'error'
        assert issue_dict['value'] == '42'
    
    def test_validation_report(self):
        """Test reporte de validación."""
        report = ValidationReport(
            result_id='test_123',
            validation_level=ValidationLevel.STANDARD
        )
        
        assert report.passed == True
        assert len(report.issues) == 0
        
        # Añadir issue de warning
        report.add_issue(ValidationIssue(
            level=ValidationStatus.WARNING,
            category='test',
            message='Warning'
        ))
        assert report.passed == True  # Warnings no fallan
        
        # Añadir issue de error
        report.add_issue(ValidationIssue(
            level=ValidationStatus.ERROR,
            category='test',
            message='Error'
        ))
        assert report.passed == False  # Errors fallan
        
        # Test obtener issues por nivel
        warnings = report.get_issues_by_level(ValidationStatus.WARNING)
        assert len(warnings) == 1
        errors = report.get_issues_by_level(ValidationStatus.ERROR)
        assert len(errors) == 1


class TestResultValidation:
    """Tests de validación de resultados."""
    
    @pytest.fixture
    def valid_single_result(self):
        """Crea un resultado single-run válido."""
        return StandardResult(
            result_id='test_single_001',
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo(
                name='test_problem',
                problem_type='optimization',
                dimension=10,
                optimal_value=100.0
            ),
            algorithm_info=AlgorithmInfo(
                name='test_algorithm',
                version='1.0',
                parameters={'pop_size': 30}
            ),
            execution_info=ExecutionInfo(
                platform='test',
                python_version='3.8',
                total_time=10.5,
                metadata={'seeds': [42]}
            ),
            data=SingleRunResult(
                run_id=1,
                seed=42,
                best_fitness=105.5,
                execution_time=10.5,
                iterations_completed=100,
                convergence_curve=[150.0, 130.0, 120.0, 110.0, 105.5],
                best_solution=[[0, 1, 2, 0], [0, 3, 4, 0]]
            )
        )
    
    @pytest.fixture
    def valid_multi_result(self):
        """Crea un resultado multi-run válido."""
        fitness_values = [105.5, 108.2, 106.7, 107.1, 105.9]
        return StandardResult(
            result_id='test_multi_001',
            result_type=ResultType.MULTI_RUN,
            timestamp=datetime.now(),
            problem_info=ProblemInfo(
                name='test_problem',
                problem_type='optimization',
                dimension=10,
                optimal_value=100.0
            ),
            algorithm_info=AlgorithmInfo(
                name='test_algorithm',
                version='1.0',
                parameters={'pop_size': 30}
            ),
            execution_info=ExecutionInfo(
                platform='test',
                python_version='3.8',
                total_time=52.5,
                metadata={'seeds': [42, 43, 44, 45, 46]}
            ),
            data=MultiRunStatistics(
                total_runs=5,
                best_fitness=min(fitness_values),
                worst_fitness=max(fitness_values),
                mean_fitness=np.mean(fitness_values),
                std_fitness=np.std(fitness_values),
                median_fitness=np.median(fitness_values),
                all_fitness_values=fitness_values,
                all_execution_times=[10.5, 10.2, 10.8, 10.6, 10.4]
            )
        )
    
    def test_validate_valid_single_result(self, valid_single_result):
        """Test validación de resultado válido single-run."""
        validator = ResultValidator()
        report = validator.validate_result(valid_single_result)
        
        assert report.passed == True
        assert len(report.issues) == 0
        assert report.summary['algorithm'] == 'test_algorithm'
        assert report.summary['best_fitness'] == 105.5
    
    def test_validate_valid_multi_result(self, valid_multi_result):
        """Test validación de resultado válido multi-run."""
        validator = ResultValidator()
        report = validator.validate_result(valid_multi_result)
        
        assert report.passed == True
        assert len(report.issues) == 0
        assert report.summary['total_runs'] == 5
    
    def test_validate_missing_fields(self):
        """Test validación con campos faltantes."""
        # Resultado sin problem_info
        result = StandardResult(
            result_id='test_invalid_001',
            result_type=ResultType.SINGLE_RUN,
            timestamp=datetime.now(),
            problem_info=None,  # Campo faltante
            algorithm_info=AlgorithmInfo(name='test'),
            execution_info=ExecutionInfo(platform='test', python_version='3.8'),
            data=SingleRunResult(
                run_id=1,
                seed=42,
                best_fitness=100.0,
                execution_time=10.0
            )
        )
        
        validator = ResultValidator()
        report = validator.validate_result(result)
        
        assert report.passed == False
        assert any(i.field == 'problem_info' for i in report.issues)
    
    def test_validate_numeric_errors(self, valid_single_result):
        """Test validación de errores numéricos."""
        # Modificar con valor NaN
        valid_single_result.data.best_fitness = float('nan')
        
        validator = ResultValidator()
        report = validator.validate_result(valid_single_result)
        
        assert report.passed == False
        assert any(i.category == 'numeric' and i.level == ValidationStatus.CRITICAL 
                  for i in report.issues)
    
    def test_validate_convergence_curve(self, valid_single_result):
        """Test validación de curva de convergencia."""
        # Curva con deterioros
        valid_single_result.data.convergence_curve = [100, 90, 95, 85, 90, 80]
        
        validator = ResultValidator()
        report = validator.validate_result(valid_single_result)
        
        # Debería generar warning por deterioros
        warnings = report.get_issues_by_level(ValidationStatus.WARNING)
        assert any('deterioration' in i.message for i in warnings)
    
    def test_validate_vrp_solution(self, valid_single_result):
        """Test validación de solución VRP."""
        # Cambiar a problema VRP
        valid_single_result.problem_info.name = 'vrp_test'
        valid_single_result.problem_info.dimension = 5  # 4 clientes + depósito
        
        # Solución inválida - nodo 2 visitado dos veces
        valid_single_result.data.best_solution = [[0, 1, 2, 0], [0, 2, 3, 0]]
        
        validator = ResultValidator(ValidationLevel.STRICT)
        report = validator.validate_result(valid_single_result)
        
        assert report.passed == False
        assert any('visited multiple times' in i.message for i in report.issues)
    
    def test_validate_consistency(self, valid_multi_result):
        """Test validación de consistencia."""
        # Modificar mean para que no coincida
        valid_multi_result.data.mean_fitness = 200.0  # Valor incorrecto
        
        validator = ResultValidator()
        report = validator.validate_result(valid_multi_result)
        
        assert report.passed == False
        assert any(i.category == 'consistency' for i in report.issues)
    
    def test_validate_solution_quality(self, valid_single_result):
        """Test validación de calidad de solución."""
        # Solución mejor que óptima
        valid_single_result.data.best_fitness = 90.0  # Menor que optimal_value=100
        
        validator = ResultValidator(ValidationLevel.STRICT)
        report = validator.validate_result(valid_single_result)
        
        assert report.passed == False
        assert any(i.level == ValidationStatus.CRITICAL and 
                  'better than optimal' in i.message for i in report.issues)
    
    def test_validate_statistical_properties(self, valid_multi_result):
        """Test validación de propiedades estadísticas."""
        # Pocos runs para validez estadística
        valid_multi_result.data.total_runs = 5
        
        validator = ResultValidator(ValidationLevel.SCIENTIFIC)
        report = validator.validate_result(valid_multi_result)
        
        # Debería advertir sobre pocos runs
        warnings = report.get_issues_by_level(ValidationStatus.WARNING)
        assert any('30' in i.message for i in warnings)
    
    def test_custom_validator(self, valid_single_result):
        """Test validador personalizado."""
        def custom_validator(result, report):
            if result.data.best_fitness > 100:
                report.add_issue(ValidationIssue(
                    level=ValidationStatus.WARNING,
                    category='custom',
                    message='Fitness too high'
                ))
        
        validator = ResultValidator()
        validator.add_custom_validator('high_fitness', custom_validator)
        
        report = validator.validate_result(valid_single_result)
        
        assert any(i.category == 'custom' for i in report.issues)


class TestValidationIO:
    """Tests de entrada/salida de reportes."""
    
    def test_save_load_report(self, valid_single_result):
        """Test guardar y cargar reporte."""
        validator = ResultValidator()
        report = validator.validate_result(valid_single_result)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Guardar
            validator.save_report(report, temp_path)
            assert temp_path.exists()
            
            # Cargar
            loaded_report = validator.load_report(temp_path)
            assert loaded_report.result_id == report.result_id
            assert loaded_report.passed == report.passed
            assert len(loaded_report.issues) == len(report.issues)
            
        finally:
            temp_path.unlink()
    
    def test_batch_validation(self, valid_single_result, valid_multi_result):
        """Test validación por lotes."""
        validator = ResultValidator()
        results = [valid_single_result, valid_multi_result]
        
        reports = validator.validate_batch(results)
        
        assert len(reports) == 2
        assert valid_single_result.result_id in reports
        assert valid_multi_result.result_id in reports
        assert all(r.passed for r in reports.values())


class TestSpecializedValidators:
    """Tests de validadores especializados."""
    
    def test_vrp_validator(self, valid_single_result):
        """Test validador específico de VRP."""
        valid_single_result.problem_info.name = 'vrp_test'
        
        validator = ResultValidator()
        vrp_val = create_vrp_validator(capacity_check=True)
        validator.add_custom_validator('vrp', vrp_val)
        
        report = validator.validate_result(valid_single_result)
        
        # Debería advertir sobre falta de capacidad
        warnings = report.get_issues_by_level(ValidationStatus.WARNING)
        assert any('capacity' in i.message for i in warnings)
    
    def test_convergence_validator(self, valid_single_result):
        """Test validador de convergencia."""
        # Convergencia con poca mejora
        valid_single_result.data.convergence_curve = [100.0, 99.5, 99.0, 98.5, 98.0]
        
        validator = ResultValidator()
        conv_val = create_convergence_validator(min_improvement=0.05)  # 5%
        validator.add_custom_validator('convergence', conv_val)
        
        report = validator.validate_result(valid_single_result)
        
        # Debería advertir sobre poca mejora
        warnings = report.get_issues_by_level(ValidationStatus.WARNING)
        assert any('Low improvement' in i.message for i in warnings)
    
    def test_quick_validate(self, valid_single_result):
        """Test validación rápida."""
        assert quick_validate(valid_single_result) == True
        
        # Con error
        valid_single_result.data.best_fitness = float('nan')
        assert quick_validate(valid_single_result) == False


class TestValidationLevels:
    """Tests de diferentes niveles de validación."""
    
    def test_basic_validation(self, valid_single_result):
        """Test nivel básico solo valida estructura."""
        # Añadir error numérico que solo se detecta en STANDARD+
        valid_single_result.data.best_fitness = -10.0  # Negativo
        
        validator = ResultValidator(ValidationLevel.BASIC)
        report = validator.validate_result(valid_single_result)
        
        # BASIC no debería detectar el error numérico
        assert report.passed == True
    
    def test_standard_validation(self, valid_single_result):
        """Test nivel estándar detecta errores numéricos."""
        valid_single_result.data.best_fitness = -10.0
        
        validator = ResultValidator(ValidationLevel.STANDARD)
        report = validator.validate_result(valid_single_result)
        
        # STANDARD sí debería detectarlo
        assert report.passed == False
        assert any(i.category == 'numeric' for i in report.issues)
    
    def test_strict_validation(self, valid_single_result):
        """Test nivel estricto incluye validación de restricciones."""
        valid_single_result.problem_info.name = 'vrp_test'
        valid_single_result.data.best_solution = [[0, 1, 0], [0, 2, 3, 0]]  # Falta nodo 4
        valid_single_result.problem_info.dimension = 5
        
        validator = ResultValidator(ValidationLevel.STRICT)
        report = validator.validate_result(valid_single_result)
        
        assert report.passed == False
        assert any('Missing nodes' in i.message for i in report.issues)
    
    def test_scientific_validation(self, valid_multi_result):
        """Test nivel científico incluye análisis estadístico."""
        # Añadir outlier
        valid_multi_result.data.all_fitness_values = [100, 101, 102, 103, 200]  # 200 es outlier
        valid_multi_result.data.mean_fitness = np.mean(valid_multi_result.data.all_fitness_values)
        valid_multi_result.data.std_fitness = np.std(valid_multi_result.data.all_fitness_values)
        
        validator = ResultValidator(ValidationLevel.SCIENTIFIC)
        report = validator.validate_result(valid_multi_result)
        
        warnings = report.get_issues_by_level(ValidationStatus.WARNING)
        assert any('outlier' in i.message for i in warnings)