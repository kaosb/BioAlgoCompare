#!/usr/bin/env python3
"""
Analyze version proliferation in the codebase.
"""

import os
import re
from collections import defaultdict
from pathlib import Path

def analyze_version_files():
    """Analyze all files with version suffixes."""
    version_files = defaultdict(list)
    version_pattern = re.compile(r'(.+?)_v(\d+)(.*?)$')
    
    # Scan all Python files
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                match = version_pattern.match(file.replace('.py', ''))
                if match:
                    base_name = match.group(1)
                    version = match.group(2)
                    suffix = match.group(3)
                    full_path = os.path.join(root, file)
                    version_files[base_name].append({
                        'path': full_path,
                        'version': version,
                        'suffix': suffix,
                        'category': categorize_file(full_path)
                    })
    
    return version_files

def categorize_file(filepath):
    """Categorize a file based on its path."""
    if 'algorithms' in filepath and 'base' in filepath:
        return 'base_class'
    elif 'algorithms' in filepath:
        return 'algorithm'
    elif 'tests/deprecated' in filepath:
        return 'deprecated_test'
    elif 'tests' in filepath:
        return 'test'
    elif 'utils' in filepath:
        return 'utility'
    elif 'problems' in filepath:
        return 'problem'
    else:
        return 'other'

def print_analysis(version_files):
    """Print analysis results."""
    print("=" * 80)
    print("VERSION PROLIFERATION ANALYSIS")
    print("=" * 80)
    
    # Summary by category
    category_counts = defaultdict(int)
    total_files = 0
    
    for base_name, versions in version_files.items():
        for v in versions:
            category_counts[v['category']] += 1
            total_files += 1
    
    print(f"\nTotal versioned files: {total_files}")
    print("\nBy category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")
    
    # Detailed breakdown
    print("\n" + "=" * 80)
    print("DETAILED BREAKDOWN")
    print("=" * 80)
    
    # Group by category
    by_category = defaultdict(list)
    for base_name, versions in version_files.items():
        for v in versions:
            by_category[v['category']].append((base_name, v))
    
    # Base classes (highest priority)
    if 'base_class' in by_category:
        print("\n1. BASE CLASSES (Critical - Already migrated in TODO #101):")
        for base_name, v in sorted(by_category['base_class']):
            print(f"   - {v['path']}")
    
    # Algorithms
    if 'algorithm' in by_category:
        print("\n2. ALGORITHM IMPLEMENTATIONS:")
        algo_versions = defaultdict(list)
        for base_name, v in by_category['algorithm']:
            algo_versions[base_name].append(v)
        
        for algo_name, versions in sorted(algo_versions.items()):
            print(f"   {algo_name}:")
            for v in sorted(versions, key=lambda x: x['version']):
                print(f"     - v{v['version']}: {v['path']}")
    
    # Utilities
    if 'utility' in by_category:
        print("\n3. UTILITIES:")
        for base_name, v in sorted(by_category['utility']):
            print(f"   - {v['path']}")
    
    # Problems
    if 'problem' in by_category:
        print("\n4. PROBLEMS:")
        for base_name, v in sorted(by_category['problem']):
            print(f"   - {v['path']}")
    
    # Tests (non-deprecated)
    if 'test' in by_category:
        print("\n5. ACTIVE TESTS:")
        for base_name, v in sorted(by_category['test']):
            print(f"   - {v['path']}")
    
    # Deprecated tests
    if 'deprecated_test' in by_category:
        print("\n6. DEPRECATED TESTS (Can be removed):")
        for base_name, v in sorted(by_category['deprecated_test']):
            print(f"   - {v['path']}")
    
    # Migration recommendation
    print("\n" + "=" * 80)
    print("MIGRATION RECOMMENDATIONS")
    print("=" * 80)
    
    print("\nPhase 1: Remove deprecated tests (18 files)")
    print("Phase 2: Consolidate algorithm implementations (18 _v2 + 1 _v3)")
    print("Phase 3: Update utilities to use unified architecture (2 files)")
    print("Phase 4: Update problem implementations (1 file)")
    print("Phase 5: Clean up base class backups (7 files)")
    print("Phase 6: Update remaining tests (4 files)")

if __name__ == "__main__":
    version_files = analyze_version_files()
    print_analysis(version_files)