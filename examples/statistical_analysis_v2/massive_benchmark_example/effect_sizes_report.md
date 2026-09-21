# Effect Size Analysis Report

## Effect Sizes vs Best Algorithm

**Best performing algorithm: WOA**

| Algorithm | A12 | Interpretation | Cliff's δ | Interpretation |
|-----------|-----|----------------|-----------|----------------|
| SMO | 0.760 | large | 0.520 | large |
| AHA | 0.740 | large | 0.480 | large |
| FOA | 0.720 | large | 0.440 | medium |
| HHO | 0.680 | medium | 0.360 | medium |
| SMA | 0.600 | small | 0.200 | small |
| GTO | 0.560 | small | 0.120 | negligible |
| GVOA | 0.520 | negligible | 0.040 | negligible |
| WOA | 0.500 | negligible | 0.000 | negligible |

### Interpretation Guide

- **A12 > 0.5**: The best algorithm outperforms this algorithm
- **A12 = 0.5**: No difference in performance
- **A12 < 0.5**: This algorithm outperforms the best (shouldn't happen)

## Pairwise Vargha-Delaney A12

*Read as: P(row algorithm < column algorithm)*

| Algorithm | AHA | FOA | GTO | GVOA | HHO | SMA | SMO | WOA |
|-----------|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| AHA | 0.500 | 0.400 | 0.240 | 0.280 | 0.320 | 0.240 | 0.480 | 0.260 |
| FOA | 0.600 | 0.500 | 0.300 | 0.300 | 0.420 | 0.260 | 0.600 | 0.280 |
| GTO | 0.760 | 0.700 | 0.500 | 0.460 | 0.700 | 0.540 | 0.760 | 0.440 |
| GVOA | 0.720 | 0.700 | 0.540 | 0.500 | 0.660 | 0.580 | 0.720 | 0.480 |
| HHO | 0.680 | 0.580 | 0.300 | 0.340 | 0.500 | 0.340 | 0.640 | 0.320 |
| SMA | 0.760 | 0.740 | 0.460 | 0.420 | 0.660 | 0.500 | 0.760 | 0.400 |
| SMO | 0.520 | 0.400 | 0.240 | 0.280 | 0.360 | 0.240 | 0.500 | 0.240 |
| WOA | 0.740 | 0.720 | 0.560 | 0.520 | 0.680 | 0.600 | 0.760 | 0.500 |

## Pairwise Cliff's Delta

*Positive values indicate row algorithm is better than column algorithm*

| Algorithm | AHA | FOA | GTO | GVOA | HHO | SMA | SMO | WOA |
|-----------|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| AHA | +0.000 | -0.200 | -0.520 | -0.440 | -0.360 | -0.520 | -0.040 | -0.480 |
| FOA | +0.200 | +0.000 | -0.400 | -0.400 | -0.160 | -0.480 | +0.200 | -0.440 |
| GTO | +0.520 | +0.400 | +0.000 | -0.080 | +0.400 | +0.080 | +0.520 | -0.120 |
| GVOA | +0.440 | +0.400 | +0.080 | +0.000 | +0.320 | +0.160 | +0.440 | -0.040 |
| HHO | +0.360 | +0.160 | -0.400 | -0.320 | +0.000 | -0.320 | +0.280 | -0.360 |
| SMA | +0.520 | +0.480 | -0.080 | -0.160 | +0.320 | +0.000 | +0.520 | -0.200 |
| SMO | +0.040 | -0.200 | -0.520 | -0.440 | -0.280 | -0.520 | +0.000 | -0.520 |
| WOA | +0.480 | +0.440 | +0.120 | +0.040 | +0.360 | +0.200 | +0.520 | +0.000 |

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
