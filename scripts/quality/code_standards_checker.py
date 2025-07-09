#!/usr/bin/env python3
"""
Code standards checker for BioAlgoCompare.

This module implements automated checking and enforcement of code standards
including style, documentation, complexity, and best practices.
"""

import ast
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a code standard violation."""
    file: str
    line: int
    column: int
    rule: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    category: str  # 'style', 'doc', 'complexity', 'security', 'performance'
    fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file': self.file,
            'location': f"{self.file}:{self.line}:{self.column}",
            'rule': self.rule,
            'severity': self.severity,
            'message': self.message,
            'category': self.category,
            'fixable': self.fixable
        }


@dataclass
class CheckResult:
    """Results from code standards check."""
    violations: List[Violation] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    passed: bool = True
    
    def add_violation(self, violation: Violation):
        """Add a violation."""
        self.violations.append(violation)
        if violation.severity == 'error':
            self.passed = False
    
    def summary(self) -> Dict[str, int]:
        """Get summary of violations."""
        summary = defaultdict(int)
        for v in self.violations:
            summary[v.severity] += 1
            summary[f"{v.category}_{v.severity}"] += 1
        return dict(summary)


class CodeStandardsChecker:
    """Main code standards checker."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize checker with configuration."""
        self.project_root = Path(__file__).parent.parent.parent
        self.config = self._load_config(config_path)
        self.results = CheckResult()
        
        # Patterns
        self.algorithm_pattern = re.compile(r'^[A-Z]{2,6}$')  # Algorithm abbreviations
        self.class_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')  # PascalCase
        self.function_pattern = re.compile(r'^[a-z_][a-z0-9_]*$')  # snake_case
        self.constant_pattern = re.compile(r'^[A-Z][A-Z0-9_]*$')  # UPPER_SNAKE_CASE
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load configuration."""
        default_config = {
            'max_line_length': 88,
            'max_complexity': 15,
            'min_coverage': 80,
            'required_docstring_sections': ['Args', 'Returns'],
            'algorithm_required_methods': [
                '__init__',
                '_create_individual', 
                'initialize_population',
                'run'
            ],
            'exclude_patterns': [
                '**/__pycache__/**',
                '**/venv/**',
                '**/.git/**',
                '**/build/**',
                '**/dist/**'
            ]
        }
        
        if config_path and config_path.exists():
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def check_all(self, path: Optional[Path] = None) -> CheckResult:
        """Run all checks on the codebase."""
        if path is None:
            path = self.project_root
        
        logger.info(f"Running code standards checks on {path}")
        
        # Find Python files
        python_files = self._find_python_files(path)
        logger.info(f"Found {len(python_files)} Python files")
        
        # Run checks
        for file_path in python_files:
            self._check_file(file_path)
        
        # Run tool-based checks
        self._run_ruff_check(path)
        self._run_mypy_check(path)
        self._check_test_coverage(path)
        
        # Calculate metrics
        self._calculate_metrics(python_files)
        
        return self.results
    
    def _find_python_files(self, path: Path) -> List[Path]:
        """Find all Python files to check."""
        files = []
        
        for pattern in ['**/*.py']:
            for file_path in path.glob(pattern):
                # Check exclusions
                if any(file_path.match(exc) for exc in self.config['exclude_patterns']):
                    continue
                files.append(file_path)
        
        return sorted(files)
    
    def _check_file(self, file_path: Path) -> None:
        """Check a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.results.add_violation(Violation(
                    file=str(file_path),
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    rule='syntax-error',
                    severity='error',
                    message=f"Syntax error: {e.msg}",
                    category='style'
                ))
                return
            
            # Run AST-based checks
            self._check_naming_conventions(tree, file_path, content)
            self._check_docstrings(tree, file_path)
            self._check_complexity(tree, file_path)
            self._check_type_hints(tree, file_path)
            
            # Run text-based checks
            self._check_imports(content, file_path)
            self._check_security_patterns(content, file_path)
            
            # Algorithm-specific checks
            if 'algorithms' in str(file_path) and file_path.stem not in ['__init__', 'base']:
                self._check_algorithm_implementation(tree, file_path)
            
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
    
    def _check_naming_conventions(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check naming conventions."""
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            # Check class names
            if isinstance(node, ast.ClassDef):
                if not self.class_pattern.match(node.name):
                    self.results.add_violation(Violation(
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        rule='naming-class',
                        severity='error',
                        message=f"Class name '{node.name}' should be PascalCase",
                        category='style',
                        fixable=True
                    ))
            
            # Check function names
            elif isinstance(node, ast.FunctionDef):
                if not self.function_pattern.match(node.name):
                    self.results.add_violation(Violation(
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        rule='naming-function',
                        severity='error',
                        message=f"Function name '{node.name}' should be snake_case",
                        category='style',
                        fixable=True
                    ))
            
            # Check constants
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        if not self.constant_pattern.match(target.id):
                            self.results.add_violation(Violation(
                                file=str(file_path),
                                line=node.lineno,
                                column=node.col_offset,
                                rule='naming-constant',
                                severity='warning',
                                message=f"Constant '{target.id}' should be UPPER_SNAKE_CASE",
                                category='style',
                                fixable=True
                            ))
    
    def _check_docstrings(self, tree: ast.AST, file_path: Path) -> None:
        """Check docstring presence and format."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                
                # Check presence
                if not docstring:
                    # Skip private methods and test functions
                    if node.name.startswith('_') and not node.name.startswith('__'):
                        continue
                    if node.name.startswith('test_'):
                        continue
                    
                    self.results.add_violation(Violation(
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        rule='missing-docstring',
                        severity='warning',
                        message=f"Missing docstring for {type(node).__name__} '{node.name}'",
                        category='doc'
                    ))
                else:
                    # Check format (Google style)
                    self._check_docstring_format(docstring, node, file_path)
    
    def _check_docstring_format(self, docstring: str, node: ast.AST, file_path: Path) -> None:
        """Check docstring format (Google style)."""
        if isinstance(node, ast.FunctionDef):
            # Check for required sections
            has_args = 'Args:' in docstring or 'Arguments:' in docstring
            has_returns = 'Returns:' in docstring or 'Return:' in docstring
            
            # Check if function has parameters
            if node.args.args and not has_args:
                self.results.add_violation(Violation(
                    file=str(file_path),
                    line=node.lineno,
                    column=node.col_offset,
                    rule='docstring-missing-args',
                    severity='warning',
                    message=f"Function '{node.name}' has parameters but missing Args section",
                    category='doc'
                ))
            
            # Check if function returns value
            returns_value = any(
                isinstance(n, ast.Return) and n.value is not None
                for n in ast.walk(node)
            )
            if returns_value and not has_returns:
                self.results.add_violation(Violation(
                    file=str(file_path),
                    line=node.lineno,
                    column=node.col_offset,
                    rule='docstring-missing-returns',
                    severity='warning',
                    message=f"Function '{node.name}' returns value but missing Returns section",
                    category='doc'
                ))
    
    def _check_complexity(self, tree: ast.AST, file_path: Path) -> None:
        """Check cyclomatic complexity."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                
                if complexity > self.config['max_complexity']:
                    self.results.add_violation(Violation(
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        rule='high-complexity',
                        severity='warning',
                        message=f"Function '{node.name}' has complexity {complexity} (max: {self.config['max_complexity']})",
                        category='complexity'
                    ))
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_type_hints(self, tree: ast.AST, file_path: Path) -> None:
        """Check for type hints."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private methods and test functions
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                if node.name.startswith('test_'):
                    continue
                
                # Check return type
                if node.returns is None and node.name != '__init__':
                    self.results.add_violation(Violation(
                        file=str(file_path),
                        line=node.lineno,
                        column=node.col_offset,
                        rule='missing-return-type',
                        severity='warning',
                        message=f"Function '{node.name}' missing return type hint",
                        category='style'
                    ))
                
                # Check parameter types
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != 'self':
                        self.results.add_violation(Violation(
                            file=str(file_path),
                            line=node.lineno,
                            column=node.col_offset,
                            rule='missing-param-type',
                            severity='warning',
                            message=f"Parameter '{arg.arg}' in '{node.name}' missing type hint",
                            category='style'
                        ))
    
    def _check_imports(self, content: str, file_path: Path) -> None:
        """Check import statements."""
        lines = content.split('\n')
        import_section_started = False
        last_import_type = None  # 'stdlib', 'third-party', 'local'
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith(('import ', 'from ')):
                import_section_started = True
                
                # Determine import type
                if 'algorithms' in stripped or 'problems' in stripped or 'utils' in stripped:
                    current_type = 'local'
                elif any(pkg in stripped for pkg in ['numpy', 'pandas', 'matplotlib', 'scipy']):
                    current_type = 'third-party'
                else:
                    current_type = 'stdlib'
                
                # Check import order
                if last_import_type and current_type != last_import_type:
                    type_order = {'stdlib': 0, 'third-party': 1, 'local': 2}
                    if type_order.get(current_type, 3) < type_order.get(last_import_type, -1):
                        self.results.add_violation(Violation(
                            file=str(file_path),
                            line=i,
                            column=0,
                            rule='import-order',
                            severity='warning',
                            message=f"Import order: {current_type} imports should come after {last_import_type}",
                            category='style',
                            fixable=True
                        ))
                
                last_import_type = current_type
                
            elif import_section_started and stripped and not stripped.startswith('#'):
                # Non-import line after imports started
                import_section_started = False
    
    def _check_security_patterns(self, content: str, file_path: Path) -> None:
        """Check for security issues."""
        lines = content.split('\n')
        
        # Patterns to check
        security_patterns = [
            (r'eval\s*\(', 'Use of eval() is dangerous'),
            (r'exec\s*\(', 'Use of exec() is dangerous'),
            (r'__import__\s*\(', 'Dynamic imports can be security risk'),
            (r'pickle\.load', 'Pickle can execute arbitrary code'),
            (r'input\s*\(', 'Use of input() in library code'),
            (r'os\.system\s*\(', 'Use subprocess instead of os.system'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in security_patterns:
                if re.search(pattern, line):
                    self.results.add_violation(Violation(
                        file=str(file_path),
                        line=i,
                        column=0,
                        rule='security-risk',
                        severity='error',
                        message=message,
                        category='security'
                    ))
    
    def _check_algorithm_implementation(self, tree: ast.AST, file_path: Path) -> None:
        """Check algorithm implementation requirements."""
        # Find main algorithm class
        algorithm_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if inherits from MetaheuristicAlgorithm
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'MetaheuristicAlgorithm':
                        algorithm_class = node
                        break
        
        if not algorithm_class:
            return
        
        # Check required methods
        methods = {n.name for n in algorithm_class.body if isinstance(n, ast.FunctionDef)}
        
        for required_method in self.config['algorithm_required_methods']:
            if required_method not in methods:
                self.results.add_violation(Violation(
                    file=str(file_path),
                    line=algorithm_class.lineno,
                    column=algorithm_class.col_offset,
                    rule='algorithm-missing-method',
                    severity='error',
                    message=f"Algorithm class missing required method '{required_method}'",
                    category='style'
                ))
        
        # Check for paper reference in docstring
        docstring = ast.get_docstring(algorithm_class)
        if docstring and 'Based on:' not in docstring and 'Reference:' not in docstring:
            self.results.add_violation(Violation(
                file=str(file_path),
                line=algorithm_class.lineno,
                column=algorithm_class.col_offset,
                rule='algorithm-missing-reference',
                severity='warning',
                message="Algorithm class should include paper reference in docstring",
                category='doc'
            ))
    
    def _run_ruff_check(self, path: Path) -> None:
        """Run ruff linter."""
        try:
            result = subprocess.run(
                ['ruff', 'check', '--format', 'json', str(path)],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                violations = json.loads(result.stdout)
                for v in violations:
                    self.results.add_violation(Violation(
                        file=v['filename'],
                        line=v['location']['row'],
                        column=v['location']['column'],
                        rule=v['code'],
                        severity='error' if v['code'].startswith('E') else 'warning',
                        message=v['message'],
                        category='style',
                        fixable=v.get('fix') is not None
                    ))
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to run ruff: {e}")
    
    def _run_mypy_check(self, path: Path) -> None:
        """Run mypy type checker."""
        try:
            result = subprocess.run(
                ['mypy', '--json-report', '-', str(path)],
                capture_output=True,
                text=True
            )
            
            # Parse mypy output
            for line in result.stdout.split('\n'):
                if ': error:' in line or ': warning:' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        file_path = parts[0]
                        line_num = int(parts[1]) if parts[1].isdigit() else 0
                        severity = 'error' if 'error' in parts[2] else 'warning'
                        message = parts[3].strip()
                        
                        self.results.add_violation(Violation(
                            file=file_path,
                            line=line_num,
                            column=0,
                            rule='type-error',
                            severity=severity,
                            message=message,
                            category='type'
                        ))
        except subprocess.SubprocessError as e:
            logger.warning(f"Failed to run mypy: {e}")
    
    def _check_test_coverage(self, path: Path) -> None:
        """Check test coverage."""
        try:
            # Run coverage
            subprocess.run(
                ['coverage', 'run', '-m', 'pytest', str(path / 'tests')],
                capture_output=True
            )
            
            # Get coverage report
            result = subprocess.run(
                ['coverage', 'report', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                coverage_data = json.loads(result.stdout)
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                
                if total_coverage < self.config['min_coverage']:
                    self.results.add_violation(Violation(
                        file='coverage',
                        line=0,
                        column=0,
                        rule='low-coverage',
                        severity='warning',
                        message=f"Test coverage {total_coverage:.1f}% is below minimum {self.config['min_coverage']}%",
                        category='test'
                    ))
                
                self.results.metrics['test_coverage'] = total_coverage
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to check coverage: {e}")
    
    def _calculate_metrics(self, files: List[Path]) -> None:
        """Calculate code metrics."""
        total_lines = 0
        total_loc = 0  # Lines of code (non-empty, non-comment)
        total_classes = 0
        total_functions = 0
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                total_lines += len(lines)
                total_loc += sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
                
                # Count classes and functions
                tree = ast.parse(''.join(lines))
                total_classes += sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
                total_functions += sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
            except:
                pass
        
        self.results.metrics.update({
            'total_files': len(files),
            'total_lines': total_lines,
            'total_loc': total_loc,
            'total_classes': total_classes,
            'total_functions': total_functions,
            'average_file_size': total_lines / len(files) if files else 0
        })
    
    def generate_report(self, output_format: str = 'text') -> str:
        """Generate report of violations."""
        if output_format == 'json':
            return json.dumps({
                'passed': self.results.passed,
                'summary': self.results.summary(),
                'violations': [v.to_dict() for v in self.results.violations],
                'metrics': self.results.metrics
            }, indent=2)
        
        # Text format
        report = ["=" * 80]
        report.append("CODE STANDARDS CHECK REPORT")
        report.append("=" * 80)
        
        # Summary
        summary = self.results.summary()
        report.append(f"\nStatus: {'PASSED' if self.results.passed else 'FAILED'}")
        report.append(f"Total violations: {len(self.results.violations)}")
        report.append(f"  Errors: {summary.get('error', 0)}")
        report.append(f"  Warnings: {summary.get('warning', 0)}")
        report.append(f"  Info: {summary.get('info', 0)}")
        
        # Metrics
        if self.results.metrics:
            report.append("\nCode Metrics:")
            for key, value in self.results.metrics.items():
                report.append(f"  {key}: {value}")
        
        # Violations by category
        if self.results.violations:
            report.append("\nViolations by Category:")
            by_category = defaultdict(list)
            for v in self.results.violations:
                by_category[v.category].append(v)
            
            for category, violations in sorted(by_category.items()):
                report.append(f"\n{category.upper()} ({len(violations)} violations):")
                for v in violations[:10]:  # Show first 10
                    report.append(f"  {v.file}:{v.line} [{v.rule}] {v.message}")
                if len(violations) > 10:
                    report.append(f"  ... and {len(violations) - 10} more")
        
        # Fixable violations
        fixable = [v for v in self.results.violations if v.fixable]
        if fixable:
            report.append(f"\n{len(fixable)} violations can be automatically fixed")
        
        report.append("=" * 80)
        
        return '\n'.join(report)
    
    def fix_violations(self, dry_run: bool = False) -> int:
        """Attempt to fix auto-fixable violations."""
        fixed_count = 0
        
        # Group violations by file
        by_file = defaultdict(list)
        for v in self.results.violations:
            if v.fixable:
                by_file[v.file].append(v)
        
        for file_path, violations in by_file.items():
            try:
                # Run ruff format
                if not dry_run:
                    subprocess.run(['ruff', 'format', file_path], check=True)
                    subprocess.run(['ruff', 'check', '--fix', file_path], check=True)
                
                fixed_count += len(violations)
                logger.info(f"Fixed {len(violations)} violations in {file_path}")
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to fix {file_path}: {e}")
        
        return fixed_count


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check code standards')
    parser.add_argument('path', nargs='?', help='Path to check (default: project root)')
    parser.add_argument('--fix', action='store_true', help='Fix auto-fixable violations')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Initialize checker
    config_path = Path(args.config) if args.config else None
    checker = CodeStandardsChecker(config_path)
    
    # Run checks
    path = Path(args.path) if args.path else None
    results = checker.check_all(path)
    
    # Fix violations if requested
    if args.fix:
        fixed = checker.fix_violations()
        print(f"Fixed {fixed} violations")
        
        # Re-run checks
        checker = CodeStandardsChecker(config_path)
        results = checker.check_all(path)
    
    # Generate report
    report = checker.generate_report(args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
    else:
        print(report)
    
    # Exit with error if failed
    sys.exit(0 if results.passed else 1)


if __name__ == '__main__':
    main()