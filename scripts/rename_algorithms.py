#!/usr/bin/env python3
"""
Simple script to rename algorithm files from *_v2.py to *.py
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def rename_algorithms():
    """Rename algorithm files removing _v2 suffix."""
    algorithms_dir = Path("algorithms")
    backup_dir = Path(f"legacy/algorithms_v2_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create backup directory
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all _v2 algorithm files (excluding base and template)
    v2_files = [f for f in algorithms_dir.glob("*_v2.py") 
                if not ('base' in f.name or 'template' in f.name)]
    
    print(f"Found {len(v2_files)} algorithm files to rename")
    print(f"Backup directory: {backup_dir}")
    print("-" * 60)
    
    renamed_count = 0
    for v2_file in sorted(v2_files):
        new_name = v2_file.stem.replace('_v2', '') + '.py'
        new_path = v2_file.parent / new_name
        
        # Check if target exists
        if new_path.exists():
            print(f"⚠️  SKIP: {new_name} already exists")
            continue
        
        # Backup original
        backup_path = backup_dir / v2_file.name
        shutil.copy2(v2_file, backup_path)
        
        # Rename
        v2_file.rename(new_path)
        print(f"✅ {v2_file.name} → {new_name}")
        renamed_count += 1
    
    print("-" * 60)
    print(f"✅ Renamed {renamed_count} files")
    print(f"📁 Backups saved to: {backup_dir}")
    
    # Handle special case: hoa_v3.py
    v3_file = algorithms_dir / "hoa_v3.py"
    if v3_file.exists():
        print(f"\n⚠️  Note: {v3_file.name} still exists and needs manual review")
    
    return renamed_count

if __name__ == "__main__":
    rename_algorithms()