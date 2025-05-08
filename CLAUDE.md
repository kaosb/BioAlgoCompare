# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project implements various bio-inspired metaheuristic optimization algorithms for solving Vehicle Routing Problems (VRP). It's part of academic research for the Chilean Computing Conference 2025, aimed at evaluating and comparing recent bio-inspired algorithms applied to VRP.

## **User Documentation and Usage Instructions**

This section provides a consistent, professional, and complete reference of the scripts, their parameters, possible formats, architecture, and main customizable features, as required for reproducibility and systematic experimentation.

### **Main Scripts Overview**

| Script                | Purpose                                                                           | Entry Point       |
|----------------------|----------------------------------------------------------------------------------|------------------|
| `run.py`             | Execution of a metaheuristic algorithm or all algorithms for one VRP instance      | CLI              |
| `analyze_results.py` | Run benchmarks across algorithms and instances, full analysis, stats/visual report | CLI              |
| Custom algos         | New algorithms via adding to `algorithms/`                                         | Python import    |

#### **Order of Precedence**
- For simple runs, use `run.py`
- For integrated benchmarking/analysis, use `analyze_results.py` (superseedes `run.py` for research workflows)
- All CLIs support comprehensive parameterization; `analyze_results.py` can both run new benchmarks or analyze existing result files

---

### **Script: run.py**

Launches metaheuristic optimization for a given VRP instance.

#### **Parameters / CLI options**

| Option                      | Purpose/Format                               | Default      |
|-----------------------------|----------------------------------------------|--------------|
| `--algorithm`, `-a`         | Algorithm: `hoa`, `apo`, `egto`, `fgo`, `foa`, `all` | (Required)   |
| `--instance`, `-i`          | VRP Instance name (without extension)         | (Required)   |
| `--iterations`, `-n`        | Number of main iterations (INT)               | 100          |
| `--population`, `-pop`      | Population size (INT)                         | 30           |
| `--runs`, `-r`              | Number of independent runs                    | 1            |
| `--seed`, `-s`              | Random seed (INT)                             | None         |
| `--visualize/--no-visualize`| Toggle visual output (matplotlib, PNG)        | True         |
| `--save/--no-save`          | Save results to CSV/PNG                       | True         |
| `--parallel/--no-parallel`/`-p` | Enable parallel execution                | False        |

#### **Formats Supported**
- VRP Instances: `data/vrp/{NAME}.vrp` (CVRPLIB format)
- Output: Results as CSV in `results/`, solution/convergence as PNG images

#### **Example Usages**
```
python run.py --algorithm hoa --instance A-n32-k5 --iterations 100 --population 30
python run.py --algorithm all --instance A-n32-k5 --runs 5 --parallel
python run.py --algorithm egto --instance E-n22-k4 --iterations 300 --population 50
```

---

### **Script: analyze_results.py**

Provides an integrated workflow to run new experiments/benchmarks or analyze existing result files. Features systematic comparison, stats, and advanced reporting.

#### **Parameters / CLI options**

| Option                      | Purpose/Format                                         | Default   |
|-----------------------------|--------------------------------------------------------|-----------|
| `--input`, `-i`             | Input file (CSV or JSON benchmark output)              |           |
| `--run-benchmark/--no-run-benchmark` | Run new experiments as benchmark                   | False     |
| `--instances`, `-inst`      | Instances to run (multi, if run-benchmark)            |           |
| `--algorithms`, `-a`        | Algorithms to run (multi, if run-benchmark)           |           |
| `--runs`, `-r`              | Runs per algorithm/instance                           | 5         |
| `--iterations`, `-n`        | Iterations per run                                    | 100       |
| `--population`, `-p`        | Population size per algorithm                         | 30        |
| `--seed`, `-s`              | Random seed for reproducibility                       | 42        |
| `--parallel/--no-parallel`  | Enable parallel execution                             | False     |
| `--optimize/--no-optimize`  | Apply local search to solutions                       | False     |
| `--output-dir`, `-o`        | Output directory (auto if not specified)              | <auto>    |

#### **Formats Supported**
- VRP Instance files: `data/vrp/*.vrp`
- Benchmark input: CSV (flat, with Algorithm/Instance columns) or JSON benchmark as saved by `run_benchmark`
- Results: HTML benchmark/statistical report, PNG graphs saved under `results/` or the output dir selected

#### **Example Usages**
```
python analyze_results.py --run-benchmark --optimize --parallel \
    --instances E-n22-k4 P-n16-k8 \
    --algorithms hoa foa egto
python analyze_results.py --input results/benchmark_20250508_123456.json
```

---

## **Architecture Overview**

- **Core (algorithms/)**: Each bio-inspired algorithm implements a subclass of the base metaheuristic interface (`MetaheuristicAlgorithm`). All receive `problem`, `population_size`, `max_iterations`, and optionally `seed` as parameters. Additional algorithm-specific parameters are set in each class.
- **Problems (problems/)**: Implements VRP as a combinatorial optimization problem, including decoding from continuous domain to routes, enforcing constraints, and evaluating fitness.
- **Utils (utils/)**: Provides genetic operators (`operators.py`), VRP-specific local search (`vrp_operators.py`), advanced statistical analysis (`statistical_analysis.py`), visualization (`visualization.py`), and benchmarking tools (`benchmarking.py`).
- **Data (data/vrp/)**: Benchmarking VRP instances in standard format.
- **Scripts**: `run.py` and `analyze_results.py` encapsulate the main research/evaluation workflows.

#### **Main Customizable Features (Parametrization)**
- `population_size`, `max_iterations`, `seed`, and algorithm-specific parameters can be set per execution
- Integration of custom algorithms requires subclassing `MetaheuristicAlgorithm` (see `algorithms/base.py`)
- CLI scripts allow full parameterization of workloads including instance/algorithm selection, repetitions, parallelization, and output control
- Benchmark/analysis script can apply local search to all outputs (toggleable with `--optimize`)

---

### **Example Usage/Workflows**
1. **Run and benchmark all algorithms:**
```bash
python run.py -a all -i E-n22-k4 -r 5 -p
```

2. **Comprehensive benchmarking & statistical analysis:**
```bash
python analyze_results.py --run-benchmark --optimize --parallel -inst E-n22-k4 A-n32-k5 -a all
```

3. **Analyze existing benchmark results:**
```bash
python analyze_results.py --input results/benchmark_20250508_123456.json
```

---

## **Professional and Consistent Documentation**

- All scripts use professional, consistent CLI documentation and include usage notes via the `--help` flag.
- All features and parameters can be accessed via CLI, and each script checks/corrects for invalid combinations. Scripts are robust for research use.
- Main scripts support both single-run/algorithm and batched, parallel multi-algorithm benchmarking.
- Full provenance and reproducibility: random seed, parameters, and all main outputs (solutions, convergence, reports) are saved/visualized.

---

## **Adding New Algorithms**

- To add a new method, subclass `MetaheuristicAlgorithm` in `algorithms/base.py` and implement: population initialization, update, convergence
- Add import and CLI mapping in both `run.py` and `analyze_results.py` for integration with all experiment workflows
- Ensure new methods respect the VRP solution interface: operate over encoding as described in `problems/vrp.py`

---

## **References**
- All information provided here is based on the latest project state as of 2024-06
- For more detail on improvements, see `README_MEJORAS.md`
- For reproducibility, always specify seed and record command line used

---

**This documentation ensures a consistent, appropriate, and professional reference for all code users, reviewers, and future maintainers.**

## Project Architecture (Quick Reference)

### Core Components

1. **Algorithms** (`algorithms/` directory):
   - Each file implements a different bio-inspired algorithm
   - All inherit from the base class in `base.py`
   - Algorithms include HOA, APO, EGTO, FGO, FOA and others

2. **Problems** (`problems/` directory):
   - Defines problem representations
   - Current implementation focuses on VRP in `vrp.py`

3. **Utilities** (`utils/` directory):
   - `operators.py`: Basic genetic operators
   - `visualization.py`: Basic visualization tools
   - `benchmarking.py`: Tools for systematic algorithm comparison
   - `statistical_analysis.py`: Statistical tests and analysis
   - `vrp_operators.py`: VRP-specific operators and local search methods

4. **Main Scripts**:
   - `run.py`: Main execution script with CLI options
   - `analyze_results.py`: Integrated analysis script

### Data Flow

1. A VRP problem instance is loaded from data/vrp/
2. The selected algorithm(s) optimize the problem
3. Results are collected, visualized, and saved
4. Optional: Statistical analysis and benchmarking can be performed

## Important Implementation Details

1. **Algorithm Interface**:
   - All algorithms implement a common interface
   - Key methods include initialize(), execute(), and get_convergence_curve()

2. **VRP Solution Representation**:
   - Continuous values are adapted to combinatorial problems through ordinal encoding
   - Solutions are decoded respecting vehicle capacity constraints

3. **Parallelization**:
   - The project supports parallel execution for benchmarks and multiple runs
   - Uses Python's multiprocessing Pool

4. **Results Storage**:
   - Results are saved in CSV format
   - Visualization outputs are saved as PNG images
   - Benchmark results can be saved as JSON for later analysis