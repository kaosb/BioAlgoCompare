# Scripts Directory

This directory contains all executable scripts and CLI tools for the BioAlgoCompare project.

## Directory Structure

```
scripts/
├── cli/                 # Main CLI commands
│   ├── __init__.py
│   ├── analyze.py      # Unified CLI interface (main entry point)
│   ├── run.py          # Single algorithm run command
│   ├── benchmark.py    # Benchmarking command
│   ├── run_with_schema.py    # Run with result schema
│   └── run_with_tracker.py   # Run with experiment tracking
├── tools/              # Supporting tools
│   ├── __init__.py
│   ├── clean.py        # Cleanup utilities
│   ├── inventory.py    # Project inventory tool
│   ├── manage_datasets.py    # Dataset management
│   ├── migrate_algorithm.py  # Algorithm migration helper
│   ├── manage_plugins.py     # Plugin management tool
│   └── run_dashboard.py      # Dashboard launcher
├── examples/           # Example scripts
│   └── (various example scripts)
├── config/             # Configuration files
│   └── (configuration modules)
├── db/                 # Database utilities
│   └── (database modules)
└── deprecated/         # Deprecated scripts (for reference only)
```

## Main Entry Points

### 1. CLI Interface (`cli/analyze.py`)
The main unified CLI interface accessible via `bioalgo` command:

```bash
# Run a single algorithm
bioalgo run --algorithm hoa --instance E-n22-k4 --iterations 100

# Run benchmark
bioalgo benchmark --algorithms "hoa,egto,foa" --instances "E-n22-k4,P-n16-k8"

# Run massive benchmark
bioalgo massive --runs 1000 --algorithm hoa --instances E-n22-k4
```

### 2. Plugin Management (`tools/manage_plugins.py`)
Manage algorithm plugins:

```bash
# List available plugins
bioalgo-plugins list

# Install a plugin
bioalgo-plugins install path/to/plugin.py

# Get plugin info
bioalgo-plugins info my_algorithm
```

### 3. Dashboard (`tools/run_dashboard.py`)
Launch the real-time monitoring dashboard:

```bash
python scripts/tools/run_dashboard.py
```

## Development Notes

- All new CLI commands should be added to the `cli/` directory
- Supporting tools and utilities go in `tools/`
- Example scripts for users go in `examples/`
- Do not add new scripts to `deprecated/`

## Import Structure

When importing from scripts in other parts of the project:

```python
# For CLI commands
from scripts.cli.analyze import main
from scripts.cli.run import run_algorithm

# For tools
from scripts.tools.clean import cleanup_results
from scripts.tools.inventory import generate_inventory
```