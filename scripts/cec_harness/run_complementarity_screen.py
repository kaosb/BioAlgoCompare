"""
Complementarity screen — Paso 1 of the transfer line (pre-registro v2 §5.7).

Lesson from the C1 ladder: DE+PSO is a DOMINATED pair (PSO wins 6/6), and no
cooperation mechanism can rescue a portfolio of one good + one bad solver. Before
testing any further mechanism, find a COMPLEMENTARY pool: solvers that win on
DIFFERENT functions, so the virtual-best (VBS) meaningfully beats the single-best
(SBS). Only there does cooperation have theoretical room to help.

Method: run each faithful solver ISOLATED at full budget B (paired seeds) on the
taxonomy function set; build the function x solver error matrix; for every pair
(A, B) compute the complementarity gain

    gain(A,B) = mean_f [ (err_SBS(f) - min(err_A(f), err_B(f))) / (|err_SBS(f)| + eps) ]

where SBS is the better-ranked solver of the pair across functions. High gain =
each wins where the other loses. Pairs must support the il_model hook to be
eligible for parametric transfer (DE, PSO, GWO, GA, ACO).

    python scripts/cec_harness/run_complementarity_screen.py
    RUNS=15 BUDGET=5000 python .../run_complementarity_screen.py

Output: results/cooperative/complementarity_screen.json + printed matrix/top pairs.
"""

import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402

from problems.continuous.cec_problem import CECProblem, run_with_fes  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from algorithms.ssa import SSA  # noqa: E402
from algorithms.woa import WOA  # noqa: E402
from utils.provenance import provenance  # noqa: E402

FUNCS = [1, 4, 6, 9, 15, 23]          # taxonomy set (F22 excluded, anomalous)
DIM = 10
BUDGET = int(os.environ.get("BUDGET", "5000"))
RUNS = int(os.environ.get("RUNS", "15"))
POP = 30

# il_model-hook support (eligible for parametric transfer): DE, PSO, GWO, GA, ACO.
SOLVERS = {
    "DE": (DE, True), "PSO": (PSO, True), "GWO": (GWO, True),
    "GA": (GA, True), "ACO": (ACO, True),
    "SSA": (SSA, False), "WOA": (WOA, False),   # context only (no hook)
}

OUT_DIR = os.path.join(_REPO_ROOT, "results", "cooperative")
OUT_PATH = os.path.join(OUT_DIR, "complementarity_screen.json")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    med = {}       # solver -> {func: median error}
    print(f"[screen] {len(SOLVERS)} solvers x {len(FUNCS)} funcs x {RUNS} runs, "
          f"B={BUDGET} 10D")
    for name, (cls, _) in SOLVERS.items():
        med[name] = {}
        for f in FUNCS:
            errs = [float(run_with_fes(cls, CECProblem("CEC2014", f, DIM),
                                       pop_size=POP, max_fes=BUDGET, seed=3000 + r))
                    for r in range(RUNS)]
            med[name][f"F{f}"] = float(np.median(errs))
        print(f"  {name:5s} " + "  ".join(f"F{f}={med[name][f'F{f}']:.2e}"
                                          for f in FUNCS))

    # per-function ranks (1 = best)
    ranks = {n: {} for n in med}
    for f in FUNCS:
        vals = sorted(med.items(), key=lambda kv: kv[1][f"F{f}"])
        for pos, (n, _) in enumerate(vals):
            ranks[n][f"F{f}"] = pos + 1
    mean_rank = {n: float(np.mean(list(r.values()))) for n, r in ranks.items()}

    # pairwise complementarity among hook-supporting solvers
    eligible = [n for n, (_, hook) in SOLVERS.items() if hook]
    pairs = []
    for i, a in enumerate(eligible):
        for b in eligible[i + 1:]:
            sbs = a if mean_rank[a] <= mean_rank[b] else b
            gains, a_wins, b_wins = [], 0, 0
            for f in FUNCS:
                ea, eb = med[a][f"F{f}"], med[b][f"F{f}"]
                es = med[sbs][f"F{f}"]
                gains.append((es - min(ea, eb)) / (abs(es) + 1e-12))
                if ea < eb:
                    a_wins += 1
                elif eb < ea:
                    b_wins += 1
            pairs.append({
                "pair": f"{a}+{b}", "sbs": sbs,
                "gain_vbs_over_sbs": float(np.mean(gains)),
                "wins": {a: a_wins, b: b_wins},
                "balanced": bool(min(a_wins, b_wins) >= 2),
            })
    pairs.sort(key=lambda p: -p["gain_vbs_over_sbs"])

    out = {"config": {"funcs": FUNCS, "dim": DIM, "budget": BUDGET, "runs": RUNS,
                      "pop": POP, "eligible_hook": eligible},
           "medians": med, "ranks": ranks, "mean_rank": mean_rank,
           "pairs": pairs, "provenance": provenance()}
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2)

    print("\n=== RANK medio (1=mejor) ===")
    for n, r in sorted(mean_rank.items(), key=lambda kv: kv[1]):
        print(f"  {n:5s} {r:.2f}")
    print("\n=== TOP pares por complementariedad (hook-eligible) ===")
    for p in pairs[:6]:
        print(f"  {p['pair']:10s} gain={p['gain_vbs_over_sbs']:.3f} "
              f"wins={p['wins']} balanced={p['balanced']} (SBS={p['sbs']})")
    print(f"\n-> {OUT_PATH}")


if __name__ == "__main__":
    main()
