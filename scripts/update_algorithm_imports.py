#!/usr/bin/env python3
"""
Update all imports from algorithms.*_v2 to algorithms.* after renaming.
"""

import os
import re
from pathlib import Path
from datetime import datetime

def update_imports():
    """Update all algorithm imports removing _v2 suffix."""
    backup_dir = Path(f"legacy/imports_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Patterns to replace
    replacements = [
        # from algorithms.hoa_v2 import HOAV2
        (r'from algorithms\.(\w+)_v2 import', r'from algorithms.\1 import'),
        # import algorithms.hoa_v2
        (r'import algorithms\.(\w+)_v2\b', r'import algorithms.\1'),
        # algorithms.hoa_v2.HOAV2
        (r'algorithms\.(\w+)_v2\.', r'algorithms.\1.'),
        # "hoa_v2" in strings (e.g., algorithm selection)
        (r'"(\w+)_v2"', r'"\1"'),
        (r"'(\w+)_v2'", r"'\1'"),
    ]
    
    files_updated = 0
    errors = []
    
    # Find all Python files
    for root, dirs, files in os.walk('.'):
        # Skip directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'legacy', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                
                # Skip backup directories
                if 'legacy' in str(filepath) or 'backup' in str(filepath):
                    continue
                
                try:
                    content = filepath.read_text()
                    original_content = content
                    
                    # Apply all replacements
                    for pattern, replacement in replacements:
                        content = re.sub(pattern, replacement, content)
                    
                    # Only process if changes were made
                    if content != original_content:
                        # Backup original
                        backup_path = backup_dir / filepath.relative_to('.')
                        backup_path.parent.mkdir(parents=True, exist_ok=True)
                        backup_path.write_text(original_content)
                        
                        # Write updated content
                        filepath.write_text(content)
                        print(f"✅ Updated: {filepath}")
                        files_updated += 1
                        
                except Exception as e:
                    error_msg = f"❌ Error updating {filepath}: {e}"
                    print(error_msg)
                    errors.append(error_msg)
    
    print("-" * 60)
    print(f"✅ Updated {files_updated} files")
    print(f"📁 Backups saved to: {backup_dir}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    
    return files_updated, errors

if __name__ == "__main__":
    update_imports()