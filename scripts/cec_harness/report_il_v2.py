"""Audited v2 report for the IL cross-algorithm study (remediates audit
findings M5, M6 and the implementation auditor's direction-label risk).

Changes vs stage_report (v1):
  * Direction label decided by the MEDIAN of paired differences (rank-consistent
    with the Wilcoxon test), not by the difference of means.
  * Multiple-comparison control: Holm-Bonferroni over the 41 per-function
    Wilcoxon p-values per (algorithm, budget); both raw and Holm-corrected
    better/equal/worse counts are reported.
  * Effect size: Vargha-Delaney A12 (probability that an IL run beats a paired
    base run) per function, summarized as the median across functions.
  * Scale-robust improvement: median across functions of the median paired
    log10-error improvement, complementing the (scale-fragile) relative
    improvement of means.

Reads results/il_pipeline/eval[ _fes50000]/ and writes
results/il_pipeline/il_ood_report_v2[_fes50000].json.
"""

import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IL = os.path.join(_REPO, "results", "il_pipeline")
ALGOS = ["DE", "PSO", "GA", "GWO", "ACO", "HO"]
TEST = ([("CEC2017", f) for f in range(1, 30)]
        + [("CEC2022", f) for f in range(1, 13)])
EPS = 1e-12
FLOOR = 1e-30  # log floor for exact zeros


def a12(x, y):
    """Vargha-Delaney A12: P(x < y) + 0.5 P(x == y) for minimization
    (probability that a value from x (IL) is better, i.e. smaller, than y)."""
    x = np.asarray(x)[:, None]
    y = np.asarray(y)[None, :]
    return float(((x < y).sum() + 0.5 * (x == y).sum()) / (x.shape[0] * y.shape[1]))


def holm(pvals, alpha=0.05):
    """Return boolean array: reject H0 per Holm-Bonferroni."""
    p = np.asarray(pvals)
    order = np.argsort(p)
    m = len(p)
    reject = np.zeros(m, dtype=bool)
    for rank, idx in enumerate(order):
        if p[idx] <= alpha / (m - rank):
            reject[idx] = True
        else:
            break
    return reject


def analyze(eval_dir):
    per_algo = {}
    for algo in ALGOS:
        rows = []
        for suite, fnum in TEST:
            path = os.path.join(eval_dir, f"{algo}__{suite}__F{fnum}.json")
            if not os.path.exists(path):
                continue
            r = json.load(open(path))
            b = np.asarray(r["base"], dtype=float)
            i = np.asarray(r["il"], dtype=float)
            diff = b - i
            med_diff = float(np.median(diff))
            if np.allclose(diff, 0.0, atol=1e-12):
                p = 1.0
            else:
                try:
                    _, p = wilcoxon(b, i)
                except ValueError:
                    p = 1.0
            # scale-robust paired improvement in log10 space (floor exact 0s)
            logdiff = np.log10(np.maximum(b, FLOOR)) - np.log10(np.maximum(i, FLOOR))
            rows.append({
                "suite": suite, "fnum": fnum, "p": float(p),
                "med_diff": med_diff,
                "rel_mean": float((b.mean() - i.mean()) / (abs(b.mean()) + EPS)),
                "med_log10_impr": float(np.median(logdiff)),
                "a12": a12(i, b),
            })
        pvals = [r["p"] for r in rows]
        rej_raw = [p < 0.05 for p in pvals]
        rej_holm = holm(pvals)
        for r, rr, rh in zip(rows, rej_raw, rej_holm):
            direction = "better" if r["med_diff"] > 0 else ("worse" if r["med_diff"] < 0 else "equal")
            r["verdict_raw"] = direction if rr and direction != "equal" else "equal"
            r["verdict_holm"] = direction if rh and direction != "equal" else "equal"
        def count(key):
            return {v: sum(1 for r in rows if r[key] == v)
                    for v in ("better", "equal", "worse")}
        per_algo[algo] = {
            "rows": rows,
            "bew_raw": count("verdict_raw"),
            "bew_holm": count("verdict_holm"),
            "median_rel_mean": float(np.median([r["rel_mean"] for r in rows])),
            "median_med_log10_impr": float(np.median([r["med_log10_impr"] for r in rows])),
            "median_a12": float(np.median([r["a12"] for r in rows])),
        }
    return per_algo


def main():
    for tag, sub in [("5e3", "eval"), ("5e4", "eval_fes50000")]:
        d = os.path.join(IL, sub)
        if not os.path.isdir(d):
            continue
        res = analyze(d)
        suffix = "" if sub == "eval" else "_fes50000"
        out = os.path.join(IL, f"il_ood_report_v2{suffix}.json")
        with open(out, "w") as fh:
            json.dump(res, fh, indent=2)
        print(f"\n=== {tag} (audited v2; direction=median diff; n=41) ===")
        print(f"{'algo':5} {'BEW raw':>10} {'BEW Holm':>10} {'medA12':>7} "
              f"{'med rel%':>9} {'med log10':>10}")
        for a in ALGOS:
            r = res[a]
            braw = "{better}/{equal}/{worse}".format(**r["bew_raw"])
            bh = "{better}/{equal}/{worse}".format(**r["bew_holm"])
            print(f"{a:5} {braw:>10} {bh:>10} {r['median_a12']:>7.3f} "
                  f"{r['median_rel_mean']*100:>+8.1f}% {r['median_med_log10_impr']:>+9.3f}")
        print(f"saved {out}")


if __name__ == "__main__":
    main()
