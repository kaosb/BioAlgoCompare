#!/usr/bin/env python3
"""
Script de migración al sistema unificado de resultados.

Ayuda a migrar código que usa sistemas antiguos (ExperimentTracker,
ResultIntegration, etc.) al nuevo sistema unificado basado en
StandardResultV2 y ResultPipeline.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any
import ast
import argparse


class ResultSystemMigrator:
    """Migrador para actualizar código al sistema unificado de resultados."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.changes_made = []
        
        # Mapeo de imports antiguos a nuevos
        self.import_mappings = {
            # ExperimentTracker → Pipeline
            'from utils.experiment_tracker import ExperimentTracker': 
                'from utils.results import ResultPipeline',
            'from utils.experiment_tracker import ExperimentRecord':
                'from utils.results import StandardResultV2',
            
            # ResultIntegration → Pipeline
            'from utils.result_integration import ResultIntegration':
                'from utils.results import ResultPipeline',
            
            # ResultsDatabase directo → via Pipeline
            'from utils.results_database import ResultsDatabase':
                'from utils.results import ResultPipeline',
            
            # StandardResult v1 → v2
            'from utils.result_schema import StandardResult':
                'from utils.results import StandardResultV2',
            
            # Imports más específicos
            'import utils.experiment_tracker':
                'import utils.results',
            'import utils.result_integration':
                'import utils.results',
        }
        
        # Mapeo de clases/funciones
        self.class_mappings = {
            'ExperimentTracker': 'ResultPipeline',
            'ExperimentRecord': 'StandardResultV2',
            'ResultIntegration': 'ResultPipeline',
            'StandardResult': 'StandardResultV2',
        }
        
        # Mapeo de métodos
        self.method_mappings = {
            # ExperimentTracker methods
            'start_experiment': 'process',
            'end_experiment': 'process',
            'log_iteration': None,  # No longer needed
            'save_experiment': 'save',
            'load_experiment': 'load',
            
            # ResultIntegration methods
            'integrate_results': 'process',
            'convert_to_standard': 'process',
        }
    
    def migrate_file(self, filepath: Path) -> bool:
        """
        Migra un archivo Python al nuevo sistema.
        
        Args:
            filepath: Ruta del archivo a migrar
            
        Returns:
            True si se hicieron cambios
        """
        try:
            content = filepath.read_text()
            original_content = content
            
            # 1. Actualizar imports
            for old_import, new_import in self.import_mappings.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    self.changes_made.append(
                        f"{filepath}: Updated import '{old_import}' → '{new_import}'"
                    )
            
            # 2. Actualizar nombres de clases
            for old_class, new_class in self.class_mappings.items():
                # Patrón para instanciación
                pattern = rf'\b{old_class}\s*\('
                replacement = f'{new_class}('
                content = re.sub(pattern, replacement, content)
                
                # Patrón para type hints
                pattern = rf':\s*{old_class}\b'
                replacement = f': {new_class}'
                content = re.sub(pattern, replacement, content)
            
            # 3. Actualizar llamadas a métodos
            content = self._update_method_calls(content)
            
            # 4. Añadir comentarios de migración
            if content != original_content:
                # Añadir comentario al inicio del archivo
                migration_comment = (
                    "# MIGRATION NOTE: This file has been updated to use the unified result system.\n"
                    "# Old imports from experiment_tracker, result_integration, etc. have been replaced.\n"
                    "# Please review the changes and update any custom logic as needed.\n\n"
                )
                
                if not content.startswith("# MIGRATION NOTE:"):
                    content = migration_comment + content
            
            # 5. Guardar cambios
            if content != original_content:
                if not self.dry_run:
                    # Backup original
                    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
                    filepath.rename(backup_path)
                    
                    # Write migrated content
                    filepath.write_text(content)
                    
                    self.changes_made.append(f"{filepath}: File migrated successfully")
                else:
                    self.changes_made.append(f"{filepath}: Would be migrated (dry run)")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error migrating {filepath}: {e}")
            return False
    
    def _update_method_calls(self, content: str) -> str:
        """Actualiza llamadas a métodos obsoletos."""
        # Ejemplo: tracker.start_experiment() → pipeline.process()
        patterns = [
            (r'tracker\.start_experiment\([^)]*\)', 'pipeline.process(result)'),
            (r'tracker\.end_experiment\([^)]*\)', 'pipeline.process(result)'),
            (r'integration\.integrate_results\([^)]*\)', 'pipeline.process(result)'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def find_files_to_migrate(self, root_dir: Path) -> List[Path]:
        """
        Encuentra archivos que necesitan migración.
        
        Args:
            root_dir: Directorio raíz para buscar
            
        Returns:
            Lista de archivos que usan sistemas antiguos
        """
        files_to_migrate = []
        
        # Patrones que indican uso de sistemas antiguos
        old_patterns = [
            'ExperimentTracker',
            'ExperimentRecord',
            'ResultIntegration',
            'experiment_tracker',
            'result_integration',
        ]
        
        for py_file in root_dir.rglob('*.py'):
            # Skip migration scripts and backups
            if 'migrate' in str(py_file) or py_file.suffix == '.backup':
                continue
            
            try:
                content = py_file.read_text()
                for pattern in old_patterns:
                    if pattern in content:
                        files_to_migrate.append(py_file)
                        break
            except:
                pass
        
        return files_to_migrate
    
    def generate_migration_report(self) -> str:
        """Genera reporte de migración."""
        report = ["=" * 80]
        report.append("MIGRATION REPORT - Unified Result System")
        report.append("=" * 80)
        report.append("")
        
        if self.dry_run:
            report.append("MODE: DRY RUN (no changes made)")
        else:
            report.append("MODE: LIVE (changes applied)")
        
        report.append("")
        report.append(f"Total changes: {len(self.changes_made)}")
        report.append("")
        
        if self.changes_made:
            report.append("Changes made:")
            for change in self.changes_made:
                report.append(f"  - {change}")
        else:
            report.append("No changes needed.")
        
        report.append("")
        report.append("=" * 80)
        
        # Add migration guide
        report.append("\nMIGRATION GUIDE:")
        report.append("-" * 40)
        report.append("\nKey changes to review:")
        report.append("1. ExperimentTracker → ResultPipeline")
        report.append("2. ExperimentRecord → StandardResultV2")
        report.append("3. Manual result creation → Automatic via pipeline")
        report.append("4. Separate tracking/storage → Unified pipeline")
        report.append("\nExample usage:")
        report.append("```python")
        report.append("from utils.results import ResultPipeline, StandardResultV2")
        report.append("")
        report.append("# Create pipeline")
        report.append("pipeline = ResultPipeline()")
        report.append("")
        report.append("# Process result from algorithm")
        report.append("result = create_result_from_algorithm(algorithm)")
        report.append("processed_result = pipeline.process(result)")
        report.append("")
        report.append("# Export in various formats")
        report.append("pipeline.export(result.result_id, 'json', 'output.json')")
        report.append("pipeline.export(result.result_id, 'latex', 'output.tex')")
        report.append("```")
        
        return "\n".join(report)


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(
        description='Migrate to unified result system'
    )
    parser.add_argument(
        '--directory', '-d',
        type=str,
        default='.',
        help='Directory to search for files to migrate'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (default is dry run)'
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Migrate a specific file'
    )
    
    args = parser.parse_args()
    
    # Create migrator
    migrator = ResultSystemMigrator(dry_run=not args.execute)
    
    # Find or use specific file
    if args.file:
        files_to_migrate = [Path(args.file)]
    else:
        root_dir = Path(args.directory)
        files_to_migrate = migrator.find_files_to_migrate(root_dir)
    
    print(f"Found {len(files_to_migrate)} files to migrate")
    
    # Migrate files
    for filepath in files_to_migrate:
        print(f"Processing {filepath}...")
        migrator.migrate_file(filepath)
    
    # Generate report
    report = migrator.generate_migration_report()
    print(report)
    
    # Save report
    report_path = Path('migration_report_unified_results.txt')
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == '__main__':
    main()