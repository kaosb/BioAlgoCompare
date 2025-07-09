# Statistical Analysis v2 Examples

This directory contains example outputs from the BioAlgoCompare Statistical Analysis Module v2, demonstrating the corrected Critical Distance (CD) calculation and effect size measures.

## Examples Included

### 1. Simple Example (`simple_example/`)
A small dataset with 5 algorithms (HOA, FOA, EGTO, WOA, HHO) tested on 2 instances (P-n16-k8, E-n22-k4) with 3 runs each.

**Files:**
- `input_data.csv`: Input data used for analysis
- `stats_report.md`: Complete statistical analysis report
- `cd_diagram.png`: Critical Difference diagram
- `effect_sizes.csv`: Effect sizes vs best algorithm
- `effect_sizes_report.md`: Detailed effect size analysis
- `software_versions.json`: Software environment details

**Key Results:**
- No significant differences detected (p = 0.091578)
- CD = 4.3130 (with k=5, n=2)
- Best algorithm: EGTO
- All algorithms show large effect sizes when compared to EGTO

### 2. Massive Benchmark Example (`massive_benchmark_example/`)
Analysis of a real benchmark with 8 algorithms tested on 5 instances with 1000 runs each.

**Files:**
- `stats_report.md`: Complete statistical analysis report
- `cd_diagram.png`: Critical Difference diagram showing algorithm groupings
- `effect_sizes.csv`: Effect sizes for all algorithms
- `effect_sizes_report.md`: Pairwise effect size matrices
- `software_versions.json`: Software environment details

**Key Results:**
- Significant differences detected (p = 0.000374)
- CD = 4.6954 (with k=8, n=5) - **Corrected value!**
- Best algorithms: GVOA (rank 2.20), WOA (rank 2.70)
- Clear separation between top performers and others

## How to Run Your Own Analysis

```bash
# Basic statistical analysis
python scripts/analyze_v2.py stats \
  --csv your_results.csv \
  --out output_directory

# With extended tests (Quade test)
python scripts/analyze_v2.py stats \
  --csv your_results.csv \
  --out output_directory \
  --extended-tests

# Effect sizes only
python scripts/analyze_v2.py effect-size \
  --csv your_results.csv \
  --out output_directory \
  --vs-best
```

## CSV Input Format

Your input CSV must contain at least these columns:
- `Algorithm`: Algorithm name
- `Instance`: Problem instance name
- One of: `Best`, `Best Fitness`, or `Value`: Performance metric

Example:
```csv
Algorithm,Instance,Best
HOA,P-n16-k8,460.5
HOA,E-n22-k4,382.4
FOA,P-n16-k8,455.2
...
```

## Critical Distance Correction

The v2 module implements the corrected CD formula:
```
CD = q_alpha/sqrt(2) * sqrt(k(k+1)/(6n))
```

Where:
- k = number of algorithms
- n = number of instances
- q_alpha = Studentized range statistic

This correction ensures proper statistical interpretation of the Nemenyi post-hoc test.
