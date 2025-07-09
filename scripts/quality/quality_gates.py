#!/usr/bin/env python3
"""
Sistema de Quality Gates locales para BioAlgoCompare.

Ejecuta una suite completa de verificaciones de calidad antes
de permitir commits, sin usar recursos en la nube.
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import argparse
import os


@dataclass
class QualityCheck:
    """Representa una verificación de calidad."""
    name: str
    command: List[str]
    description: str
    required: bool = True
    timeout: int = 60
    success_message: str = "✅ Check passed"
    failure_message: str = "❌ Check failed"


@dataclass
class QualityGateResult:
    """Resultado de un quality gate."""
    check_name: str
    passed: bool
    duration: float
    output: str
    error: Optional[str] = None
    
    @property
    def status_icon(self) -> str:
        """Icono de estado."""
        return "✅" if self.passed else "❌"


@dataclass
class QualityReport:
    """Reporte completo de quality gates."""
    timestamp: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    total_duration: float
    results: List[QualityGateResult] = field(default_factory=list)
    
    @property
    def all_passed(self) -> bool:
        """Si todos los checks pasaron."""
        return self.passed_checks == self.total_checks
    
    @property
    def pass_rate(self) -> float:
        """Porcentaje de checks pasados."""
        return (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0


class QualityGateRunner:
    """Ejecutor de quality gates locales."""
    
    # Definición de todos los quality checks
    QUALITY_CHECKS = [
        # Formato y estilo
        QualityCheck(
            name="code_formatting",
            command=["ruff", "format", "--check", "."],
            description="Verificar formato de código",
            required=True
        ),
        
        # Linting
        QualityCheck(
            name="code_linting",
            command=["ruff", "check", "."],
            description="Verificar calidad del código",
            required=True
        ),
        
        # Tests críticos
        QualityCheck(
            name="critical_tests",
            command=["pytest", "tests/test_algorithms_convergence.py", 
                    "tests/test_reproducibility_system.py", "-xvs", "-k", "not slow"],
            description="Ejecutar tests críticos",
            required=True,
            timeout=120
        ),
        
        # Complejidad
        QualityCheck(
            name="complexity_check",
            command=["python", "scripts/quality/check_complexity.py", 
                    "--max-complexity", "15", "algorithms/", "utils/"],
            description="Verificar complejidad del código",
            required=False
        ),
        
        # Naming conventions
        QualityCheck(
            name="naming_conventions",
            command=["python", "scripts/quality/check_naming.py", 
                    "algorithms/", "utils/", "problems/"],
            description="Verificar convenciones de nombres",
            required=False
        ),
        
        # Imports circulares
        QualityCheck(
            name="circular_imports",
            command=["python", "scripts/analyze_imports.py", "--check-only"],
            description="Detectar imports circulares",
            required=True
        ),
        
        # Reproducibilidad
        QualityCheck(
            name="reproducibility",
            command=["python", "scripts/enforce_reproducibility.py", 
                    "--directory", "algorithms"],
            description="Verificar estándares de reproducibilidad",
            required=True
        ),
        
        # Seguridad básica
        QualityCheck(
            name="security_check",
            command=["bandit", "-r", ".", "-ll", "-i", 
                    "--exclude", "tests,legacy,deprecated"],
            description="Verificar vulnerabilidades de seguridad",
            required=False,
            timeout=90
        ),
        
        # Type checking (opcional)
        QualityCheck(
            name="type_checking",
            command=["mypy", "algorithms/", "utils/", 
                    "--ignore-missing-imports", "--no-strict-optional"],
            description="Verificar tipos",
            required=False,
            timeout=120
        ),
        
        # Documentación
        QualityCheck(
            name="docstring_coverage",
            command=["interrogate", "-vv", "--fail-under", "50", 
                    "--ignore-init-method", "--ignore-init-module",
                    "algorithms/", "utils/"],
            description="Verificar cobertura de documentación",
            required=False
        ),
    ]
    
    def __init__(self, 
                 checks: Optional[List[str]] = None,
                 skip_checks: Optional[List[str]] = None,
                 required_only: bool = False,
                 parallel: bool = False):
        """
        Inicializa el runner.
        
        Args:
            checks: Lista de checks específicos a ejecutar
            skip_checks: Lista de checks a omitir
            required_only: Solo ejecutar checks requeridos
            parallel: Ejecutar checks en paralelo
        """
        self.checks_to_run = self._filter_checks(checks, skip_checks, required_only)
        self.parallel = parallel
        self.results: List[QualityGateResult] = []
    
    def _filter_checks(self, 
                      checks: Optional[List[str]],
                      skip_checks: Optional[List[str]],
                      required_only: bool) -> List[QualityCheck]:
        """Filtra los checks a ejecutar."""
        all_checks = self.QUALITY_CHECKS.copy()
        
        # Filtrar por required
        if required_only:
            all_checks = [c for c in all_checks if c.required]
        
        # Filtrar por nombres específicos
        if checks:
            all_checks = [c for c in all_checks if c.name in checks]
        
        # Omitir checks
        if skip_checks:
            all_checks = [c for c in all_checks if c.name not in skip_checks]
        
        return all_checks
    
    def run_check(self, check: QualityCheck) -> QualityGateResult:
        """
        Ejecuta un check individual.
        
        Args:
            check: Check a ejecutar
            
        Returns:
            Resultado del check
        """
        print(f"\n🔍 {check.description}...")
        start_time = time.time()
        
        try:
            # Ejecutar comando
            result = subprocess.run(
                check.command,
                capture_output=True,
                text=True,
                timeout=check.timeout
            )
            
            duration = time.time() - start_time
            
            # Determinar si pasó
            passed = result.returncode == 0
            
            # Crear resultado
            return QualityGateResult(
                check_name=check.name,
                passed=passed,
                duration=duration,
                output=result.stdout,
                error=result.stderr if not passed else None
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return QualityGateResult(
                check_name=check.name,
                passed=False,
                duration=duration,
                output="",
                error=f"Timeout after {check.timeout} seconds"
            )
        except Exception as e:
            duration = time.time() - start_time
            return QualityGateResult(
                check_name=check.name,
                passed=False,
                duration=duration,
                output="",
                error=str(e)
            )
    
    def run_all_checks(self) -> QualityReport:
        """
        Ejecuta todos los checks configurados.
        
        Returns:
            Reporte completo
        """
        print("🚀 Running Quality Gates...\n")
        print(f"Executing {len(self.checks_to_run)} checks")
        print("=" * 60)
        
        start_time = time.time()
        self.results = []
        
        if self.parallel:
            # Ejecución paralela (futuro)
            # Por ahora ejecutamos secuencialmente
            pass
        
        # Ejecución secuencial
        for check in self.checks_to_run:
            result = self.run_check(check)
            self.results.append(result)
            
            # Mostrar resultado inmediato
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            print(f"   {status} ({result.duration:.2f}s)")
            
            # Si es requerido y falla, preguntar si continuar
            if not result.passed and check.required:
                print(f"\n⚠️  Required check '{check.name}' failed!")
                if result.error:
                    print(f"Error: {result.error}")
                
                response = input("\nContinue with remaining checks? (y/N): ")
                if response.lower() != 'y':
                    break
        
        # Crear reporte
        total_duration = time.time() - start_time
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            total_checks=len(self.results),
            passed_checks=passed,
            failed_checks=failed,
            total_duration=total_duration,
            results=self.results
        )
        
        return report
    
    def print_summary(self, report: QualityReport):
        """
        Imprime resumen del reporte.
        
        Args:
            report: Reporte a mostrar
        """
        print("\n" + "=" * 60)
        print("📊 QUALITY GATES SUMMARY")
        print("=" * 60)
        
        # Tabla de resultados
        print(f"\n{'Check':<25} {'Status':<10} {'Duration':<10} {'Required'}")
        print("-" * 60)
        
        for result in report.results:
            # Buscar si es requerido
            check = next((c for c in self.QUALITY_CHECKS if c.name == result.check_name), None)
            required = "Yes" if check and check.required else "No"
            
            status = "PASSED" if result.passed else "FAILED"
            print(f"{result.check_name:<25} {status:<10} {result.duration:>6.2f}s    {required}")
        
        # Estadísticas
        print("\n" + "-" * 60)
        print(f"Total checks: {report.total_checks}")
        print(f"Passed: {report.passed_checks} ({report.pass_rate:.1f}%)")
        print(f"Failed: {report.failed_checks}")
        print(f"Total time: {report.total_duration:.2f}s")
        
        # Resultado final
        print("\n" + "=" * 60)
        if report.all_passed:
            print("✅ ALL QUALITY GATES PASSED!")
            print("Your code is ready to commit.")
        else:
            print("❌ QUALITY GATES FAILED!")
            print("\nFailed checks:")
            for result in report.results:
                if not result.passed:
                    print(f"  - {result.check_name}: {result.error or 'See output above'}")
            print("\nPlease fix the issues before committing.")
    
    def save_report(self, report: QualityReport, filepath: Path):
        """
        Guarda el reporte en archivo.
        
        Args:
            report: Reporte a guardar
            filepath: Ruta del archivo
        """
        report_data = {
            'timestamp': report.timestamp,
            'summary': {
                'total_checks': report.total_checks,
                'passed': report.passed_checks,
                'failed': report.failed_checks,
                'pass_rate': report.pass_rate,
                'duration': report.total_duration
            },
            'results': [
                {
                    'check': r.check_name,
                    'passed': r.passed,
                    'duration': r.duration,
                    'error': r.error
                }
                for r in report.results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)


def create_git_hook():
    """Crea o actualiza el git pre-commit hook."""
    hook_path = Path(".git/hooks/pre-commit")
    
    hook_content = """#!/bin/bash
# BioAlgoCompare Pre-commit Quality Gates

echo "🚀 Running BioAlgoCompare Quality Gates..."

# Ejecutar quality gates requeridos
python scripts/quality/quality_gates.py --required-only

# Capturar código de salida
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ Quality gates failed. Commit aborted."
    echo "💡 Run 'python scripts/quality/quality_gates.py' for detailed report"
    exit 1
fi

echo "✅ All quality gates passed!"
exit 0
"""
    
    # Crear directorio hooks si no existe
    hook_path.parent.mkdir(exist_ok=True)
    
    # Escribir hook
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Hacer ejecutable
    os.chmod(hook_path, 0o755)
    
    print(f"✅ Git pre-commit hook created at {hook_path}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Run local quality gates for BioAlgoCompare'
    )
    parser.add_argument(
        '--checks',
        nargs='+',
        help='Specific checks to run'
    )
    parser.add_argument(
        '--skip',
        nargs='+',
        help='Checks to skip'
    )
    parser.add_argument(
        '--required-only',
        action='store_true',
        help='Only run required checks'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available checks'
    )
    parser.add_argument(
        '--install-hook',
        action='store_true',
        help='Install git pre-commit hook'
    )
    parser.add_argument(
        '--report',
        type=Path,
        help='Save report to file'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run checks in parallel (experimental)'
    )
    
    args = parser.parse_args()
    
    # Listar checks disponibles
    if args.list:
        print("Available Quality Checks:")
        print("=" * 60)
        for check in QualityGateRunner.QUALITY_CHECKS:
            req = "Required" if check.required else "Optional"
            print(f"{check.name:<25} {check.description:<35} [{req}]")
        return 0
    
    # Instalar hook
    if args.install_hook:
        create_git_hook()
        return 0
    
    # Ejecutar quality gates
    runner = QualityGateRunner(
        checks=args.checks,
        skip_checks=args.skip,
        required_only=args.required_only,
        parallel=args.parallel
    )
    
    report = runner.run_all_checks()
    runner.print_summary(report)
    
    # Guardar reporte si se solicita
    if args.report:
        runner.save_report(report, args.report)
        print(f"\n📄 Report saved to {args.report}")
    
    # Retornar código de salida
    return 0 if report.all_passed else 1


if __name__ == '__main__':
    sys.exit(main())