# Scripts and Documentation Reorganization Plan

## Current Issues

1. **Scripts Organization**
   - Multiple run scripts with overlapping functionality (run.py, run_with_metadata.py, run_with_schema.py, run_with_tracker.py)
   - Tools scattered in different locations
   - CLI commands not clearly organized

2. **Documentation Issues**
   - Developer documentation mixed with user documentation
   - Many migration checklists that should be consolidated
   - Missing clear hierarchy and navigation
   - Redundant information across multiple files

## Proposed Structure

### 1. Scripts Reorganization

```
scripts/
├── cli/                        # Main CLI commands
│   ├── __init__.py
│   ├── main.py                # Single entry point (bioalgo command)
│   ├── commands/              # Organized by functionality
│   │   ├── __init__.py
│   │   ├── run.py            # Unified run command with all options
│   │   ├── benchmark.py      # Unified benchmark command
│   │   ├── analyze.py        # Analysis and reporting
│   │   ├── massive.py        # Massive benchmarking
│   │   └── dashboard.py      # Real-time monitoring
│   └── config/
│       ├── __init__.py
│       └── algorithms.py
├── tools/                     # Standalone utility scripts
│   ├── __init__.py
│   ├── clean.py
│   ├── migrate_algorithm.py
│   ├── manage_datasets.py
│   ├── manage_plugins.py
│   └── check_reproducibility.py
├── maintenance/               # System maintenance scripts
│   ├── enforce_random_state.py
│   ├── update_dependencies.py
│   └── verify_installation.py
└── deprecated/                # Keep old scripts temporarily
    ├── run_v1.py
    ├── run_with_schema.py
    └── run_with_tracker.py
```

### 2. Documentation Reorganization

```
docs/
├── index.md                   # Main documentation entry
├── quickstart.md             # Getting started guide
├── installation.md           # Installation instructions
│
├── user/                     # End-user documentation
│   ├── cli_reference.md      # Complete CLI reference
│   ├── configuration.md      # Configuration options
│   ├── examples.md           # Usage examples
│   └── troubleshooting.md    # Common issues
│
├── algorithms/               # Algorithm documentation
│   ├── overview.md           # Algorithm comparison table
│   ├── implementation.md     # Implementation details
│   └── reference/            # Individual algorithm docs
│       ├── aha.md
│       ├── apo.md
│       └── ...
│
├── developer/                # Developer documentation
│   ├── architecture.md       # System architecture
│   ├── api_reference.md      # API documentation
│   ├── contributing.md       # Contribution guidelines
│   ├── testing.md            # Testing guide
│   └── guides/               # Development guides
│       ├── adding_algorithms.md
│       ├── validation_system.md
│       ├── plugin_development.md
│       └── metadata_system.md
│
├── scientific/               # Scientific documentation
│   ├── methodology.md        # Research methodology
│   ├── reproducibility.md    # Reproducibility guide
│   ├── statistical_analysis.md
│   └── benchmarking.md       # Benchmarking methodology
│
├── reference/                # Technical reference
│   ├── schemas/              # Data schemas
│   ├── api/                  # API docs (auto-generated)
│   └── changelog/            # Version history
│
└── tutorials/                # Step-by-step tutorials
    ├── first_experiment.md
    ├── custom_algorithm.md
    └── publication_ready.md
```

## Implementation Steps

### Phase 1: Scripts Consolidation
1. Create unified CLI entry point (main.py)
2. Merge run scripts into single command with options
3. Consolidate benchmark scripts
4. Move tools to appropriate directories
5. Update imports and references

### Phase 2: Documentation Restructuring
1. Create new directory structure
2. Consolidate migration checklists into single guide
3. Separate user and developer documentation
4. Create clear navigation with index files
5. Remove redundant content

### Phase 3: Integration
1. Update README with new structure
2. Update CLI help messages
3. Create documentation navigation
4. Update CI/CD references
5. Test all commands and links

### Phase 4: Cleanup
1. Archive deprecated scripts
2. Remove obsolete documentation
3. Update all references in code
4. Final testing

## Benefits

1. **Clarity**: Clear separation of concerns
2. **Discoverability**: Easy to find relevant information
3. **Maintainability**: Less duplication, easier updates
4. **User Experience**: Simpler CLI, better documentation
5. **Development**: Clear guidelines and structure