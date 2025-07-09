#!/usr/bin/env python3
"""
Analiza archivos masivos (1000+ líneas) y detecta duplicación de código.
"""

import os
from pathlib import Path
from collections import defaultdict
import ast
import hashlib
from typing import Dict, List, Tuple, Set


class LargeFileAnalyzer:
    def __init__(self, threshold: int = 1000):
        self.threshold = threshold
        self.large_files = []
        self.function_signatures = defaultdict(list)
        self.duplicate_candidates = []
        
    def analyze_directory(self, root_dir: Path) -> Dict[str, any]:
        """Analiza todos los archivos Python en el directorio."""
        print("=" * 80)
        print(f"ANALYZING LARGE FILES (>{self.threshold} lines)")
        print("=" * 80)
        
        # Encontrar archivos grandes
        for py_file in root_dir.rglob("*.py"):
            # Skip algunas carpetas
            if any(skip in str(py_file) for skip in ['.git', '__pycache__', 'venv', '.tox']):
                continue
            
            try:
                content = py_file.read_text()
                line_count = len(content.splitlines())
                
                if line_count >= self.threshold:
                    self.large_files.append({
                        'path': py_file,
                        'lines': line_count,
                        'size_kb': py_file.stat().st_size / 1024,
                        'functions': self._extract_functions(content, py_file)
                    })
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
        
        # Ordenar por tamaño
        self.large_files.sort(key=lambda x: x['lines'], reverse=True)
        
        # Analizar duplicación
        self._find_duplicates()
        
        return self._generate_report()
    
    def _extract_functions(self, content: str, filepath: Path) -> List[Dict]:
        """Extrae información de funciones/clases del archivo."""
        functions = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Calcular hash del cuerpo de la función
                    func_body = ast.unparse(node) if hasattr(ast, 'unparse') else ""
                    func_hash = hashlib.md5(func_body.encode()).hexdigest()[:8]
                    
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [d.id if isinstance(d, ast.Name) else str(d) 
                                     for d in node.decorator_list],
                        'hash': func_hash,
                        'file': str(filepath)
                    }
                    
                    functions.append(func_info)
                    
                    # Registrar para detección de duplicados
                    signature = f"{node.name}({','.join(func_info['args'])})"
                    self.function_signatures[signature].append({
                        'file': str(filepath),
                        'line': node.lineno,
                        'hash': func_hash
                    })
                    
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'type': 'class',
                        'methods': sum(1 for n in node.body if isinstance(n, ast.FunctionDef)),
                        'file': str(filepath)
                    }
                    functions.append(class_info)
                    
        except SyntaxError:
            print(f"Syntax error in {filepath}")
        
        return functions
    
    def _find_duplicates(self):
        """Encuentra funciones potencialmente duplicadas."""
        for signature, locations in self.function_signatures.items():
            if len(locations) > 1:
                # Agrupar por hash para encontrar duplicados exactos
                by_hash = defaultdict(list)
                for loc in locations:
                    by_hash[loc['hash']].append(loc)
                
                for hash_val, locs in by_hash.items():
                    if len(locs) > 1:
                        self.duplicate_candidates.append({
                            'signature': signature,
                            'hash': hash_val,
                            'locations': locs
                        })
    
    def _generate_report(self) -> Dict[str, any]:
        """Genera reporte del análisis."""
        print(f"\nFound {len(self.large_files)} large files (>={self.threshold} lines)")
        print("-" * 80)
        
        # Top 10 archivos más grandes
        print("\nTOP 10 LARGEST FILES:")
        for i, file_info in enumerate(self.large_files[:10]):
            rel_path = os.path.relpath(file_info['path'])
            print(f"{i+1:2d}. {rel_path}")
            print(f"    Lines: {file_info['lines']:,}")
            print(f"    Size: {file_info['size_kb']:.1f} KB")
            print(f"    Functions/Classes: {len(file_info['functions'])}")
            
            # Mostrar algunas funciones
            if file_info['functions']:
                print("    Key components:")
                for func in file_info['functions'][:5]:
                    if 'type' in func and func['type'] == 'class':
                        print(f"      - class {func['name']} ({func['methods']} methods)")
                    else:
                        print(f"      - {func['name']}() at line {func['line']}")
                if len(file_info['functions']) > 5:
                    print(f"      ... and {len(file_info['functions']) - 5} more")
            print()
        
        # Análisis por categoría
        print("\nFILE CATEGORIES:")
        categories = defaultdict(list)
        for file_info in self.large_files:
            path = str(file_info['path'])
            if 'test' in path:
                categories['tests'].append(file_info)
            elif 'utils' in path:
                categories['utilities'].append(file_info)
            elif 'algorithms' in path:
                categories['algorithms'].append(file_info)
            elif 'scripts' in path:
                categories['scripts'].append(file_info)
            else:
                categories['other'].append(file_info)
        
        for category, files in categories.items():
            total_lines = sum(f['lines'] for f in files)
            print(f"\n{category.upper()}: {len(files)} files, {total_lines:,} total lines")
            for f in files[:3]:
                rel_path = os.path.relpath(f['path'])
                print(f"  - {rel_path} ({f['lines']:,} lines)")
            if len(files) > 3:
                print(f"  ... and {len(files) - 3} more")
        
        # Duplicación detectada
        if self.duplicate_candidates:
            print("\n" + "=" * 80)
            print("POTENTIAL DUPLICATE FUNCTIONS:")
            print("-" * 80)
            
            for dup in self.duplicate_candidates[:10]:
                print(f"\nDuplicate: {dup['signature']}")
                print(f"Hash: {dup['hash']}")
                print("Found in:")
                for loc in dup['locations']:
                    rel_path = os.path.relpath(loc['file'])
                    print(f"  - {rel_path}:{loc['line']}")
        
        # Recomendaciones
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("-" * 80)
        
        recommendations = []
        
        # Archivos extremadamente grandes
        very_large = [f for f in self.large_files if f['lines'] > 2000]
        if very_large:
            recommendations.append({
                'issue': 'Extremely large files',
                'files': very_large,
                'action': 'Split into smaller, focused modules'
            })
        
        # Muchas funciones duplicadas
        if len(self.duplicate_candidates) > 10:
            recommendations.append({
                'issue': f'{len(self.duplicate_candidates)} duplicate functions detected',
                'action': 'Extract common functions to shared modules'
            })
        
        # Tests muy grandes
        large_tests = [f for f in categories.get('tests', []) if f['lines'] > 1500]
        if large_tests:
            recommendations.append({
                'issue': 'Large test files',
                'files': large_tests,
                'action': 'Split tests by functionality or use parametrization'
            })
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['issue']}")
            print(f"   Action: {rec['action']}")
            if 'files' in rec:
                print("   Affected files:")
                for f in rec['files'][:3]:
                    rel_path = os.path.relpath(f['path'])
                    print(f"   - {rel_path} ({f['lines']:,} lines)")
        
        # Estadísticas finales
        total_large_lines = sum(f['lines'] for f in self.large_files)
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS:")
        print("-" * 80)
        print(f"Total large files: {len(self.large_files)}")
        print(f"Total lines in large files: {total_large_lines:,}")
        print(f"Average lines per large file: {total_large_lines // len(self.large_files) if self.large_files else 0:,}")
        print(f"Duplicate function signatures: {len(self.duplicate_candidates)}")
        
        return {
            'large_files': self.large_files,
            'categories': dict(categories),
            'duplicates': self.duplicate_candidates,
            'recommendations': recommendations,
            'statistics': {
                'total_files': len(self.large_files),
                'total_lines': total_large_lines,
                'duplicate_functions': len(self.duplicate_candidates)
            }
        }


def main():
    analyzer = LargeFileAnalyzer(threshold=1000)
    results = analyzer.analyze_directory(Path('.'))
    
    # Guardar reporte detallado
    report_path = Path('large_files_analysis.md')
    with open(report_path, 'w') as f:
        f.write("# Large Files Analysis Report\n\n")
        f.write(f"Generated: {Path.cwd()}\n\n")
        
        f.write("## Files Over 1000 Lines\n\n")
        for file_info in results['large_files']:
            rel_path = os.path.relpath(file_info['path'])
            f.write(f"### {rel_path}\n")
            f.write(f"- Lines: {file_info['lines']:,}\n")
            f.write(f"- Size: {file_info['size_kb']:.1f} KB\n")
            f.write(f"- Components: {len(file_info['functions'])}\n\n")
    
    print(f"\n\nDetailed report saved to: {report_path}")


if __name__ == '__main__':
    main()