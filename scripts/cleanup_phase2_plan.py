#!/usr/bin/env python3
"""
Phase 2: Plan for consolidating algorithm implementations.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_algorithm_versions():
    """Analyze algorithm version files and their dependencies."""
    algorithms_dir = Path("algorithms")
    
    # Find all algorithm files with version suffixes
    v2_algorithms = list(algorithms_dir.glob("*_v2.py"))
    v3_algorithms = list(algorithms_dir.glob("*_v3.py"))
    
    # Exclude base classes and templates
    v2_algorithms = [f for f in v2_algorithms if not ('base' in f.name or 'template' in f.name)]
    v3_algorithms = [f for f in v3_algorithms if not ('base' in f.name or 'template' in f.name)]
    
    print("=" * 80)
    print("PHASE 2: ALGORITHM CONSOLIDATION PLAN")
    print("=" * 80)
    
    print(f"\nFound {len(v2_algorithms)} v2 algorithms:")
    for alg in sorted(v2_algorithms):
        base_name = alg.stem.replace('_v2', '')
        print(f"  - {alg.name} → {base_name}.py")
    
    if v3_algorithms:
        print(f"\nFound {len(v3_algorithms)} v3 algorithms:")
        for alg in sorted(v3_algorithms):
            base_name = alg.stem.replace('_v3', '')
            print(f"  - {alg.name} → {base_name}.py (needs special handling)")
    
    # Check for conflicts
    print("\n" + "=" * 80)
    print("CONFLICT ANALYSIS")
    print("=" * 80)
    
    conflicts = []
    for alg in v2_algorithms:
        base_name = alg.stem.replace('_v2', '')
        base_file = algorithms_dir / f"{base_name}.py"
        if base_file.exists():
            conflicts.append((alg, base_file))
    
    if conflicts:
        print(f"\n⚠️  Found {len(conflicts)} potential conflicts:")
        for v2_file, base_file in conflicts:
            print(f"  - {v2_file.name} conflicts with existing {base_file.name}")
    else:
        print("\n✅ No conflicts found - safe to rename")
    
    # Find dependencies
    print("\n" + "=" * 80)
    print("DEPENDENCY ANALYSIS")
    print("=" * 80)
    
    # Files that import v2 algorithms
    import_pattern = re.compile(r'from algorithms\.(\w+_v\d+) import|import algorithms\.(\w+_v\d+)')
    
    dependencies = defaultdict(list)
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden and cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                try:
                    content = filepath.read_text()
                    matches = import_pattern.findall(content)
                    for match in matches:
                        module = match[0] or match[1]
                        dependencies[module].append(str(filepath))
                except:
                    pass
    
    print("\nFiles importing versioned algorithms:")
    for module, files in sorted(dependencies.items()):
        if '_v' in module and not 'base' in module:
            print(f"\n{module}:")
            for f in sorted(set(files)):
                print(f"  - {f}")
    
    # Migration steps
    print("\n" * 2 + "=" * 80)
    print("MIGRATION STEPS")
    print("=" * 80)
    
    print("\n1. Create consolidated versions:")
    print("   - For each *_v2.py, rename to *.py")
    print("   - For hoa_v3.py, merge with hoa_v2.py if needed")
    
    print("\n2. Update imports in:")
    print("   - Test files")
    print("   - Benchmark scripts")
    print("   - Factory modules")
    print("   - Example scripts")
    
    print("\n3. Update algorithm registries:")
    print("   - algorithms/__init__.py")
    print("   - config files")
    
    print("\n4. Run tests to verify:")
    print("   - Convergence tests")
    print("   - Validation tests")
    print("   - Benchmark scripts")
    
    return v2_algorithms, v3_algorithms, dependencies

if __name__ == "__main__":
    analyze_algorithm_versions()