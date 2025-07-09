#!/usr/bin/env python3
"""
Script maestro para organizar y limpiar todos los imports del proyecto.
Ejecuta análisis, limpieza y reorganización de imports.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime


class ImportOrganizer:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'analyses': {},
            'fixes': {},
            'errors': []
        }
        
    def run_full_cleanup(self):
        """Ejecuta limpieza completa de imports."""
        print("=" * 80)
        print("IMPORT ORGANIZATION AND CLEANUP")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print("=" * 80)
        
        # 1. Análisis de imports
        print("\n📊 Phase 1: Import Analysis")
        self._run_import_analysis()
        
        # 2. Detección de dependencias circulares
        print("\n🔄 Phase 2: Circular Dependency Detection")
        self._run_circular_detection()
        
        # 3. Limpieza de imports no usados
        print("\n🧹 Phase 3: Unused Import Cleanup")
        self._run_unused_cleanup()
        
        # 4. Organización de imports
        print("\n📐 Phase 4: Import Organization")
        self._run_import_organization()
        
        # 5. Verificación final
        print("\n✅ Phase 5: Final Verification")
        self._run_verification()
        
        # Generar reporte final
        self._generate_final_report()
    
    def _run_import_analysis(self):
        """Ejecuta análisis de imports."""
        try:
            cmd = ['python', 'scripts/analyze_imports.py']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Import analysis completed")
                self.results['analyses']['imports'] = 'Success'
                
                # Leer resultados si existen
                report_path = Path('import_analysis_report.json')
                if report_path.exists():
                    with open(report_path) as f:
                        data = json.load(f)
                        print(f"  - Total modules: {data['statistics']['total_modules']}")
                        print(f"  - Circular dependencies: {data['statistics']['circular_dependencies']}")
                        print(f"  - Star imports: {data['statistics']['star_imports']}")
                        print(f"  - Unused imports: {data['statistics']['unused_imports']}")
            else:
                print("❌ Import analysis failed")
                self.results['errors'].append({
                    'phase': 'import_analysis',
                    'error': result.stderr
                })
                
        except Exception as e:
            print(f"❌ Error during import analysis: {e}")
            self.results['errors'].append({
                'phase': 'import_analysis',
                'error': str(e)
            })
    
    def _run_circular_detection(self):
        """Ejecuta detección de dependencias circulares."""
        try:
            cmd = ['python', 'scripts/fix_circular_dependencies.py']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Circular dependency analysis completed")
                self.results['analyses']['circular'] = 'Success'
                
                # Leer resultados
                report_path = Path('circular_dependencies_report.json')
                if report_path.exists():
                    with open(report_path) as f:
                        data = json.load(f)
                        print(f"  - Total cycles: {data['total_cycles']}")
                        print(f"  - Affected modules: {data['affected_modules']}")
                        
                        if data['total_cycles'] > 0:
                            print("\n  ⚠️  Action required: Review generated refactoring scripts")
            else:
                print("❌ Circular dependency detection failed")
                self.results['errors'].append({
                    'phase': 'circular_detection',
                    'error': result.stderr
                })
                
        except Exception as e:
            print(f"❌ Error during circular detection: {e}")
            self.results['errors'].append({
                'phase': 'circular_detection',
                'error': str(e)
            })
    
    def _run_unused_cleanup(self):
        """Ejecuta limpieza de imports no usados."""
        try:
            cmd = ['python', 'scripts/fix_unused_imports.py']
            if not self.dry_run:
                cmd.append('--fix')
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Unused import cleanup completed")
                self.results['fixes']['unused'] = 'Success'
                
                # Mostrar algunos resultados
                if self.dry_run:
                    # Contar archivos con problemas en el output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Found issues in' in line:
                            print(f"  - {line.strip()}")
                else:
                    for line in result.stdout.split('\n'):
                        if 'Fixed' in line and 'files' in line:
                            print(f"  - {line.strip()}")
            else:
                print("❌ Unused import cleanup failed")
                self.results['errors'].append({
                    'phase': 'unused_cleanup',
                    'error': result.stderr
                })
                
        except Exception as e:
            print(f"❌ Error during unused cleanup: {e}")
            self.results['errors'].append({
                'phase': 'unused_cleanup',
                'error': str(e)
            })
    
    def _run_import_organization(self):
        """Organiza imports con isort."""
        try:
            # Configurar isort
            isort_config = [
                'isort',
                '.',
                '--profile', 'black',
                '--line-length', '88',
                '--multi-line', '3',
                '--trailing-comma',
                '--force-grid-wrap', '0',
                '--use-parentheses',
                '--ensure-newline-before-comments'
            ]
            
            if self.dry_run:
                isort_config.extend(['--check-only', '--diff'])
            
            result = subprocess.run(isort_config, capture_output=True, text=True)
            
            if result.returncode == 0 or (self.dry_run and result.stdout):
                print("✅ Import organization completed")
                self.results['fixes']['organization'] = 'Success'
                
                if self.dry_run and result.stdout:
                    # Contar archivos que serían modificados
                    files = set()
                    for line in result.stdout.split('\n'):
                        if line.startswith('---') or line.startswith('+++'):
                            if '/' in line:
                                files.add(line.split()[1])
                    print(f"  - Would organize {len(files)} files")
                elif not self.dry_run:
                    print("  - All imports organized according to standards")
            else:
                print("❌ Import organization failed")
                if result.stderr:
                    self.results['errors'].append({
                        'phase': 'import_organization',
                        'error': result.stderr
                    })
                    
        except Exception as e:
            print(f"❌ Error during import organization: {e}")
            self.results['errors'].append({
                'phase': 'import_organization',
                'error': str(e)
            })
    
    def _run_verification(self):
        """Verifica el estado final de los imports."""
        try:
            # Ejecutar análisis rápido para verificar
            cmd = ['python', '-m', 'py_compile']
            
            # Verificar algunos archivos clave
            test_files = [
                'algorithms/__init__.py',
                'utils/__init__.py',
                'problems/__init__.py'
            ]
            
            all_good = True
            for file in test_files:
                if Path(file).exists():
                    result = subprocess.run(cmd + [file], capture_output=True)
                    if result.returncode != 0:
                        all_good = False
                        print(f"  ❌ Syntax error in {file}")
            
            if all_good:
                print("  ✅ All test files compile successfully")
                self.results['verification'] = 'Success'
            else:
                self.results['verification'] = 'Failed'
                
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            self.results['errors'].append({
                'phase': 'verification',
                'error': str(e)
            })
    
    def _generate_final_report(self):
        """Genera reporte final consolidado."""
        print("\n" + "=" * 80)
        print("FINAL REPORT")
        print("=" * 80)
        
        # Resumen de resultados
        successful = sum(1 for phase in self.results['analyses'].values() 
                        if phase == 'Success')
        successful += sum(1 for phase in self.results['fixes'].values() 
                         if phase == 'Success')
        
        print(f"\n📊 Summary:")
        print(f"  - Mode: {'DRY RUN' if self.dry_run else 'EXECUTED'}")
        print(f"  - Successful phases: {successful}")
        print(f"  - Errors: {len(self.results['errors'])}")
        
        # Archivos de reporte generados
        print(f"\n📄 Generated reports:")
        reports = [
            'import_analysis_report.json',
            'circular_dependencies_report.json',
            'circular_dependencies_analysis.md'
        ]
        
        for report in reports:
            if Path(report).exists():
                print(f"  - {report}")
        
        # Próximos pasos
        print(f"\n🎯 Next steps:")
        
        if self.dry_run:
            print("  1. Review the analysis results")
            print("  2. Run with --execute to apply fixes")
            print("  3. Review and apply circular dependency refactoring scripts")
        else:
            print("  1. Review changes with git diff")
            print("  2. Run tests to ensure nothing broke")
            print("  3. Apply circular dependency refactoring if needed")
        
        # Guardar reporte final
        report_path = Path('import_cleanup_final_report.json')
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Final report saved to: {report_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Organize and clean project imports')
    parser.add_argument('--execute', action='store_true',
                       help='Execute cleanup (default is dry run)')
    args = parser.parse_args()
    
    organizer = ImportOrganizer(dry_run=not args.execute)
    organizer.run_full_cleanup()


if __name__ == '__main__':
    main()