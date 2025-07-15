# 📖 BioAlgoCompare - Unified Command Reference

> Comprehensive guide for using BioAlgoCompare's command-line interface with scientific rigor and reproducibility.

## 📑 Table of Contents

1. [Quick Start](#quick-start)
2. [Unified CLI (`analyze.py`)](#unified-cli-analyzepy)
3. [Individual Algorithm Execution](#individual-algorithm-execution)
4. [Comparative Benchmarking](#comparative-benchmarking)
5. [Massive Benchmarking](#massive-benchmarking)
6. [Statistical Analysis](#statistical-analysis)
7. [Data Conversion](#data-conversion)
8. [Available Algorithms](#available-algorithms)
9. [VRP Instances](#vrp-instances)
10. [Output Files](#output-files)
11. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

```bash
# Run a single algorithm
python scripts/analyze.py run --algorithm sho --instance A-n32-k5

# Run comparative benchmark
python scripts/analyze.py benchmark --algorithms "sho,foa,egto" --instances "A-n32-k5,P-n16-k8"

# Run massive benchmark (1000+ runs)
python scripts/analyze.py massive --algorithm all --instances E-n22-k4 --runs 1000

# Perform statistical analysis
python scripts/analyze.py stats --csv results/benchmark_results.csv --out results/analysis
```

---

## 📊 Unified CLI (`analyze.py`)

The unified command-line interface provides all functionality through subcommands:

### Subcommands

| Command | Purpose | Example |
|---------|---------|---------|
| `run` | Execute single algorithm | `analyze.py run --algorithm ho --instance A-n32-k5` |
| `benchmark` | Compare multiple algorithms | `analyze.py benchmark --algorithms "ho,sho,foa"` |
| `massive` | Execute 1000+ runs | `analyze.py massive --runs 1000` |
| `stats` | Statistical analysis | `analyze.py stats --csv results.csv` |
| `convert` | Convert JSON to CSV | `analyze.py convert --json data.json` |
| `analyze_csv` | Analyze existing CSV | `analyze.py analyze_csv --csv data.csv` |

### Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--help` | Show help message | - |
| `--version` | Show version | - |

---

## 🎯 Individual Algorithm Execution

### Basic Usage

```bash
python scripts/analyze.py run [OPTIONS]
```

### Options

| Parameter | Short | Description | Default | Required |
|-----------|-------|-------------|---------|----------|
| `--algorithm` | `-a` | Algorithm name or "all" | - | Yes |
| `--instance` | `-i` | VRP instance name | - | Yes |
| `--iterations` | `-n` | Number of iterations | 100 | No |
| `--population` | `-p` | Population size | 30 | No |
| `--runs` | `-r` | Independent executions | 1 | No |
| `--seed` | `-s` | Random seed | None | No |
| `--visualize` | - | Show visualizations | True | No |
| `--save` | - | Save results | True | No |
| `--output` | `-o` | Output directory | results/ | No |
| `--parallel` | - | Use parallel execution | False | No |

### Examples

```bash
# Single run with visualization
python scripts/analyze.py run --algorithm ho --instance A-n32-k5 --visualize

# Multiple runs with specific parameters
python scripts/analyze.py run \
    --algorithm egto \
    --instance E-n51-k5 \
    --iterations 300 \
    --population 50 \
    --runs 10 \
    --seed 42

# All algorithms in parallel
python scripts/analyze.py run --algorithm all --instance P-n16-k8 --parallel
```

---

## 🔬 Comparative Benchmarking

### Basic Usage

```bash
python scripts/analyze.py benchmark [OPTIONS]
```

### Options

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--algorithms` | Comma-separated list | - | "ho,sho,foa" |
| `--instances` | Comma-separated list | All in data/vrp | "A-n32-k5,P-n16-k8" |
| `--runs` | Runs per algorithm | 30 | 50 |
| `--iterations` | Max iterations | 100 | 200 |
| `--population` | Population size | 30 | 40 |
| `--seed` | Random seed | None | 42 |
| `--parallel` | Parallel execution | False | - |
| `--output` | Output directory | results/benchmark_* | custom_dir |

### Examples

```bash
# Compare specific algorithms
python scripts/analyze.py benchmark \
    --algorithms "ho,sho,foa,egto" \
    --instances "A-n32-k5,E-n22-k4" \
    --runs 30 \
    --parallel

# Benchmark all algorithms
python scripts/analyze.py benchmark \
    --algorithms all \
    --instances "P-n16-k8" \
    --runs 50 \
    --iterations 200
```

---

## 📈 Massive Benchmarking

For statistically significant results (1000+ runs):

### Basic Usage

```bash
python scripts/analyze.py massive [OPTIONS]
```

### Options

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `--runs` | Number of runs | 1000 | No |
| `--algorithm` | Single algorithm or "all" | - | Yes |
| `--instances` | Comma-separated list | - | Yes |
| `--population` | Population size | 30 | No |
| `--iterations` | Max iterations | 100 | No |
| `--seed` | Base seed | None | No |
| `--parallel` | Use multiprocessing | False | No |
| `--checkpoint` | Checkpoint interval | 100 | No |
| `--resume` | Resume from checkpoint | False | No |

### Features

- **Checkpointing**: Automatic save every N runs
- **Resume capability**: Continue interrupted experiments
- **Progress tracking**: Real-time progress with ETA
- **Memory efficient**: Processes data in batches

### Examples

```bash
# Basic massive run
python scripts/analyze.py massive \
    --algorithm sho \
    --instances "A-n32-k5,E-n22-k4" \
    --runs 1000

# Resume interrupted run
python scripts/analyze.py massive \
    --algorithm egto \
    --instances "P-n16-k8" \
    --runs 5000 \
    --resume \
    --checkpoint 500

# All algorithms with parallel processing
python scripts/analyze.py massive \
    --algorithm all \
    --instances "E-n51-k5" \
    --runs 1000 \
    --parallel
```

---

## 📊 Statistical Analysis

### Basic Usage

```bash
python scripts/analyze.py stats [OPTIONS]
```

### Options

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--csv` | Input CSV file | Yes |
| `--out` | Output directory | Yes |
| `--alpha` | Significance level | No (0.05) |

### Analyses Performed

1. **Descriptive Statistics**
   - Mean, median, std deviation
   - Min, max, quartiles
   - Success rates

2. **Statistical Tests**
   - Friedman test
   - Nemenyi post-hoc test
   - Wilcoxon signed-rank test
   - Quade test

3. **Effect Size Measures**
   - Vargha-Delaney A12
   - Cliff's delta

4. **Visualizations**
   - Critical difference diagrams
   - Box plots
   - Convergence curves
   - Heat maps

### Example

```bash
python scripts/analyze.py stats \
    --csv results/massive_20240110_143022/results.csv \
    --out results/analysis_paper \
    --alpha 0.05
```

---

## 🔄 Data Conversion

### JSON to CSV Conversion

```bash
python scripts/analyze.py convert \
    --json results/benchmark_results.json \
    --csv results/benchmark_results.csv
```

### Analyze Existing CSV

```bash
python scripts/analyze.py analyze_csv \
    --csv results/existing_results.csv \
    --out results/analysis
```

---

## 🧬 Available Algorithms

| Code | Full Name | Year | Category |
|------|-----------|------|----------|
| `woa` | Whale Optimization Algorithm | 2016 | Marine mammals |
| `rro` | Raven Roosting Optimization | 2016 | Birds |
| `sho` | Spotted Hyena Optimizer | 2017 | Terrestrial mammals |
| `apa` | Artificial Pangolin Algorithm | 2025 | Terrestrial mammals |
| `egto` | Enhanced Gorilla Troops Optimizer | 2021 | Primates |
| `foa` | Flamingo Optimization Algorithm | 2024 | Birds |
| `ho` | Hippopotamus Optimization | 2024 | Semi-aquatic mammals |
| `smo` | Starling Murmuration Optimizer | 2024 | Birds |
| `mrfo` | Manta Ray Foraging Optimization | 2020 | Marine animals |
| `opa` | Orca Predator Algorithm | 2024 | Marine mammals |
| `bao` | Beluga Whale Optimization | 2022 | Marine mammals |
| `tga` | Tasmanian Devil Algorithm | 2022 | Terrestrial mammals |
| `aha` | Artificial Hummingbird Algorithm | 2021 | Birds |
| `fsa` | Fish Swarm Algorithm | 2002 | Fish |
| `slsa` | Sea Lion Algorithm | 2019 | Marine mammals |
| `eho` | Elephant Herding Optimization | 2016 | Terrestrial mammals |
| `lsa` | Lightning Search Algorithm | 2015 | Natural phenomena |

**Note**: `hoa` is an alias for `sho` (Spotted Hyena Optimizer)

---

## 📁 VRP Instances

Standard CVRP instances available in `data/vrp/`:

| Instance | Nodes | Vehicles | Optimal | Difficulty |
|----------|-------|----------|---------|------------|
| A-n32-k5 | 32 | 5 | 784 | Medium |
| P-n16-k8 | 16 | 8 | 450 | Easy |
| E-n22-k4 | 22 | 4 | 375 | Easy |
| B-n31-k5 | 31 | 5 | 672 | Medium |
| E-n51-k5 | 51 | 5 | 521 | Hard |

---

## 📂 Output Files

### Directory Structure

```
results/
├── benchmark_YYYYMMDD_HHMMSS/
│   ├── benchmark_results.json    # Raw results
│   ├── results.csv              # Tabulated results
│   ├── summary_report.txt       # Summary statistics
│   └── plots/                   # Visualizations
├── massive_YYYYMMDD_HHMMSS/
│   ├── results.csv              # All run data
│   ├── checkpoint_*.pkl         # Resume files
│   └── summary.json             # Summary metrics
└── analysis_YYYYMMDD_HHMMSS/
    ├── statistical_summary.json  # Full statistics
    ├── friedman_results.txt     # Test results
    ├── wilcoxon_matrix.csv      # Pairwise comparisons
    ├── critical_difference.png   # CD diagram
    └── convergence_curves.png    # Algorithm convergence
```

### File Formats

**results.csv**:
```csv
Algorithm,Instance,Run,Best_Cost,Time,Mean,Std,Success_Rate
HO,A-n32-k5,1,812.45,2.34,825.12,15.23,0.85
```

**statistical_summary.json**:
```json
{
  "friedman": {
    "statistic": 45.23,
    "p_value": 0.0001,
    "significant": true
  },
  "rankings": {
    "HO": 2.1,
    "SHO": 2.5,
    "EGTO": 3.2
  }
}
```

---

## 🔧 Troubleshooting

### Common Issues

1. **Module Not Found**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/optimizacion"
   ```

2. **Permission Denied**
   ```bash
   chmod +x scripts/analyze.py
   ```

3. **Memory Issues with Massive Runs**
   - Use smaller checkpoint intervals
   - Process instances sequentially
   - Reduce population size

4. **Parallel Execution Errors**
   - Disable with `--no-parallel`
   - Check CPU count availability
   - Ensure proper multiprocessing support

### Debug Mode

Add logging for detailed execution info:
```bash
python scripts/analyze.py run --algorithm ho --instance A-n32-k5 --log-level DEBUG
```

---

## 📚 Further Reading

- [Algorithm Implementations](../algorithms/README.md)
- [Statistical Methods](./guides/statistical_analysis.md)
- [VRP Problem Details](../problems/README.md)
- [Contributing Guide](../CONTRIBUTING.md)

---

*Last updated: January 2025*