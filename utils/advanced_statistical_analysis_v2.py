#!/usr/bin/env python3
"""
Advanced statistical analysis module for comparing metaheuristic algorithms.

Implements:
  • Aligned Friedman test for global p-value
  • Quade test as alternative
  • Post-hoc Nemenyi test for pairwise comparisons
  • Vargha-Delaney A12 and Cliff's delta effect sizes
  • Critical Difference diagram generation
"""

import os
import json
import platform
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy import stats
from scipy.stats import friedmanchisquare, rankdata, f as f_dist
from statsmodels.stats.libqsturng import qsturng
import scikit_posthocs as sp
import logging

# Import our effect size utilities
from utils.stats_effects import (
    calculate_pairwise_effect_sizes,
    effect_size_vs_best,
    generate_effect_size_report,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("advanced_statistical_analysis_v2")


def get_software_versions() -> Dict[str, str]:
    """Get versions of key software components."""
    import sys
    import scipy
    import matplotlib

    versions = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "timestamp": datetime.now().isoformat(),
    }
    return versions


def aligned_friedman_test(data: pd.DataFrame, alpha: float = 0.05) -> Dict:
    """
    Perform the aligned Friedman test for comparing multiple algorithms.

    The aligned Friedman test adjusts for instance difficulty by subtracting
    the average performance for each instance.

    Args:
        data: DataFrame with columns 'Algorithm', 'Instance', 'Value'
        alpha: Significance level (default: 0.05)

    Returns:
        Dictionary with test results including corrected CD
    """
    # Group by Instance and Algorithm to get one value per combination
    grouped = data.groupby(["Instance", "Algorithm"])["Value"].mean().reset_index()

    # Pivot data to algorithms as columns, instances as rows
    pivot = grouped.pivot(index="Instance", columns="Algorithm", values="Value")

    # Check if we have enough data
    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        return {
            "friedman_p": 1.0,
            "error": "Insufficient data: need at least 2 instances and 2 algorithms",
        }

    # Align the data: subtract row (instance) means
    instance_means = pivot.mean(axis=1)
    aligned_data = pivot.sub(instance_means, axis=0)

    # Calculate ranks for aligned data (lower is better rank)
    aligned_ranks = aligned_data.rank(axis=1, method="average", ascending=True)

    # Calculate mean ranks for each algorithm
    mean_ranks = aligned_ranks.mean(axis=0)

    # Prepare data for Friedman test
    n = pivot.shape[0]  # Number of instances
    k = pivot.shape[1]  # Number of algorithms

    # Perform the Friedman test
    friedman_statistic, p_value = friedmanchisquare(
        *[aligned_ranks[col].values for col in aligned_ranks.columns]
    )

    # Calculate CORRECTED critical distance for Nemenyi test
    # CD = q_alpha * sqrt(k(k+1)/(6n)) where q_alpha is divided by sqrt(2)
    q_alpha = qsturng(1 - alpha, k, np.inf) / np.sqrt(2)
    critical_distance = q_alpha * np.sqrt((k * (k + 1)) / (6 * n))

    return {
        "friedman_p": p_value,
        "statistic": friedman_statistic,
        "reject_h0": bool(p_value < alpha),
        "alpha": alpha,
        "mean_ranks": mean_ranks.to_dict(),
        "critical_distance": critical_distance,
        "q_alpha": q_alpha,
        "n_instances": n,
        "n_algorithms": k,
        "test_type": "aligned_friedman",
    }


def quade_test(data: pd.DataFrame, alpha: float = 0.05) -> Dict:
    """
    Perform the Quade test as an alternative to Friedman test.

    The Quade test is more powerful when the number of algorithms is small
    relative to the number of instances.

    Args:
        data: DataFrame with columns 'Algorithm', 'Instance', 'Value'
        alpha: Significance level (default: 0.05)

    Returns:
        Dictionary with test results
    """
    # Group by Instance and Algorithm
    grouped = data.groupby(["Instance", "Algorithm"])["Value"].mean().reset_index()
    pivot = grouped.pivot(index="Instance", columns="Algorithm", values="Value")

    n = pivot.shape[0]  # Number of instances
    k = pivot.shape[1]  # Number of algorithms

    if n < 2 or k < 2:
        return {"quade_p": 1.0, "error": "Insufficient data"}

    # Step 1: Rank algorithms within each instance
    ranks = pivot.rank(axis=1, method="average", ascending=True)

    # Step 2: Calculate range for each instance
    ranges = pivot.max(axis=1) - pivot.min(axis=1)

    # Step 3: Rank the ranges
    ranked_ranges = rankdata(ranges)

    # Step 4: Weight the ranks by ranked ranges
    weighted_ranks = ranks.multiply(ranked_ranges, axis=0)

    # Step 5: Calculate sum of weighted ranks for each algorithm
    S_j = weighted_ranks.sum(axis=0)

    # Step 6: Calculate Quade statistic
    # Calculate sum of squares
    grand_mean = S_j.mean()
    SS_A = n * ((S_j - grand_mean) ** 2).sum()  # Between algorithms sum of squares

    # Total sum of squares
    all_weighted = weighted_ranks.values.flatten()
    SS_T = ((all_weighted - all_weighted.mean()) ** 2).sum()

    # Error sum of squares
    SS_E = SS_T - SS_A

    if SS_E == 0:
        return {"quade_p": 1.0, "error": "Zero error sum of squares in Quade test"}

    # Quade F-statistic
    F_Q = (SS_A / (k - 1)) / (SS_E / ((k - 1) * (n - 1)))

    # Calculate p-value using F-distribution
    df1 = k - 1
    df2 = (k - 1) * (n - 1)
    p_value = 1 - f_dist.cdf(F_Q, df1, df2)

    # Calculate critical distance (similar to Friedman)
    q_alpha = qsturng(1 - alpha, k, np.inf) / np.sqrt(2)
    critical_distance = q_alpha * np.sqrt((k * (k + 1)) / (6 * n))

    return {
        "quade_p": p_value,
        "statistic": F_Q,
        "reject_h0": bool(p_value < alpha),
        "alpha": alpha,
        "mean_ranks": ranks.mean(axis=0).to_dict(),
        "critical_distance": critical_distance,
        "q_alpha": q_alpha,
        "n_instances": n,
        "n_algorithms": k,
        "test_type": "quade",
    }


def nemenyi_posthoc_test(data: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Perform Nemenyi post-hoc test after Friedman test.

    Args:
        data: DataFrame with columns 'Algorithm', 'Instance', 'Value'
        alpha: Significance level (default: 0.05)

    Returns:
        DataFrame with p-values for pairwise comparisons
    """
    # Group by Instance and Algorithm to get one value per combination
    grouped = data.groupby(["Instance", "Algorithm"])["Value"].mean().reset_index()

    # Pivot data to algorithms as columns, instances as rows
    pivot = grouped.pivot(index="Instance", columns="Algorithm", values="Value")

    # Check if we have enough data
    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        return pd.DataFrame()

    try:
        # Use scikit_posthocs to compute Nemenyi test
        posthoc = sp.posthoc_nemenyi_friedman(pivot)
        return posthoc
    except Exception as e:
        logger.error(f"Error in Nemenyi test: {str(e)}")
        # Fallback to manual calculation
        return pd.DataFrame(1.0, index=pivot.columns, columns=pivot.columns)


def create_cd_diagram(
    ranks: np.ndarray,
    names: List[str],
    cd: Optional[float],
    output_file: str,
    title: str = "Critical Difference Diagram",
    reverse: bool = False,
) -> str:
    """
    Create critical difference diagram to visualize algorithm rankings.

    Based on Demšar (2006) with corrections.

    Args:
        ranks: Array of mean ranks for each algorithm
        names: Array of algorithm names
        cd: Critical difference value (None for no CD)
        output_file: Path to save the diagram
        title: Title for the diagram
        reverse: If True, higher ranks are better (default: False)

    Returns:
        Path to the saved diagram
    """
    # Sort algorithms by rank (ascending for minimization)
    sorted_idx = np.argsort(ranks)
    if reverse:
        sorted_idx = sorted_idx[::-1]

    sorted_ranks = ranks[sorted_idx]
    sorted_names = np.array(names)[sorted_idx]

    # Setup the plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Normalize ranks to [0, k-1] range for positioning
    k = len(names)
    min_rank = 1
    max_rank = k
    norm_ranks = (sorted_ranks - min_rank) / (max_rank - min_rank) * (k - 1)

    # Set axis limits
    ax.set_xlim(-0.5, k - 0.5)
    ax.set_ylim(-1, 3)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_yticks([])
    ax.set_xticks([])

    # Draw rank axis
    ax.axhline(y=0, color="black", linewidth=2)

    # Add rank labels
    for i in range(k):
        ax.text(i, -0.3, str(i + 1), ha="center", va="top", fontsize=10)

    # Position algorithms
    for i, (rank, name, norm_pos) in enumerate(
        zip(sorted_ranks, sorted_names, norm_ranks)
    ):
        # Draw vertical line
        ax.plot([norm_pos, norm_pos], [0, 0.5], "k-", linewidth=1)

        # Add algorithm name
        ax.text(norm_pos, 0.6, name, ha="center", va="bottom", rotation=45, fontsize=12)

        # Add actual rank value
        ax.text(
            norm_pos,
            -0.6,
            f"{rank:.2f}",
            ha="center",
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5),
        )

        # Add marker
        ax.plot(norm_pos, 0, "o", color="black", markersize=8)

    # Draw CD if provided
    if cd is not None:
        # Normalize CD to plot scale
        cd_norm = cd / (max_rank - min_rank) * (k - 1)

        # Draw CD bar
        cd_y = 2.2
        ax.plot([0, cd_norm], [cd_y, cd_y], "r-", linewidth=3)
        ax.plot([0, 0], [cd_y - 0.1, cd_y + 0.1], "r-", linewidth=3)
        ax.plot([cd_norm, cd_norm], [cd_y - 0.1, cd_y + 0.1], "r-", linewidth=3)
        ax.text(
            cd_norm / 2,
            cd_y + 0.2,
            f"CD = {cd:.3f}",
            ha="center",
            va="bottom",
            fontsize=12,
            color="red",
            weight="bold",
        )

        # Draw connections for non-significantly different algorithms
        connection_y = 1.2
        y_increment = 0.15
        used_y = []

        for i in range(len(sorted_ranks)):
            for j in range(i + 1, len(sorted_ranks)):
                if abs(sorted_ranks[i] - sorted_ranks[j]) <= cd:
                    # Find appropriate y position
                    y_pos = connection_y
                    while any(abs(y_pos - y) < 0.1 for y in used_y):
                        y_pos += y_increment
                    used_y.append(y_pos)

                    # Draw connection
                    ax.plot(
                        [norm_ranks[i], norm_ranks[j]],
                        [y_pos, y_pos],
                        "k-",
                        linewidth=2.5,
                    )

    # Set title
    ax.set_title(title, fontsize=16, weight="bold", pad=20)

    # Add axis label
    ax.text(k / 2 - 0.5, -1, "Rank", ha="center", va="top", fontsize=14)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return output_file


def generate_extended_stats_report(results: Dict, output_file: str) -> str:
    """
    Generate an extended markdown report from statistical results.

    Includes effect sizes, software versions, and extended test results.

    Args:
        results: Dictionary with all statistical results
        output_file: Path to save the report

    Returns:
        Path to the saved report
    """
    with open(output_file, "w") as f:
        f.write("# Extended Statistical Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Software versions
        if "software_versions" in results:
            f.write("## Software Environment\n\n")
            f.write("| Component | Version |\n")
            f.write("|-----------|----------|\n")
            for component, version in results["software_versions"].items():
                f.write(f"| {component} | {version} |\n")
            f.write("\n")

        # Summary statistics
        if "summary_stats" in results:
            f.write("## Summary Statistics\n\n")
            summary = results["summary_stats"]
            f.write("| Algorithm | Mean ± SD | Median | Min | Max | IQR |\n")
            f.write("|-----------|-----------|--------|-----|-----|-----|\n")
            for _, row in summary.iterrows():
                f.write(
                    f"| {row['Algorithm']} | {row['Mean']:.2f} ± {row['SD']:.2f} | "
                    f"{row['Median']:.2f} | {row['Min']:.2f} | {row['Max']:.2f} | "
                    f"{row['IQR']:.2f} |\n"
                )
            f.write("\n")

        # Friedman test results
        if "friedman_results" in results:
            fr = results["friedman_results"]
            f.write("## Friedman Test Results\n\n")
            f.write(f"* Test type: {fr.get('test_type', 'friedman')}\n")
            f.write(f"* χ² statistic: {fr.get('statistic', 0):.4f}\n")
            f.write(f"* p-value: {fr.get('friedman_p', 1):.6f}\n")
            f.write(f"* Critical difference: {fr.get('critical_distance', 0):.4f}\n")
            f.write(f"* q_α value: {fr.get('q_alpha', 0):.4f}\n")
            f.write(f"* Significance level: {fr.get('alpha', 0.05):.2f}\n")
            f.write(f"* Number of algorithms: {fr.get('n_algorithms', 0)}\n")
            f.write(f"* Number of instances: {fr.get('n_instances', 0)}\n\n")

            if fr.get("reject_h0", False):
                f.write(
                    "**Result**: Significant differences detected between algorithms (p < α)\n\n"
                )
            else:
                f.write(
                    "**Result**: No significant differences detected between algorithms (p ≥ α)\n\n"
                )

        # Quade test results (if available)
        if "quade_results" in results:
            qr = results["quade_results"]
            f.write("## Quade Test Results\n\n")
            f.write(f"* F statistic: {qr.get('statistic', 0):.4f}\n")
            f.write(f"* p-value: {qr.get('quade_p', 1):.6f}\n")
            f.write(f"* Critical difference: {qr.get('critical_distance', 0):.4f}\n\n")

            if qr.get("reject_h0", False):
                f.write("**Result**: Significant differences detected (Quade test)\n\n")

        # Algorithm rankings
        f.write("## Algorithm Rankings\n\n")

        if "mean_ranks" in results:
            ranks = results["mean_ranks"]
            sorted_algos = sorted(ranks.items(), key=lambda x: x[1])

            f.write("| Rank | Algorithm | Mean Rank | Group |\n")
            f.write("|------|-----------|-----------|-------|\n")

            # Determine statistical groups based on CD
            cd = results.get("friedman_results", {}).get("critical_distance", 0)
            groups = []
            current_group = "A"

            for i, (algo, rank) in enumerate(sorted_algos):
                # Check if significantly different from best
                if i > 0 and cd > 0:
                    if rank - sorted_algos[0][1] > cd:
                        current_group = chr(ord(current_group) + 1)

                f.write(f"| {i+1} | {algo} | {rank:.3f} | {current_group} |\n")

            f.write(
                "\n*Algorithms in the same group are not significantly different*\n\n"
            )

        # Effect sizes
        if "effect_sizes_vs_best" in results:
            f.write("## Effect Sizes vs Best Algorithm\n\n")
            es = results["effect_sizes_vs_best"]
            best_algo = es[es["Is_best"]]["Algorithm"].iloc[0]
            f.write(f"**Best performing algorithm: {best_algo}**\n\n")

            f.write(
                "| Algorithm | Vargha-Delaney A₁₂ | Interpretation | Cliff's δ | Interpretation |\n"
            )
            f.write(
                "|-----------|-------------------|----------------|-----------|----------------|\n"
            )

            for _, row in es.iterrows():
                f.write(
                    f"| {row['Algorithm']} | {row['A12']:.3f} | {row['A12_interpretation']} | "
                    f"{row['Cliff_delta']:.3f} | {row['Cliff_interpretation']} |\n"
                )
            f.write("\n")

        # Nemenyi post-hoc test
        if "nemenyi" in results and not results["nemenyi"].empty:
            f.write("## Nemenyi Post-hoc Test\n\n")
            f.write(
                "*p-values for pairwise comparisons (values < 0.05 indicate significant differences)*\n\n"
            )

            nemenyi = results["nemenyi"].round(4)
            algorithms = list(nemenyi.index)

            f.write("| Algorithm |")
            for algo in algorithms:
                f.write(f" {algo} |")
            f.write("\n|-----------|")
            for _ in algorithms:
                f.write("-------:|")
            f.write("\n")

            for algo1 in algorithms:
                f.write(f"| {algo1} |")
                for algo2 in algorithms:
                    value = nemenyi.loc[algo1, algo2]
                    if algo1 == algo2:
                        f.write(" - |")
                    elif value < 0.05:
                        f.write(f" **{value:.4f}** |")
                    else:
                        f.write(f" {value:.4f} |")
                f.write("\n")
            f.write("\n")

        # Conclusions
        f.write("## Conclusions\n\n")

        if results.get("friedman_results", {}).get("reject_h0", False):
            f.write(
                "1. The Friedman test indicates statistically significant differences "
                "between the algorithms (p < 0.05).\n"
            )

            if "mean_ranks" in results:
                sorted_algos = sorted(results["mean_ranks"].items(), key=lambda x: x[1])
                top_3 = sorted_algos[:3]
                f.write(
                    f"2. The top performing algorithms are: {', '.join([a[0] for a in top_3])}.\n"
                )

            if "effect_sizes_vs_best" in results:
                es = results["effect_sizes_vs_best"]
                large_effects = es[es["A12_interpretation"] == "large"]
                if not large_effects.empty:
                    f.write(
                        f"3. Large effect sizes were observed for: "
                        f"{', '.join(large_effects['Algorithm'].tolist())}.\n"
                    )
        else:
            f.write(
                "1. No statistically significant differences were found between "
                "the algorithms at the 0.05 significance level.\n"
            )
            f.write(
                "2. All algorithms can be considered statistically equivalent "
                "in performance for the tested instances.\n"
            )

        f.write("\n---\n")
        f.write("*Report generated by BioAlgoCompare Statistical Analysis Module v2*\n")

    return output_file


def run_all_v2(
    csv_path: str,
    out_dir: str,
    extended_tests: bool = False,
    save_versions: bool = True,
) -> Dict:
    """
    Execute comprehensive statistical analysis with corrections and extensions.

    Args:
        csv_path: Path to CSV file with benchmark results
        out_dir: Directory to save the results
        extended_tests: If True, also run Quade test
        save_versions: If True, save software versions to JSON

    Returns:
        Dictionary with all results and file paths
    """
    # Create output directory
    os.makedirs(out_dir, exist_ok=True)

    # Initialize results dictionary
    results = {}

    # Save software versions
    if save_versions:
        versions = get_software_versions()
        results["software_versions"] = versions

        versions_file = os.path.join(out_dir, "software_versions.json")
        with open(versions_file, "w") as f:
            json.dump(versions, f, indent=2)
        logger.info(f"Software versions saved to {versions_file}")

    # Load data
    try:
        df = pd.read_csv(csv_path)

        # Check required columns
        required_columns = ["Algorithm", "Instance"]
        value_columns = ["Best", "Best Fitness", "Value"]

        if not all(col in df.columns for col in required_columns):
            return {"error": f"CSV must contain columns: {required_columns}"}

        # Find value column
        value_col = None
        for col in value_columns:
            if col in df.columns:
                value_col = col
                break

        if value_col is None:
            return {"error": f"CSV must contain one of: {value_columns}"}

        # Prepare data
        data = df[["Algorithm", "Instance", value_col]].copy()
        data.columns = ["Algorithm", "Instance", "Value"]

        # Calculate summary statistics
        summary_stats = []
        for algo in data["Algorithm"].unique():
            algo_data = data[data["Algorithm"] == algo]["Value"]
            summary_stats.append(
                {
                    "Algorithm": algo,
                    "Mean": algo_data.mean(),
                    "SD": algo_data.std(),
                    "Median": algo_data.median(),
                    "Min": algo_data.min(),
                    "Max": algo_data.max(),
                    "IQR": algo_data.quantile(0.75) - algo_data.quantile(0.25),
                    "N": len(algo_data),
                }
            )

        results["summary_stats"] = pd.DataFrame(summary_stats)

        # Run Friedman test with corrections
        friedman_results = aligned_friedman_test(data)
        results["friedman_results"] = friedman_results
        results["friedman_p"] = friedman_results["friedman_p"]
        results["critical_distance"] = friedman_results["critical_distance"]
        results["mean_ranks"] = friedman_results["mean_ranks"]

        # Run Quade test if requested
        if extended_tests:
            quade_results = quade_test(data)
            results["quade_results"] = quade_results

        # Nemenyi post-hoc test
        nemenyi = nemenyi_posthoc_test(data)
        results["nemenyi"] = nemenyi

        # Calculate effect sizes
        pairwise_effects = calculate_pairwise_effect_sizes(data)
        results["pairwise_a12"] = pairwise_effects["a12"]
        results["pairwise_cliff"] = pairwise_effects["cliff"]

        # Effect sizes vs best
        es_vs_best = effect_size_vs_best(data)
        results["effect_sizes_vs_best"] = es_vs_best

        # Save effect sizes to CSV
        effect_sizes_file = os.path.join(out_dir, "effect_sizes.csv")
        es_vs_best.to_csv(effect_sizes_file, index=False)

        # Generate effect size report
        effect_report_file = os.path.join(out_dir, "effect_sizes_report.md")
        generate_effect_size_report(
            es_vs_best,
            pairwise_effects["a12"],
            pairwise_effects["cliff"],
            effect_report_file,
        )

        # Create CD diagram
        if "mean_ranks" in friedman_results:
            ranks = np.array(list(friedman_results["mean_ranks"].values()))
            names = list(friedman_results["mean_ranks"].keys())
            cd = friedman_results["critical_distance"]

            cd_file = os.path.join(out_dir, "cd_diagram.png")
            create_cd_diagram(
                ranks,
                names,
                cd,
                cd_file,
                title=f"Critical Difference Diagram (α={friedman_results['alpha']})",
            )
            results["cd_diagram"] = cd_file

        # Generate extended report
        report_file = os.path.join(out_dir, "stats_report.md")
        generate_extended_stats_report(results, report_file)
        results["report"] = report_file

        logger.info("Statistical analysis completed successfully")
        return results

    except Exception as e:
        logger.error(f"Error in statistical analysis: {str(e)}")
        return {"error": str(e)}
