#!/usr/bin/env python3
"""
Script para consolidar las utilidades de benchmarking duplicadas.
Combina benchmarking.py y benchmarking_v2.py en una versión unificada.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import difflib


class BenchmarkingConsolidator:
    def __init__(self):
        self.benchmarking_v1 = Path("utils/benchmarking.py")
        self.benchmarking_v2 = Path("utils/benchmarking_v2.py")
        self.functions_v1 = {}
        self.functions_v2 = {}
        self.classes_v1 = {}
        self.classes_v2 = {}
        self.imports_v1 = []
        self.imports_v2 = []
        
    def analyze_files(self):
        """Analiza ambos archivos para encontrar duplicación."""
        print("=" * 80)
        print("ANALYZING BENCHMARKING FILES")
        print("=" * 80)
        
        # Analizar v1
        if self.benchmarking_v1.exists():
            content_v1 = self.benchmarking_v1.read_text()
            self._analyze_content(content_v1, "v1")
            print(f"\n{self.benchmarking_v1}:")
            print(f"  - Functions: {len(self.functions_v1)}")
            print(f"  - Classes: {len(self.classes_v1)}")
            print(f"  - Lines: {len(content_v1.splitlines())}")
        
        # Analizar v2
        if self.benchmarking_v2.exists():
            content_v2 = self.benchmarking_v2.read_text()
            self._analyze_content(content_v2, "v2")
            print(f"\n{self.benchmarking_v2}:")
            print(f"  - Functions: {len(self.functions_v2)}")
            print(f"  - Classes: {len(self.classes_v2)}")
            print(f"  - Lines: {len(content_v2.splitlines())}")
        
        # Encontrar duplicación
        self._find_duplication()
        
    def _analyze_content(self, content: str, version: str):
        """Analiza el contenido de un archivo."""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if version == "v1":
                        self.functions_v1[node.name] = {
                            'line': node.lineno,
                            'args': [arg.arg for arg in node.args.args],
                            'decorators': [d.id if isinstance(d, ast.Name) else str(d) 
                                         for d in node.decorator_list]
                        }
                    else:
                        self.functions_v2[node.name] = {
                            'line': node.lineno,
                            'args': [arg.arg for arg in node.args.args],
                            'decorators': [d.id if isinstance(d, ast.Name) else str(d) 
                                         for d in node.decorator_list]
                        }
                
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    if version == "v1":
                        self.classes_v1[node.name] = {
                            'line': node.lineno,
                            'methods': methods,
                            'bases': [b.id if isinstance(b, ast.Name) else str(b) 
                                    for b in node.bases]
                        }
                    else:
                        self.classes_v2[node.name] = {
                            'line': node.lineno,
                            'methods': methods,
                            'bases': [b.id if isinstance(b, ast.Name) else str(b) 
                                    for b in node.bases]
                        }
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if version == "v1":
                        self.imports_v1.append(ast.unparse(node))
                    else:
                        self.imports_v2.append(ast.unparse(node))
                        
        except SyntaxError as e:
            print(f"Syntax error in {version}: {e}")
    
    def _find_duplication(self):
        """Encuentra elementos duplicados entre versiones."""
        print("\n" + "=" * 80)
        print("DUPLICATION ANALYSIS")
        print("=" * 80)
        
        # Funciones duplicadas
        common_functions = set(self.functions_v1.keys()) & set(self.functions_v2.keys())
        if common_functions:
            print(f"\nDuplicate functions ({len(common_functions)}):")
            for func in sorted(common_functions):
                args_v1 = self.functions_v1[func]['args']
                args_v2 = self.functions_v2[func]['args']
                if args_v1 == args_v2:
                    print(f"  - {func}() [identical signature]")
                else:
                    print(f"  - {func}() [different args: v1={args_v1}, v2={args_v2}]")
        
        # Clases duplicadas
        common_classes = set(self.classes_v1.keys()) & set(self.classes_v2.keys())
        if common_classes:
            print(f"\nDuplicate classes ({len(common_classes)}):")
            for cls in sorted(common_classes):
                methods_v1 = set(self.classes_v1[cls]['methods'])
                methods_v2 = set(self.classes_v2[cls]['methods'])
                common_methods = methods_v1 & methods_v2
                print(f"  - {cls} ({len(common_methods)} common methods)")
        
        # Funciones únicas
        unique_v1 = set(self.functions_v1.keys()) - set(self.functions_v2.keys())
        unique_v2 = set(self.functions_v2.keys()) - set(self.functions_v1.keys())
        
        if unique_v1:
            print(f"\nUnique to v1 ({len(unique_v1)}):")
            for func in sorted(unique_v1)[:10]:
                print(f"  - {func}()")
            if len(unique_v1) > 10:
                print(f"  ... and {len(unique_v1) - 10} more")
        
        if unique_v2:
            print(f"\nUnique to v2 ({len(unique_v2)}):")
            for func in sorted(unique_v2)[:10]:
                print(f"  - {func}()")
            if len(unique_v2) > 10:
                print(f"  ... and {len(unique_v2) - 10} more")
    
    def generate_consolidation_plan(self):
        """Genera plan de consolidación."""
        print("\n" + "=" * 80)
        print("CONSOLIDATION PLAN")
        print("=" * 80)
        
        # Calcular estadísticas
        total_functions = len(set(self.functions_v1.keys()) | set(self.functions_v2.keys()))
        duplicate_functions = len(set(self.functions_v1.keys()) & set(self.functions_v2.keys()))
        
        print(f"\nTotal unique functions: {total_functions}")
        print(f"Duplicate functions: {duplicate_functions}")
        print(f"Potential reduction: {duplicate_functions} functions")
        
        # Plan de acción
        print("\nRecommended actions:")
        print("1. Create utils/benchmarking_unified.py with:")
        print("   - All unique functions from both versions")
        print("   - Best implementation of duplicate functions")
        print("   - Consolidated imports")
        
        print("\n2. Key consolidations:")
        
        # Analizar clases principales
        if "BenchmarkRunner" in self.classes_v1 or "BenchmarkRunner" in self.classes_v2:
            print("   - Merge BenchmarkRunner implementations")
        
        if "MetadataEnhancedBenchmark" in self.classes_v2:
            print("   - Integrate MetadataEnhancedBenchmark into main class")
        
        print("\n3. Migration strategy:")
        print("   - Update all imports to use unified version")
        print("   - Add deprecation warnings to old files")
        print("   - Move old files to legacy/ after verification")
        
        # Generar esquema de archivo unificado
        self._generate_unified_structure()
    
    def _generate_unified_structure(self):
        """Genera estructura propuesta para archivo unificado."""
        print("\n" + "=" * 80)
        print("PROPOSED UNIFIED STRUCTURE")
        print("=" * 80)
        
        structure = """
# utils/benchmarking_unified.py

\"\"\"
Unified benchmarking utilities for BioAlgoCompare.
Consolidates functionality from benchmarking.py and benchmarking_v2.py.
\"\"\"

# Imports (consolidated and deduplicated)
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
...

# Core Classes
class UnifiedBenchmarkRunner:
    \"\"\"Combines BenchmarkRunner with MetadataEnhancedBenchmark.\"\"\"
    
    def __init__(self, capture_metadata=True):
        # Unified initialization
        pass
    
    def run_benchmark(self, algorithms, problems, **kwargs):
        # Main benchmark method with optional metadata
        pass
    
    def run_parallel(self, ...):
        # Parallel execution support
        pass

# Utility Functions (deduplicated)
def calculate_statistics(...):
    # Best implementation from either version
    pass

def export_results(...):
    # Unified export functionality
    pass

# Backward compatibility
BenchmarkRunner = UnifiedBenchmarkRunner  # Alias for compatibility
MetadataEnhancedBenchmark = UnifiedBenchmarkRunner  # Alias
"""
        print(structure)
        
        # Guardar plan
        plan_path = Path("benchmarking_consolidation_plan.md")
        with open(plan_path, 'w') as f:
            f.write("# Benchmarking Consolidation Plan\n\n")
            f.write("## Analysis Summary\n\n")
            f.write(f"- benchmarking.py: {len(self.functions_v1)} functions, {len(self.classes_v1)} classes\n")
            f.write(f"- benchmarking_v2.py: {len(self.functions_v2)} functions, {len(self.classes_v2)} classes\n")
            f.write(f"- Duplicate functions: {len(set(self.functions_v1.keys()) & set(self.functions_v2.keys()))}\n")
            f.write("\n## Proposed Structure\n\n")
            f.write("```python\n")
            f.write(structure)
            f.write("```\n")
        
        print(f"\nDetailed plan saved to: {plan_path}")


def main():
    consolidator = BenchmarkingConsolidator()
    consolidator.analyze_files()
    consolidator.generate_consolidation_plan()


if __name__ == '__main__':
    main()