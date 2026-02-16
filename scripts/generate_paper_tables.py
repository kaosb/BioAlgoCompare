#!/usr/bin/env python3
"""Generate LaTeX tables for the IWINAC 2026 paper.

Reads QC-DVRP experiment results and produces tables formatted for
Springer LNCS class, ready for \\input{} in the paper.

Output tables:
    - Table 2: Comparative results (Mean +/- Std for ADT, DSR, WBI)
    - Table 3: Friedman ranks and p-values
    - Table 4: Pairwise Wilcoxon comparisons (optional)

Usage:
    python scripts/generate_paper_tables.py --input results/dvrp_*/results.json
    python scripts/generate_paper_tables.py --input results/dvrp_*/results.json --output tables/
"""
import click
import json
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.benchmarking import DVRPBenchmarkResult


def load_results(json_path):
    """Load DVRP results from JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    results = {}
    for name, d in data.items():
        results[name] = DVRPBenchmarkResult.from_dict(d)
    return results


def generate_results_table(results, output_path):
    """Generate Table 2: Comparative results.

    Format: Algorithm | ADT (mean +/- std) | DSR (mean +/- std) | WBI (mean +/- std)
    Best values in bold.
    """
    rows = []
    metrics_data = {}

    for name, r in results.items():
        m = r.compute_metrics()
        metrics_data[name] = m
        rows.append({
            "name": name,
            "adt_mean": m["adt"]["mean"],
            "adt_std": m["adt"]["std"],
            "dsr_mean": m["dsr"]["mean"],
            "dsr_std": m["dsr"]["std"],
            "wbi_mean": m["wbi"]["mean"],
            "wbi_std": m["wbi"]["std"],
        })

    # Find best values (ADT: lower, DSR: higher, WBI: lower)
    best_adt = min(r["adt_mean"] for r in rows)
    best_dsr = max(r["dsr_mean"] for r in rows)
    best_wbi = min(r["wbi_mean"] for r in rows)

    def _bold(val, best, fmt, higher_better=False):
        s = fmt.format(val)
        if higher_better:
            return f"\\textbf{{{s}}}" if val >= best else s
        return f"\\textbf{{{s}}}" if val <= best else s

    latex = []
    latex.append("\\begin{table}[t]")
    latex.append("\\caption{Comparative results of metaheuristic algorithms on the QC-DVRP simulation (30 independent runs).}")
    latex.append("\\label{tab:results}")
    latex.append("\\centering")
    latex.append("\\begin{tabular}{lcccccc}")
    latex.append("\\hline")
    latex.append("Algorithm & \\multicolumn{2}{c}{ADT (min)} & \\multicolumn{2}{c}{DSR (\\%)} & \\multicolumn{2}{c}{WBI} \\\\")
    latex.append(" & Mean & Std & Mean & Std & Mean & Std \\\\")
    latex.append("\\hline")

    for r in rows:
        adt_m = _bold(r["adt_mean"], best_adt, "{:.2f}")
        dsr_m = _bold(r["dsr_mean"], best_dsr, "{:.1f}", higher_better=True)
        wbi_m = _bold(r["wbi_mean"], best_wbi, "{:.2f}")

        latex.append(
            f"{r['name']} & {adt_m} & {r['adt_std']:.2f} "
            f"& {dsr_m} & {r['dsr_std']:.1f} "
            f"& {wbi_m} & {r['wbi_std']:.2f} \\\\"
        )

    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")

    content = "\n".join(latex)
    with open(output_path, "w") as f:
        f.write(content)

    return content


def generate_friedman_table(results, output_path):
    """Generate Table 3: Friedman ranks and statistical test results.

    Performs Friedman test on ADT, DSR, and WBI separately.
    """
    from scipy.stats import friedmanchisquare, rankdata

    metrics_tables = {}

    for metric_key, metric_label, higher_better in [
        ("adt", "ADT", False),
        ("dsr", "DSR", True),
        ("wbi", "WBI", False),
    ]:
        # Build data matrix: rows = runs, columns = algorithms
        algo_names = list(results.keys())
        n_runs = min(len(r.adt_values) for r in results.values())

        data_matrix = np.zeros((n_runs, len(algo_names)))
        for j, name in enumerate(algo_names):
            r = results[name]
            values = getattr(r, f"{metric_key}_values")[:n_runs]
            data_matrix[:, j] = values

        # Compute ranks per run
        ranks = np.zeros_like(data_matrix)
        for i in range(n_runs):
            if higher_better:
                ranks[i] = rankdata(-data_matrix[i])  # Higher is better -> rank 1
            else:
                ranks[i] = rankdata(data_matrix[i])  # Lower is better -> rank 1

        avg_ranks = ranks.mean(axis=0)

        # Friedman test
        if n_runs >= 3 and len(algo_names) >= 3:
            samples = [data_matrix[:, j] for j in range(len(algo_names))]
            stat, p_value = friedmanchisquare(*samples)
        else:
            stat, p_value = 0, 1.0

        metrics_tables[metric_key] = {
            "label": metric_label,
            "algo_names": algo_names,
            "avg_ranks": avg_ranks,
            "statistic": stat,
            "p_value": p_value,
        }

    # Generate LaTeX
    latex = []
    latex.append("\\begin{table}[t]")
    latex.append("\\caption{Friedman test results and average ranks for each metric.}")
    latex.append("\\label{tab:friedman}")
    latex.append("\\centering")
    latex.append("\\begin{tabular}{l" + "c" * len(list(results.keys())) + "cc}")
    latex.append("\\hline")

    algo_names = list(results.keys())
    header = "Metric & " + " & ".join(algo_names) + " & $\\chi^2$ & $p$-value \\\\"
    latex.append(header)
    latex.append("\\hline")

    for key, table in metrics_tables.items():
        ranks_str = " & ".join(f"{r:.2f}" for r in table["avg_ranks"])
        sig = "^*" if table["p_value"] < 0.05 else ""
        latex.append(
            f"{table['label']} & {ranks_str} "
            f"& {table['statistic']:.2f} & {table['p_value']:.4f}{sig} \\\\"
        )

    latex.append("\\hline")
    latex.append("\\multicolumn{" + str(len(algo_names) + 3) + "}{l}{$^*$ Significant at $\\alpha = 0.05$} \\\\")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")

    content = "\n".join(latex)
    with open(output_path, "w") as f:
        f.write(content)

    return content


@click.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to DVRP results JSON")
@click.option("--output", "-o", "output_dir", default=None, help="Output directory for .tex files")
def main(input_path, output_dir):
    """Generate LaTeX tables from QC-DVRP experiment results."""
    if output_dir is None:
        output_dir = os.path.dirname(input_path)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading results from {input_path}...")
    results = load_results(input_path)
    print(f"Found {len(results)} algorithms with results")

    # Generate Table 2: Comparative results
    table2_path = os.path.join(output_dir, "table_results.tex")
    content = generate_results_table(results, table2_path)
    print(f"\nTable 2 (Results):\n{content}\n")
    print(f"Saved to {table2_path}")

    # Generate Table 3: Friedman ranks
    table3_path = os.path.join(output_dir, "table_friedman.tex")
    content = generate_friedman_table(results, table3_path)
    print(f"\nTable 3 (Friedman):\n{content}\n")
    print(f"Saved to {table3_path}")

    print(f"\nAll tables saved to {output_dir}")


if __name__ == "__main__":
    main()
