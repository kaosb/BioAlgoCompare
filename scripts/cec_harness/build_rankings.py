"""Build per-problem ranks and aggregated (mean) ranks for a set of cells.

Given a collection of cell summaries (each carrying ``mean`` over replicas, the
algorithm name and the problem identity), this module:

1. Builds a matrix ``mean_perf[problem][algo]`` (mean best_error over replicas).
2. Ranks the algorithms within each problem (lower error == better == rank 1)
   using ``scipy.stats.rankdata`` with ``method='average'`` for ties. To avoid
   spurious tie-breaking from floating-point noise, near-equal values
   (``|delta| < tol``) are pre-clustered to a shared canonical value so they
   receive an identical (averaged) rank.
3. Averages each algorithm's per-problem ranks over all problems in the set.

A "problem" here is the pair (suite, F, dim); MaxFES is *not* part of the
problem identity, so rankings are normally built per (dim, max_fes) config by
the caller filtering the cell list beforehand.
"""

from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.stats import rankdata

TOL = 1e-8


def problem_key(cell: dict) -> Tuple[str, int, int]:
    """Identity of a problem instance: (suite, fnum, dim)."""
    return (cell["suite"], int(cell["fnum"]), int(cell["dim"]))


def _cluster_ties(values: Sequence[float], tol: float = TOL) -> np.ndarray:
    """Snap values that are within ``tol`` of each other to a shared value.

    Sorts the values, walks them, and assigns every member of a contiguous
    near-equal run the run's first value. This guarantees ``rankdata`` treats
    them as exact ties (identical averaged rank) without altering the ordering
    of genuinely distinct values.
    """
    vals = np.asarray(values, dtype=float)
    order = np.argsort(vals, kind="mergesort")
    canon = vals.copy()
    cluster_anchor = vals[order[0]]
    for idx in order:
        if abs(vals[idx] - cluster_anchor) < tol:
            canon[idx] = cluster_anchor
        else:
            cluster_anchor = vals[idx]
            canon[idx] = cluster_anchor
    return canon


def build_rankings(cells: List[dict], tol: float = TOL) -> dict:
    """Return per-problem ranks and aggregated mean ranks.

    Args:
        cells: cell summaries that all belong to the same config (the caller is
            responsible for filtering by dim/max_fes if desired).
        tol: tie tolerance for pre-clustering near-equal means.

    Returns:
        dict with:
          * ``algos``: sorted list of algorithm names.
          * ``problems``: sorted list of (suite, fnum, dim) tuples.
          * ``mean_perf``: {problem: {algo: mean_error}}.
          * ``per_problem_ranks``: {problem: {algo: rank}}.
          * ``avg_ranks``: {algo: mean rank over problems} (lower == better).
    """
    algos = sorted({c["algo"] for c in cells})
    problems = sorted({problem_key(c) for c in cells})

    mean_perf: Dict[Tuple, Dict[str, float]] = {p: {} for p in problems}
    for c in cells:
        mean_perf[problem_key(c)][c["algo"]] = float(c["mean"])

    per_problem_ranks: Dict[Tuple, Dict[str, float]] = {}
    rank_accum = {a: [] for a in algos}

    for p in problems:
        row = mean_perf[p]
        # Require every algorithm present for a fair per-problem ranking.
        present = [a for a in algos if a in row]
        vals = np.array([row[a] for a in present], dtype=float)
        canon = _cluster_ties(vals, tol=tol)
        ranks = rankdata(canon, method="average")  # 1 == best (lowest error)
        prank = {a: float(r) for a, r in zip(present, ranks)}
        per_problem_ranks[p] = prank
        for a in present:
            rank_accum[a].append(prank[a])

    avg_ranks = {
        a: (float(np.mean(rank_accum[a])) if rank_accum[a] else float("nan"))
        for a in algos
    }

    return {
        "algos": algos,
        "problems": problems,
        "mean_perf": mean_perf,
        "per_problem_ranks": per_problem_ranks,
        "avg_ranks": avg_ranks,
    }


def filter_cells(cells: List[dict], dim: int, max_fes: int) -> List[dict]:
    """Subset cells matching a (dim, max_fes) configuration."""
    return [
        c for c in cells if int(c["dim"]) == int(dim) and int(c["max_fes"]) == int(max_fes)
    ]
