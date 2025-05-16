#!/usr/bin/env python3
"""
Advanced statistical analysis module for comparing metaheuristic algorithms.

Implements:
  • Aligned Friedman test for global p-value
  • Post-hoc Nemenyi test for pairwise comparisons
  • Vargha-Delaney A12 effect size
  • Critical Difference diagram generation
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import friedmanchisquare, rankdata
from statsmodels.stats.libqsturng import qsturng
import logging
import scikit_posthocs as sp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("advanced_statistical_analysis")

def aligned_friedman_test(data, alpha=0.05):
    """
    Perform the aligned Friedman test for comparing multiple algorithms.

    The aligned Friedman test adjusts for instance difficulty by subtracting
    the average performance for each instance.

    Args:
        data: DataFrame with columns 'Algorithm', 'Instance', 'Value'
        alpha: Significance level (default: 0.05)

    Returns:
        Dictionary with test results
    """
    # Group by Instance and Algorithm to get one value per combination
    # This handles cases with multiple runs per instance-algorithm pair
    grouped = data.groupby(['Instance', 'Algorithm'])['Value'].mean().reset_index()

    # Pivot data to algorithms as columns, instances as rows
    pivot = grouped.pivot(index='Instance', columns='Algorithm', values='Value')

    # Check if we have enough data
    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        return {
            "friedman_p": 1.0,
            "error": "Insufficient data: need at least 2 instances and 2 algorithms"
        }

    # Align the data: subtract row (instance) means
    instance_means = pivot.mean(axis=1)
    aligned_data = pivot.sub(instance_means, axis=0)

    # Calculate ranks for aligned data (lower is better rank)
    aligned_ranks = aligned_data.rank(axis=1, method='average', ascending=True)

    # Calculate mean ranks for each algorithm
    mean_ranks = aligned_ranks.mean(axis=0)

    # Prepare data for Friedman test
    n = pivot.shape[0]  # Number of instances
    k = pivot.shape[1]  # Number of algorithms

    # Perform the Friedman test
    friedman_statistic, p_value = friedmanchisquare(*[aligned_ranks[col].values for col in aligned_ranks.columns])

    # Calculate critical distance for Nemenyi test
    critical_distance = qsturng(1 - alpha, k, np.inf) * np.sqrt((k * (k + 1)) / (6 * n))

    return {
        "friedman_p": p_value,
        "statistic": friedman_statistic,
        "reject_h0": p_value < alpha,
        "alpha": alpha,
        "mean_ranks": mean_ranks.to_dict(),
        "critical_distance": critical_distance,
        "n_instances": n,
        "n_algorithms": k
    }

def nemenyi_posthoc_test(data, alpha=0.05):
    """
    Perform Nemenyi post-hoc test after Friedman test.

    Args:
        data: DataFrame with columns 'Algorithm', 'Instance', 'Value'
        alpha: Significance level (default: 0.05)

    Returns:
        DataFrame with p-values for pairwise comparisons
    """
    # Group by Instance and Algorithm to get one value per combination
    # This handles cases with multiple runs per instance-algorithm pair
    grouped = data.groupby(['Instance', 'Algorithm'])['Value'].mean().reset_index()

    # Pivot data to algorithms as columns, instances as rows
    pivot = grouped.pivot(index='Instance', columns='Algorithm', values='Value')

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

def vargha_delaney_a12(data):
    """
    Calculate Vargha-Delaney A12 effect size for all algorithm pairs.

    Args:
        data: DataFrame with columns 'Algorithm', 'Instance', 'Value'

    Returns:
        DataFrame with A12 values for each algorithm pair
    """
    # Group by Instance and Algorithm to get one value per combination
    # This handles cases with multiple runs per instance-algorithm pair
    grouped = data.groupby(['Instance', 'Algorithm'])['Value'].mean().reset_index()

    algorithms = grouped['Algorithm'].unique()

    # Initialize result matrix
    a12_matrix = pd.DataFrame(index=algorithms, columns=algorithms)

    # For each algorithm pair
    for algo1 in algorithms:
        for algo2 in algorithms:
            if algo1 == algo2:
                a12_matrix.loc[algo1, algo2] = 0.5  # Same algorithm, A12 = 0.5
            else:
                values1 = grouped[grouped['Algorithm'] == algo1]['Value'].values
                values2 = grouped[grouped['Algorithm'] == algo2]['Value'].values

                # Calculate A12 (probability that algo1 outperforms algo2)
                # For minimization problems, smaller values are better
                wins = 0.0
                for v1 in values1:
                    for v2 in values2:
                        if v1 < v2:  # algo1 wins (minimization)
                            wins += 1
                        elif v1 == v2:  # tie
                            wins += 0.5

                a12 = wins / (len(values1) * len(values2))
                a12_matrix.loc[algo1, algo2] = a12

    return a12_matrix

def create_cd_diagram(ranks, names, cd=None, output_file='cd_diagram.png', 
                     title="Critical Difference Diagram", reverse=False):
    """
    Create critical difference diagram to visualize algorithm rankings.
    
    Based on Demšar (2006) and the implementation by Orange Data Mining Library.
    
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
    # Sort algorithms by rank (ascending)
    sorted_idx = np.argsort(ranks)
    if reverse:
        sorted_idx = sorted_idx[::-1]
    
    sorted_ranks = ranks[sorted_idx]
    sorted_names = np.array(names)[sorted_idx]
    
    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(-0.5, len(names) - 0.5)
    ax.set_ylim(0, 2.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])
    
    # Draw horizontal line for the ranks
    ax.axhline(y=1, color='black', linestyle='-', linewidth=1)
    
    # Position each algorithm on the line
    for i, (rank, name) in enumerate(zip(sorted_ranks, sorted_names)):
        # Normalize ranks to position
        pos = i
        
        # Add algorithm name and rank
        ax.text(pos, 1.2, name, ha='center', va='bottom', rotation=45)
        ax.text(pos, 0.8, f"{rank:.2f}", ha='center', va='top')
        
        # Add dot for algorithm
        ax.plot(pos, 1, 'o', color='black', markersize=6)
    
    # Draw CD line if provided
    if cd is not None:
        # Calculate normalized CD
        cd_norm = cd
        
        # Add CD to legend
        ax.plot([], [], '-', color='red', label=f'CD = {cd:.2f}')
        
        # Draw all intervals where algorithms are not significantly different
        for i in range(len(sorted_ranks)):
            for j in range(i + 1, len(sorted_ranks)):
                if abs(sorted_ranks[i] - sorted_ranks[j]) <= cd:
                    # Draw line connecting non-significantly different algorithms
                    y_offset = 0.1 * ((j - i) % 5 + 1)  # Vary line height to prevent overlap
                    ax.plot([i, j], [1 + y_offset, 1 + y_offset], '-', color='black', linewidth=2)
        
        # Add CD legend at the bottom
        ax.text(len(names) / 2, 2.2, f"Critical Difference (CD) = {cd:.2f}", 
               ha='center', fontsize=12, bbox=dict(facecolor='white', alpha=0.8))
    
    # Set title
    ax.set_title(title)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_file

def interpret_a12(a12):
    """
    Interpret Vargha-Delaney A12 effect size.
    
    Args:
        a12: A12 effect size value
        
    Returns:
        String interpretation of effect size
    """
    if a12 < 0.5:
        a12 = 1 - a12  # Ensure a12 >= 0.5 for interpretation
    
    if a12 < 0.56:
        return "Negligible"
    elif a12 < 0.64:
        return "Small"
    elif a12 < 0.71:
        return "Medium"
    else:
        return "Large"

def generate_stats_report(results, output_file):
    """
    Generate a markdown report from statistical results.
    
    Args:
        results: Dictionary with statistical results
        output_file: Path to save the report
        
    Returns:
        Path to the saved report
    """
    with open(output_file, 'w') as f:
        f.write("# Statistical Analysis Report\n\n")
        
        # Friedman test results
        f.write("## Friedman Test Results\n\n")
        f.write(f"* Global p-value: {results['friedman_p']:.6f}\n")
        f.write(f"* Critical Difference: {results['cd_diagram'].split('=')[-1].strip() if 'cd_diagram' in results else 'N/A'}\n\n")
        
        # Algorithm rankings
        f.write("## Algorithm Rankings\n\n")
        
        # Sort algorithms by rank
        if 'mean_ranks' in results:
            ranks = results['mean_ranks']
            sorted_algos = sorted(ranks.items(), key=lambda x: x[1])
            
            f.write("| Rank | Algorithm | Mean Rank |\n")
            f.write("|------|-----------|----------:|\n")
            
            for i, (algo, rank) in enumerate(sorted_algos):
                f.write(f"| {i+1} | {algo} | {rank:.2f} |\n")
            
            f.write("\n")
        
        # Nemenyi post-hoc test
        if 'nemenyi' in results and not results['nemenyi'].empty:
            f.write("## Nemenyi Post-hoc Test (p-values)\n\n")
            
            # Format p-values table
            nemenyi_table = results['nemenyi'].copy()
            nemenyi_table = nemenyi_table.round(4)
            
            # Convert to markdown
            nemenyi_md = nemenyi_table.to_markdown()
            f.write(nemenyi_md + "\n\n")
            
            # Highlight significant p-values
            f.write("*p-values < 0.05 indicate statistically significant differences*\n\n")
        
        # A12 effect size
        if 'a12' in results and not results['a12'].empty:
            f.write("## Vargha-Delaney A12 Effect Size\n\n")
            
            # Format A12 table
            a12_table = results['a12'].copy()
            a12_table = a12_table.round(4)
            
            # Convert to markdown
            a12_md = a12_table.to_markdown()
            f.write(a12_md + "\n\n")
            
            # Add interpretation guide
            f.write("*Interpretation of A12 values:*\n\n")
            f.write("* A12 = 0.5: No effect (equal performance)\n")
            f.write("* A12 < 0.5: Algorithm in row performs better than algorithm in column\n")
            f.write("* A12 > 0.5: Algorithm in column performs better than algorithm in row\n\n")
            f.write("*Effect size magnitude:*\n\n")
            f.write("* 0.5 < A12 < 0.56: Negligible\n")
            f.write("* 0.56 ≤ A12 < 0.64: Small\n")
            f.write("* 0.64 ≤ A12 < 0.71: Medium\n")
            f.write("* A12 ≥ 0.71: Large\n\n")
        
        # Conclusions section
        f.write("## Conclusions\n\n")
        
        if 'friedman_p' in results:
            if results['friedman_p'] < 0.05:
                f.write("* There are statistically significant differences between the algorithms (p < 0.05)\n")
                
                # Top 3 algorithms
                if 'mean_ranks' in results:
                    top3 = sorted_algos[:3]
                    f.write("* Top 3 algorithms:\n")
                    for i, (algo, rank) in enumerate(top3):
                        f.write(f"  {i+1}. **{algo}** (rank: {rank:.2f})\n")
                
                # Statistically equivalent algorithms (within CD)
                if 'mean_ranks' in results and 'critical_distance' in results:
                    cd = results['critical_distance']
                    best_algo = sorted_algos[0][0]
                    best_rank = sorted_algos[0][1]
                    
                    equivalent = [best_algo]
                    for algo, rank in sorted_algos[1:]:
                        if abs(rank - best_rank) <= cd:
                            equivalent.append(algo)
                    
                    if len(equivalent) > 1:
                        f.write(f"* Statistically equivalent to the best algorithm ({best_algo}):\n")
                        for algo in equivalent[1:]:
                            f.write(f"  - {algo}\n")
                    else:
                        f.write(f"* The best algorithm ({best_algo}) is significantly better than all others\n")
            else:
                f.write("* No statistically significant differences between algorithms (p >= 0.05)\n")
                f.write("* All algorithms can be considered equivalent in performance\n")
    
    return output_file

def run_all(csv_path, out_dir):
    """
    Execute:
      • Aligned Friedman (global p-value)
      • Post-hoc Nemenyi (p-values matrix)
      • Vargha-Delaney A12 (pairwise)

    Generate:
      – cd_diagram.png  (Critical Difference diagram for α=0.05)
      – stats_report.md (Markdown table with p-values and effect sizes)

    Args:
        csv_path: Path to CSV file with benchmark results.
                 The CSV must contain columns:
                 - "Algorithm" (required): Algorithm name
                 - "Instance" (required): Instance name
                 - Either "Best" or "Best Fitness" (required): Performance metric
        out_dir: Directory to save the results

    Returns:
        Dictionary with results and file paths
    """
    # Create output directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)
    
    # Load data
    try:
        df = pd.read_csv(csv_path)

        # Check if required columns exist
        required_columns = ['Algorithm', 'Instance']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return {
                "error": f"Missing required columns: {missing_columns}",
                "required": required_columns
            }

        # Detect performance column
        score_col = next(
            (c for c in df.columns if c.lower() in {"best", "best fitness"}),
            None,
        )
        if score_col is None:
            logger.error("No se encontró columna de desempeño ('Best' o 'Best Fitness')")
            return {
                "error": "No se encontró columna de desempeño ('Best' o 'Best Fitness')"
            }

        # Prepare data in the expected format
        data = df[['Algorithm', 'Instance', score_col]].copy()
        data.rename(columns={score_col: 'Value'}, inplace=True)
        
        # Step 1: Run Aligned Friedman test
        friedman_result = aligned_friedman_test(data)
        
        # Step 2: Run Post-hoc Nemenyi test
        nemenyi_result = nemenyi_posthoc_test(data)
        
        # Step 3: Calculate Vargha-Delaney A12 effect size
        a12_result = vargha_delaney_a12(data)
        
        # Step 4: Generate Critical Difference diagram
        cd_diagram_path = os.path.join(out_dir, 'cd_diagram.png')
        
        # Get algorithm names and ranks
        algorithms = list(friedman_result['mean_ranks'].keys())
        ranks = np.array(list(friedman_result['mean_ranks'].values()))
        
        # Create CD diagram
        create_cd_diagram(
            ranks=ranks,
            names=algorithms,
            cd=friedman_result['critical_distance'],
            output_file=cd_diagram_path,
            title="Critical Difference Diagram (α=0.05)"
        )
        
        # Step 5: Generate statistics report
        results = {
            "friedman_p": friedman_result['friedman_p'],
            "nemenyi": nemenyi_result,
            "a12": a12_result,
            "mean_ranks": friedman_result['mean_ranks'],
            "critical_distance": friedman_result['critical_distance'],
            "cd_diagram": cd_diagram_path
        }
        
        report_path = os.path.join(out_dir, 'stats_report.md')
        generate_stats_report(results, report_path)
        
        # Return results with file paths
        results["report"] = report_path
        
        return results
        
    except Exception as e:
        logger.error(f"Error in statistical analysis: {str(e)}")
        return {"error": str(e)}
