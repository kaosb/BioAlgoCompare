#!/usr/bin/env python3
"""
Automatic import migration script for BioAlgoCompare.

This script automatically migrates all algorithm files to use the new
unified core architecture while preserving backward compatibility.

The migration process:
1. Scans all algorithm files for legacy imports
2. Updates import statements to use migration wrappers
3. Validates that algorithms still work after migration
4. Creates backup files for safety
5. Logs all changes for review

Usage:
    python scripts/migration/migrate_imports.py [--dry-run] [--backup]
"""

import os
import re
import shutil
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImportMigrator:
    """Handles automatic migration of import statements."""
    
    def __init__(self, project_root: Path, dry_run: bool = False, create_backup: bool = True):
        """
        Initialize the import migrator.
        
        Args:
            project_root: Root directory of the project
            dry_run: If True, only show what would be changed
            create_backup: If True, create backup files
        """
        self.project_root = project_root
        self.dry_run = dry_run
        self.create_backup = create_backup
        
        # Migration mappings
        self.import_mappings = {
            # Legacy base imports
            'from algorithms.base_v2 import': 'from algorithms.base_v2_migration import',
            'from algorithms.base_v3 import': 'from algorithms.base_v3_migration import',
            'from algorithms.base_v2_managed import': 'from algorithms.base_v2_migration import',
            'from algorithms.base_v2_enhanced import': 'from algorithms.base_v2_migration import',
            'from algorithms.base_v2_original import': 'from algorithms.base_v2_migration import',
            'from algorithms.base_v2_random import': 'from algorithms.base_v2_migration import',
            'from algorithms.base_v2_enforced import': 'from algorithms.base_v2_migration import',
            
            # Direct imports
            'import algorithms.base_v2': 'import algorithms.base_v2_migration as algorithms.base_v2',
            'import algorithms.base_v3': 'import algorithms.base_v3_migration as algorithms.base_v3',
        }
        
        # Files to migrate
        self.algorithm_patterns = [
            'algorithms/**/*.py',
            'algorithms_v2/**/*.py',
            'tests/**/test_*_migration.py'
        ]
        
        # Files to exclude
        self.exclude_patterns = [
            '**/core/**',
            '**/legacy_compatibility.py',
            '**/*_migration.py',
            '**/deprecated/**',
            '**/__pycache__/**'
        ]
        
        # Statistics
        self.stats = {
            'files_scanned': 0,
            'files_modified': 0,
            'imports_updated': 0,
            'errors': 0
        }
    
    def find_algorithm_files(self) -> List[Path]:
        """Find all algorithm files that need migration."""
        files = []
        
        for pattern in self.algorithm_patterns:
            pattern_files = list(self.project_root.glob(pattern))
            files.extend(pattern_files)
        
        # Filter out excluded files
        filtered_files = []
        for file_path in files:
            should_exclude = False
            
            for exclude_pattern in self.exclude_patterns:
                if file_path.match(exclude_pattern):
                    should_exclude = True
                    break
            
            if not should_exclude and file_path.is_file() and file_path.suffix == '.py':
                filtered_files.append(file_path)
        
        return filtered_files
    
    def analyze_file(self, file_path: Path) -> Tuple[List[str], List[Tuple[int, str, str]]]:
        """
        Analyze a file for legacy imports.
        
        Returns:
            Tuple of (current_imports, needed_changes)
        """
        current_imports = []
        needed_changes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for import statements
                for old_import, new_import in self.import_mappings.items():
                    if line.startswith(old_import):
                        current_imports.append(line)
                        new_line = line.replace(old_import, new_import)
                        needed_changes.append((line_num, line, new_line))
                        break
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            self.stats['errors'] += 1
        
        return current_imports, needed_changes
    
    def migrate_file(self, file_path: Path) -> bool:
        """
        Migrate a single file.
        
        Returns:
            True if file was modified, False otherwise
        """
        current_imports, needed_changes = self.analyze_file(file_path)
        
        if not needed_changes:
            return False
        
        logger.info(f"Migrating {file_path} ({len(needed_changes)} changes)")
        
        if self.dry_run:
            for line_num, old_line, new_line in needed_changes:
                logger.info(f"  Line {line_num}: {old_line} -> {new_line}")
            return True
        
        # Create backup if requested
        if self.create_backup:
            backup_path = file_path.with_suffix(f".py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply changes
            for line_num, old_line, new_line in needed_changes:
                content = content.replace(old_line, new_line)
                logger.debug(f"  Updated line {line_num}: {old_line} -> {new_line}")
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.stats['imports_updated'] += len(needed_changes)
            return True
            
        except Exception as e:
            logger.error(f"Error migrating {file_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def validate_migration(self, file_path: Path) -> bool:
        """
        Validate that a migrated file can still be imported.
        
        Returns:
            True if validation successful, False otherwise
        """
        try:
            # Try to import the module
            module_name = str(file_path.relative_to(self.project_root)).replace('/', '.').replace('.py', '')
            
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            logger.debug(f"Validation successful: {file_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Validation failed for {file_path}: {e}")
            return False
    
    def run_migration(self) -> Dict[str, any]:
        """
        Run the complete migration process.
        
        Returns:
            Dictionary with migration results
        """
        logger.info(f"Starting import migration ({'dry-run' if self.dry_run else 'live'} mode)")
        
        # Find files to migrate
        algorithm_files = self.find_algorithm_files()
        logger.info(f"Found {len(algorithm_files)} algorithm files to check")
        
        migrated_files = []
        validation_failures = []
        
        # Process each file
        for file_path in algorithm_files:
            self.stats['files_scanned'] += 1
            
            if self.migrate_file(file_path):
                migrated_files.append(file_path)
                self.stats['files_modified'] += 1
                
                # Validate migration if not dry run
                if not self.dry_run and not self.validate_migration(file_path):
                    validation_failures.append(file_path)
        
        # Generate report
        results = {
            'success': self.stats['errors'] == 0,
            'statistics': self.stats,
            'migrated_files': migrated_files,
            'validation_failures': validation_failures,
            'dry_run': self.dry_run
        }
        
        self._print_migration_report(results)
        
        return results
    
    def _print_migration_report(self, results: Dict[str, any]):
        """Print a summary report of the migration."""
        stats = results['statistics']
        
        logger.info("=" * 60)
        logger.info("MIGRATION REPORT")
        logger.info("=" * 60)
        logger.info(f"Mode: {'DRY RUN' if results['dry_run'] else 'LIVE MIGRATION'}")
        logger.info(f"Files scanned: {stats['files_scanned']}")
        logger.info(f"Files modified: {stats['files_modified']}")
        logger.info(f"Imports updated: {stats['imports_updated']}")
        logger.info(f"Errors: {stats['errors']}")
        
        if results['migrated_files']:
            logger.info(f"\nMigrated files ({len(results['migrated_files'])}):")
            for file_path in results['migrated_files']:
                logger.info(f"  - {file_path}")
        
        if results['validation_failures']:
            logger.warning(f"\nValidation failures ({len(results['validation_failures'])}):")
            for file_path in results['validation_failures']:
                logger.warning(f"  - {file_path}")
        
        if results['success']:
            logger.info("\n✅ Migration completed successfully!")
        else:
            logger.error(f"\n❌ Migration completed with {stats['errors']} errors")
        
        if results['dry_run']:
            logger.info("\nTo apply these changes, run without --dry-run")


def create_migration_wrappers(project_root: Path):
    """Create migration wrapper files for all legacy base files."""
    base_files = [
        'algorithms/base_v2.py',
        'algorithms/base_v3.py',
        'algorithms/base_v2_managed.py',
        'algorithms/base_v2_enhanced.py',
        'algorithms/base_v2_original.py',
        'algorithms/base_v2_random.py',
        'algorithms/base_v2_enforced.py'
    ]
    
    migration_content = '''"""
Migration wrapper for {original_file}

⚠️  DEPRECATED: This module is deprecated and will be removed in version 3.0.
Please import from algorithms.core instead:

    from algorithms.core import MetaheuristicAlgorithm, Individual

This wrapper provides backward compatibility while issuing deprecation warnings.
"""

from algorithms.legacy_compatibility import (
    LegacyMetaheuristicAlgorithm as MetaheuristicAlgorithm,
    LegacyIndividual as Individual,
    LegacyProblem as AbstractProblem,
    CoreMoveContext as MoveContext,
    deprecation_warning
)

# Issue deprecation warning
deprecation_warning(
    "{original_file}",
    "algorithms.core",
    version="3.0"
)

# Export expected classes
__all__ = [
    'MetaheuristicAlgorithm',
    'Individual', 
    'AbstractProblem',
    'MoveContext'
]
'''
    
    for base_file in base_files:
        file_path = project_root / base_file
        if file_path.exists():
            # Create backup
            backup_path = file_path.with_suffix(f".py.pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backed up {base_file} to {backup_path}")
            
            # Create migration wrapper
            wrapper_content = migration_content.format(original_file=base_file)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(wrapper_content)
            
            logger.info(f"Created migration wrapper for {base_file}")


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="Migrate BioAlgoCompare imports to unified architecture")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), help='Project root directory')
    parser.add_argument('--create-wrappers', action='store_true', help='Create migration wrappers for legacy base files')
    
    args = parser.parse_args()
    
    # Validate project root
    if not (args.project_root / 'algorithms').exists():
        logger.error(f"Invalid project root: {args.project_root}")
        return 1
    
    try:
        # Create migration wrappers if requested
        if args.create_wrappers:
            logger.info("Creating migration wrappers for legacy base files...")
            create_migration_wrappers(args.project_root)
        
        # Run import migration
        migrator = ImportMigrator(
            project_root=args.project_root,
            dry_run=args.dry_run,
            create_backup=not args.no_backup
        )
        
        results = migrator.run_migration()
        
        return 0 if results['success'] else 1
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())