#!/usr/bin/env python3
"""
Phase 2: Consolidate algorithm implementations by removing version suffixes.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
import ast

class AlgorithmConsolidator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.backup_dir = Path(f"legacy/backup_phase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.changes_log = []
        
    def consolidate_algorithms(self):
        """Main consolidation process."""
        print("=" * 80)
        print("PHASE 2: ALGORITHM CONSOLIDATION")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print("=" * 80)
        
        # Step 1: Identify algorithm files
        algorithms_dir = Path("algorithms")
        v2_files = list(algorithms_dir.glob("*_v2.py"))
        v3_files = list(algorithms_dir.glob("*_v3.py"))
        
        # Exclude base classes and templates
        v2_algorithms = [f for f in v2_files if not ('base' in f.name or 'template' in f.name)]
        v3_algorithms = [f for f in v3_files if not ('base' in f.name or 'template' in f.name)]
        
        print(f"\nFound {len(v2_algorithms)} v2 algorithms to consolidate")
        print(f"Found {len(v3_algorithms)} v3 algorithms to handle")
        
        # Step 2: Create backup
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nBackup directory: {self.backup_dir}")
        
        # Step 3: Process v2 algorithms
        print("\n" + "-" * 40)
        print("CONSOLIDATING V2 ALGORITHMS")
        print("-" * 40)
        
        for v2_file in sorted(v2_algorithms):
            new_name = v2_file.stem.replace('_v2', '') + '.py'
            new_path = v2_file.parent / new_name
            
            print(f"\n{v2_file.name} → {new_name}")
            
            if not self.dry_run:
                # Backup
                backup_path = self.backup_dir / v2_file.name
                shutil.copy2(v2_file, backup_path)
                
                # Rename
                v2_file.rename(new_path)
                print(f"  ✅ Renamed")
            else:
                print(f"  [DRY RUN] Would rename")
            
            self.changes_log.append(('rename', str(v2_file), str(new_path)))
        
        # Step 4: Handle v3 algorithms (special case)
        if v3_algorithms:
            print("\n" + "-" * 40)
            print("HANDLING V3 ALGORITHMS")
            print("-" * 40)
            
            for v3_file in v3_algorithms:
                print(f"\n{v3_file.name}:")
                print("  ⚠️  Requires manual review - keeping as is for now")
                # In real implementation, we'd analyze if v3 should replace v2
        
        # Step 5: Update imports
        print("\n" + "-" * 40)
        print("UPDATING IMPORTS")
        print("-" * 40)
        
        self.update_imports_across_codebase()
        
        # Step 6: Summary
        print("\n" + "=" * 80)
        print("CONSOLIDATION SUMMARY")
        print("=" * 80)
        
        if self.dry_run:
            print("\n🔍 DRY RUN COMPLETE")
            print(f"Would rename {len(v2_algorithms)} algorithm files")
            print(f"Would update imports in {len(self.get_files_with_imports())} files")
            print("\nRun with --execute to perform actual changes")
        else:
            print("\n✅ CONSOLIDATION COMPLETE")
            print(f"Renamed {len(v2_algorithms)} algorithm files")
            print(f"Updated imports in {len(self.get_files_with_imports())} files")
            print(f"Backups saved to: {self.backup_dir}")
        
        # Save changes log
        self.save_changes_log()
        
    def update_imports_across_codebase(self):
        """Update all imports from *_v2 to base names."""
        files_to_update = self.get_files_with_imports()
        
        for filepath in files_to_update:
            self.update_imports_in_file(filepath)
    
    def get_files_with_imports(self):
        """Find all files that import versioned algorithms."""
        files_with_imports = []
        import_pattern = re.compile(r'from algorithms\.(\w+)_v2 import|import algorithms\.(\w+)_v2')
        
        for root, dirs, files in os.walk('.'):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'legacy']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    try:
                        content = filepath.read_text()
                        if import_pattern.search(content):
                            files_with_imports.append(filepath)
                    except:
                        pass
        
        return files_with_imports
    
    def update_imports_in_file(self, filepath):
        """Update imports in a single file."""
        try:
            content = filepath.read_text()
            original_content = content
            
            # Update various import patterns
            patterns = [
                # from algorithms.hoa_v2 import HOAV2
                (r'from algorithms\.(\w+)_v2 import', r'from algorithms.\1 import'),
                # import algorithms.hoa_v2
                (r'import algorithms\.(\w+)_v2', r'import algorithms.\1'),
                # algorithms.hoa_v2.HOAV2
                (r'algorithms\.(\w+)_v2\.', r'algorithms.\1.'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                if not self.dry_run:
                    # Backup original
                    backup_path = self.backup_dir / 'imports' / filepath.relative_to('.')
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(filepath, backup_path)
                    
                    # Write updated content
                    filepath.write_text(content)
                    print(f"  ✅ Updated: {filepath}")
                else:
                    print(f"  [DRY RUN] Would update: {filepath}")
                
                self.changes_log.append(('update_imports', str(filepath), 'success'))
        except Exception as e:
            print(f"  ❌ Error updating {filepath}: {e}")
            self.changes_log.append(('update_imports', str(filepath), f'error: {e}'))
    
    def save_changes_log(self):
        """Save a log of all changes made."""
        if not self.dry_run:
            log_path = self.backup_dir / 'changes_log.txt'
            with open(log_path, 'w') as f:
                f.write(f"Algorithm Consolidation Log\n")
                f.write(f"Date: {datetime.now()}\n")
                f.write(f"{'=' * 60}\n\n")
                
                for action, target, result in self.changes_log:
                    f.write(f"{action}: {target} → {result}\n")
            
            print(f"\nChanges log saved to: {log_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Consolidate algorithm implementations')
    parser.add_argument('--execute', action='store_true', help='Execute changes (default is dry run)')
    args = parser.parse_args()
    
    consolidator = AlgorithmConsolidator(dry_run=not args.execute)
    consolidator.consolidate_algorithms()

if __name__ == "__main__":
    main()