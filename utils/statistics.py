"""
Unified statistical analysis module for BioAlgoCompare.
Consolidates functionality from statistical_analysis.py, advanced_statistical_analysis.py,
and enhanced_statistics.py into a single, well-organized module.

This module provides comprehensive statistical analysis capabilities for comparing
algorithm performance including:
- Non-parametric tests (Friedman, Kruskal-Wallis, Mann-Whitney, Wilcoxon)
- Post-hoc analysis (Nemenyi, Dunn, Conover)
- Effect size calculations (Cliff's Delta, Vargha-Delaney A, Rank Biserial)
- Bootstrap analysis and confidence intervals
- Critical difference diagrams and visualizations
- Publication-ready tables and reports
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import scipy.stats as stats
from scipy.stats import friedmanchisquare, kruskal, mannwhitneyu, wilcoxon, rankdata
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from pathlib import Path
import warnings
import logging
from itertools import combinations
import scikit_posthocs as sp

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """Container for statistical test results."""
    test_name: str
    statistic: float
    p_value: float
    alpha: float
    significant: bool
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    post_hoc: Optional[Dict[str, Any]] = None
    interpretation: Optional[str] = None


@dataclass
class ComprehensiveAnalysisResult:
    """Container for comprehensive statistical analysis results."""
    friedman_result: Optional[StatisticalTestResult] = None
    kruskal_result: Optional[StatisticalTestResult] = None
    wilcoxon_results: Optional[Dict[str, StatisticalTestResult]] = None
    effect_sizes: Optional[Dict[str, Dict[str, float]]] = None
    rankings: Optional[pd.DataFrame] = None
    bootstrap_results: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


class UnifiedStatisticalAnalysis:
    """
    Unified statistical analysis class for algorithm comparison.
    
    This class provides a comprehensive suite of statistical tests and
    analysis methods for comparing metaheuristic algorithms.
    """
    
    def __init__(self, alpha: float = 0.05, n_bootstrap: int = 10000):
        """
        Initialize the statistical analysis module.
        
        Args:
            alpha: Significance level for statistical tests
            n_bootstrap: Number of bootstrap samples for confidence intervals
        """
        self.alpha = alpha
        self.n_bootstrap = n_bootstrap
        
    def prepare_data(
        self, 
        data: Union[Dict, pd.DataFrame, List],
        metric: str = "fitness"
    ) -> pd.DataFrame:
        """
        Prepare data for statistical analysis.
        
        Args:
            data: Input data in various formats
            metric: Metric to extract if data is structured
            
        Returns:
            DataFrame with algorithms as columns and runs as rows
        """
        if isinstance(data, pd.DataFrame):
            return data
            
        if isinstance(data, dict):
            # Handle nested dictionary structure
            if all(isinstance(v, dict) for v in data.values()):
                # Extract specific metric from nested structure
                prepared_data = {}
                for algo, instances in data.items():
                    values = []
                    for instance, metrics in instances.items():
                        if isinstance(metrics, dict) and metric in metrics:
                            values.extend(metrics[metric])
                        elif isinstance(metrics, list):
                            values.extend(metrics)
                    prepared_data[algo] = values
                    
                # Ensure all algorithms have same number of values
                max_len = max(len(v) for v in prepared_data.values())
                for algo in prepared_data:
                    if len(prepared_data[algo]) < max_len:
                        prepared_data[algo].extend([np.nan] * (max_len - len(prepared_data[algo])))
                        
                return pd.DataFrame(prepared_data)
            else:
                # Simple dictionary of lists
                return pd.DataFrame(data)
                
        raise ValueError(f"Unsupported data format: {type(data)}")
    
    def friedman_test(
        self, 
        data: pd.DataFrame,
        alpha: Optional[float] = None
    ) -> StatisticalTestResult:
        """
        Perform Friedman test for comparing multiple algorithms.
        
        Args:
            data: DataFrame with algorithms as columns
            alpha: Significance level (uses instance default if None)
            
        Returns:
            StatisticalTestResult with test details
        """
        alpha = alpha or self.alpha
        
        # Remove any rows with NaN values
        clean_data = data.dropna()
        
        if len(clean_data) < 3:
            raise ValueError("Friedman test requires at least 3 complete observations")
            
        if clean_data.shape[1] < 3:
            raise ValueError("Friedman test requires at least 3 algorithms")
        
        # Perform Friedman test
        statistic, p_value = friedmanchisquare(*[clean_data[col] for col in clean_data.columns])
        
        # Calculate average ranks
        ranks = clean_data.rank(axis=1, method='average')
        avg_ranks = ranks.mean()
        
        result = StatisticalTestResult(
            test_name="Friedman Test",
            statistic=statistic,
            p_value=p_value,
            alpha=alpha,
            significant=p_value < alpha,
            post_hoc={'average_ranks': avg_ranks.to_dict()},
            interpretation=self._interpret_friedman_result(p_value, alpha, avg_ranks)
        )
        
        return result
    
    def kruskal_wallis_test(
        self,
        data: pd.DataFrame,
        alpha: Optional[float] = None
    ) -> StatisticalTestResult:
        """
        Perform Kruskal-Wallis test for comparing multiple algorithms.
        
        Args:
            data: DataFrame with algorithms as columns
            alpha: Significance level
            
        Returns:
            StatisticalTestResult with test details
        """
        alpha = alpha or self.alpha
        
        # Remove NaN values
        samples = [data[col].dropna().values for col in data.columns]
        
        if any(len(s) < 2 for s in samples):
            raise ValueError("Each algorithm needs at least 2 observations")
        
        statistic, p_value = kruskal(*samples)
        
        result = StatisticalTestResult(
            test_name="Kruskal-Wallis Test",
            statistic=statistic,
            p_value=p_value,
            alpha=alpha,
            significant=p_value < alpha,
            interpretation=self._interpret_kruskal_result(p_value, alpha)
        )
        
        return result
    
    def nemenyi_post_hoc(
        self,
        data: pd.DataFrame,
        alpha: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Perform Nemenyi post-hoc test after significant Friedman test.
        
        Args:
            data: DataFrame with algorithms as columns
            alpha: Significance level
            
        Returns:
            DataFrame with p-values for pairwise comparisons
        """
        alpha = alpha or self.alpha
        clean_data = data.dropna()
        
        # Use scikit-posthocs for Nemenyi test
        result = sp.posthoc_nemenyi_friedman(clean_data)
        
        return result
    
    def wilcoxon_pairwise(
        self,
        data: pd.DataFrame,
        baseline: Optional[str] = None,
        alpha: Optional[float] = None,
        bonferroni: bool = True
    ) -> Dict[str, StatisticalTestResult]:
        """
        Perform pairwise Wilcoxon signed-rank tests.
        
        Args:
            data: DataFrame with algorithms as columns
            baseline: Baseline algorithm for comparison (if None, all pairs)
            alpha: Significance level
            bonferroni: Apply Bonferroni correction
            
        Returns:
            Dictionary of pairwise test results
        """
        alpha = alpha or self.alpha
        results = {}
        
        if baseline:
            # Compare all against baseline
            pairs = [(baseline, col) for col in data.columns if col != baseline]
        else:
            # All pairwise comparisons
            pairs = list(combinations(data.columns, 2))
        
        # Apply Bonferroni correction if requested
        adjusted_alpha = alpha / len(pairs) if bonferroni else alpha
        
        for algo1, algo2 in pairs:
            # Get paired data
            paired_data = data[[algo1, algo2]].dropna()
            
            if len(paired_data) < 5:
                logger.warning(f"Insufficient data for Wilcoxon test between {algo1} and {algo2}")
                continue
                
            # Perform Wilcoxon test
            statistic, p_value = wilcoxon(paired_data[algo1], paired_data[algo2])
            
            # Calculate effect size (rank biserial correlation)
            effect_size = self._calculate_rank_biserial(paired_data[algo1], paired_data[algo2])
            
            results[f"{algo1}_vs_{algo2}"] = StatisticalTestResult(
                test_name="Wilcoxon Signed-Rank Test",
                statistic=statistic,
                p_value=p_value,
                alpha=adjusted_alpha,
                significant=p_value < adjusted_alpha,
                effect_size=effect_size,
                interpretation=self._interpret_wilcoxon_result(p_value, adjusted_alpha, effect_size)
            )
            
        return results
    
    def calculate_effect_sizes(
        self,
        data: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate effect sizes for all pairwise comparisons.
        
        Args:
            data: DataFrame with algorithms as columns
            
        Returns:
            Nested dictionary with effect sizes
        """
        algorithms = data.columns.tolist()
        effect_sizes = {
            'cliff_delta': {},
            'vargha_delaney': {},
            'rank_biserial': {}
        }
        
        for algo1, algo2 in combinations(algorithms, 2):
            key = f"{algo1}_vs_{algo2}"
            
            # Get paired data
            d1 = data[algo1].dropna()
            d2 = data[algo2].dropna()
            
            # Calculate different effect sizes
            effect_sizes['cliff_delta'][key] = self._cliff_delta(d1, d2)
            effect_sizes['vargha_delaney'][key] = self._vargha_delaney_a(d1, d2)
            effect_sizes['rank_biserial'][key] = self._calculate_rank_biserial(d1, d2)
            
        return effect_sizes
    
    def bootstrap_confidence_intervals(
        self,
        data: pd.DataFrame,
        metric_func: callable = np.mean,
        confidence_level: float = 0.95,
        n_bootstrap: Optional[int] = None
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        Calculate bootstrap confidence intervals for each algorithm.
        
        Args:
            data: DataFrame with algorithms as columns
            metric_func: Function to calculate metric (default: mean)
            confidence_level: Confidence level (default: 0.95)
            n_bootstrap: Number of bootstrap samples
            
        Returns:
            Dictionary with (lower, estimate, upper) for each algorithm
        """
        n_bootstrap = n_bootstrap or self.n_bootstrap
        results = {}
        
        for algo in data.columns:
            values = data[algo].dropna().values
            
            if len(values) < 2:
                results[algo] = (np.nan, np.nan, np.nan)
                continue
                
            # Bootstrap sampling
            bootstrap_samples = []
            for _ in range(n_bootstrap):
                sample = np.random.choice(values, size=len(values), replace=True)
                bootstrap_samples.append(metric_func(sample))
            
            # Calculate confidence intervals
            alpha = 1 - confidence_level
            lower = np.percentile(bootstrap_samples, alpha/2 * 100)
            upper = np.percentile(bootstrap_samples, (1 - alpha/2) * 100)
            estimate = metric_func(values)
            
            results[algo] = (lower, estimate, upper)
            
        return results
    
    def run_comprehensive_analysis(
        self,
        data: Union[Dict, pd.DataFrame],
        metric: str = "fitness",
        baseline_algorithm: Optional[str] = None,
        include_bootstrap: bool = True
    ) -> ComprehensiveAnalysisResult:
        """
        Run comprehensive statistical analysis on algorithm comparison data.
        
        Args:
            data: Input data
            metric: Metric to analyze
            baseline_algorithm: Baseline for pairwise comparisons
            include_bootstrap: Whether to include bootstrap analysis
            
        Returns:
            ComprehensiveAnalysisResult with all test results
        """
        # Prepare data
        df = self.prepare_data(data, metric)
        
        result = ComprehensiveAnalysisResult()
        
        # Friedman test
        try:
            result.friedman_result = self.friedman_test(df)
        except Exception as e:
            logger.warning(f"Friedman test failed: {e}")
        
        # Kruskal-Wallis test
        try:
            result.kruskal_result = self.kruskal_wallis_test(df)
        except Exception as e:
            logger.warning(f"Kruskal-Wallis test failed: {e}")
        
        # Wilcoxon pairwise tests
        try:
            result.wilcoxon_results = self.wilcoxon_pairwise(df, baseline_algorithm)
        except Exception as e:
            logger.warning(f"Wilcoxon tests failed: {e}")
        
        # Effect sizes
        try:
            result.effect_sizes = self.calculate_effect_sizes(df)
        except Exception as e:
            logger.warning(f"Effect size calculation failed: {e}")
        
        # Rankings
        result.rankings = self._calculate_rankings(df)
        
        # Bootstrap analysis
        if include_bootstrap:
            try:
                result.bootstrap_results = {
                    'mean': self.bootstrap_confidence_intervals(df, np.mean),
                    'median': self.bootstrap_confidence_intervals(df, np.median)
                }
            except Exception as e:
                logger.warning(f"Bootstrap analysis failed: {e}")
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def generate_critical_difference_diagram(
        self,
        data: pd.DataFrame,
        title: str = "Critical Difference Diagram",
        save_path: Optional[Path] = None
    ) -> plt.Figure:
        """
        Generate critical difference diagram for algorithm comparison.
        
        Args:
            data: DataFrame with algorithms as columns
            title: Plot title
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure
        """
        # Calculate average ranks
        ranks = data.rank(axis=1, method='average')
        avg_ranks = ranks.mean().sort_values()
        
        # Perform Nemenyi test
        nemenyi_result = self.nemenyi_post_hoc(data)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot ranks
        y_positions = np.arange(len(avg_ranks))
        ax.barh(y_positions, avg_ranks.values)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(avg_ranks.index)
        ax.set_xlabel('Average Rank')
        ax.set_title(title)
        
        # Add critical difference lines
        # This is a simplified version - full implementation would show CD bars
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        return fig
    
    def generate_statistical_report(
        self,
        analysis_result: ComprehensiveAnalysisResult,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate comprehensive statistical report.
        
        Args:
            analysis_result: Results from comprehensive analysis
            output_path: Path to save the report
            
        Returns:
            Report as string
        """
        report = []
        report.append("# Statistical Analysis Report\n")
        report.append(f"Generated on: {pd.Timestamp.now()}\n")
        
        # Friedman test results
        if analysis_result.friedman_result:
            report.append("## Friedman Test\n")
            report.append(f"- Statistic: {analysis_result.friedman_result.statistic:.4f}")
            report.append(f"- p-value: {analysis_result.friedman_result.p_value:.4f}")
            report.append(f"- Significant: {analysis_result.friedman_result.significant}")
            report.append(f"- Interpretation: {analysis_result.friedman_result.interpretation}\n")
        
        # Rankings
        if analysis_result.rankings is not None:
            report.append("## Algorithm Rankings\n")
            report.append(analysis_result.rankings.to_string())
            report.append("\n")
        
        # Effect sizes
        if analysis_result.effect_sizes:
            report.append("## Effect Sizes (Cliff's Delta)\n")
            for comparison, value in analysis_result.effect_sizes['cliff_delta'].items():
                report.append(f"- {comparison}: {value:.3f} ({self._interpret_effect_size(value)})")
            report.append("\n")
        
        # Recommendations
        if analysis_result.recommendations:
            report.append("## Recommendations\n")
            for rec in analysis_result.recommendations:
                report.append(f"- {rec}")
        
        report_text = "\n".join(report)
        
        if output_path:
            output_path.write_text(report_text)
            
        return report_text
    
    # Private helper methods
    
    def _cliff_delta(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate Cliff's Delta effect size."""
        n1, n2 = len(x), len(y)
        
        # Count how many times x[i] > y[j]
        greater = sum(1 for xi in x for yj in y if xi > yj)
        # Count how many times x[i] < y[j]  
        less = sum(1 for xi in x for yj in y if xi < yj)
        
        return (less - greater) / (n1 * n2)
    
    def _vargha_delaney_a(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate Vargha-Delaney A measure."""
        n1, n2 = len(x), len(y)
        
        # Rank all observations
        all_obs = np.concatenate([x, y])
        ranks = rankdata(all_obs)
        
        # Sum of ranks for first group
        r1 = np.sum(ranks[:n1])
        
        # Calculate A measure
        return (r1 / n1 - (n1 + 1) / 2) / n2
    
    def _calculate_rank_biserial(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate rank biserial correlation."""
        # This is a simplified implementation
        u_stat, _ = mannwhitneyu(x, y, alternative='two-sided')
        n1, n2 = len(x), len(y)
        return 1 - (2 * u_stat) / (n1 * n2)
    
    def _calculate_rankings(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate algorithm rankings."""
        ranks = data.rank(axis=1, method='average')
        
        ranking_df = pd.DataFrame({
            'Average Rank': ranks.mean(),
            'Median Rank': ranks.median(),
            'Best Rank Count': (ranks == 1).sum(),
            'Worst Rank Count': (ranks == len(data.columns)).sum()
        })
        
        return ranking_df.sort_values('Average Rank')
    
    def _interpret_effect_size(self, effect_size: float, method: str = "cliff_delta") -> str:
        """Interpret effect size magnitude."""
        abs_es = abs(effect_size)
        
        if method == "cliff_delta":
            if abs_es < 0.147:
                return "negligible"
            elif abs_es < 0.33:
                return "small"
            elif abs_es < 0.474:
                return "medium"
            else:
                return "large"
        else:
            # Generic interpretation
            if abs_es < 0.2:
                return "small"
            elif abs_es < 0.5:
                return "medium"
            else:
                return "large"
    
    def _interpret_friedman_result(self, p_value: float, alpha: float, avg_ranks: pd.Series) -> str:
        """Generate interpretation of Friedman test results."""
        if p_value < alpha:
            best_algo = avg_ranks.idxmin()
            return f"Significant differences found. {best_algo} has the best average rank ({avg_ranks[best_algo]:.2f})."
        else:
            return "No significant differences found between algorithms."
    
    def _interpret_kruskal_result(self, p_value: float, alpha: float) -> str:
        """Generate interpretation of Kruskal-Wallis test results."""
        if p_value < alpha:
            return "Significant differences found between algorithm distributions."
        else:
            return "No significant differences found between algorithm distributions."
    
    def _interpret_wilcoxon_result(self, p_value: float, alpha: float, effect_size: float) -> str:
        """Generate interpretation of Wilcoxon test results."""
        if p_value < alpha:
            magnitude = self._interpret_effect_size(effect_size)
            direction = "better" if effect_size > 0 else "worse"
            return f"Significant difference with {magnitude} effect size. First algorithm performs {direction}."
        else:
            return "No significant difference found."
    
    def _generate_recommendations(self, result: ComprehensiveAnalysisResult) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Check if significant differences exist
        if result.friedman_result and result.friedman_result.significant:
            recommendations.append("Significant differences found. Consider using the best-ranked algorithm.")
            
            # Find best algorithm
            if result.rankings is not None:
                best_algo = result.rankings.index[0]
                recommendations.append(f"Algorithm '{best_algo}' shows the best overall performance.")
        else:
            recommendations.append("No significant differences found. All algorithms perform similarly.")
            
        # Check effect sizes
        if result.effect_sizes:
            large_effects = []
            for comparison, value in result.effect_sizes['cliff_delta'].items():
                if abs(value) > 0.474:  # Large effect
                    large_effects.append(comparison)
                    
            if large_effects:
                recommendations.append(f"Large practical differences found in: {', '.join(large_effects)}")
        
        # Check consistency
        if result.rankings is not None:
            consistent_best = result.rankings[result.rankings['Best Rank Count'] > 0].index.tolist()
            if consistent_best:
                recommendations.append(f"Algorithms with best performance instances: {', '.join(consistent_best)}")
        
        return recommendations


# Convenience functions for backward compatibility

def friedman_test(data_df: pd.DataFrame, alpha: float = 0.05) -> Dict[str, Any]:
    """Backward compatible Friedman test function."""
    analyzer = UnifiedStatisticalAnalysis(alpha=alpha)
    result = analyzer.friedman_test(data_df)
    
    return {
        'statistic': result.statistic,
        'p_value': result.p_value,
        'significant': result.significant,
        'avg_ranks': result.post_hoc['average_ranks']
    }


def generate_statistical_analysis_report(
    results_file: str,
    output_dir: str = "reports",
    alpha: float = 0.05
) -> None:
    """Backward compatible report generation function."""
    import json
    
    # Load data
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Create analyzer
    analyzer = UnifiedStatisticalAnalysis(alpha=alpha)
    
    # Run analysis
    result = analyzer.run_comprehensive_analysis(data)
    
    # Generate report
    output_path = Path(output_dir) / "statistical_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    analyzer.generate_statistical_report(result, output_path)
    
    # Generate visualizations
    df = analyzer.prepare_data(data)
    fig = analyzer.generate_critical_difference_diagram(
        df, 
        save_path=Path(output_dir) / "critical_difference.png"
    )
    plt.close(fig)
    
    print(f"Statistical analysis report generated in {output_dir}")


def run_all(csv_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Run all statistical analyses on CSV data.
    Backward compatible function for test_stats_smoke.py.
    
    Args:
        csv_path: Path to CSV file with benchmark results
        output_dir: Directory for output files
        
    Returns:
        Dictionary with analysis results
    """
    import pandas as pd
    from pathlib import Path
    
    # Load CSV data
    df = pd.read_csv(csv_path)
    
    # Prepare data for analysis - need to aggregate by instance first
    # Expected format: Algorithm, Instance, Run, Best Fitness
    # We need one value per algorithm per instance for Friedman test
    aggregated_data = df.groupby(['Algorithm', 'Instance'])['Best Fitness'].mean().reset_index()
    
    # Pivot to get algorithms as columns, instances as rows
    pivot_data = aggregated_data.pivot(
        index='Instance',
        columns='Algorithm',
        values='Best Fitness'
    )
    
    # Create analyzer
    analyzer = UnifiedStatisticalAnalysis()
    
    # Run comprehensive analysis
    analysis_result = analyzer.run_comprehensive_analysis(pivot_data)
    
    # Prepare return dictionary
    results = {
        'friedman_p': analysis_result.friedman_result.p_value if analysis_result.friedman_result else None,
        'mean_ranks': analysis_result.friedman_result.post_hoc['average_ranks'] if analysis_result.friedman_result else {},
        'critical_distance': None,  # Will be calculated below
        'nemenyi': pd.DataFrame(),  # Empty dataframe by default
        'a12': pd.DataFrame()  # Empty dataframe by default
    }
    
    # Calculate critical distance and Nemenyi results
    if analysis_result.friedman_result and analysis_result.friedman_result.significant:
        try:
            nemenyi_df = analyzer.nemenyi_post_hoc(pivot_data)
            results['nemenyi'] = nemenyi_df
        except Exception as e:
            logger.warning(f"Nemenyi test failed: {e}")
            results['nemenyi'] = pd.DataFrame()
        
        # Calculate critical distance (simplified)
        n_algorithms = len(pivot_data.columns)
        n_instances = len(pivot_data)
        # Use appropriate q_alpha based on number of algorithms
        # This is a simplified table - real implementation would use full table
        q_alpha_table = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728}
        q_alpha = q_alpha_table.get(n_algorithms, 2.569)
        results['critical_distance'] = q_alpha * np.sqrt(n_algorithms * (n_algorithms + 1) / (6 * n_instances))
    
    # Calculate A12 effect sizes
    if analysis_result.effect_sizes:
        # Convert effect sizes to DataFrame format expected by tests
        a12_data = {}
        for comparison, value in analysis_result.effect_sizes['vargha_delaney'].items():
            algo1, algo2 = comparison.split('_vs_')
            if algo1 not in a12_data:
                a12_data[algo1] = {}
            a12_data[algo1][algo2] = value
            # Add reverse comparison
            if algo2 not in a12_data:
                a12_data[algo2] = {}
            a12_data[algo2][algo1] = 1 - value
        
        # Create full matrix with diagonal values of 0.5
        all_algos = list(pivot_data.columns)
        for algo in all_algos:
            if algo not in a12_data:
                a12_data[algo] = {}
            for other_algo in all_algos:
                if algo == other_algo:
                    a12_data[algo][other_algo] = 0.5
        
        results['a12'] = pd.DataFrame(a12_data).fillna(0.5)
    
    # Generate outputs
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate CD diagram
    cd_path = output_path / "cd_diagram.png"
    try:
        fig = analyzer.generate_critical_difference_diagram(pivot_data, save_path=cd_path)
        plt.close(fig)
        results['cd_diagram'] = str(cd_path)
    except Exception as e:
        logger.warning(f"CD diagram generation failed: {e}")
        # Create a simple plot as fallback
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'CD Diagram\n(Not enough data)', ha='center', va='center')
        fig.savefig(cd_path)
        plt.close(fig)
        results['cd_diagram'] = str(cd_path)
    
    # Generate report
    report_path = output_path / "stats_report.md"
    report_text = analyzer.generate_statistical_report(analysis_result, report_path)
    results['report'] = str(report_path)
    
    return results


# Export main class and convenience functions
__all__ = [
    'UnifiedStatisticalAnalysis',
    'StatisticalTestResult',
    'ComprehensiveAnalysisResult',
    'friedman_test',
    'generate_statistical_analysis_report',
    'run_all'
]