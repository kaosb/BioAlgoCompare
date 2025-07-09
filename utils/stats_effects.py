#!/usr/bin/env python3
"""
Effect size calculations for statistical analysis.

Implements:
  • Vargha-Delaney A12 effect size
  • Cliff's delta
  • Effect size interpretation utilities
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Union


def vargha_delaney_a12(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Vargha-Delaney A12 effect size.

    A12 measures the probability that a value from x is smaller than
    a value from y (for minimization problems).

    Args:
        x: First sample
        y: Second sample

    Returns:
        A12 value between 0 and 1:
        - 0.5: no difference
        - < 0.5: y tends to be smaller
        - > 0.5: x tends to be smaller
    """
    n_x = len(x)
    n_y = len(y)

    # Count wins for x (minimization: smaller is better)
    wins = 0.0
    ties = 0.0

    for xi in x:
        for yi in y:
            if xi < yi:
                wins += 1
            elif xi == yi:
                ties += 0.5

    a12 = (wins + ties) / (n_x * n_y)
    return a12


def cliff_delta(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Cliff's delta effect size.

    Cliff's delta is a non-parametric effect size that quantifies
    the amount of overlap between two distributions.

    Args:
        x: First sample
        y: Second sample

    Returns:
        Delta value between -1 and 1:
        - 0: complete overlap
        - -1: all values in y are larger than x
        - +1: all values in x are larger than y
    """
    n_x = len(x)
    n_y = len(y)

    # Count dominances
    dominance = 0

    for xi in x:
        for yi in y:
            if xi < yi:  # For minimization
                dominance += 1
            elif xi > yi:
                dominance -= 1

    delta = dominance / (n_x * n_y)
    return delta


def interpret_a12(a12: float) -> str:
    """
    Interpret Vargha-Delaney A12 effect size.

    Based on Vargha & Delaney (2000) thresholds.

    Args:
        a12: A12 effect size value

    Returns:
        String interpretation
    """
    # Convert to magnitude (distance from 0.5)
    magnitude = abs(a12 - 0.5)

    if magnitude < 0.06:  # |A12 - 0.5| < 0.06
        return "negligible"
    elif magnitude < 0.14:  # |A12 - 0.5| < 0.14
        return "small"
    elif magnitude < 0.21:  # |A12 - 0.5| < 0.21
        return "medium"
    else:
        return "large"


def interpret_cliff_delta(delta: float) -> str:
    """
    Interpret Cliff's delta effect size.

    Based on Romano et al. (2006) thresholds.

    Args:
        delta: Cliff's delta value

    Returns:
        String interpretation
    """
    magnitude = abs(delta)

    if magnitude < 0.147:
        return "negligible"
    elif magnitude < 0.33:
        return "small"
    elif magnitude < 0.474:
        return "medium"
    else:
        return "large"


def calculate_pairwise_effect_sizes(
    data: pd.DataFrame,
    value_col: str = "Value",
    algorithm_col: str = "Algorithm",
    instance_col: str = "Instance",
) -> Dict[str, pd.DataFrame]:
    """
    Calculate pairwise effect sizes for all algorithm pairs.

    Args:
        data: DataFrame with algorithm results
        value_col: Column name for performance values
        algorithm_col: Column name for algorithm names
        instance_col: Column name for instance names

    Returns:
        Dictionary with 'a12' and 'cliff' DataFrames
    """
    # Get unique algorithms
    algorithms = sorted(data[algorithm_col].unique())
    n_algos = len(algorithms)

    # Initialize matrices
    a12_matrix = pd.DataFrame(index=algorithms, columns=algorithms, dtype=float)
    cliff_matrix = pd.DataFrame(index=algorithms, columns=algorithms, dtype=float)

    # Calculate pairwise effect sizes
    for i, algo1 in enumerate(algorithms):
        for j, algo2 in enumerate(algorithms):
            if i == j:
                a12_matrix.loc[algo1, algo2] = 0.5
                cliff_matrix.loc[algo1, algo2] = 0.0
            else:
                # Get values for each algorithm
                values1 = data[data[algorithm_col] == algo1][value_col].values
                values2 = data[data[algorithm_col] == algo2][value_col].values

                # Calculate effect sizes
                a12 = vargha_delaney_a12(values1, values2)
                delta = cliff_delta(values1, values2)

                a12_matrix.loc[algo1, algo2] = a12
                cliff_matrix.loc[algo1, algo2] = delta

    return {"a12": a12_matrix, "cliff": cliff_matrix}


def effect_size_vs_best(
    data: pd.DataFrame,
    value_col: str = "Value",
    algorithm_col: str = "Algorithm",
    instance_col: str = "Instance",
) -> pd.DataFrame:
    """
    Calculate effect sizes of each algorithm versus the best performing algorithm.

    Args:
        data: DataFrame with algorithm results
        value_col: Column name for performance values
        algorithm_col: Column name for algorithm names
        instance_col: Column name for instance names

    Returns:
        DataFrame with effect sizes vs best algorithm
    """
    # Find best algorithm (lowest mean value for minimization)
    mean_values = data.groupby(algorithm_col)[value_col].mean()
    best_algo = mean_values.idxmin()

    # Get values for best algorithm
    best_values = data[data[algorithm_col] == best_algo][value_col].values

    # Calculate effect sizes vs best
    results = []

    for algo in data[algorithm_col].unique():
        if algo == best_algo:
            results.append(
                {
                    "Algorithm": algo,
                    "A12": 0.5,
                    "A12_interpretation": "negligible",
                    "Cliff_delta": 0.0,
                    "Cliff_interpretation": "negligible",
                    "Is_best": True,
                }
            )
        else:
            algo_values = data[data[algorithm_col] == algo][value_col].values

            # Calculate effect sizes
            a12 = vargha_delaney_a12(best_values, algo_values)
            delta = cliff_delta(best_values, algo_values)

            results.append(
                {
                    "Algorithm": algo,
                    "A12": a12,
                    "A12_interpretation": interpret_a12(a12),
                    "Cliff_delta": delta,
                    "Cliff_interpretation": interpret_cliff_delta(delta),
                    "Is_best": False,
                }
            )

    return pd.DataFrame(results).sort_values("A12", ascending=False)


def generate_effect_size_report(
    effect_sizes_vs_best: pd.DataFrame,
    pairwise_a12: pd.DataFrame,
    pairwise_cliff: pd.DataFrame,
    output_file: str,
) -> None:
    """
    Generate a detailed effect size report.

    Args:
        effect_sizes_vs_best: DataFrame with effect sizes vs best algorithm
        pairwise_a12: DataFrame with pairwise A12 values
        pairwise_cliff: DataFrame with pairwise Cliff's delta values
        output_file: Path to save the report
    """
    with open(output_file, "w") as f:
        f.write("# Effect Size Analysis Report\n\n")

        # Effect sizes vs best algorithm
        f.write("## Effect Sizes vs Best Algorithm\n\n")
        best_algo = effect_sizes_vs_best[effect_sizes_vs_best["Is_best"]][
            "Algorithm"
        ].iloc[0]
        f.write(f"**Best performing algorithm: {best_algo}**\n\n")

        f.write("| Algorithm | A12 | Interpretation | Cliff's δ | Interpretation |\n")
        f.write("|-----------|-----|----------------|-----------|----------------|\n")

        for _, row in effect_sizes_vs_best.iterrows():
            f.write(
                f"| {row['Algorithm']} | {row['A12']:.3f} | {row['A12_interpretation']} | "
                f"{row['Cliff_delta']:.3f} | {row['Cliff_interpretation']} |\n"
            )

        f.write("\n### Interpretation Guide\n\n")
        f.write("- **A12 > 0.5**: The best algorithm outperforms this algorithm\n")
        f.write("- **A12 = 0.5**: No difference in performance\n")
        f.write(
            "- **A12 < 0.5**: This algorithm outperforms the best (shouldn't happen)\n\n"
        )

        # Pairwise A12 matrix
        f.write("## Pairwise Vargha-Delaney A12\n\n")
        f.write("*Read as: P(row algorithm < column algorithm)*\n\n")

        # Convert to markdown table
        algorithms = list(pairwise_a12.index)
        f.write("| Algorithm |")
        for algo in algorithms:
            f.write(f" {algo} |")
        f.write("\n|-----------|")
        for _ in algorithms:
            f.write("-----:|")
        f.write("\n")

        for algo1 in algorithms:
            f.write(f"| {algo1} |")
            for algo2 in algorithms:
                value = pairwise_a12.loc[algo1, algo2]
                f.write(f" {value:.3f} |")
            f.write("\n")

        # Pairwise Cliff's delta matrix
        f.write("\n## Pairwise Cliff's Delta\n\n")
        f.write(
            "*Positive values indicate row algorithm is better than column algorithm*\n\n"
        )

        f.write("| Algorithm |")
        for algo in algorithms:
            f.write(f" {algo} |")
        f.write("\n|-----------|")
        for _ in algorithms:
            f.write("-----:|")
        f.write("\n")

        for algo1 in algorithms:
            f.write(f"| {algo1} |")
            for algo2 in algorithms:
                value = pairwise_cliff.loc[algo1, algo2]
                f.write(f" {value:+.3f} |")
            f.write("\n")

        f.write("\n### Effect Size Thresholds\n\n")
        f.write("**Vargha-Delaney A12:**\n")
        f.write("- Negligible: |A12 - 0.5| < 0.06\n")
        f.write("- Small: 0.06 ≤ |A12 - 0.5| < 0.14\n")
        f.write("- Medium: 0.14 ≤ |A12 - 0.5| < 0.21\n")
        f.write("- Large: |A12 - 0.5| ≥ 0.21\n\n")

        f.write("**Cliff's Delta:**\n")
        f.write("- Negligible: |δ| < 0.147\n")
        f.write("- Small: 0.147 ≤ |δ| < 0.33\n")
        f.write("- Medium: 0.33 ≤ |δ| < 0.474\n")
        f.write("- Large: |δ| ≥ 0.474\n")
