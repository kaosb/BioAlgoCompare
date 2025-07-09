#!/usr/bin/env python3
"""
Script to reorganize documentation structure according to the new plan.
"""

import os
import shutil
from pathlib import Path


def create_new_structure():
    """Create the new documentation directory structure."""
    
    base_dir = Path("docs")
    
    # New structure
    new_dirs = [
        "user",
        "algorithms/reference",
        "developer/guides",
        "scientific",
        "reference/schemas",
        "reference/api",
        "reference/changelog",
        "tutorials"
    ]
    
    print("📁 Creating new directory structure...")
    for dir_path in new_dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")


def move_files():
    """Move files to their new locations."""
    
    moves = {
        # User documentation
        "docs/user/CLI.md": "docs/user/cli_reference.md",
        "docs/user/INSTALLATION.md": "docs/installation.md",
        "docs/user/QUICKSTART.md": "docs/quickstart.md",
        
        # Algorithm docs
        "docs/algorithms/individual/*.md": "docs/algorithms/reference/",
        
        # Developer guides
        "docs/developer/ALGORITHM_MIXINS.md": "docs/developer/guides/algorithm_mixins.md",
        "docs/developer/ERROR_HANDLING.md": "docs/developer/guides/error_handling.md",
        "docs/developer/PLUGIN_SYSTEM.md": "docs/developer/guides/plugin_development.md",
        "docs/developer/VALIDATION_SYSTEM.md": "docs/developer/guides/validation_system.md",
        "docs/metadata_system.md": "docs/developer/guides/metadata_system.md",
        
        # Reference
        "docs/changelog/*.md": "docs/reference/changelog/",
        "docs/developer/schemas/*.md": "docs/reference/schemas/",
        
        # Scientific docs
        "docs/scientific/*.md": "docs/scientific/",
        
        # Technical docs
        "docs/technical/architecture.md": "docs/developer/architecture.md",
        "docs/technical/implementation.md": "docs/developer/implementation.md",
    }
    
    print("\n📄 Moving files...")
    for src_pattern, dst in moves.items():
        if '*' in src_pattern:
            # Handle glob patterns
            base_path = Path(src_pattern.split('*')[0])
            if base_path.exists():
                for src_file in base_path.glob('*.md'):
                    dst_path = Path(dst) / src_file.name
                    if src_file.exists() and not dst_path.exists():
                        shutil.copy2(src_file, dst_path)
                        print(f"  ✓ {src_file.name} → {dst}")
        else:
            # Handle single files
            src_path = Path(src_pattern)
            dst_path = Path(dst)
            if src_path.exists():
                if dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                if not dst_path.exists():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    print(f"  ✓ {src_path.name} → {dst_path.parent}")


def create_index_files():
    """Create index files for navigation."""
    
    index_files = {
        "docs/index.md": """# BioAlgoCompare Documentation

Welcome to the BioAlgoCompare documentation!

## Quick Links

- [Getting Started](quickstart.md)
- [Installation Guide](installation.md)
- [CLI Reference](user/cli_reference.md)
- [Algorithm Overview](algorithms/overview.md)

## Documentation Structure

### For Users
- **[User Guide](user/)** - How to use BioAlgoCompare
- **[Tutorials](tutorials/)** - Step-by-step guides
- **[Examples](user/examples.md)** - Usage examples

### For Developers
- **[Developer Guide](developer/)** - Architecture and development
- **[API Reference](reference/api/)** - Complete API documentation
- **[Contributing](developer/contributing.md)** - How to contribute

### Scientific Background
- **[Methodology](scientific/methodology.md)** - Research methodology
- **[Statistical Analysis](scientific/statistical_analysis.md)** - Analysis methods
- **[Reproducibility](scientific/reproducibility.md)** - Ensuring reproducible research

### Reference
- **[Algorithm Reference](algorithms/reference/)** - Individual algorithm details
- **[Data Schemas](reference/schemas/)** - Data format specifications
- **[Changelog](reference/changelog/)** - Version history
""",
        
        "docs/user/index.md": """# User Documentation

This section contains documentation for users of BioAlgoCompare.

## Contents

- [CLI Reference](cli_reference.md) - Complete command-line interface reference
- [Configuration](configuration.md) - How to configure BioAlgoCompare
- [Examples](examples.md) - Common usage examples
- [Troubleshooting](troubleshooting.md) - Solutions to common problems

## Quick Start

See the [Quickstart Guide](../quickstart.md) for a quick introduction.
""",
        
        "docs/developer/index.md": """# Developer Documentation

This section contains documentation for developers working on BioAlgoCompare.

## Contents

- [Architecture](architecture.md) - System architecture overview
- [API Reference](api_reference.md) - Complete API documentation
- [Contributing](contributing.md) - How to contribute to the project
- [Testing](testing.md) - Testing guidelines and procedures

## Guides

- [Adding Algorithms](guides/adding_algorithms.md) - How to add new algorithms
- [Validation System](guides/validation_system.md) - Result validation framework
- [Plugin Development](guides/plugin_development.md) - Creating plugins
- [Metadata System](guides/metadata_system.md) - Metadata capture system
""",
        
        "docs/tutorials/index.md": """# Tutorials

Step-by-step guides for common tasks.

## Available Tutorials

- [First Experiment](first_experiment.md) - Run your first experiment
- [Custom Algorithm](custom_algorithm.md) - Implement a custom algorithm
- [Publication Ready](publication_ready.md) - Prepare results for publication

## Prerequisites

Before starting these tutorials, make sure you have:
1. Installed BioAlgoCompare (see [Installation](../installation.md))
2. Basic understanding of optimization algorithms
3. Familiarity with Python and command line
"""
    }
    
    print("\n📝 Creating index files...")
    for path, content in index_files.items():
        file_path = Path(path)
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  ✓ {path}")


def consolidate_migration_checklists():
    """Consolidate all migration checklists into a single guide."""
    
    print("\n📋 Consolidating migration checklists...")
    
    migration_dir = Path("docs/developer")
    checklists = sorted(migration_dir.glob("migration_checklist_*.md"))
    
    if checklists:
        consolidated = Path("docs/developer/guides/migration_guide.md")
        
        with open(consolidated, 'w') as out:
            out.write("# Algorithm Migration Guide\n\n")
            out.write("This guide consolidates all algorithm migration checklists.\n\n")
            out.write("## Overview\n\n")
            out.write("All algorithms have been migrated to v2 with the following features:\n")
            out.write("- Base class inheritance (MetaheuristicAlgorithm)\n")
            out.write("- Proper random state management\n")
            out.write("- Result schema compliance\n")
            out.write("- Validation system integration\n\n")
            
            out.write("## Individual Algorithm Status\n\n")
            
            for checklist in checklists:
                algo_name = checklist.stem.replace("migration_checklist_", "").upper()
                out.write(f"### {algo_name}\n")
                out.write(f"See original checklist: [{checklist.name}](../{checklist.name})\n\n")
        
        print(f"  ✓ Consolidated {len(checklists)} checklists")


def create_navigation():
    """Create navigation file for documentation."""
    
    nav_content = """# Documentation Navigation

## Quick Navigation

### Getting Started
- [Home](index.md)
- [Installation](installation.md)
- [Quickstart](quickstart.md)

### User Documentation
- [CLI Reference](user/cli_reference.md)
- [Configuration](user/configuration.md)
- [Examples](user/examples.md)
- [Troubleshooting](user/troubleshooting.md)

### Algorithms
- [Overview](algorithms/overview.md)
- [Implementation Details](algorithms/implementation.md)
- [Algorithm Reference](algorithms/reference/)

### Developer Documentation
- [Architecture](developer/architecture.md)
- [API Reference](developer/api_reference.md)
- [Contributing](developer/contributing.md)
- [Testing](developer/testing.md)

### Developer Guides
- [Adding Algorithms](developer/guides/adding_algorithms.md)
- [Validation System](developer/guides/validation_system.md)
- [Plugin Development](developer/guides/plugin_development.md)
- [Metadata System](developer/guides/metadata_system.md)

### Scientific Documentation
- [Methodology](scientific/methodology.md)
- [Statistical Analysis](scientific/statistical_analysis.md)
- [Reproducibility](scientific/reproducibility.md)
- [Benchmarking](scientific/benchmarking.md)

### Reference
- [Data Schemas](reference/schemas/)
- [API Documentation](reference/api/)
- [Changelog](reference/changelog/)

### Tutorials
- [First Experiment](tutorials/first_experiment.md)
- [Custom Algorithm](tutorials/custom_algorithm.md)
- [Publication Ready](tutorials/publication_ready.md)
"""
    
    nav_file = Path("docs/NAVIGATION.md")
    nav_file.write_text(nav_content)
    print("\n🧭 Created navigation file")


def cleanup_old_structure():
    """Clean up redundant files after reorganization."""
    
    print("\n🧹 Cleanup suggestions (manual review required):")
    
    # Files that might be redundant after reorganization
    potential_cleanup = [
        "docs/developer/migration_checklist_*.md",
        "docs/developer/project/TODO_*.md",
        "docs/development/consolidation_plan*.md",
    ]
    
    for pattern in potential_cleanup:
        print(f"  - Review: {pattern}")


def main():
    """Main reorganization function."""
    print("🚀 Starting documentation reorganization...\n")
    
    # Create new structure
    create_new_structure()
    
    # Move files
    move_files()
    
    # Create index files
    create_index_files()
    
    # Consolidate migration checklists
    consolidate_migration_checklists()
    
    # Create navigation
    create_navigation()
    
    # Suggest cleanup
    cleanup_old_structure()
    
    print("\n✅ Documentation reorganization complete!")
    print("\n📋 Next steps:")
    print("  1. Review the new structure in docs/")
    print("  2. Update any broken links in README.md")
    print("  3. Remove redundant files after verification")
    print("  4. Update CI/CD documentation references")


if __name__ == "__main__":
    main()