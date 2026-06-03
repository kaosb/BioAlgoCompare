#!/usr/bin/env python3
"""Compute the full statistical analysis for a QC-DVRP results_detailed.csv:
Friedman (k algos, N runs), average ranks, Nemenyi CD, pairwise Wilcoxon vs a
reference algorithm, and Vargha-Delaney A12 effect sizes vs the reference.

Usage: python scripts/analyze_dvrp_stats.py results/<dir>/results_detailed.csv [--ref HO]
"""
import sys
import click
import numpy as np
import pandas as pd
from collections import defaultdict
from scipy import stats

METRICS = [("ADT", False), ("DSR", True), ("WBI", False), ("Fitness", False)]  # (name, higher_better)


def a12(x, y):
    m, n = len(x), len(y)
    gt = sum(np.sum(xi > y) for xi in x)
    eq = sum(np.sum(xi == y) for xi in x)
    return (gt + 0.5 * eq) / (m * n)


@click.command()
@click.argument("csv_path")
@click.option("--ref", default="HO")
def main(csv_path, ref):
    rows = list(pd.read_csv(csv_path).to_dict("records"))
    algs = sorted({r["Algorithm"] for r in rows}, key=lambda a: (a != ref, a))
    k = len(algs)

    def matrix(metric):
        d = defaultdict(dict)
        for r in rows:
            d[int(r["Run"])][r["Algorithm"]] = float(r[metric])
        runs = sorted(d.keys())
        return np.array([[d[run][a] for a in algs] for run in runs]), runs

    N = len(matrix("Fitness")[1])
    qa = {6: 2.850, 7: 2.949, 5: 2.728}.get(k, 2.949)  # Nemenyi q_alpha (alpha=0.05)
    CD = qa * np.sqrt(k * (k + 1) / (6 * N))
    print(f"Algorithms (k={k}): {algs} | N={N} | Nemenyi CD={CD:.3f}\n")

    for m, hb in METRICS:
        M, _ = matrix(m)
        chi2, p = stats.friedmanchisquare(*[M[:, j] for j in range(k)])
        Msign = -M if hb else M
        R = np.array([stats.rankdata(row) for row in Msign])
        ranks = R.mean(axis=0)
        order = np.argsort(ranks)
        print(f"=== {m} (higher_better={hb}) | Friedman chi2={chi2:.2f} p={p:.3g} ===")
        for j in order:
            print(f"   {algs[j]:7} rank={ranks[j]:.2f}  mean={M[:,j].mean():.2f}±{M[:,j].std(ddof=1):.2f}")
        # vs reference
        ri = algs.index(ref)
        for j in range(k):
            if j == ri:
                continue
            w = stats.wilcoxon(M[:, ri], M[:, j]).pvalue
            eff = a12(M[:, ri], M[:, j])
            mag = "grande" if abs(eff - .5) >= .214 else "medio" if abs(eff - .5) >= .14 else "peq/triv"
            print(f"     {ref} vs {algs[j]:7} Wilcoxon p={w:.4f}  A12={eff:.3f} ({mag})")
        print()


if __name__ == "__main__":
    main()
