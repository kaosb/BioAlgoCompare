# BioAlgoCompare Examples

This directory contains example outputs and demonstrations of various BioAlgoCompare features.

## Available Examples

### 1. Statistical Analysis v2 (`statistical_analysis_v2/`)
Demonstrates the corrected statistical analysis module with:
- Corrected Critical Distance (CD) calculation
- Vargha-Delaney A12 and Cliff's delta effect sizes
- Friedman and Quade tests
- Complete analysis reports with visualizations

See [statistical_analysis_v2/README.md](statistical_analysis_v2/README.md) for details.

## Running Examples

Most examples include both input data and generated outputs. To reproduce:

```bash
# Statistical analysis
python scripts/analyze_v2.py stats --csv examples/statistical_analysis_v2/simple_example/input_data.csv --out your_output

# Compare with provided outputs to verify correctness
```
