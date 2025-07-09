# BioAlgoCompare Quick Start Guide

Welcome to BioAlgoCompare! This guide will help you get started with using bio-inspired optimization algorithms for solving Vehicle Routing Problems (VRP).

## Table of Contents
1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Running Multiple Algorithms](#running-multiple-algorithms)
4. [Comparative Benchmarking](#comparative-benchmarking)
5. [Massive Statistical Analysis](#massive-statistical-analysis)
6. [Visualization Options](#visualization-options)
7. [Common Use Cases](#common-use-cases)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bioalgocompare.git
cd bioalgocompare
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package:
```bash
pip install -e .
```

## Basic Usage

### Running a Single Algorithm

The simplest way to run an algorithm is using the unified CLI:

```bash
# Run Earthworm Algorithm on a small VRP instance
python scripts/analyze.py run --algorithm ewa --instance P-n16-k8 --iterations 100

# Run with more control
python scripts/analyze.py run \
    --algorithm foa \
    --instance E-n22-k4 \
    --population 50 \
    --iterations 200 \
    --runs 5 \
    --seed 42
```

### Available Options

- `--algorithm/-a`: Algorithm to use (see list below)
- `--instance/-i`: VRP instance name
- `--iterations/-n`: Number of iterations (default: 100)
- `--population/-pop`: Population size (default: 30)
- `--runs/-r`: Number of independent runs (default: 1)
- `--seed/-s`: Random seed for reproducibility
- `--parallel/-p`: Enable parallel execution
- `--visualize/--no-visualize`: Show/hide visualizations

### Available Algorithms

| Code | Algorithm Name | Best For |
|------|---------------|----------|
| `ewa` | Earthworm Algorithm | Balanced exploration/exploitation |
| `foa` | Fossa Optimization | Strong exploitation |
| `aha` | Artificial Hummingbird | Complex search spaces |
| `gto` | Gorilla Troops Optimizer | Multi-modal problems |
| `woa` | Whale Optimization | Global optimization |
| `hho` | Harris Hawks Optimization | Fast convergence |
| `sma` | Slime Mould Algorithm | Adaptive search |
| `opa` | Orca Predator Algorithm | VRP-specific optimization |

Use `all` to run all algorithms.

## Running Multiple Algorithms

### Sequential Comparison
```bash
# Run all algorithms on the same instance
python scripts/analyze.py run --algorithm all --instance P-n16-k8
```

### Parallel Execution
```bash
# Run multiple algorithms in parallel
python scripts/analyze.py run \
    --algorithm all \
    --instance E-n22-k4 \
    --runs 10 \
    --parallel
```

## Comparative Benchmarking

For rigorous algorithm comparison with statistical analysis:

```bash
# Run a new benchmark
python scripts/analyze.py benchmark --run-benchmark \
    --instances P-n16-k8,E-n22-k4,A-n32-k5 \
    --algorithms ewa,foa,gto,woa \
    --runs 30 \
    --parallel

# Analyze existing results
python scripts/analyze.py benchmark --input results/benchmark_20250708.csv
```

The benchmark mode provides:
- Statistical significance tests (Friedman, Wilcoxon)
- Performance rankings
- HTML report with visualizations
- CSV export of all results

## Massive Statistical Analysis

For publication-quality results with 1000+ runs:

```bash
# Run massive benchmark (warning: time-intensive)
python scripts/analyze.py massive \
    --algorithm ewa,foa,gto \
    --runs 1000 \
    --parallel

# Resume interrupted benchmark
python scripts/analyze.py massive --resume
```

Features:
- Automatic checkpointing every 100 runs
- Comprehensive statistical analysis
- Publication-ready LaTeX tables
- Detailed convergence analysis

## Visualization Options

### Solution Visualization
Shows the routes found by the algorithm:
- Depot marked with a square
- Customers as circles
- Routes in different colors

### Convergence Plots
Shows fitness improvement over iterations:
- Best fitness curve
- Average fitness (if multiple runs)
- Iteration milestones

### Statistical Plots
- Box plots for algorithm comparison
- Heatmaps for pairwise comparisons
- Critical difference diagrams

## Common Use Cases

### 1. Quick Algorithm Test
```bash
# Test if an algorithm works on your problem
python scripts/analyze.py run --algorithm ewa --instance P-n16-k8 --visualize
```

### 2. Find Best Algorithm for an Instance
```bash
# Compare all algorithms with moderate runs
python scripts/analyze.py benchmark --run-benchmark \
    --instances YOUR_INSTANCE \
    --algorithms all \
    --runs 20
```

### 3. Reproducible Research
```bash
# Use fixed seed for reproducibility
python scripts/analyze.py run \
    --algorithm foa \
    --instance E-n22-k4 \
    --runs 30 \
    --seed 12345
```

### 4. Production Optimization
```bash
# Focus on best performers with more iterations
python scripts/analyze.py run \
    --algorithm opa \
    --instance YOUR_INSTANCE \
    --iterations 500 \
    --population 100 \
    --runs 10 \
    --parallel
```

### 5. Algorithm Development
```python
# Use programmatically for custom algorithms
from algorithms import get_algorithm
from problems.vrp import VRPProblem

# Load problem
problem = VRPProblem()
problem.load_instance('P-n16-k8')

# Run algorithm
AlgoClass = get_algorithm('ewa')
algo = AlgoClass(problem, population_size=30)
algo.initialize_population()
best = algo.run(iterations=100)

print(f"Best fitness: {best.fitness()}")
```

## Tips for Best Results

1. **Population Size**: Generally 30-50 works well, but larger instances may benefit from 100+
2. **Iterations**: Start with 100-200 for testing, use 500+ for final results
3. **Multiple Runs**: Use at least 30 runs for statistical validity
4. **Parallel Execution**: Enable for multiple runs or algorithms
5. **Seed Setting**: Always set seed for reproducible research

## Next Steps

- Read the [Algorithm Selection Guide](ALGORITHM_SELECTION_GUIDE.md) to choose the best algorithm
- Check the [Utils Module Guide](technical/UTILS_MODULE_GUIDE.md) for advanced features
- See [Integration Guide](INTEGRATION_GUIDE.md) to add custom algorithms
- Review [Statistical Analysis Guide](STATISTICAL_ANALYSIS_GUIDE.md) for research

## Troubleshooting

### Memory Issues
- Reduce population size
- Use fewer parallel workers
- Process results in batches

### Slow Performance
- Enable parallel execution
- Reduce visualization frequency
- Use compiled operators

### No Convergence
- Increase iterations
- Try different algorithms
- Adjust population size

For more help, check the full documentation or open an issue on GitHub.