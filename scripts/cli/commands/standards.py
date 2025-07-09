"""
Code standards enforcement commands for BioAlgoCompare.
"""

import click
import sys
import subprocess
from pathlib import Path
from typing import Optional, List
import json


@click.group()
def standards():
    """Code standards checking and enforcement."""
    pass


@standards.command()
@click.argument('path', required=False, type=click.Path(exists=True))
@click.option('--fix', is_flag=True, help='Automatically fix violations where possible')
@click.option('--format', type=click.Choice(['text', 'json', 'github']), default='text')
@click.option('--output', '-o', type=click.Path(), help='Output file')
@click.option('--category', type=click.Choice(['all', 'style', 'doc', 'complexity', 'security', 'type']), 
              default='all', help='Check specific category only')
@click.option('--fail-on-warning', is_flag=True, help='Treat warnings as errors')
def check(path, fix, format, output, category, fail_on_warning):
    """
    Check code against project standards.
    
    Performs comprehensive checks including:
    - Code style (PEP 8, naming conventions)
    - Documentation (docstrings, comments)
    - Type hints and annotations
    - Complexity metrics
    - Security patterns
    - Algorithm implementation requirements
    
    Examples:
    
        # Check entire project
        bioalgo standards check
        
        # Check specific directory with fixes
        bioalgo standards check algorithms/ --fix
        
        # Generate JSON report
        bioalgo standards check --format json -o report.json
        
        # Check only documentation
        bioalgo standards check --category doc
    """
    from scripts.quality.code_standards_checker import CodeStandardsChecker
    
    click.echo("🔍 Checking code standards...")
    
    # Initialize checker
    checker = CodeStandardsChecker()
    
    # Run checks
    check_path = Path(path) if path else None
    results = checker.check_all(check_path)
    
    # Filter by category if specified
    if category != 'all':
        results.violations = [v for v in results.violations if v.category == category]
    
    # Apply fixes if requested
    if fix:
        click.echo("\n🔧 Applying automatic fixes...")
        fixed_count = checker.fix_violations()
        click.echo(f"✅ Fixed {fixed_count} violations")
        
        # Re-run checks after fixes
        checker = CodeStandardsChecker()
        results = checker.check_all(check_path)
    
    # Handle fail-on-warning
    if fail_on_warning:
        results.passed = len(results.violations) == 0
    
    # Generate report
    if format == 'github':
        # GitHub Actions format
        for v in results.violations:
            level = 'error' if v.severity == 'error' else 'warning'
            click.echo(f"::{level} file={v.file},line={v.line},col={v.column}::{v.message}")
    else:
        report = checker.generate_report(format)
        
        if output:
            with open(output, 'w') as f:
                f.write(report)
            click.echo(f"📄 Report saved to {output}")
        else:
            click.echo(report)
    
    # Summary
    if format == 'text':
        summary = results.summary()
        if results.passed:
            click.echo("\n✅ All checks passed!")
        else:
            click.echo(f"\n❌ Found {len(results.violations)} violations:")
            click.echo(f"   Errors: {summary.get('error', 0)}")
            click.echo(f"   Warnings: {summary.get('warning', 0)}")
    
    sys.exit(0 if results.passed else 1)


@standards.command()
@click.option('--output', '-o', default='standards/code-standards.md', help='Output file')
@click.option('--format', type=click.Choice(['markdown', 'html', 'pdf']), default='markdown')
def generate_docs(output, format):
    """
    Generate code standards documentation.
    
    Creates comprehensive documentation of all coding standards,
    conventions, and best practices for the project.
    """
    click.echo(f"📝 Generating standards documentation...")
    
    if format != 'markdown':
        click.echo(f"❌ Format '{format}' not yet implemented", err=True)
        sys.exit(1)
    
    # The documentation is already created
    standards_file = Path('standards/code-standards.md')
    if standards_file.exists():
        click.echo(f"✅ Standards documentation available at {standards_file}")
    else:
        click.echo("❌ Standards documentation not found", err=True)
        sys.exit(1)


@standards.command()
@click.option('--check-only', is_flag=True, help='Only check, do not fix')
@click.option('--algorithms', is_flag=True, help='Format algorithm files to standard template')
def format(check_only, algorithms):
    """
    Format code to match project standards.
    
    Applies automatic formatting using configured tools:
    - Ruff for Python code formatting
    - Import sorting and organization
    - Docstring formatting
    
    Examples:
    
        # Format all Python files
        bioalgo standards format
        
        # Check formatting without changes
        bioalgo standards format --check-only
        
        # Format algorithms to standard template
        bioalgo standards format --algorithms
    """
    click.echo("🎨 Formatting code to standards...")
    
    # Run ruff format
    cmd = ['ruff', 'format']
    if check_only:
        cmd.append('--check')
    
    result = subprocess.run(cmd + ['.'], capture_output=True, text=True)
    
    if result.returncode == 0:
        click.echo("✅ Code formatting complete")
    else:
        click.echo("❌ Formatting failed:", err=True)
        click.echo(result.stderr, err=True)
        sys.exit(1)
    
    # Run import sorting
    click.echo("\n🔄 Sorting imports...")
    result = subprocess.run(['ruff', 'check', '--fix', '--select', 'I', '.'], 
                          capture_output=True, text=True)
    
    if algorithms:
        click.echo("\n🧬 Formatting algorithm files...")
        _format_algorithms()


def _format_algorithms():
    """Format algorithm files to match template."""
    from pathlib import Path
    import ast
    
    algorithms_dir = Path('algorithms')
    template_path = Path('standards/algorithm-template.py')
    
    if not template_path.exists():
        click.echo("❌ Algorithm template not found", err=True)
        return
    
    # Read template structure
    with open(template_path) as f:
        template_content = f.read()
    
    # Parse template AST
    template_tree = ast.parse(template_content)
    
    # Process each algorithm file
    for algo_file in algorithms_dir.glob('*.py'):
        if algo_file.stem in ['__init__', 'base']:
            continue
        
        click.echo(f"  Checking {algo_file.name}...")
        
        # Here we would implement algorithm-specific formatting
        # For now, just check basic structure
        try:
            with open(algo_file) as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for required elements
            has_individual_class = False
            has_algorithm_class = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if 'Individual' in node.name:
                        has_individual_class = True
                    elif any(base.id == 'MetaheuristicAlgorithm' 
                            for base in node.bases 
                            if isinstance(base, ast.Name)):
                        has_algorithm_class = True
            
            if has_individual_class and has_algorithm_class:
                click.echo(f"    ✅ {algo_file.name} follows template structure")
            else:
                click.echo(f"    ⚠️  {algo_file.name} may need restructuring")
        except Exception as e:
            click.echo(f"    ❌ Error processing {algo_file.name}: {e}")


@standards.command()
def validate_pr():
    """
    Validate code changes for pull request.
    
    Runs all required checks for code review:
    - Code standards compliance
    - Test coverage requirements
    - Documentation completeness
    - Performance benchmarks
    
    This command is typically run in CI/CD pipelines.
    """
    click.echo("🔍 Validating pull request...")
    
    checks = [
        ("Code Standards", ["python", "scripts/quality/code_standards_checker.py"]),
        ("Tests", ["pytest", "--cov", "--cov-report=term-missing"]),
        ("Type Checking", ["mypy", "algorithms", "problems", "utils"]),
        ("Security", ["bandit", "-r", "algorithms", "problems", "utils", "scripts"]),
    ]
    
    failed_checks = []
    
    for check_name, cmd in checks:
        click.echo(f"\n▶️  Running {check_name}...")
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            click.echo(f"✅ {check_name} passed")
        else:
            click.echo(f"❌ {check_name} failed")
            failed_checks.append(check_name)
    
    if failed_checks:
        click.echo(f"\n❌ Validation failed. Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        click.echo("\n✅ All validations passed! Ready for review.")


@standards.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--staged', is_flag=True, help='Check only staged files')
def pre_commit(files, staged):
    """
    Pre-commit hook for standards enforcement.
    
    Checks files before commit to ensure they meet standards.
    This command is typically called by git pre-commit hooks.
    
    Examples:
    
        # Check specific files
        bioalgo standards pre-commit file1.py file2.py
        
        # Check staged files
        bioalgo standards pre-commit --staged
    """
    if staged:
        # Get staged files
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f.endswith('.py')]
    
    if not files:
        click.echo("No Python files to check")
        sys.exit(0)
    
    click.echo(f"Checking {len(files)} files...")
    
    # Run checks on each file
    from scripts.quality.code_standards_checker import CodeStandardsChecker
    
    checker = CodeStandardsChecker()
    all_passed = True
    
    for file_path in files:
        file_path = Path(file_path)
        if not file_path.exists():
            continue
        
        # Check single file
        checker.results.violations = []  # Reset
        checker._check_file(file_path)
        
        if checker.results.violations:
            all_passed = False
            click.echo(f"\n❌ {file_path}:")
            for v in checker.results.violations:
                click.echo(f"  {v.line}:{v.column} [{v.rule}] {v.message}")
        else:
            click.echo(f"✅ {file_path}")
    
    if not all_passed:
        click.echo("\n❌ Some files have violations. Please fix before committing.")
        click.echo("Run 'bioalgo standards check --fix' to auto-fix some issues.")
        sys.exit(1)
    else:
        click.echo("\n✅ All files pass standards checks!")


@standards.command()
@click.option('--include-metrics', is_flag=True, help='Include code metrics')
def report(include_metrics):
    """
    Generate comprehensive standards compliance report.
    
    Creates a detailed report of the current codebase compliance
    with all defined standards.
    """
    from scripts.quality.code_standards_checker import CodeStandardsChecker
    import datetime
    
    click.echo("📊 Generating standards compliance report...")
    
    checker = CodeStandardsChecker()
    results = checker.check_all()
    
    # Generate report
    report_lines = [
        "# BioAlgoCompare Standards Compliance Report",
        f"\nGenerated: {datetime.datetime.now().isoformat()}",
        "\n## Summary",
        f"- **Status**: {'✅ PASSED' if results.passed else '❌ FAILED'}",
        f"- **Total Files**: {results.metrics.get('total_files', 0)}",
        f"- **Total Lines**: {results.metrics.get('total_lines', 0):,}",
        f"- **Lines of Code**: {results.metrics.get('total_loc', 0):,}",
        f"- **Test Coverage**: {results.metrics.get('test_coverage', 0):.1f}%",
    ]
    
    # Violations summary
    summary = results.summary()
    report_lines.extend([
        "\n## Violations Summary",
        f"- **Total**: {len(results.violations)}",
        f"- **Errors**: {summary.get('error', 0)}",
        f"- **Warnings**: {summary.get('warning', 0)}",
        f"- **Info**: {summary.get('info', 0)}",
    ])
    
    # By category
    by_category = {}
    for v in results.violations:
        by_category[v.category] = by_category.get(v.category, 0) + 1
    
    report_lines.extend([
        "\n### By Category",
    ])
    for cat, count in sorted(by_category.items()):
        report_lines.append(f"- **{cat.title()}**: {count}")
    
    if include_metrics:
        report_lines.extend([
            "\n## Code Metrics",
            f"- **Classes**: {results.metrics.get('total_classes', 0)}",
            f"- **Functions**: {results.metrics.get('total_functions', 0)}",
            f"- **Average File Size**: {results.metrics.get('average_file_size', 0):.0f} lines",
        ])
    
    # Top violations
    if results.violations:
        report_lines.extend([
            "\n## Top Violations",
            "| File | Line | Rule | Message |",
            "|------|------|------|---------|",
        ])
        
        for v in results.violations[:20]:
            report_lines.append(
                f"| {Path(v.file).name} | {v.line} | {v.rule} | {v.message} |"
            )
    
    # Save report
    report_path = Path('standards-report.md')
    report_path.write_text('\n'.join(report_lines))
    
    click.echo(f"\n✅ Report saved to {report_path}")
    
    # Display summary
    if results.passed:
        click.echo("\n🎉 Codebase meets all standards!")
    else:
        click.echo(f"\n⚠️  Found {len(results.violations)} violations to address")


@standards.command()
@click.argument('algorithm_name')
@click.option('--output', '-o', help='Output file name')
@click.option('--paper-title', prompt='Paper title', help='Title of the paper')
@click.option('--paper-authors', prompt='Paper authors', help='Authors of the paper')
@click.option('--paper-year', prompt='Paper year', type=int, help='Publication year')
@click.option('--paper-doi', prompt='Paper DOI (optional)', default='', help='DOI of the paper')
def new_algorithm(algorithm_name, output, paper_title, paper_authors, paper_year, paper_doi):
    """
    Create new algorithm from standard template.
    
    Generates a new algorithm implementation file following
    project standards and conventions.
    
    Example:
    
        bioalgo standards new-algorithm WOA \\
            --paper-title "The Whale Optimization Algorithm" \\
            --paper-authors "Mirjalili and Lewis" \\
            --paper-year 2016 \\
            --paper-doi "10.1016/j.advengsoft.2016.01.008"
    """
    from string import Template
    from pathlib import Path
    
    # Validate algorithm name
    if not algorithm_name.isupper() or len(algorithm_name) > 6:
        click.echo("❌ Algorithm name should be uppercase abbreviation (2-6 chars)", err=True)
        sys.exit(1)
    
    # Read template
    template_path = Path('standards/algorithm-template.py')
    if not template_path.exists():
        click.echo("❌ Algorithm template not found", err=True)
        sys.exit(1)
    
    with open(template_path) as f:
        template_content = f.read()
    
    # Simple substitution (in practice, would use proper templating)
    replacements = {
        'Algorithm Name': f'{algorithm_name} Algorithm',
        'ABBREVIATION': algorithm_name,
        'AlgorithmNameIndividual': f'{algorithm_name}Individual',
        'AlgorithmAbbreviation': algorithm_name,
        'algorithm_name': algorithm_name.lower(),
        'Author(s)': paper_authors,
        'Year': str(paper_year),
        'Paper Title': paper_title,
        'xxx.xxx/xxx': paper_doi or 'TBD',
    }
    
    content = template_content
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Output file
    if not output:
        output = f'algorithms/{algorithm_name.lower()}.py'
    
    output_path = Path(output)
    
    # Check if exists
    if output_path.exists():
        if not click.confirm(f"File {output_path} exists. Overwrite?"):
            sys.exit(0)
    
    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    
    click.echo(f"\n✅ Created new algorithm template: {output_path}")
    click.echo("\nNext steps:")
    click.echo("1. Implement the algorithm logic in the move() method")
    click.echo("2. Update the mathematical formulation section")
    click.echo("3. Add algorithm-specific parameters")
    click.echo("4. Write comprehensive tests")
    click.echo("5. Run standards check: bioalgo standards check " + str(output_path))


# Create command alias
enforce = standards