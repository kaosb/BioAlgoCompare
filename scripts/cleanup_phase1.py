#!/usr/bin/env python3
"""
Phase 1: Remove deprecated migration tests safely.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def cleanup_deprecated_tests():
    """Remove deprecated migration tests."""
    deprecated_dir = Path("tests/deprecated/migration_tests")
    backup_dir = Path(f"legacy/backup_phase1_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if not deprecated_dir.exists():
        print("❌ Deprecated tests directory not found")
        return False
    
    # Get list of files to remove
    migration_tests = list(deprecated_dir.glob("test_*_v2_migration.py"))
    
    print(f"Found {len(migration_tests)} deprecated migration tests")
    
    # Create backup directory
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup and remove files
    removed_count = 0
    for test_file in migration_tests:
        # Backup
        backup_path = backup_dir / test_file.name
        shutil.copy2(test_file, backup_path)
        
        # Remove
        test_file.unlink()
        print(f"✅ Removed: {test_file.name}")
        removed_count += 1
    
    # Check if README exists
    readme_path = deprecated_dir / "README.md"
    if readme_path.exists():
        # Update README to reflect removal
        with open(readme_path, 'w') as f:
            f.write("# Deprecated Migration Tests\n\n")
            f.write("All v2 migration tests have been removed as part of TODO #103.\n")
            f.write(f"Tests were backed up to: {backup_dir}\n")
            f.write(f"Removal date: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    print(f"\n✅ Phase 1 Complete: Removed {removed_count} deprecated tests")
    print(f"📁 Backup location: {backup_dir}")
    
    return True

if __name__ == "__main__":
    cleanup_deprecated_tests()