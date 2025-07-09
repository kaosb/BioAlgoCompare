# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioAlgoCompare is a rigorous statistical evaluation platform for bio-inspired algorithms solving the Vehicle Routing Problem (VRP). The project implements 18 metaheuristic algorithms with extensive benchmarking capabilities, statistical analysis, and scientific visualization tools.

## Common Development Commands

### Installation and Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running Tests
```bash
# Run all tests with coverage
pytest --cov=algorithms --cov=problems --cov=utils --cov=scripts --cov-report=term-missing --cov-report=xml

# Run specific test file
pytest tests/test_algorithms_convergence.py

# Run tests excluding slow ones
pytest -k "not slow"

# Run tests with tox for multiple Python versions
tox
```

### Linting and Code Quality
```bash
# Run ruff linter (configured in pyproject.toml)
ruff check .

# Format code with ruff
ruff format .

# Check specific directories
ruff check algorithms/ problems/ utils/ scripts/
```

### Running Algorithms
```bash
# Basic algorithm execution
python scripts/analyze.py run --algorithm hoa --instance E-n22-k4 --iterations 100 --population 30

# Using installed CLI command
bioalgo run --algorithm egto --instance P-n16-k8 --iterations 100 --population 30

# Run with visualization
bioalgo run --algorithm foa --instance A-n32-k5 --visualize --save
```

### Benchmarking Commands
```bash
# Run benchmark with multiple algorithms
bioalgo benchmark --run-benchmark --instances "E-n22-k4,P-n16-k8" --algorithms "hoa,foa,egto" --runs 10 --parallel

# Massive benchmark (1000+ runs)
bioalgo massive --runs 1000 --algorithm hoa --algorithm egto --instances E-n22-k4 --parallel --resume

# Analyze existing results
bioalgo benchmark --input results/benchmark_results.json
```

## Architecture Overview

### Core Components

1. **Algorithm Framework** (`algorithms/`)
   - Base classes: `Individual` and `MetaheuristicAlgorithm` in `base.py`
   - All algorithms inherit from these base classes and implement required methods
   - Each algorithm must implement: `initialize_population()`, `move()` (for individuals), and algorithm-specific movement rules

2. **Problem Definition** (`problems/`)
   - `VRPProblem` class handles VRP instance loading, distance matrix computation, and solution evaluation
   - Supports CVRPLIB format for standard benchmark instances
   - Implements penalty-based constraint handling

3. **Benchmarking System** (`utils/benchmarking.py`, `utils/improved/enhanced_benchmarking.py`)
   - Supports single runs, parallel execution, and massive benchmarking
   - Automatic checkpoint/resume functionality for interrupted runs
   - Results stored in JSON format with comprehensive metrics

4. **Statistical Analysis** (`utils/statistical_analysis.py`, `utils/improved/enhanced_statistics.py`)
   - Non-parametric tests: Friedman, Kruskal-Wallis, Mann-Whitney
   - Post-hoc analysis: Nemenyi, Wilcoxon with Bonferroni correction
   - Effect size calculations: Cliff's Delta, Vargha-Delaney
   - 95% confidence intervals and critical difference diagrams

5. **Main Entry Points**
   - `scripts/analyze.py`: Unified CLI interface (installed as `bioalgo` command)
   - `scripts/run_massive.py`: Specialized script for massive parallel benchmarks
   - All scripts use Click framework for professional CLI interfaces

### Key Design Patterns

1. **Algorithm Implementation Pattern**
   ```python
   class NewAlgorithm(MetaheuristicAlgorithm):
       def __init__(self, problem, population_size=30, max_iterations=100, seed=None):
           super().__init__(problem, population_size, max_iterations, seed)
           # Algorithm-specific parameters
       
       def _create_individual(self):
           # Return instance of algorithm-specific Individual subclass
           pass
       
       def initialize_population(self):
           # Initialize population with _create_individual()
           pass
   ```

2. **VRP Solution Encoding**
   - Solutions use ordinal encoding: continuous values → permutation
   - Route construction respects vehicle capacity constraints
   - Penalty-based evaluation for infeasible solutions

3. **Parallel Execution**
   - Uses multiprocessing.Pool for algorithm-level parallelism
   - Progress tracking with tqdm
   - Automatic CPU core detection and load balancing

### Important Implementation Details

1. **Random Seed Management**
   - All algorithms accept seed parameter for reproducibility
   - Seeds propagated through numpy and random modules
   - Critical for scientific comparison

2. **Performance Metrics**
   - Best fitness, mean fitness, standard deviation
   - Execution time per iteration
   - Gap to optimal solution (when known)
   - Convergence history tracking

3. **File Organization**
   - Results stored with timestamp: `{instance}_{timestamp}.csv`
   - Summary files: `{instance}_{timestamp}_summary.csv`
   - Benchmark reports in HTML format with interactive visualizations

4. **Error Handling**
   - Graceful handling of algorithm failures
   - Checkpoint system prevents loss of partial results
   - Comprehensive logging to `analyze.log` and `benchmark.log`

## VRP-Specific Considerations

1. **Instance Files** (`data/vrp/`)
   - Standard CVRPLIB format
   - NODE_COORD_SECTION and DEMAND_SECTION required
   - Depot always at index 0

2. **Solution Representation**
   - Permutation of customer nodes (excluding depot)
   - Routes constructed greedily respecting capacity
   - Invalid solutions heavily penalized but not rejected

3. **Optimal Values**
   - Stored in `utils/benchmarking.py:OPTIMAL_VALUES`
   - Used for gap calculation in benchmarks
   - Critical for algorithm comparison

## Testing Strategy

1. **Unit Tests** (`tests/`)
   - Algorithm convergence tests
   - VRP operator tests
   - Statistical analysis validation
   - CLI command tests

2. **Integration Tests**
   - End-to-end benchmarking
   - Parallel execution verification
   - Checkpoint/resume functionality

3. **Performance Tests**
   - Timing tests for iteration speed
   - Scalability tests with different instance sizes

## Important Notes

- The project is actively used for academic research (CISTI 2025 conference)
- Maintain backward compatibility with existing result formats
- All algorithms must be deterministic when seed is provided
- Performance is critical - avoid unnecessary object creation in hot loops
- Statistical rigor is paramount - use appropriate tests for sample sizes