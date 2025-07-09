# Legacy Files and Structure Cleanup Plan

## Current Issues

1. **Renamed but Missing Legacy Files**
   - Git shows files renamed from `algorithms/*.py` to `legacy/algorithms/*.py`
   - But `legacy/` directory doesn't exist
   - This creates confusion in git status

2. **Deleted Files in Working Directory**
   - `analyze_solomon_results.py`
   - `convert_solomon_format.py`
   - `ejecutar_benchmark.sh`
   - Multiple script files

3. **Deprecated Scripts Directory**
   - `scripts/deprecated/` exists but contains minimal files
   - Unclear what should be there vs deleted

4. **Structure Issues**
   - Multiple locations for similar functionality
   - Unclear hierarchy in some areas

## Cleanup Actions

### Phase 1: Resolve Legacy Algorithm Files

**Option A: Complete the Legacy Move (Recommended)**
- Create `legacy/algorithms/` directory
- Move v1 algorithms there for reference
- Update `.gitignore` to exclude legacy from new development
- Document the migration in CHANGELOG

**Option B: Remove Legacy Files Completely**
- Delete all v1 algorithm files
- Create a git tag `v1-final` before deletion
- Cleaner but loses immediate reference

### Phase 2: Clean Deleted Files

1. **Solomon-related scripts**
   - These appear to be experimental/temporary
   - Can be safely removed from tracking

2. **Old benchmark scripts**
   - Replaced by new unified system
   - Safe to remove

### Phase 3: Reorganize Scripts

```
scripts/
├── cli/                 # Main CLI commands
│   ├── __init__.py
│   ├── run.py          # Single run command
│   ├── benchmark.py    # Benchmarking command
│   └── analyze.py      # Analysis command
├── tools/              # Supporting tools
│   ├── __init__.py
│   ├── migrate.py      # Data migration
│   ├── validate.py     # Result validation
│   └── export.py       # Export utilities
├── examples/           # Example scripts
│   └── *.py
└── README.md          # Script documentation
```

### Phase 4: Clean Documentation

```
docs/
├── user/              # User documentation
│   ├── quickstart.md
│   ├── installation.md
│   └── cli_reference.md
├── developer/         # Developer documentation
│   ├── architecture.md
│   ├── contributing.md
│   └── api/          # API reference
├── algorithms/        # Algorithm documentation
│   └── {algorithm}.md
├── theory/           # Theoretical background
│   └── *.md
└── changelog/        # Version history
    └── *.md
```

### Phase 5: Update Configuration Files

1. **Update .gitignore**
   ```
   # Legacy code (for reference only)
   /legacy/
   
   # Temporary and experimental
   /temp/
   /experimental/
   
   # Results and outputs
   /results/
   /exports/
   ```

2. **Create .gitattributes**
   ```
   # Mark generated files
   docs/api/* linguist-generated=true
   
   # Mark vendored files
   legacy/* linguist-vendored=true
   ```

## Execution Order

1. **Backup Current State**
   ```bash
   git stash push -m "Pre-cleanup backup"
   git tag pre-cleanup-backup
   ```

2. **Handle Legacy Files**
   ```bash
   # Create legacy structure
   mkdir -p legacy/algorithms
   
   # Complete the moves git thinks happened
   git mv algorithms/*.py legacy/algorithms/ 2>/dev/null || true
   ```

3. **Clean Deleted Files**
   ```bash
   # Remove from git tracking
   git rm analyze_solomon_results.py
   git rm convert_solomon_format.py
   git rm ejecutar_benchmark.sh
   ```

4. **Reorganize Scripts**
   ```bash
   # Create new structure
   mkdir -p scripts/{cli,tools}
   
   # Move files
   mv scripts/core/*.py scripts/cli/
   mv scripts/utilities/*.py scripts/tools/
   ```

5. **Update Imports**
   - Update all imports to reflect new structure
   - Update setup.py entry points

6. **Commit Changes**
   ```bash
   git add -A
   git commit -m "refactor: Clean legacy files and reorganize structure
   
   - Move v1 algorithms to legacy/ directory  
   - Reorganize scripts into cli/ and tools/
   - Remove obsolete Solomon analysis scripts
   - Update documentation structure
   
   Part of stabilization effort (TODO #83)"
   ```

## Benefits

1. **Cleaner Git Status** - No confusing renamed files
2. **Clear Structure** - Obvious where everything belongs
3. **Better Organization** - Logical grouping of functionality
4. **Easier Navigation** - Developers can find things quickly
5. **Reduced Confusion** - No ambiguity about what's current vs legacy