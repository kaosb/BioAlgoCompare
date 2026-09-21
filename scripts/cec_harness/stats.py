"""Statistical analysis for the CEC PoC.

Provides:

* ``friedman_test`` — omnibus Friedman test over the per-problem performance
  matrix (rows = problems, cols = algorithms).
* ``shaffer_posthoc`` — all-pairs post-hoc on the Friedman ranks with Shaffer's
  *static* multiple-comparison correction. scikit-posthocs 0.11.x does not ship
  a ``posthoc_shaffer`` function, so the Shaffer static procedure is implemented
  here on top of the standard Friedman rank z-statistics (Demsar 2006; Garcia &
  Herrera 2008). ``posthoc_conover_friedman`` from scikit-posthocs is also
  computed as a cross-check / equivalent post-hoc.
* ``wilcoxon_bew`` — Wilcoxon signed-rank "better/equal/worse" tally of a
  reference algorithm (HO) against each competitor, counting on how many
  problems HO is significantly better, statistically indistinguishable, or
  significantly worse (alpha=0.05).
"""

import math
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.stats import friedmanchisquare, norm, wilcoxon, rankdata

try:
    import scikit_posthocs as sp
except ImportError:  # pragma: no cover
    sp = None


# --------------------------------------------------------------------------
# Friedman omnibus
# --------------------------------------------------------------------------
def friedman_test(perf_matrix: np.ndarray) -> dict:
    """Friedman test over a (problems x algorithms) performance matrix.

    Lower values are better (errors). Returns the statistic, p-value, df and
    the mean rank per algorithm column.
    """
    perf_matrix = np.asarray(perf_matrix, dtype=float)
    n_problems, k = perf_matrix.shape
    stat, p = friedmanchisquare(*[perf_matrix[:, j] for j in range(k)])

    # Mean ranks per column (rank within each row, lower error -> rank 1).
    ranks = np.vstack([rankdata(perf_matrix[i, :]) for i in range(n_problems)])
    mean_ranks = ranks.mean(axis=0)
    return {
        "statistic": float(stat),
        "p_value": float(p),
        "df": int(k - 1),
        "n_problems": int(n_problems),
        "k": int(k),
        "mean_ranks": mean_ranks.tolist(),
    }


# --------------------------------------------------------------------------
# Shaffer static post-hoc
# --------------------------------------------------------------------------
def _shaffer_s(k: int) -> List[int]:
    """S(k): possible numbers of true null hypotheses among k(k-1)/2 pairwise
    comparisons of k groups (Shaffer 1986). Returns the sorted set of values.
    """
    # Recursive definition: S(0)=S(1)={0}; otherwise
    # S(k) = U_{j=1..k} { C(j,2) + s : s in S(k-j) }.
    cache: Dict[int, set] = {0: {0}, 1: {0}}

    def S(m: int) -> set:
        if m in cache:
            return cache[m]
        out = set()
        for j in range(1, m + 1):
            cj2 = j * (j - 1) // 2
            for s in S(m - j):
                out.add(cj2 + s)
        cache[m] = out
        return out

    return sorted(S(k))


def _shaffer_static_thresholds(k: int) -> List[int]:
    """For each ordered comparison index i (1-based among m=k(k-1)/2 pairs),
    the Shaffer static value t_i = max number of hypotheses that can be
    simultaneously true given that i-1 have been rejected.
    """
    m = k * (k - 1) // 2
    svals = _shaffer_s(k)  # sorted ascending, max is m
    # t_i is the largest element of S(k) that is <= m - i + 1.
    thresholds = []
    for i in range(1, m + 1):
        cap = m - i + 1
        t_i = max(s for s in svals if s <= cap)
        thresholds.append(t_i)
    return thresholds


def shaffer_posthoc(perf_matrix: np.ndarray, algos: Sequence[str], alpha: float = 0.05) -> dict:
    """All-pairs post-hoc with Shaffer static correction on Friedman ranks.

    Pairwise z-statistic (Demsar 2006):
        z_ij = (R_i - R_j) / sqrt(k(k+1) / (6 N))
    with two-sided p-values, sorted ascending, then corrected with Shaffer's
    static thresholds: adjusted_p_(i) = min(1, t_i * p_(i)) made monotone.
    """
    perf_matrix = np.asarray(perf_matrix, dtype=float)
    n_problems, k = perf_matrix.shape
    ranks = np.vstack([rankdata(perf_matrix[i, :]) for i in range(n_problems)])
    mean_ranks = ranks.mean(axis=0)

    se = math.sqrt(k * (k + 1) / (6.0 * n_problems))

    pairs = list(combinations(range(k), 2))
    raw = []
    for (a, b) in pairs:
        z = (mean_ranks[a] - mean_ranks[b]) / se
        p = 2.0 * (1.0 - norm.cdf(abs(z)))
        raw.append({"a": algos[a], "b": algos[b], "z": float(z), "p_raw": float(p)})

    # Sort by raw p ascending and apply Shaffer static thresholds.
    order = sorted(range(len(raw)), key=lambda idx: raw[idx]["p_raw"])
    thresholds = _shaffer_static_thresholds(k)
    adj = [None] * len(raw)
    running_max = 0.0
    for rank_i, idx in enumerate(order):
        t_i = thresholds[rank_i]
        a_p = min(1.0, t_i * raw[idx]["p_raw"])
        running_max = max(running_max, a_p)  # enforce monotonicity
        adj[idx] = running_max

    results = []
    for idx, r in enumerate(raw):
        results.append({
            **r,
            "p_shaffer": float(adj[idx]),
            "significant": bool(adj[idx] < alpha),
        })

    out = {
        "mean_ranks": {algos[j]: float(mean_ranks[j]) for j in range(k)},
        "pairs": results,
    }

    # Cross-check with scikit-posthocs Conover-Friedman if available.
    if sp is not None:
        try:
            conover = sp.posthoc_conover_friedman(perf_matrix)
            conover.index = list(algos)
            conover.columns = list(algos)
            out["conover_friedman"] = conover.to_dict()
        except Exception as exc:  # pragma: no cover
            out["conover_friedman_error"] = str(exc)
    return out


# --------------------------------------------------------------------------
# Wilcoxon better / equal / worse
# --------------------------------------------------------------------------
def wilcoxon_bew(
    raw_cells: List[dict],
    reference: str,
    competitors: Sequence[str],
    dim: int,
    max_fes: int,
    alpha: float = 0.05,
) -> Dict[str, dict]:
    """Per-problem Wilcoxon signed-rank tally of ``reference`` vs each competitor.

    For each (suite, F, dim) problem in the (dim, max_fes) config, runs a paired
    Wilcoxon signed-rank test over the ``n_reps`` best_errors of reference vs
    competitor. Counts, across problems, in how many the reference is
    significantly BETTER (lower median error, p<alpha), EQUAL (p>=alpha), or
    WORSE (higher median, p<alpha).
    """
    # Index cells by (algo, suite, fnum) for this config.
    idx = {}
    for c in raw_cells:
        if int(c["dim"]) != int(dim) or int(c["max_fes"]) != int(max_fes):
            continue
        idx[(c["algo"], c["suite"], int(c["fnum"]))] = c

    problems = sorted({(s, f) for (a, s, f) in idx if a == reference})

    table = {}
    for comp in competitors:
        better = equal = worse = 0
        details = []
        for (suite, fnum) in problems:
            ref_cell = idx.get((reference, suite, fnum))
            cmp_cell = idx.get((comp, suite, fnum))
            if ref_cell is None or cmp_cell is None:
                continue
            x = np.asarray(ref_cell["best_errors"], dtype=float)
            y = np.asarray(cmp_cell["best_errors"], dtype=float)
            med_ref = float(np.median(x))
            med_cmp = float(np.median(y))
            diff = x - y
            if np.allclose(diff, 0.0):
                # Identical samples: no difference.
                equal += 1
                outcome = "equal"
                pval = 1.0
            else:
                try:
                    _, pval = wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
                except ValueError:
                    pval = 1.0
                if pval < alpha:
                    if med_ref < med_cmp:
                        better += 1
                        outcome = "better"
                    else:
                        worse += 1
                        outcome = "worse"
                else:
                    equal += 1
                    outcome = "equal"
            details.append({
                "suite": suite, "fnum": fnum,
                "median_ref": med_ref, "median_cmp": med_cmp,
                "p": float(pval), "outcome": outcome,
            })
        table[comp] = {
            "better": better, "equal": equal, "worse": worse,
            "n_problems": better + equal + worse,
            "details": details,
        }
    return table
