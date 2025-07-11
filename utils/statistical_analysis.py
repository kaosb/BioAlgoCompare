"""
Unified Statistical Analysis Module for BioAlgoCompare

This module consolidates all statistical analysis functionality, including:
- Non-parametric tests (Friedman, Nemenyi, Quade, Wilcoxon)
- Effect size measures (Vargha-Delaney A12, Cliff's delta)
- Critical Difference diagrams with corrected formula
- Comprehensive reporting in Markdown and HTML formats
- Software version tracking for reproducibility

The implementation follows rigorous scientific standards for algorithm comparison
following best practices in computational intelligence research.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import friedmanchisquare, wilcoxon, rankdata
from statsmodels.stats.libqsturng import qsturng
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any, Union
import warnings
import sys
import platform
import json
from datetime import datetime
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")


class AdvancedStatisticalAnalysis:
    """
    Unified statistical analysis class for algorithm comparison.

    This class provides comprehensive statistical tests and effect size measures
    for comparing multiple algorithms across multiple problem instances.
    """

    def __init__(
        self,
        results_df: pd.DataFrame,
        algorithm_col: str = "Algorithm",
        instance_col: str = "Instance",
        value_col: str = "Best_Cost",
        minimize: bool = True,
    ):
        """
        Initialize the statistical analysis.

        Args:
            results_df: DataFrame with benchmark results
            algorithm_col: Column name for algorithms
            instance_col: Column name for instances
            value_col: Column name for values to compare
            minimize: Whether lower values are better
        """
        self.results_df = results_df.copy()
        self.algorithm_col = algorithm_col
        self.instance_col = instance_col
        self.value_col = value_col
        self.minimize = minimize

        # Prepare data for analysis
        self.pivot_df = self._prepare_data()
        self.n_algorithms = len(self.pivot_df.columns)
        self.n_instances = len(self.pivot_df)

    def _prepare_data(self) -> pd.DataFrame:
        """Prepare data in pivot format for statistical tests."""
        # Group by algorithm and instance, taking mean if multiple runs
        grouped = (
            self.results_df.groupby([self.algorithm_col, self.instance_col])[
                self.value_col
            ]
            .mean()
            .reset_index()
        )

        # Pivot to have algorithms as columns and instances as rows
        pivot = grouped.pivot(
            index=self.instance_col, columns=self.algorithm_col, values=self.value_col
        )

        return pivot

    def friedman_test(self) -> Dict[str, Any]:
        """
        Perform Friedman test for comparing multiple algorithms.

        Returns:
            Dictionary with test statistic, p-value, and interpretation
        """
        # Ensure we have enough data
        if self.n_algorithms < 3:
            return {
                "error": "Friedman test requires at least 3 algorithms",
                "n_algorithms": self.n_algorithms,
            }

        if self.n_instances < 2:
            return {
                "error": "Friedman test requires at least 2 instances",
                "n_instances": self.n_instances,
            }

        # Perform Friedman test
        statistic, p_value = friedmanchisquare(
            *[self.pivot_df[col].values for col in self.pivot_df.columns]
        )

        # Calculate average ranks
        ranks = self.pivot_df.rank(axis=1, ascending=self.minimize)
        avg_ranks = ranks.mean().sort_values()

        return {
            "test": "Friedman",
            "statistic": statistic,
            "p_value": p_value,
            "df": self.n_algorithms - 1,
            "n_algorithms": self.n_algorithms,
            "n_instances": self.n_instances,
            "significant": p_value < 0.05,
            "average_ranks": avg_ranks.to_dict(),
            "interpretation": self._interpret_friedman(p_value),
        }

    def quade_test(self) -> Dict[str, Any]:
        """
        Perform Quade test as an alternative to Friedman test.
        Quade test weights instances by their range of values.

        Returns:
            Dictionary with test statistic, p-value, and interpretation
        """
        if self.n_algorithms < 3 or self.n_instances < 2:
            return {
                "error": f"Quade test requires at least 3 algorithms and 2 instances. Got {self.n_algorithms} algorithms and {self.n_instances} instances"
            }

        # Step 1: Rank within each instance
        ranks = self.pivot_df.rank(axis=1, method="average", ascending=self.minimize)

        # Step 2: Calculate range for each instance
        ranges = self.pivot_df.max(axis=1) - self.pivot_df.min(axis=1)

        # Step 3: Rank the ranges
        range_ranks = rankdata(ranges)

        # Step 4: Calculate weighted ranks
        weighted_ranks = ranks.multiply(range_ranks, axis=0)

        # Step 5: Calculate sum of weighted ranks for each algorithm
        S_j = weighted_ranks.sum(axis=0)

        # Step 6: Calculate Quade statistic using ANOVA approach
        n = self.n_instances
        k = self.n_algorithms

        # Total sum of weighted ranks
        total_sum = weighted_ranks.sum().sum()

        # Correction factor
        CF = (total_sum**2) / (n * k)

        # Sum of squares
        SS_total = (weighted_ranks**2).sum().sum() - CF
        SS_algorithms = (S_j**2).sum() / n - CF
        SS_error = SS_total - SS_algorithms

        # Degrees of freedom
        df_algorithms = k - 1
        df_error = (n - 1) * (k - 1)

        # Mean squares
        MS_algorithms = SS_algorithms / df_algorithms
        MS_error = SS_error / df_error

        # F-statistic
        F_statistic = MS_algorithms / MS_error if MS_error > 0 else 0

        # P-value from F-distribution
        p_value = 1 - stats.f.cdf(F_statistic, df_algorithms, df_error)

        # Average weighted ranks
        avg_weighted_ranks = S_j / n

        return {
            "test": "Quade",
            "statistic": F_statistic,
            "p_value": p_value,
            "df_algorithms": df_algorithms,
            "df_error": df_error,
            "n_algorithms": self.n_algorithms,
            "n_instances": self.n_instances,
            "significant": p_value < 0.05,
            "average_weighted_ranks": avg_weighted_ranks.sort_values().to_dict(),
            "interpretation": self._interpret_quade(p_value),
        }

    def nemenyi_test(self, alpha: float = 0.05) -> Dict[str, Any]:
        """
        Perform Nemenyi post-hoc test with corrected Critical Difference.

        Args:
            alpha: Significance level

        Returns:
            Dictionary with critical distance, pairwise comparisons, and groups
        """
        # Calculate average ranks
        ranks = self.pivot_df.rank(axis=1, ascending=self.minimize)
        avg_ranks = ranks.mean()

        # Get critical value from Studentized range distribution
        k = self.n_algorithms
        n = self.n_instances

        # CORRECTED FORMULA: q_alpha / sqrt(2)
        q_alpha = qsturng(1 - alpha, k, np.inf) / np.sqrt(2)

        # Critical distance with corrected formula
        critical_distance = q_alpha * np.sqrt((k * (k + 1)) / (6 * n))

        # Pairwise rank differences
        pairwise_diff = {}
        significant_diff = {}

        algorithms = list(avg_ranks.index)
        for i in range(len(algorithms)):
            for j in range(i + 1, len(algorithms)):
                alg1, alg2 = algorithms[i], algorithms[j]
                diff = abs(avg_ranks[alg1] - avg_ranks[alg2])
                pairwise_diff[f"{alg1} vs {alg2}"] = diff
                significant_diff[f"{alg1} vs {alg2}"] = diff > critical_distance

        # Find homogeneous groups
        groups = self._find_homogeneous_groups(avg_ranks, critical_distance)

        return {
            "test": "Nemenyi",
            "alpha": alpha,
            "critical_distance": critical_distance,
            "q_alpha": q_alpha * np.sqrt(2),  # Original q_alpha for reference
            "average_ranks": avg_ranks.sort_values().to_dict(),
            "pairwise_differences": pairwise_diff,
            "significant_differences": significant_diff,
            "homogeneous_groups": groups,
            "interpretation": self._interpret_nemenyi(significant_diff),
        }

    def wilcoxon_test(
        self, algorithm1: str, algorithm2: str, alternative: str = "two-sided"
    ) -> Dict[str, Any]:
        """
        Perform Wilcoxon signed-rank test between two algorithms.

        Args:
            algorithm1: First algorithm name
            algorithm2: Second algorithm name
            alternative: 'two-sided', 'less', or 'greater'

        Returns:
            Dictionary with test results
        """
        if (
            algorithm1 not in self.pivot_df.columns
            or algorithm2 not in self.pivot_df.columns
        ):
            return {"error": f"Algorithms must be in {list(self.pivot_df.columns)}"}

        data1 = self.pivot_df[algorithm1].values
        data2 = self.pivot_df[algorithm2].values

        # Perform Wilcoxon test
        statistic, p_value = wilcoxon(data1, data2, alternative=alternative)

        # Calculate effect size (rank-biserial correlation)
        differences = data1 - data2
        positive_ranks = rankdata([abs(d) for d in differences if d > 0])
        negative_ranks = rankdata([abs(d) for d in differences if d < 0])

        W_plus = sum(positive_ranks) if len(positive_ranks) > 0 else 0
        W_minus = sum(negative_ranks) if len(negative_ranks) > 0 else 0

        n = len([d for d in differences if d != 0])
        if n > 0:
            r = (W_plus - W_minus) / (n * (n + 1) / 2)
        else:
            r = 0

        return {
            "test": "Wilcoxon signed-rank",
            "algorithm1": algorithm1,
            "algorithm2": algorithm2,
            "statistic": statistic,
            "p_value": p_value,
            "alternative": alternative,
            "effect_size_r": r,
            "significant": p_value < 0.05,
            "interpretation": self._interpret_wilcoxon(
                p_value, r, algorithm1, algorithm2
            ),
        }

    def vargha_delaney_a12(self, algorithm1: str, algorithm2: str) -> Dict[str, Any]:
        """
        Calculate Vargha-Delaney A12 effect size.

        A12 measures the probability that algorithm1 yields better values than algorithm2.

        Args:
            algorithm1: First algorithm name
            algorithm2: Second algorithm name

        Returns:
            Dictionary with A12 value and interpretation
        """
        if (
            algorithm1 not in self.pivot_df.columns
            or algorithm2 not in self.pivot_df.columns
        ):
            return {"error": f"Algorithms must be in {list(self.pivot_df.columns)}"}

        x = self.pivot_df[algorithm1].values
        y = self.pivot_df[algorithm2].values

        n_x = len(x)
        n_y = len(y)

        # Count wins and ties
        wins = 0.0
        ties = 0.0

        for xi in x:
            for yi in y:
                if self.minimize:
                    if xi < yi:
                        wins += 1
                    elif xi == yi:
                        ties += 0.5
                else:
                    if xi > yi:
                        wins += 1
                    elif xi == yi:
                        ties += 0.5

        a12 = (wins + ties) / (n_x * n_y)

        # Interpretation
        magnitude = self._interpret_a12_magnitude(a12)

        return {
            "measure": "Vargha-Delaney A12",
            "algorithm1": algorithm1,
            "algorithm2": algorithm2,
            "a12": a12,
            "interpretation": magnitude,
            "favors": algorithm1 if a12 > 0.5 else algorithm2,
            "description": f"Probability that {algorithm1} performs better than {algorithm2}: {a12:.3f}",
        }

    def cliff_delta(self, algorithm1: str, algorithm2: str) -> Dict[str, Any]:
        """
        Calculate Cliff's delta effect size.

        Cliff's delta is a non-parametric effect size that quantifies the amount
        of difference between two groups.

        Args:
            algorithm1: First algorithm name
            algorithm2: Second algorithm name

        Returns:
            Dictionary with Cliff's delta and interpretation
        """
        if (
            algorithm1 not in self.pivot_df.columns
            or algorithm2 not in self.pivot_df.columns
        ):
            return {"error": f"Algorithms must be in {list(self.pivot_df.columns)}"}

        x = self.pivot_df[algorithm1].values
        y = self.pivot_df[algorithm2].values

        n_x = len(x)
        n_y = len(y)

        # Calculate dominance
        dominance = 0
        for xi in x:
            for yi in y:
                if self.minimize:
                    if xi < yi:
                        dominance += 1
                    elif xi > yi:
                        dominance -= 1
                else:
                    if xi > yi:
                        dominance += 1
                    elif xi < yi:
                        dominance -= 1

        delta = dominance / (n_x * n_y)

        # Interpretation
        magnitude = self._interpret_cliff_magnitude(abs(delta))

        return {
            "measure": "Cliff's delta",
            "algorithm1": algorithm1,
            "algorithm2": algorithm2,
            "delta": delta,
            "magnitude": magnitude,
            "interpretation": self._interpret_cliff_delta(
                delta, algorithm1, algorithm2
            ),
            "favors": algorithm1
            if delta > 0
            else algorithm2
            if delta < 0
            else "neither",
        }

    def generate_cd_diagram(
        self,
        alpha: float = 0.05,
        filename: Optional[str] = None,
        title: str = "Critical Difference Diagram",
    ) -> None:
        """
        Generate Critical Difference diagram with corrected CD calculation.

        Args:
            alpha: Significance level
            filename: Output filename (if None, displays plot)
            title: Plot title
        """
        # Get Nemenyi test results
        nemenyi_results = self.nemenyi_test(alpha)
        avg_ranks = nemenyi_results["average_ranks"]
        cd = nemenyi_results["critical_distance"]

        # Sort algorithms by rank
        sorted_algs = sorted(avg_ranks.items(), key=lambda x: x[1])

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Parameters
        y_start = 0.2
        y_increment = 0.1
        x_start = 1
        x_end = self.n_algorithms

        # Draw rank axis
        ax.plot([x_start, x_end], [y_start, y_start], "k-", linewidth=2)

        # Add tick marks and labels
        for i in range(1, self.n_algorithms + 1):
            ax.plot([i, i], [y_start - 0.02, y_start + 0.02], "k-", linewidth=2)
            ax.text(i, y_start - 0.05, str(i), ha="center", va="top", fontsize=10)

        # Plot algorithms
        y_pos = y_start + y_increment
        for i, (alg, rank) in enumerate(sorted_algs):
            ax.plot(rank, y_pos, "ko", markersize=8)
            ax.text(rank + 0.05, y_pos, alg, ha="left", va="center", fontsize=10)
            y_pos += y_increment * 0.5

        # Draw CD bar
        cd_y = y_start - 0.15
        ax.plot([x_start, x_start + cd], [cd_y, cd_y], "r-", linewidth=3)
        ax.text(
            x_start + cd / 2,
            cd_y - 0.03,
            f"CD = {cd:.3f}",
            ha="center",
            va="top",
            fontsize=10,
            color="red",
        )

        # Draw groups
        groups = nemenyi_results["homogeneous_groups"]
        group_y = y_start + y_increment * len(sorted_algs) * 0.5 + 0.1

        for i, group in enumerate(groups):
            group_algs = [alg for alg, rank in sorted_algs if alg in group]
            if len(group_algs) > 1:
                ranks = [avg_ranks[alg] for alg in group_algs]
                min_rank = min(ranks)
                max_rank = max(ranks)
                ax.plot([min_rank, max_rank], [group_y, group_y], "b-", linewidth=2)
                group_y += 0.05

        # Formatting
        ax.set_xlim(x_start - 0.5, x_end + 0.5)
        ax.set_ylim(0, group_y + 0.1)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")

        # Add info text
        info_text = f"Friedman p-value: {self.friedman_test()['p_value']:.4f}\n"
        info_text += f"k={self.n_algorithms}, N={self.n_instances}, α={alpha}"
        ax.text(
            0.02,
            0.98,
            info_text,
            transform=ax.transAxes,
            verticalalignment="top",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=300, bbox_inches="tight")
            plt.close()
        else:
            plt.show()

    def generate_comprehensive_report(
        self, output_dir: str = ".", alpha: float = 0.05, extended_tests: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistical analysis report.

        Args:
            output_dir: Directory to save report files
            alpha: Significance level
            extended_tests: Whether to include extended tests

        Returns:
            Dictionary with all test results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {
            "metadata": self._get_metadata(),
            "summary_statistics": self._get_summary_statistics(),
            "friedman_test": self.friedman_test(),
            "nemenyi_test": self.nemenyi_test(alpha),
        }

        if extended_tests:
            results["quade_test"] = self.quade_test()

            # Pairwise Wilcoxon tests for top algorithms
            avg_ranks = results["friedman_test"]["average_ranks"]
            top_algorithms = sorted(avg_ranks.items(), key=lambda x: x[1])[:3]

            wilcoxon_results = {}
            for i in range(len(top_algorithms)):
                for j in range(i + 1, len(top_algorithms)):
                    alg1, alg2 = top_algorithms[i][0], top_algorithms[j][0]
                    key = f"{alg1}_vs_{alg2}"
                    wilcoxon_results[key] = self.wilcoxon_test(alg1, alg2)

            results["wilcoxon_tests"] = wilcoxon_results

            # Effect sizes
            effect_sizes = {}
            algorithms = list(self.pivot_df.columns)
            for i in range(len(algorithms)):
                for j in range(i + 1, len(algorithms)):
                    alg1, alg2 = algorithms[i], algorithms[j]
                    key = f"{alg1}_vs_{alg2}"
                    effect_sizes[key] = {
                        "a12": self.vargha_delaney_a12(alg1, alg2),
                        "cliff_delta": self.cliff_delta(alg1, alg2),
                    }

            results["effect_sizes"] = effect_sizes

        # Generate visualizations
        self.generate_cd_diagram(alpha, str(output_path / "cd_diagram.png"))

        # Generate markdown report
        self._generate_markdown_report(results, output_path / "stats_report.md")

        # Save raw results
        with open(output_path / "statistical_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save CSV summaries
        self._save_csv_summaries(results, output_path)

        return results

    def _get_metadata(self) -> Dict[str, Any]:
        """Get metadata for reproducibility."""
        return {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "scipy_version": stats.__version__
            if hasattr(stats, "__version__")
            else "unknown",
            "n_algorithms": self.n_algorithms,
            "n_instances": self.n_instances,
            "algorithms": list(self.pivot_df.columns),
            "instances": list(self.pivot_df.index),
        }

    def _get_summary_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics for each algorithm."""
        summary = {}

        for alg in self.pivot_df.columns:
            values = self.pivot_df[alg].values
            summary[alg] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values),
                "q1": np.percentile(values, 25),
                "q3": np.percentile(values, 75),
            }

        return summary

    def _find_homogeneous_groups(
        self, avg_ranks: pd.Series, critical_distance: float
    ) -> List[List[str]]:
        """Find groups of algorithms with no significant differences."""
        algorithms = list(avg_ranks.sort_values().index)
        groups = []
        used = set()

        for i, alg1 in enumerate(algorithms):
            if alg1 in used:
                continue

            group = [alg1]
            for j in range(i + 1, len(algorithms)):
                alg2 = algorithms[j]
                if abs(avg_ranks[alg1] - avg_ranks[alg2]) <= critical_distance:
                    group.append(alg2)

            groups.append(group)
            used.update(group)

        return groups

    def _interpret_friedman(self, p_value: float) -> str:
        """Interpret Friedman test results."""
        if p_value < 0.001:
            return "Strong evidence of differences between algorithms (p < 0.001)"
        elif p_value < 0.01:
            return "Very strong evidence of differences between algorithms (p < 0.01)"
        elif p_value < 0.05:
            return "Significant differences between algorithms (p < 0.05)"
        else:
            return "No significant differences between algorithms (p ≥ 0.05)"

    def _interpret_quade(self, p_value: float) -> str:
        """Interpret Quade test results."""
        if p_value < 0.001:
            return "Strong evidence of differences (weighted by instance difficulty) between algorithms (p < 0.001)"
        elif p_value < 0.01:
            return "Very strong evidence of differences (weighted) between algorithms (p < 0.01)"
        elif p_value < 0.05:
            return "Significant differences (weighted) between algorithms (p < 0.05)"
        else:
            return "No significant differences (weighted) between algorithms (p ≥ 0.05)"

    def _interpret_nemenyi(self, significant_diff: Dict[str, bool]) -> str:
        """Interpret Nemenyi test results."""
        n_sig = sum(significant_diff.values())
        n_total = len(significant_diff)

        if n_sig == 0:
            return "No significant pairwise differences found"
        else:
            return f"Found {n_sig} significant pairwise differences out of {n_total} comparisons"

    def _interpret_wilcoxon(
        self, p_value: float, effect_size: float, alg1: str, alg2: str
    ) -> str:
        """Interpret Wilcoxon test results."""
        if p_value < 0.05:
            if abs(effect_size) < 0.1:
                magnitude = "negligible"
            elif abs(effect_size) < 0.3:
                magnitude = "small"
            elif abs(effect_size) < 0.5:
                magnitude = "medium"
            else:
                magnitude = "large"

            better = alg1 if effect_size > 0 else alg2
            return f"Significant difference with {magnitude} effect size. {better} performs better."
        else:
            return "No significant difference between algorithms"

    def _interpret_a12_magnitude(self, a12: float) -> str:
        """Interpret Vargha-Delaney A12 magnitude."""
        if a12 >= 0.71:
            return "large"
        elif a12 >= 0.64:
            return "medium"
        elif a12 >= 0.56:
            return "small"
        elif a12 > 0.50:
            return "negligible"
        elif a12 == 0.50:
            return "no difference"
        elif a12 >= 0.44:
            return "negligible"
        elif a12 >= 0.36:
            return "small"
        elif a12 >= 0.29:
            return "medium"
        else:
            return "large"

    def _interpret_cliff_magnitude(self, delta: float) -> str:
        """Interpret Cliff's delta magnitude."""
        if delta < 0.147:
            return "negligible"
        elif delta < 0.33:
            return "small"
        elif delta < 0.474:
            return "medium"
        else:
            return "large"

    def _interpret_cliff_delta(self, delta: float, alg1: str, alg2: str) -> str:
        """Provide interpretation of Cliff's delta value."""
        magnitude = self._interpret_cliff_magnitude(abs(delta))

        if abs(delta) < 0.147:
            return f"Negligible difference between {alg1} and {alg2}"
        else:
            better = alg1 if delta > 0 else alg2
            return f"{magnitude.capitalize()} effect size: {better} performs better"

    def _generate_markdown_report(
        self, results: Dict[str, Any], output_file: Path
    ) -> None:
        """Generate markdown report with all results."""
        with open(output_file, "w") as f:
            f.write("# Statistical Analysis Report\n\n")

            # Metadata
            f.write("## Metadata\n\n")
            f.write(f"- **Generated**: {results['metadata']['timestamp']}\n")
            f.write(f"- **Algorithms**: {results['metadata']['n_algorithms']}\n")
            f.write(f"- **Instances**: {results['metadata']['n_instances']}\n")
            f.write(
                f"- **Python Version**: {results['metadata']['python_version'].split()[0]}\n\n"
            )

            # Summary statistics
            f.write("## Summary Statistics\n\n")
            summary_df = pd.DataFrame(results["summary_statistics"]).T
            f.write(summary_df.round(2).to_markdown() + "\n\n")

            # Friedman test
            f.write("## Friedman Test\n\n")
            friedman = results["friedman_test"]
            f.write(f"- **Statistic**: {friedman['statistic']:.4f}\n")
            f.write(f"- **p-value**: {friedman['p_value']:.4f}\n")
            f.write(f"- **Interpretation**: {friedman['interpretation']}\n\n")

            f.write("### Average Ranks\n\n")
            ranks_df = pd.DataFrame(
                list(friedman["average_ranks"].items()), columns=["Algorithm", "Rank"]
            )
            ranks_df = ranks_df.sort_values("Rank")
            f.write(ranks_df.to_markdown(index=False) + "\n\n")

            # Nemenyi test
            f.write("## Nemenyi Post-hoc Test\n\n")
            nemenyi = results["nemenyi_test"]
            f.write(f"- **Critical Distance**: {nemenyi['critical_distance']:.4f}\n")
            f.write(f"- **Alpha**: {nemenyi['alpha']}\n")
            f.write(f"- **Interpretation**: {nemenyi['interpretation']}\n\n")

            # Homogeneous groups
            f.write("### Homogeneous Groups\n\n")
            for i, group in enumerate(nemenyi["homogeneous_groups"]):
                f.write(f"- **Group {i+1}**: {', '.join(group)}\n")
            f.write("\n")

            # Quade test (if available)
            if "quade_test" in results:
                f.write("## Quade Test\n\n")
                quade = results["quade_test"]
                if "error" not in quade:
                    f.write(f"- **F-statistic**: {quade['statistic']:.4f}\n")
                    f.write(f"- **p-value**: {quade['p_value']:.4f}\n")
                    f.write(f"- **Interpretation**: {quade['interpretation']}\n\n")

            # Effect sizes (if available)
            if "effect_sizes" in results:
                f.write("## Effect Sizes\n\n")
                f.write("### Vargha-Delaney A12\n\n")

                a12_data = []
                for comparison, effects in results["effect_sizes"].items():
                    a12_result = effects["a12"]
                    if "error" not in a12_result:
                        a12_data.append(
                            {
                                "Comparison": comparison.replace("_", " "),
                                "A12": a12_result["a12"],
                                "Interpretation": a12_result["interpretation"],
                                "Favors": a12_result["favors"],
                            }
                        )

                if a12_data:
                    a12_df = pd.DataFrame(a12_data)
                    f.write(a12_df.round(3).to_markdown(index=False) + "\n\n")

            f.write("\n## Conclusion\n\n")
            f.write("Based on the statistical analysis:\n\n")

            if friedman["significant"]:
                f.write(
                    "1. The Friedman test shows significant differences between algorithms.\n"
                )
                f.write(
                    "2. The Nemenyi post-hoc test identifies which algorithms are significantly different.\n"
                )
                f.write(
                    "3. Effect size measures quantify the magnitude of differences.\n"
                )
            else:
                f.write(
                    "1. The Friedman test shows no significant differences between algorithms.\n"
                )
                f.write(
                    "2. All algorithms perform statistically similarly on the tested instances.\n"
                )

    def _save_csv_summaries(self, results: Dict[str, Any], output_path: Path) -> None:
        """Save CSV summaries of results."""
        # Save Friedman results
        friedman_df = pd.DataFrame(
            [
                {
                    "Test": "Friedman",
                    "Statistic": results["friedman_test"]["statistic"],
                    "p-value": results["friedman_test"]["p_value"],
                    "Significant": results["friedman_test"]["significant"],
                }
            ]
        )
        friedman_df.to_csv(output_path / "friedman_results.csv", index=False)

        # Save Nemenyi results
        nemenyi_data = []
        for comparison, is_sig in results["nemenyi_test"][
            "significant_differences"
        ].items():
            algs = comparison.split(" vs ")
            diff = results["nemenyi_test"]["pairwise_differences"][comparison]
            nemenyi_data.append(
                {
                    "Algorithm1": algs[0],
                    "Algorithm2": algs[1],
                    "Rank_Difference": diff,
                    "Significant": is_sig,
                }
            )

        nemenyi_df = pd.DataFrame(nemenyi_data)
        nemenyi_df.to_csv(output_path / "nemenyi_results.csv", index=False)

        # Save effect sizes (if available)
        if "effect_sizes" in results:
            effect_data = []
            for comparison, effects in results["effect_sizes"].items():
                algs = comparison.split("_vs_")
                a12_result = effects["a12"]
                cliff_result = effects["cliff_delta"]

                if "error" not in a12_result and "error" not in cliff_result:
                    effect_data.append(
                        {
                            "Algorithm1": algs[0],
                            "Algorithm2": algs[1],
                            "A12": a12_result["a12"],
                            "A12_Interpretation": a12_result["interpretation"],
                            "Cliff_Delta": cliff_result["delta"],
                            "Cliff_Interpretation": cliff_result["magnitude"],
                        }
                    )

            if effect_data:
                effect_df = pd.DataFrame(effect_data)
                effect_df.to_csv(output_path / "effect_sizes.csv", index=False)


# Convenience functions for backward compatibility


def perform_statistical_analysis(
    results_df: pd.DataFrame,
    output_dir: str = ".",
    alpha: float = 0.05,
    extended_tests: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to perform complete statistical analysis.

    Args:
        results_df: DataFrame with benchmark results
        output_dir: Directory to save results
        alpha: Significance level
        extended_tests: Whether to include extended tests

    Returns:
        Dictionary with all test results
    """
    analyzer = AdvancedStatisticalAnalysis(results_df)
    return analyzer.generate_comprehensive_report(output_dir, alpha, extended_tests)


def generate_cd_diagram(
    results_df: pd.DataFrame,
    alpha: float = 0.05,
    filename: Optional[str] = None,
    title: str = "Critical Difference Diagram",
) -> None:
    """
    Convenience function to generate Critical Difference diagram.

    Args:
        results_df: DataFrame with benchmark results
        alpha: Significance level
        filename: Output filename
        title: Plot title
    """
    analyzer = AdvancedStatisticalAnalysis(results_df)
    analyzer.generate_cd_diagram(alpha, filename, title)
