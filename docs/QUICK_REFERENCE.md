# BioAlgoCompare Quick Reference Guide

## Installation

```bash
# Clone and setup
git clone https://github.com/your-org/bioalgocompare.git
cd bioalgocompare
make setup  # or: python scripts/setup_environment.py

# Verify installation
bioalgo check-installation
```

## Common Commands

### Running Algorithms

```bash
# Basic run
bioalgo run -a hoa -i E-n22-k4

# With custom parameters
bioalgo run -a hoa -i E-n22-k4 --population 50 --iterations 200

# Multiple runs with different seeds
bioalgo run -a hoa -i E-n22-k4 --runs 30

# With visualization
bioalgo run -a hoa -i E-n22-k4 --visualize --save
```

### Benchmarking

```bash
# Compare multiple algorithms
bioalgo benchmark --algorithms hoa,egto,foa --instances E-n22-k4,E-n33-k4 --runs 30

# Parallel benchmark
bioalgo benchmark --algorithms all --instances E-n22-k4 --parallel --workers 8

# Resume interrupted benchmark
bioalgo benchmark --resume checkpoint.json
```

### Analysis

```bash
# Analyze results
bioalgo analyze results.json --statistical --visualize

# Compare algorithms
bioalgo analyze results.json --compare hoa,egto,foa --test friedman

# Export results
bioalgo analyze results.json --export latex --output table.tex
```

### Performance Optimization

```bash
# Run with parallel optimization
bioalgo optimize parallel -a hoa -i E-n22-k4 -r 100 --strategy auto

# Profile algorithm
bioalgo optimize profile -f run_algorithm --memory --output profile.txt

# Monitor system resources
bioalgo optimize system --benchmark
```

## Available Algorithms

| Code | Algorithm | Category | Year |
|------|-----------|----------|------|
| `hoa` | Horse Optimization Algorithm | Animal | 2021 |
| `egto` | Enhanced Gorilla Troops Optimizer | Physics | 2022 |
| `foa` | Fruit Fly Optimization Algorithm | Swarm | 2012 |
| `woa` | Whale Optimization Algorithm | Animal | 2016 |
| `hho` | Harris Hawks Optimization | Animal | 2019 |
| `gto` | Gorilla Troops Optimizer | Physics | 2021 |
| `gwo` | Grey Wolf Optimizer | Animal | 2014 |
| `rro` | Raven Roosting Optimization | Animal | 2022 |
| `sho` | Spotted Hyena Optimizer | Animal | 2017 |
| `sma` | Slime Mould Algorithm | Nature | 2020 |
| `smo` | Spider Monkey Optimization | Animal | 2014 |
| `opa` | Optimal Placement Algorithm | Human | 2019 |
| `mrfo` | Manta Ray Foraging Optimization | Animal | 2020 |
| `aha` | Artificial Hummingbird Algorithm | Animal | 2022 |
| `apo` | Artificial Protozoa Optimizer | Micro | 2022 |
| `ewa` | Earthworm Algorithm | Animal | 2018 |
| `fsa` | Fish School Algorithm | Swarm | 2008 |
| `gvoa` | Growth Optimizer with Vegetation | Nature | 2023 |

## Problem Instances

### Small (n < 50)
- `E-n22-k4`: 22 customers, 4 vehicles
- `E-n23-k3`: 23 customers, 3 vehicles  
- `E-n30-k3`: 30 customers, 3 vehicles
- `E-n33-k4`: 33 customers, 4 vehicles

### Medium (50 ≤ n < 100)
- `E-n51-k5`: 51 customers, 5 vehicles
- `E-n76-k7`: 76 customers, 7 vehicles
- `E-n76-k8`: 76 customers, 8 vehicles
- `E-n76-k10`: 76 customers, 10 vehicles

### Large (n ≥ 100)
- `E-n101-k8`: 101 customers, 8 vehicles
- `E-n101-k14`: 101 customers, 14 vehicles

## Parameter Guidelines

### Population Size
- Small instances (n < 50): 20-30
- Medium instances (50 ≤ n < 100): 30-50
- Large instances (n ≥ 100): 50-100

### Iterations
- Quick test: 50-100
- Normal run: 100-200
- High quality: 500-1000

### Algorithm-Specific Parameters

```bash
# HOA
bioalgo run -a hoa -i E-n22-k4 --pa 0.3 --pc 0.1 --beta 0.5

# EGTO  
bioalgo run -a egto -i E-n22-k4 --p 0.03 --beta 3

# WOA
bioalgo run -a woa -i E-n22-k4 --a 2 --b 1
```

## Output Files

### Result Structure
```
results/
├── {instance}_{timestamp}.csv          # Detailed results
├── {instance}_{timestamp}_summary.csv  # Summary statistics
├── {instance}_{timestamp}_conv.png     # Convergence plot
└── {instance}_{timestamp}_routes.json  # Best routes found
```

### Benchmark Reports
```
reports/
├── benchmark_{timestamp}.json          # Raw results
├── benchmark_{timestamp}_report.html   # Interactive report
├── benchmark_{timestamp}_stats.csv     # Statistical summary
└── benchmark_{timestamp}_plots/        # Visualization plots
```

## Environment Variables

```bash
# Set random seed globally
export BIOALGO_SEED=42

# Enable debug logging
export BIOALGO_LOG_LEVEL=DEBUG

# Set cache directory
export BIOALGO_CACHE_DIR=/path/to/cache

# Enable GPU acceleration
export BIOALGO_USE_GPU=1
```

## Configuration File

Create `~/.bioalgocompare/config.json`:

```json
{
  "default_algorithm": "hoa",
  "default_population": 30,
  "default_iterations": 100,
  "parallel_workers": 8,
  "cache_enabled": true,
  "output_directory": "./results",
  "visualization": {
    "style": "seaborn",
    "dpi": 300,
    "format": "png"
  }
}
```

## Python API

### Basic Usage

```python
from bioalgocompare import algorithms, problems, analyze

# Load problem
problem = problems.VRPProblem("data/vrp/E-n22-k4.vrp")

# Run algorithm
algo = algorithms.HOA(problem, population_size=30, max_iterations=100)
result = algo.run()

# Analyze results
analysis = analyze.analyze_single(result)
print(f"Best: {analysis['best_fitness']}")
print(f"Gap: {analysis['gap_to_optimal']}%")
```

### Batch Experiments

```python
from bioalgocompare import experiments

# Define experiment
exp = experiments.Experiment(
    algorithms=['hoa', 'egto', 'foa'],
    instances=['E-n22-k4', 'E-n33-k4'],
    n_runs=30
)

# Run experiment
results = exp.run(parallel=True)

# Statistical analysis
exp.analyze(results, tests=['friedman', 'nemenyi'])
```

### Custom Algorithm

```python
from bioalgocompare.algorithms import MetaheuristicAlgorithm

class MyAlgorithm(MetaheuristicAlgorithm):
    def initialize_population(self):
        # Initialize your population
        pass
        
    def update_population(self):
        # Your algorithm logic
        pass
```

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `Module not found` | Run `pip install -e .` |
| `Out of memory` | Reduce population size or use `--memory-limit` |
| `Slow execution` | Enable parallel: `--parallel --workers 8` |
| `Different results` | Set seed: `--seed 42` |
| `Import errors` | Check Python version (≥3.8) |

### Debug Mode

```bash
# Enable debug logging
bioalgo --debug run -a hoa -i E-n22-k4

# Profile execution
bioalgo optimize profile -f run_algorithm --memory

# Check system
bioalgo optimize system --show-cpu --show-memory
```

## Best Practices

1. **Always set seeds** for reproducibility
2. **Run multiple times** (30+ runs) for statistical validity
3. **Use appropriate tests** (non-parametric for small samples)
4. **Monitor resources** with `--monitor` flag
5. **Cache results** to avoid recomputation
6. **Document parameters** in experiment logs

## Getting Help

```bash
# General help
bioalgo --help

# Command-specific help
bioalgo run --help

# List all algorithms
bioalgo info algorithms

# List all instances
bioalgo info instances

# Check configuration
bioalgo info config
```

## Links

- **Documentation**: `/docs` directory
- **Examples**: `/examples` directory
- **Issues**: GitHub Issues
- **Updates**: Check CHANGELOG.md