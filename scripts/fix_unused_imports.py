#!/usr/bin/env python3
"""
Script para eliminar imports no utilizados de forma segura.
Usa autoflake y isort para limpiar y organizar imports.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Set
import json
import ast


class UnusedImportFixer:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.fixed_files = []
        self.errors = []
        
    def check_dependencies(self):
        """Verifica que las herramientas necesarias estén instaladas."""
        tools = ['autoflake', 'isort']
        missing = []
        
        for tool in tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(tool)
        
        if missing:
            print(f"⚠️  Missing tools: {', '.join(missing)}")
            print("\nInstall with:")
            print("  pip install autoflake isort")
            return False
        
        return True
    
    def find_python_files(self, root_dir: Path = Path('.')) -> List[Path]:
        """Encuentra todos los archivos Python del proyecto."""
        py_files = []
        
        for file_path in root_dir.rglob('*.py'):
            # Filtrar archivos a ignorar
            if any(skip in str(file_path) for skip in [
                '.git', '__pycache__', 'venv', '.tox', 'legacy', 
                'deprecated', 'test_', 'conftest.py'
            ]):
                continue
            
            py_files.append(file_path)
        
        return sorted(py_files)
    
    def analyze_file_imports(self, file_path: Path) -> Dict[str, List[str]]:
        """Analiza imports no utilizados en un archivo."""
        unused = {'imports': [], 'from_imports': []}
        
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            # Recolectar nombres usados
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Verificar imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split('.')[0]
                        if name not in used_names:
                            unused['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            if alias.name != '*':
                                name = alias.asname or alias.name
                                if name not in used_names:
                                    unused['from_imports'].append(
                                        f"from {node.module} import {alias.name}"
                                    )
        
        except Exception as e:
            self.errors.append({'file': str(file_path), 'error': str(e)})
        
        return unused
    
    def fix_file_with_autoflake(self, file_path: Path) -> bool:
        """Usa autoflake para eliminar imports no utilizados."""
        cmd = [
            'autoflake',
            '--remove-all-unused-imports',
            '--remove-unused-variables',
            '--in-place' if not self.dry_run else '--check',
            str(file_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if self.dry_run and result.stdout:
                print(f"\n📝 Would fix: {file_path}")
                print(result.stdout)
                return True
            elif not self.dry_run and result.returncode == 0:
                self.fixed_files.append(file_path)
                return True
                
        except Exception as e:
            self.errors.append({'file': str(file_path), 'error': str(e)})
        
        return False
    
    def organize_imports_with_isort(self, file_path: Path) -> bool:
        """Usa isort para organizar imports."""
        cmd = [
            'isort',
            '--profile', 'black',
            '--line-length', '88',
            str(file_path)
        ]
        
        if self.dry_run:
            cmd.extend(['--check-only', '--diff'])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if self.dry_run and result.stdout:
                print(f"\n🔄 Would organize: {file_path}")
                print(result.stdout)
                return True
            elif not self.dry_run and result.returncode == 0:
                return True
                
        except Exception as e:
            self.errors.append({'file': str(file_path), 'error': str(e)})
        
        return False
    
    def fix_project_imports(self):
        """Ejecuta la limpieza de imports en todo el proyecto."""
        print("=" * 80)
        print("FIXING UNUSED IMPORTS")
        print("=" * 80)
        
        if not self.check_dependencies():
            return
        
        py_files = self.find_python_files()
        print(f"\nAnalyzing {len(py_files)} Python files...")
        
        files_with_issues = 0
        
        for file_path in py_files:
            # Primero analizar para detectar problemas
            unused = self.analyze_file_imports(file_path)
            
            if unused['imports'] or unused['from_imports']:
                files_with_issues += 1
                
                # Aplicar autoflake
                if self.fix_file_with_autoflake(file_path):
                    # Luego organizar con isort
                    self.organize_imports_with_isort(file_path)
        
        # Resumen
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if self.dry_run:
            print(f"\n[DRY RUN] Found issues in {files_with_issues} files")
            print("Run with --fix to apply changes")
        else:
            print(f"\n✅ Fixed {len(self.fixed_files)} files")
            
            if self.fixed_files:
                print("\nFixed files:")
                for f in self.fixed_files[:10]:
                    print(f"  - {f}")
                if len(self.fixed_files) > 10:
                    print(f"  ... and {len(self.fixed_files) - 10} more")
        
        if self.errors:
            print(f"\n❌ Errors in {len(self.errors)} files:")
            for err in self.errors[:5]:
                print(f"  - {err['file']}: {err['error']}")
    
    def generate_report(self):
        """Genera reporte de cambios."""
        report = {
            'fixed_files': [str(f) for f in self.fixed_files],
            'errors': self.errors,
            'dry_run': self.dry_run
        }
        
        report_path = Path('import_fixes_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix unused imports')
    parser.add_argument('--fix', action='store_true',
                       help='Apply fixes (default is dry run)')
    parser.add_argument('--path', type=str, default='.',
                       help='Path to analyze (default: current directory)')
    args = parser.parse_args()
    
    fixer = UnusedImportFixer(dry_run=not args.fix)
    fixer.fix_project_imports()
    
    if not args.fix:
        fixer.generate_report()


if __name__ == '__main__':
    main()