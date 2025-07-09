#!/usr/bin/env python3
"""
Script para limpiar y organizar archivos deprecated.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class DeprecatedCleaner:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.deprecated_dirs = []
        self.deprecated_files = []
        self.total_size = 0
        self.total_lines = 0
        
    def find_deprecated(self, root_dir: Path = Path('.')):
        """Encuentra todos los archivos y directorios deprecated."""
        print("=" * 80)
        print("SEARCHING FOR DEPRECATED FILES")
        print("=" * 80)
        
        # Buscar directorios deprecated
        for path in root_dir.rglob('*'):
            if path.is_dir() and 'deprecated' in path.name.lower():
                self.deprecated_dirs.append(path)
                # Contar archivos dentro
                py_files = list(path.glob('**/*.py'))
                self.deprecated_files.extend(py_files)
        
        # Buscar archivos individuales deprecated
        for path in root_dir.rglob('*.py'):
            if 'deprecated' in path.name.lower() and path not in self.deprecated_files:
                self.deprecated_files.append(path)
        
        # Calcular estadísticas
        for file_path in self.deprecated_files:
            try:
                self.total_size += file_path.stat().st_size
                self.total_lines += len(file_path.read_text().splitlines())
            except:
                pass
        
        self._print_summary()
        
    def _print_summary(self):
        """Imprime resumen de archivos encontrados."""
        print(f"\nFound {len(self.deprecated_dirs)} deprecated directories:")
        for dir_path in sorted(self.deprecated_dirs):
            rel_path = os.path.relpath(dir_path)
            file_count = len(list(dir_path.glob('**/*.py')))
            print(f"  - {rel_path} ({file_count} Python files)")
        
        print(f"\nTotal deprecated files: {len(self.deprecated_files)}")
        print(f"Total size: {self.total_size / 1024:.1f} KB")
        print(f"Total lines: {self.total_lines:,}")
        
        # Mostrar algunos archivos
        if self.deprecated_files:
            print("\nSample deprecated files:")
            for file_path in sorted(self.deprecated_files)[:10]:
                rel_path = os.path.relpath(file_path)
                size_kb = file_path.stat().st_size / 1024
                print(f"  - {rel_path} ({size_kb:.1f} KB)")
            
            if len(self.deprecated_files) > 10:
                print(f"  ... and {len(self.deprecated_files) - 10} more")
    
    def analyze_usage(self):
        """Analiza si los archivos deprecated están siendo usados."""
        print("\n" + "=" * 80)
        print("USAGE ANALYSIS")
        print("=" * 80)
        
        # Buscar imports de archivos deprecated
        imports_found = []
        
        # Archivos a verificar
        py_files = list(Path('.').rglob('*.py'))
        
        for py_file in py_files:
            # Skip el archivo deprecated mismo
            if py_file in self.deprecated_files:
                continue
            
            try:
                content = py_file.read_text()
                
                # Buscar imports
                for deprecated_file in self.deprecated_files:
                    # Construir posibles patrones de import
                    module_path = str(deprecated_file.with_suffix('')).replace('/', '.')
                    patterns = [
                        f"from {module_path} import",
                        f"import {module_path}",
                        f'"{module_path}"',
                        f"'{module_path}'"
                    ]
                    
                    for pattern in patterns:
                        if pattern in content:
                            imports_found.append({
                                'file': py_file,
                                'imports': deprecated_file,
                                'pattern': pattern
                            })
                            break
            except:
                pass
        
        if imports_found:
            print(f"\n⚠️  WARNING: Found {len(imports_found)} imports of deprecated files:")
            for imp in imports_found[:10]:
                print(f"  - {os.path.relpath(imp['file'])} imports {os.path.relpath(imp['imports'])}")
            
            if len(imports_found) > 10:
                print(f"  ... and {len(imports_found) - 10} more")
            
            print("\nThese imports must be updated before removing deprecated files!")
        else:
            print("\n✅ No imports of deprecated files found. Safe to proceed.")
        
        return len(imports_found) == 0
    
    def create_cleanup_plan(self):
        """Crea plan de limpieza."""
        print("\n" + "=" * 80)
        print("CLEANUP PLAN")
        print("=" * 80)
        
        # Crear estructura de legacy
        legacy_root = Path('legacy/deprecated_archive')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print("\nProposed actions:")
        print(f"1. Create archive: {legacy_root}/{timestamp}/")
        print("2. Move deprecated files preserving structure")
        print("3. Create index of archived files")
        print("4. Remove empty deprecated directories")
        
        # Generar comandos
        if not self.dry_run:
            self._execute_cleanup(legacy_root / timestamp)
        else:
            print("\n[DRY RUN] No changes made. Use --execute to perform cleanup.")
    
    def _execute_cleanup(self, archive_dir: Path):
        """Ejecuta la limpieza."""
        print("\nExecuting cleanup...")
        
        # Crear directorio de archivo
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear índice
        index_path = archive_dir / 'INDEX.md'
        with open(index_path, 'w') as f:
            f.write(f"# Deprecated Files Archive\n\n")
            f.write(f"Archived on: {datetime.now()}\n\n")
            f.write(f"## Summary\n")
            f.write(f"- Total files: {len(self.deprecated_files)}\n")
            f.write(f"- Total size: {self.total_size / 1024:.1f} KB\n")
            f.write(f"- Total lines: {self.total_lines:,}\n\n")
            f.write("## Archived Files\n\n")
            
            # Mover archivos
            moved_count = 0
            for file_path in self.deprecated_files:
                rel_path = os.path.relpath(file_path)
                dest_path = archive_dir / rel_path
                
                try:
                    # Crear directorio destino
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Mover archivo
                    shutil.move(str(file_path), str(dest_path))
                    
                    # Añadir al índice
                    f.write(f"- {rel_path}\n")
                    moved_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Error moving {rel_path}: {e}")
            
            f.write(f"\n\nTotal archived: {moved_count} files\n")
        
        # Eliminar directorios vacíos
        for dir_path in self.deprecated_dirs:
            try:
                if dir_path.exists() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"  ✅ Removed empty directory: {dir_path}")
            except:
                pass
        
        print(f"\n✅ Cleanup complete! Archived {moved_count} files to {archive_dir}")
        print(f"📄 Index created at: {index_path}")
    
    def generate_report(self):
        """Genera reporte de limpieza."""
        report_path = Path('deprecated_cleanup_report.md')
        
        with open(report_path, 'w') as f:
            f.write("# Deprecated Files Cleanup Report\n\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            
            f.write("## Statistics\n")
            f.write(f"- Deprecated directories: {len(self.deprecated_dirs)}\n")
            f.write(f"- Deprecated files: {len(self.deprecated_files)}\n")
            f.write(f"- Total size: {self.total_size / 1024:.1f} KB\n")
            f.write(f"- Total lines: {self.total_lines:,}\n\n")
            
            f.write("## Deprecated Directories\n")
            for dir_path in sorted(self.deprecated_dirs):
                f.write(f"- {os.path.relpath(dir_path)}\n")
            
            f.write("\n## Impact\n")
            f.write(f"Removing deprecated files will:\n")
            f.write(f"- Free up {self.total_size / 1024:.1f} KB\n")
            f.write(f"- Remove {self.total_lines:,} lines of obsolete code\n")
            f.write(f"- Simplify project structure\n")
        
        print(f"\nReport saved to: {report_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Clean up deprecated files')
    parser.add_argument('--execute', action='store_true', 
                       help='Execute cleanup (default is dry run)')
    args = parser.parse_args()
    
    cleaner = DeprecatedCleaner(dry_run=not args.execute)
    cleaner.find_deprecated()
    
    # Verificar uso
    safe_to_proceed = cleaner.analyze_usage()
    
    if safe_to_proceed:
        cleaner.create_cleanup_plan()
    else:
        print("\n⚠️  Cannot proceed: deprecated files are still in use!")
    
    cleaner.generate_report()


if __name__ == '__main__':
    main()