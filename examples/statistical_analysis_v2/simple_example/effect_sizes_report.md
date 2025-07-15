# Effect Size Analysis Report

## Effect Sizes vs Best Algorithm

**Best performing algorithm: EGTO**

| Algorithm | A12 | Interpretation | Cliff's δ | Interpretation |
|-----------|-----|----------------|-----------|----------------|
| HOA | 0.750 | large | 0.500 | large |
| FOA | 0.750 | large | 0.500 | large |
| WOA | 0.750 | large | 0.500 | large |
| HHO | 0.750 | large | 0.500 | large |
| EGTO | 0.500 | negligible | 0.000 | negligible |

### Interpretation Guide

- **A12 > 0.5**: The best algorithm outperforms this algorithm
- **A12 = 0.5**: No difference in performance
- **A12 < 0.5**: This algorithm outperforms the best (shouldn't happen)

## Pairwise Vargha-Delaney A12

*Read as: P(row algorithm < column algorithm)*

| Algorithm | EGTO | FOA | HHO | HOA | WOA |
|-----------|-----:|-----:|-----:|-----:|-----:|
| EGTO | 0.500 | 0.750 | 0.750 | 0.750 | 0.750 |
| FOA | 0.250 | 0.500 | 0.750 | 0.750 | 0.750 |
| HHO | 0.250 | 0.250 | 0.500 | 0.694 | 0.750 |
| HOA | 0.250 | 0.250 | 0.306 | 0.500 | 0.750 |
| WOA | 0.250 | 0.250 | 0.250 | 0.250 | 0.500 |

## Pairwise Cliff's Delta

*Positive values indicate row algorithm is better than column algorithm*

| Algorithm | EGTO | FOA | HHO | HOA | WOA |
|-----------|-----:|-----:|-----:|-----:|-----:|
| EGTO | +0.000 | +0.500 | +0.500 | +0.500 | +0.500 |
| FOA | -0.500 | +0.000 | +0.500 | +0.500 | +0.500 |
| HHO | -0.500 | -0.500 | +0.000 | +0.389 | +0.500 |
| HOA | -0.500 | -0.500 | -0.389 | +0.000 | +0.500 |
| WOA | -0.500 | -0.500 | -0.500 | -0.500 | +0.000 |

### Effect Size Thresholds

**Vargha-Delaney A12:**
- Negligible: |A12 - 0.5| < 0.06
- Small: 0.06 ≤ |A12 - 0.5| < 0.14
- Medium: 0.14 ≤ |A12 - 0.5| < 0.21
- Large: |A12 - 0.5| ≥ 0.21

**Cliff's Delta:**
- Negligible: |δ| < 0.147
- Small: 0.147 ≤ |δ| < 0.33
- Medium: 0.33 ≤ |δ| < 0.474
- Large: |δ| ≥ 0.474
