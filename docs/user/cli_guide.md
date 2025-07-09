# CLI User Guide

This guide provides detailed information about using the BioAlgoCompare v2.0 unified command-line interface.

## Quick Start

```bash
# Get help
python scripts/cli/main.py --help

# Run a single algorithm
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5

# Run a small benchmark
python scripts/cli/main.py benchmark --algorithms "hoa,egto" --instances small --runs 30
```

## Commands Overview

BioAlgoCompare provides several specialized commands:

### Core Commands

- **`run`** - Execute individual algorithms on VRP instances
- **`benchmark`** - Comprehensive benchmarking with multiple algorithms/instances
- **`massive`** - Large-scale benchmarking with 1000+ runs and checkpointing
- **`analyze`** - Statistical analysis of results with hypothesis testing
- **`dashboard`** - Real-time monitoring and visualization

### Utility Commands

- **`info`** - Information and documentation
- **`tools`** - Maintenance utilities (clean, migrate, check installation)

## Detailed Command Usage

### `run` Command

Execute bio-inspired algorithms on VRP instances with various options.

#### Basic Usage

```bash
# Simple execution
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5

# With custom parameters
python scripts/cli/main.py run --algorithm egto --instance P-n16-k8 --population 50 --iterations 200
```

#### Multiple Runs

```bash
# Multiple independent runs
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5 --runs 30

# Parallel execution
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5 --runs 30 --parallel --workers 4
```

#### Advanced Features

```bash
# With metadata capture and monitoring
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5 --metadata --monitor

# With experiment tracking and plotting
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5 --track --plot --show

# Save in specific format
python scripts/cli/main.py run --algorithm hoa --instance A-n32-k5 --save --format json
```

#### Important Options

| Option | Description | Default |
|--------|-------------|---------|
| `--algorithm` | Algorithm to run (required) | - |
| `--instance` | VRP instance name (required) | - |
| `--population` | Population size | 30 |
| `--iterations` | Number of iterations | 100 |
| `--runs` | Number of independent runs | 1 |
| `--parallel` | Use parallel execution | False |
| `--metadata` | Capture system metadata | True |
| `--monitor` | Monitor resource usage | False |
| `--save` | Save results to file | False |

### `benchmark` Command

Comprehensive benchmarking with multiple algorithms and instances.

#### Benchmark Modes

The benchmark command supports three modes:

1. **`run`** (default) - Execute new benchmarks
2. **`analyze`** - Analyze existing results
3. **`compare`** - Compare specific algorithms

#### Running Benchmarks

```bash
# Basic benchmark
python scripts/cli/main.py benchmark --algorithms "hoa,egto,foa" --instances "A-n32-k5,P-n16-k8" --runs 30

# Using predefined instance sets
python scripts/cli/main.py benchmark --algorithms "hoa,egto" --instances small --runs 30

# All algorithms on standard instances
python scripts/cli/main.py benchmark --algorithms all --instances standard --runs 100 --parallel
```

#### Predefined Instance Sets

| Set | Instances | Description |
|-----|-----------|-------------|
| `tiny` | P-n16-k8, E-n22-k4 | Quick testing |
| `small` | P-n16-k8, E-n22-k4, A-n32-k5 | Small experiments |
| `medium` | A-n45-k7, B-n50-k7, E-n51-k5 | Medium complexity |
| `large` | A-n60-k9, B-n78-k10, E-n101-k8 | Large instances |
| `standard` | Common benchmark set | Standard evaluation |
| `all` | All available instances | Complete evaluation |

#### Analysis Mode

```bash
# Analyze existing results
python scripts/cli/main.py benchmark --mode analyze --input results/benchmark_20240115.json

# Generate statistical report
python scripts/cli/main.py benchmark --mode analyze --input results/ --statistical --report
```

#### Compare Mode

```bash
# Compare specific algorithms
python scripts/cli/main.py benchmark --mode compare --algorithms "hoa,egto" --instances standard --statistical
```

### `massive` Command

Large-scale benchmarking with automatic checkpointing for scientific rigor.

#### Basic Usage

```bash
# Massive benchmark with 1000 runs
python scripts/cli/main.py massive --algorithms "hoa,egto" --instances "E-n22-k4" --runs 1000

# With parallel execution
python scripts/cli/main.py massive --algorithms "hoa,egto" --instances "E-n22-k4" --runs 1000 --parallel --workers 8
```

#### Checkpointing and Resume

```bash
# Resume interrupted benchmark
python scripts/cli/main.py massive --algorithms "hoa,egto" --instances "E-n22-k4" --runs 1000 --resume

# Custom checkpoint interval
python scripts/cli/main.py massive --algorithms "hoa" --instances "E-n22-k4" --runs 1000 --checkpoint-interval 50
```

#### Resource Monitoring

```bash
# With metadata and resource monitoring
python scripts/cli/main.py massive --algorithms "hoa" --instances "E-n22-k4" --runs 1000 --metadata --monitor
```

### `analyze` Command

Statistical analysis with hypothesis testing and effect size calculations.

#### Basic Analysis

```bash
# Analyze results directory
python scripts/cli/main.py analyze --input results/

# Analyze specific file
python scripts/cli/main.py analyze --input results/benchmark_results.json
```

#### Statistical Tests

```bash
# Multiple statistical tests
python scripts/cli/main.py analyze --input results/ --tests "friedman,kruskal,mannwhitney"

# With effect sizes
python scripts/cli/main.py analyze --input results/ --tests "friedman" --effect-size

# Custom significance level
python scripts/cli/main.py analyze --input results/ --tests "friedman" --alpha 0.01
```

#### Output Formats

```bash
# HTML report with plots
python scripts/cli/main.py analyze --input results/ --format html --plot

# JSON output
python scripts/cli/main.py analyze --input results/ --format json --output analysis/

# PDF report (if available)
python scripts/cli/main.py analyze --input results/ --format pdf
```

### `dashboard` Command

Real-time monitoring and visualization interface.

```bash
# Launch dashboard
python scripts/cli/main.py dashboard

# Custom port and host
python scripts/cli/main.py dashboard --port 8080 --host 0.0.0.0

# Debug mode
python scripts/cli/main.py dashboard --debug
```

## Available Algorithms

| Code | Algorithm Name | Year |
|------|----------------|------|
| `aha` | Artificial Hummingbird Algorithm | 2022 |
| `apo` | Artificial Protozoa Optimizer | 2024 |
| `egto` | Enhanced Gorilla Troops Optimization | 2024 |
| `ewa` | Earthworm Algorithm | 2018 |
| `fgo` | Flamingo Optimization Algorithm | 2025 |
| `foa` | Fossa Optimization Algorithm | 2024 |
| `fsa` | Flamingo Search Algorithm | 2021 |
| `gto` | Gorilla Troops Optimization | 2021 |
| `gvoa` | Griffon Vultures Optimization Algorithm | 2025 |
| `hho` | Harris Hawks Optimization | 2019 |
| `hoa` | Hyena Optimization Algorithm | 2017 |
| `mrfo` | Manta Ray Foraging Optimization | 2020 |
| `opa` | Orca Predator Algorithm | 2021 |
| `rro` | Raven Roosting Optimization | 2016 |
| `sho` | Spotted Hyena Optimizer | 2017 |
| `sma` | Slime Mould Algorithm | 2020 |
| `smo` | Starling Murmuration Optimizer | 2022 |
| `woa` | Whale Optimization Algorithm | 2016 |

## Available VRP Instances

Standard CVRPLIB instances are available in the `data/vrp/` directory:

- **Small**: P-n16-k8, E-n22-k4, A-n32-k5
- **Medium**: A-n45-k7, B-n50-k7, E-n51-k5  
- **Large**: A-n60-k9, B-n78-k10, E-n101-k8

## Output Formats

### JSON Format
Complete structured data with metadata:
```json
{
  "algorithm_info": {...},
  "problem_info": {...},
  "runs": [...],
  "statistics": {...},
  "metadata": {...}
}
```

### CSV Format
Tabular data for analysis:
```csv
algorithm,instance,run,fitness,execution_time,seed
hoa,A-n32-k5,1,784.5,2.34,42
```

### Metadata Format
Enhanced format with complete reproducibility information including system details, git state, and dependencies.

## Tips and Best Practices

### For Research

1. **Always use metadata capture**: `--metadata`
2. **Use sufficient runs**: Minimum 30 runs for statistical validity
3. **Set explicit seeds**: `--seed 42` for reproducibility
4. **Use parallel execution**: `--parallel` for efficiency
5. **Monitor resources**: `--monitor` for resource usage data

### For Development

1. **Start with small instances**: Use `tiny` or `small` sets
2. **Use verbose output**: `-v` for debugging
3. **Test with single runs**: Before scaling up
4. **Use checkpoints**: For massive benchmarks

### For Publications

1. **Use massive benchmarks**: 1000+ runs for statistical power
2. **Capture complete metadata**: For reproducibility
3. **Perform statistical analysis**: Use `analyze` command
4. **Generate reports**: HTML format for presentations

## Troubleshooting

### Common Issues

1. **Algorithm not found**: Check available algorithms with `--help`
2. **Instance not found**: Verify instance files in `data/vrp/`
3. **Import errors**: Run `pip install -r requirements.txt`
4. **Permission errors**: Check output directory permissions

### Getting Help

```bash
# General help
python scripts/cli/main.py --help

# Command-specific help
python scripts/cli/main.py COMMAND --help

# Check installation
python scripts/cli/main.py tools check-installation
```

## Migration from v1

The new CLI maintains backward compatibility while providing enhanced features:

- Old script paths still work but are deprecated
- New unified interface provides better organization
- Enhanced metadata capture and monitoring
- Improved parallel execution and checkpointing

For migration guidance, see the [migration guide](../developer/guides/migration_guide.md).