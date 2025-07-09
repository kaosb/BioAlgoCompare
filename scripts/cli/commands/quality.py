"""
Comandos CLI para gestión de quality gates y calidad del código.
"""

import click
import subprocess
import json
from pathlib import Path
from datetime import datetime
import os
import sys


@click.group()
def quality():
    """Code quality and quality gates management."""
    pass


@quality.command()
@click.option('--checks', multiple=True, help='Specific checks to run')
@click.option('--skip', multiple=True, help='Checks to skip')
@click.option('--required-only', is_flag=True, help='Only run required checks')
@click.option('--report', type=click.Path(), help='Save report to file')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def check(checks, skip, required_only, report, output_json):
    """
    Run quality gates checks.
    
    Executes a comprehensive suite of quality checks locally without
    using cloud resources. All checks run on your machine.
    
    Examples:
    
        # Run all checks
        bioalgo quality check
        
        # Run only required checks
        bioalgo quality check --required-only
        
        # Run specific checks
        bioalgo quality check --checks code_formatting --checks critical_tests
        
        # Skip certain checks
        bioalgo quality check --skip type_checking --skip docstring_coverage
        
        # Save report
        bioalgo quality check --report quality_report.json
    """
    from scripts.quality.quality_gates import QualityGateRunner
    
    # Crear runner
    runner = QualityGateRunner(
        checks=list(checks) if checks else None,
        skip_checks=list(skip) if skip else None,
        required_only=required_only
    )
    
    # Ejecutar checks
    report = runner.run_all_checks()
    
    if output_json:
        # Salida JSON
        report_data = {
            'timestamp': report.timestamp,
            'summary': {
                'total_checks': report.total_checks,
                'passed': report.passed_checks,
                'failed': report.failed_checks,
                'pass_rate': report.pass_rate,
                'duration': report.total_duration,
                'all_passed': report.all_passed
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
        click.echo(json.dumps(report_data, indent=2))
    else:
        # Mostrar resumen
        runner.print_summary(report)
    
    # Guardar reporte si se solicita
    if report:
        runner.save_report(report, Path(report))
        if not output_json:
            click.echo(f"\n📄 Report saved to {report}")
    
    # Salir con código apropiado
    sys.exit(0 if report.all_passed else 1)


@quality.command()
def list():
    """
    List available quality checks.
    
    Shows all quality checks that can be run, including their
    descriptions and whether they are required or optional.
    """
    from scripts.quality.quality_gates import QualityGateRunner
    
    click.echo("\n🔍 Available Quality Checks\n")
    click.echo(f"{'Name':<25} {'Description':<40} {'Required':<10} {'Timeout'}")
    click.echo("=" * 85)
    
    for check in QualityGateRunner.QUALITY_CHECKS:
        req = click.style("Yes", fg='red') if check.required else click.style("No", fg='green')
        click.echo(f"{check.name:<25} {check.description:<40} {req:<18} {check.timeout}s")
    
    click.echo(f"\nTotal checks: {len(QualityGateRunner.QUALITY_CHECKS)}")
    required = sum(1 for c in QualityGateRunner.QUALITY_CHECKS if c.required)
    optional = len(QualityGateRunner.QUALITY_CHECKS) - required
    click.echo(f"Required: {required}, Optional: {optional}")


@quality.command()
@click.option('--force', is_flag=True, help='Overwrite existing hooks')
def install_hooks(force):
    """
    Install pre-commit hooks for quality gates.
    
    Sets up git hooks that will run quality checks automatically
    before each commit. This ensures code quality without using
    cloud CI/CD resources.
    
    Examples:
    
        # Install hooks
        bioalgo quality install-hooks
        
        # Force reinstall
        bioalgo quality install-hooks --force
    """
    # Verificar si estamos en un repositorio git
    if not Path(".git").exists():
        click.echo("❌ Not in a git repository", err=True)
        sys.exit(1)
    
    # Instalar pre-commit framework
    click.echo("📦 Installing pre-commit framework...")
    
    # Verificar si pre-commit está instalado
    try:
        subprocess.run(["pre-commit", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("Installing pre-commit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"], 
                      check=True)
    
    # Instalar hooks
    click.echo("\n🔧 Installing git hooks...")
    
    if force:
        subprocess.run(["pre-commit", "install", "--overwrite"], check=True)
        subprocess.run(["pre-commit", "install", "--hook-type", "commit-msg", "--overwrite"], 
                      check=True)
    else:
        subprocess.run(["pre-commit", "install"], check=True)
        subprocess.run(["pre-commit", "install", "--hook-type", "commit-msg"], 
                      check=True)
    
    # Crear hook adicional para quality gates
    from scripts.quality.quality_gates import create_git_hook
    create_git_hook()
    
    click.echo("\n✅ Quality gates hooks installed successfully!")
    click.echo("\nThe following will now run automatically before commits:")
    click.echo("  - Code formatting (ruff)")
    click.echo("  - Code linting")
    click.echo("  - Critical tests")
    click.echo("  - Security checks")
    click.echo("  - And more...")
    click.echo("\n💡 To run checks manually: bioalgo quality check")


@quality.command()
@click.option('--all', 'run_all', is_flag=True, help='Run on all files')
@click.option('--fix', is_flag=True, help='Auto-fix issues where possible')
def format(run_all, fix):
    """
    Format code using ruff.
    
    Ensures consistent code formatting across the project.
    By default only formats staged files.
    
    Examples:
    
        # Check formatting (no changes)
        bioalgo quality format
        
        # Fix formatting issues
        bioalgo quality format --fix
        
        # Format all files
        bioalgo quality format --all --fix
    """
    cmd = ["ruff", "format"]
    
    if not fix:
        cmd.append("--check")
    
    if run_all:
        cmd.append(".")
    else:
        # Solo archivos staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split('\n') 
                    if f and f.endswith('.py')]
            if files:
                cmd.extend(files)
            else:
                click.echo("No Python files staged for commit")
                return
        else:
            click.echo("Error getting staged files", err=True)
            sys.exit(1)
    
    # Ejecutar formato
    click.echo(f"🎨 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        if fix:
            click.echo("✅ Code formatted successfully")
        else:
            click.echo("✅ Code formatting is correct")
    else:
        click.echo("❌ Formatting issues found", err=True)
        if not fix:
            click.echo("💡 Run with --fix to auto-format")
        sys.exit(1)


@quality.command()
@click.option('--all', 'run_all', is_flag=True, help='Lint all files')
@click.option('--fix', is_flag=True, help='Auto-fix issues where possible')
def lint(run_all, fix):
    """
    Run linting checks using ruff.
    
    Checks for code quality issues, potential bugs, and style violations.
    
    Examples:
    
        # Check staged files
        bioalgo quality lint
        
        # Fix issues automatically
        bioalgo quality lint --fix
        
        # Lint entire project
        bioalgo quality lint --all
    """
    cmd = ["ruff", "check"]
    
    if fix:
        cmd.append("--fix")
    
    if run_all:
        cmd.append(".")
    else:
        # Solo archivos staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split('\n') 
                    if f and f.endswith('.py')]
            if files:
                cmd.extend(files)
            else:
                click.echo("No Python files staged for commit")
                return
        else:
            click.echo("Error getting staged files", err=True)
            sys.exit(1)
    
    # Ejecutar linting
    click.echo(f"🔍 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        click.echo("✅ No linting issues found")
    else:
        click.echo("❌ Linting issues found", err=True)
        if not fix:
            click.echo("💡 Run with --fix to auto-fix some issues")
        sys.exit(1)


@quality.command()
@click.argument('paths', nargs=-1, required=True)
@click.option('--max-complexity', type=int, default=10, 
              help='Maximum allowed complexity')
@click.option('--report', is_flag=True, help='Generate detailed report')
def complexity(paths, max_complexity, report):
    """
    Check code complexity.
    
    Analyzes cyclomatic complexity of functions and methods.
    High complexity indicates code that may be hard to understand
    and maintain.
    
    Examples:
    
        # Check specific files
        bioalgo quality complexity algorithms/hoa.py
        
        # Check directory with custom threshold
        bioalgo quality complexity algorithms/ --max-complexity 15
        
        # Generate detailed report
        bioalgo quality complexity . --report
    """
    cmd = [
        sys.executable, "scripts/quality/check_complexity.py",
        "--max-complexity", str(max_complexity)
    ]
    
    if report:
        cmd.append("--report")
    
    cmd.extend(paths)
    
    click.echo(f"🧩 Checking code complexity (max: {max_complexity})...")
    result = subprocess.run(cmd)
    
    sys.exit(result.returncode)


@quality.command()
@click.argument('paths', nargs=-1, required=True)
def naming(paths):
    """
    Check naming conventions.
    
    Ensures that all files, classes, functions, and variables
    follow Python naming conventions.
    
    Examples:
    
        # Check specific files
        bioalgo quality naming algorithms/hoa.py
        
        # Check entire directory
        bioalgo quality naming algorithms/
    """
    cmd = [sys.executable, "scripts/quality/check_naming.py"]
    cmd.extend(paths)
    
    click.echo("📛 Checking naming conventions...")
    result = subprocess.run(cmd)
    
    sys.exit(result.returncode)


@quality.command()
@click.option('--staged', is_flag=True, help='Run tests for staged files only')
@click.option('--failed', is_flag=True, help='Run only previously failed tests')
def test_critical(staged, failed):
    """
    Run critical tests only.
    
    Executes a subset of tests that are considered critical
    for code quality. These tests run quickly and catch the
    most important issues.
    
    Examples:
    
        # Run all critical tests
        bioalgo quality test-critical
        
        # Run tests related to staged files
        bioalgo quality test-critical --staged
        
        # Re-run failed tests
        bioalgo quality test-critical --failed
    """
    cmd = [
        "pytest",
        "tests/test_algorithms_convergence.py",
        "tests/test_reproducibility_system.py",
        "-xvs",
        "-k", "not slow"
    ]
    
    if failed:
        cmd.append("--lf")  # Last failed
    
    if staged:
        # Determinar qué tests ejecutar basado en archivos staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            # Mapear archivos a tests (simplificado)
            test_files = set()
            for f in files:
                if 'algorithms' in f:
                    test_files.add("tests/test_algorithms_convergence.py")
                if 'reproducibility' in f:
                    test_files.add("tests/test_reproducibility_system.py")
            
            if test_files:
                cmd = ["pytest"] + list(test_files) + ["-xvs", "-k", "not slow"]
    
    click.echo("🧪 Running critical tests...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        click.echo("\n✅ All critical tests passed")
    else:
        click.echo("\n❌ Some tests failed", err=True)
    
    sys.exit(result.returncode)


@quality.command()
@click.option('--output', '-o', default='quality_report.html',
              help='Output file for report')
@click.option('--format', type=click.Choice(['html', 'json', 'markdown']),
              default='html', help='Report format')
def report(output, format):
    """
    Generate comprehensive quality report.
    
    Creates a detailed report of code quality metrics including
    test coverage, complexity, linting issues, and more.
    
    Examples:
    
        # Generate HTML report
        bioalgo quality report
        
        # Generate markdown report
        bioalgo quality report -o report.md --format markdown
    """
    from scripts.quality.quality_gates import QualityGateRunner
    import pandas as pd
    
    click.echo("📊 Generating comprehensive quality report...")
    
    # Ejecutar todos los checks
    runner = QualityGateRunner()
    report_data = runner.run_all_checks()
    
    if format == 'json':
        # Guardar como JSON
        runner.save_report(report_data, Path(output))
        click.echo(f"✅ JSON report saved to {output}")
    
    elif format == 'markdown':
        # Generar reporte Markdown
        content = f"# Code Quality Report\n\n"
        content += f"Generated: {report_data.timestamp}\n\n"
        
        content += "## Summary\n\n"
        content += f"- Total checks: {report_data.total_checks}\n"
        content += f"- Passed: {report_data.passed_checks}\n"
        content += f"- Failed: {report_data.failed_checks}\n"
        content += f"- Pass rate: {report_data.pass_rate:.1f}%\n"
        content += f"- Duration: {report_data.total_duration:.2f}s\n\n"
        
        content += "## Results\n\n"
        content += "| Check | Status | Duration | Error |\n"
        content += "|-------|--------|----------|-------|\n"
        
        for result in report_data.results:
            status = "✅ Passed" if result.passed else "❌ Failed"
            error = result.error or "-"
            content += f"| {result.check_name} | {status} | {result.duration:.2f}s | {error} |\n"
        
        Path(output).write_text(content)
        click.echo(f"✅ Markdown report saved to {output}")
    
    else:  # HTML
        # Generar reporte HTML
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Code Quality Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; }
        .passed { color: green; }
        .failed { color: red; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Code Quality Report</h1>
    <p>Generated: {timestamp}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li>Total checks: {total_checks}</li>
            <li>Passed: <span class="passed">{passed}</span></li>
            <li>Failed: <span class="failed">{failed}</span></li>
            <li>Pass rate: {pass_rate:.1f}%</li>
            <li>Duration: {duration:.2f}s</li>
        </ul>
    </div>
    
    <h2>Results</h2>
    <table>
        <tr>
            <th>Check</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Error</th>
        </tr>
        {rows}
    </table>
</body>
</html>
"""
        
        rows = ""
        for result in report_data.results:
            status = '<span class="passed">✅ Passed</span>' if result.passed else '<span class="failed">❌ Failed</span>'
            error = result.error or "-"
            rows += f"<tr><td>{result.check_name}</td><td>{status}</td><td>{result.duration:.2f}s</td><td>{error}</td></tr>\n"
        
        html_content = html_template.format(
            timestamp=report_data.timestamp,
            total_checks=report_data.total_checks,
            passed=report_data.passed_checks,
            failed=report_data.failed_checks,
            pass_rate=report_data.pass_rate,
            duration=report_data.total_duration,
            rows=rows
        )
        
        Path(output).write_text(html_content)
        click.echo(f"✅ HTML report saved to {output}")
        
        # Intentar abrir en navegador
        import webbrowser
        webbrowser.open(f"file://{Path(output).absolute()}")


@quality.command()
def doctor():
    """
    Diagnose quality tools setup.
    
    Checks that all required tools are installed and properly
    configured for running quality gates.
    """
    click.echo("🩺 Diagnosing quality tools setup...\n")
    
    tools = [
        ("Python", [sys.executable, "--version"]),
        ("Git", ["git", "--version"]),
        ("Ruff", ["ruff", "--version"]),
        ("Pytest", ["pytest", "--version"]),
        ("Bandit", ["bandit", "--version"]),
        ("MyPy", ["mypy", "--version"]),
        ("Pre-commit", ["pre-commit", "--version"]),
    ]
    
    all_good = True
    
    for tool_name, cmd in tools:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            version = result.stdout.strip() or result.stderr.strip()
            click.echo(f"✅ {tool_name:<12} {version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo(f"❌ {tool_name:<12} Not installed or not in PATH")
            all_good = False
    
    # Verificar archivos de configuración
    click.echo("\nConfiguration files:")
    
    config_files = [
        ".pre-commit-config.yaml",
        "pyproject.toml",
        ".gitignore",
        "scripts/quality/quality_gates.py",
        "scripts/quality/check_naming.py",
        "scripts/quality/check_complexity.py"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            click.echo(f"✅ {config_file}")
        else:
            click.echo(f"❌ {config_file} - Missing")
            all_good = False
    
    # Verificar hooks
    click.echo("\nGit hooks:")
    
    hooks = [".git/hooks/pre-commit", ".git/hooks/commit-msg"]
    for hook in hooks:
        if Path(hook).exists():
            click.echo(f"✅ {hook}")
        else:
            click.echo(f"⚠️  {hook} - Not installed")
    
    # Diagnóstico final
    click.echo("\n" + "="*50)
    if all_good:
        click.echo("✅ All quality tools are properly installed!")
        click.echo("\n💡 Run 'bioalgo quality install-hooks' to set up git hooks")
    else:
        click.echo("❌ Some tools are missing")
        click.echo("\n💡 Install missing tools:")
        click.echo("   pip install ruff pytest bandit mypy pre-commit")


# Crear alias para el comando principal
check_quality = quality