"""
Helper utilities for migrating algorithms to use the enhanced base classes
and reduce code duplication.
"""

import ast
import inspect
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import re


class AlgorithmAnalyzer:
    """
    Analyzes algorithm implementations to identify opportunities
    for reducing code duplication.
    """
    
    def __init__(self):
        self.common_patterns = {
            'initialize': {
                'uniform_random': re.compile(
                    r'self\.position\s*=\s*np\.random\.uniform\(.*?\)',
                    re.MULTILINE | re.DOTALL
                ),
                'standard_init': re.compile(
                    r'def initialize\(self\).*?:\s*\n\s*self\.position\s*=.*?uniform.*?\n\s*self\.invalidate_fitness\(\)',
                    re.MULTILINE | re.DOTALL
                ),
            },
            'operators': {
                'levy_flight': re.compile(r'levy_flight|levy|Levy', re.IGNORECASE),
                'gaussian': re.compile(r'np\.random\.normal|gaussian', re.IGNORECASE),
                'cauchy': re.compile(r'cauchy|np\.random\.standard_cauchy', re.IGNORECASE),
            },
            'boundaries': {
                'clip': re.compile(r'np\.clip|clip\(', re.IGNORECASE),
                'reflect': re.compile(r'reflect|reflection', re.IGNORECASE),
            }
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """
        Analyze a single algorithm file for refactoring opportunities.
        
        Args:
            file_path: Path to the algorithm file
            
        Returns:
            Analysis results
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        results = {
            'file': str(file_path),
            'classes': self._find_classes(tree),
            'duplicated_patterns': self._find_patterns(content),
            'imports': self._analyze_imports(tree),
            'refactoring_suggestions': []
        }
        
        # Generate suggestions
        results['refactoring_suggestions'] = self._generate_suggestions(results)
        
        return results
    
    def _find_classes(self, tree: ast.Module) -> List[Dict]:
        """Find all classes and their base classes."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(f"{base.value.id}.{base.attr}")
                
                # Find methods
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'lines': item.end_lineno - item.lineno + 1 if hasattr(item, 'end_lineno') else 0
                        })
                
                classes.append({
                    'name': node.name,
                    'bases': base_classes,
                    'methods': methods,
                    'line': node.lineno
                })
        
        return classes
    
    def _find_patterns(self, content: str) -> Dict[str, List]:
        """Find common patterns in the code."""
        found_patterns = {}
        
        for category, patterns in self.common_patterns.items():
            found_patterns[category] = {}
            for name, pattern in patterns.items():
                matches = list(pattern.finditer(content))
                if matches:
                    found_patterns[category][name] = [
                        {
                            'line': content[:m.start()].count('\n') + 1,
                            'text': m.group()[:50] + '...' if len(m.group()) > 50 else m.group()
                        }
                        for m in matches
                    ]
        
        return found_patterns
    
    def _analyze_imports(self, tree: ast.Module) -> Dict[str, List[str]]:
        """Analyze imports to see what's being used."""
        imports = {
            'base_classes': [],
            'operators': [],
            'utilities': [],
            'other': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                
                if 'base' in module:
                    imports['base_classes'].extend(
                        alias.name for alias in node.names
                    )
                elif 'math_operators' in module or 'operators' in module:
                    imports['operators'].extend(
                        alias.name for alias in node.names
                    )
                elif 'utils' in module:
                    imports['utilities'].extend(
                        alias.name for alias in node.names
                    )
                else:
                    imports['other'].extend(
                        f"{module}.{alias.name}" for alias in node.names
                    )
        
        return imports
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """Generate refactoring suggestions based on analysis."""
        suggestions = []
        
        # Check for standard initialization pattern
        if 'initialize' in analysis['duplicated_patterns']:
            if 'standard_init' in analysis['duplicated_patterns']['initialize']:
                suggestions.append(
                    "Consider using IndividualWithDefaultInit base class "
                    "to inherit default initialization behavior"
                )
        
        # Check for operator usage
        operators = analysis['duplicated_patterns'].get('operators', {})
        if operators:
            if 'levy_flight' in operators and 'levy_flight' not in analysis['imports'].get('operators', []):
                suggestions.append(
                    "Import levy_flight from utils.math_operators instead of implementing locally"
                )
            if 'gaussian' in operators:
                suggestions.append(
                    "Consider using gaussian_mutation from utils.math_operators"
                )
        
        # Check for Individual classes that could be simplified
        for cls in analysis['classes']:
            if 'Individual' in cls['name']:
                # Count non-standard methods
                standard_methods = ['__init__', 'initialize', 'move']
                extra_methods = [m for m in cls['methods'] 
                               if m['name'] not in standard_methods]
                
                if not extra_methods:
                    suggestions.append(
                        f"Class {cls['name']} only has standard methods. "
                        "Consider using SimpleIndividual or dynamic creation"
                    )
        
        # Check for boundary handling
        if 'boundaries' in analysis['duplicated_patterns']:
            if 'clip' in analysis['duplicated_patterns']['boundaries']:
                suggestions.append(
                    "Use boundary_handling from utils.math_operators for consistent boundary handling"
                )
        
        return suggestions


def generate_migration_script(original_file: Path, output_file: Path) -> str:
    """
    Generate a migration script that refactors an algorithm to use
    enhanced base classes.
    
    Args:
        original_file: Path to original algorithm
        output_file: Path for refactored version
        
    Returns:
        Migration script as string
    """
    analyzer = AlgorithmAnalyzer()
    analysis = analyzer.analyze_file(original_file)
    
    # Read original content
    with open(original_file, 'r') as f:
        content = f.read()
    
    # Start building refactored version
    refactored_lines = []
    
    # Update imports
    refactored_lines.append('"""')
    refactored_lines.append(f'{original_file.stem} - Refactored Version')
    refactored_lines.append('')
    refactored_lines.append('This version uses enhanced base classes to reduce code duplication.')
    refactored_lines.append('"""')
    refactored_lines.append('')
    
    # Add necessary imports
    refactored_lines.append('import numpy as np')
    refactored_lines.append('import random')
    refactored_lines.append('from typing import Optional')
    refactored_lines.append('')
    refactored_lines.append('from algorithms.base_v2 import MetaheuristicAlgorithm, MoveContext')
    refactored_lines.append('from algorithms.base_v2_enhanced import IndividualWithDefaultInit')
    refactored_lines.append('from algorithms.validators import ParameterValidator')
    refactored_lines.append('from utils.math_operators import (')
    
    # Add commonly used operators
    operators = []
    if 'levy_flight' in str(analysis['duplicated_patterns']):
        operators.append('levy_flight')
    if 'gaussian' in str(analysis['duplicated_patterns']):
        operators.append('gaussian_mutation')
    if 'boundaries' in analysis['duplicated_patterns']:
        operators.append('boundary_handling')
    
    refactored_lines.append(f'    {", ".join(operators)}')
    refactored_lines.append(')')
    refactored_lines.append('')
    
    # Note: This is a simplified example. A full implementation would
    # need to parse and transform the AST properly.
    
    migration_script = '\n'.join(refactored_lines)
    
    # Add suggestions as comments
    migration_script += '\n\n# REFACTORING SUGGESTIONS:\n'
    for suggestion in analysis['refactoring_suggestions']:
        migration_script += f'# - {suggestion}\n'
    
    return migration_script


def batch_analyze_algorithms(algorithm_dir: Path) -> Dict[str, List[str]]:
    """
    Analyze all algorithms in a directory for refactoring opportunities.
    
    Args:
        algorithm_dir: Directory containing algorithm files
        
    Returns:
        Summary of refactoring opportunities
    """
    analyzer = AlgorithmAnalyzer()
    summary = {
        'standard_initialization_candidates': [],
        'operator_duplication': [],
        'simple_individual_candidates': [],
        'import_suggestions': []
    }
    
    # Analyze each Python file
    for file_path in algorithm_dir.glob('*_v2.py'):
        if file_path.stem.endswith('_test'):
            continue
            
        analysis = analyzer.analyze_file(file_path)
        
        # Categorize findings
        if any('IndividualWithDefaultInit' in s for s in analysis['refactoring_suggestions']):
            summary['standard_initialization_candidates'].append(str(file_path))
        
        if any('math_operators' in s for s in analysis['refactoring_suggestions']):
            summary['operator_duplication'].append(str(file_path))
        
        if any('SimpleIndividual' in s for s in analysis['refactoring_suggestions']):
            summary['simple_individual_candidates'].append(str(file_path))
    
    return summary


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_to_analyze = Path(sys.argv[1])
        analyzer = AlgorithmAnalyzer()
        results = analyzer.analyze_file(file_to_analyze)
        
        print(f"Analysis of {file_to_analyze.name}")
        print("=" * 50)
        print("\nClasses found:")
        for cls in results['classes']:
            print(f"  - {cls['name']} (extends {', '.join(cls['bases'])})")
        
        print("\nRefactoring suggestions:")
        for suggestion in results['refactoring_suggestions']:
            print(f"  - {suggestion}")
        
        print("\nDuplicated patterns found:")
        for category, patterns in results['duplicated_patterns'].items():
            if patterns:
                print(f"  {category}:")
                for pattern_name, occurrences in patterns.items():
                    print(f"    - {pattern_name}: {len(occurrences)} occurrences")
    else:
        # Batch analysis
        algorithm_dir = Path('algorithms')
        if algorithm_dir.exists():
            summary = batch_analyze_algorithms(algorithm_dir)
            
            print("Batch Analysis Summary")
            print("=" * 50)
            
            print(f"\nFiles that could use IndividualWithDefaultInit: {len(summary['standard_initialization_candidates'])}")
            for f in summary['standard_initialization_candidates'][:5]:
                print(f"  - {Path(f).name}")
            
            print(f"\nFiles with operator duplication: {len(summary['operator_duplication'])}")
            for f in summary['operator_duplication'][:5]:
                print(f"  - {Path(f).name}")
            
            print(f"\nFiles that could use SimpleIndividual: {len(summary['simple_individual_candidates'])}")
            for f in summary['simple_individual_candidates'][:5]:
                print(f"  - {Path(f).name}")