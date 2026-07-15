"""
Cooperative-transfer LADDER — C1 attribution (Fase 3, pre-registro v2).

Answers the open question left by the fixed pilot: the cooperation beats the
honest mean baseline 4/6, but IS THAT TRANSFER OR MERE PORTFOLIO? The ladder
isolates each factor with paired (CRN) contrasts (pre-registro §1, §3):

  C0_DE / C0_PSO : each solver isolated, FULL budget B          (reference)
  C1_div         : DE & PSO independent, B/2 each, NO comms, min per run
                   -> portfolio effect with a SPLIT budget
  C1_island      : DE & PSO concurrent, B/2 each, naive elite migration
                   (gate OFF = unconditional transfer)
  C3             : same, gate ON (utility + stagnation + memory)

Contrasts (Wilcoxon signed-rank paired, per function, on RAW errors + Holm):
  C1_div  vs C0_best   : does splitting+diversifying beat one full-budget solver?
                         (if the 4/6 lives HERE it is PORTFOLIO, not transfer)
  C1_island vs C1_div  : does migrating add value over no-comms portfolio?
  C3      vs C1_island : does the directed/gated mechanism add over naive?

    python scripts/cec_harness/run_cooperative_ladder.py
    RUNS=31 python .../run_cooperative_ladder.py

Output: results/cooperative/ladder_C1.json (with provenance) + printed tables.
F22 EXCLUDED (DE error==0 in 10/10, anomalous — see pre-registro §2.7).
"""

import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from cooperative import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

# taxonomy-picked (NOT complementarity-picked): uni(1), multimodal(4,9),
# hybrid(15), composition(23); F22 excluded (anomalous), F23 replaces it.
FUNCS = [1, 4, 6, 9, 15, 23]
DIM = 10
BUDGET = int(os.environ.get("BUDGET", "5000"))
RUNS = int(os.environ.get("RUNS", "31"))
POP = 30
TRANSFER_EVERY = 500
SPECS = [("DE", DE, {"population_size": POP, "max_iterations": 10**9}),
         ("PSO", PSO, {"population_size": POP, "max_iterations": 10**9})]

OUT_DIR = os.path.join(_REPO_ROOT, "results", "cooperative")
OUT_PATH = os.path.join(OUT_DIR, "ladder_C1.json")


def _isolated(cls, fnum, seed, budget):
    return float(run_with_fes(cls, CECProblem("CEC2014", fnum, DIM),
                              pop_size=POP, max_fes=budget, seed=seed))


def _c1_div(fnum, seed):
    """Portfolio, split budget, NO communication: min(DE_B/2, PSO_B/2)."""
    de = _isolated(DE, fnum, seed, BUDGET // 2)
    pso = _isolated(PSO, fnum, seed, BUDGET // 2)
    return min(de, pso)


def _coop(fnum, seed, gate):
    prob = FESLimitProblem(CECProblem("CEC2014", fnum, DIM), max_fes=BUDGET)
    runner = CooperativeRunner(prob, SPECS, transfer_every=TRANSFER_EVERY,
                               gate_enabled=gate, seed=seed)
    res = runner.run()
    # FES-fairness assert (pre-registro §2.1): total budget respected exactly.
    assert res["fes_used"] == BUDGET, (fnum, seed, gate, res["fes_used"])
    return res["best_fitness"]


def _paired(a, b):
    """Paired test 'is a < b' (a better). Returns p, rank_biserial, median_diff.

    Positive rank-biserial / negative median_diff => a tends to be better.
    """
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a                      # >0 where a is better (smaller error)
    nz = d[d != 0]
    med = float(np.median(d))
    if nz.size == 0:
        return 1.0, 0.0, med
    try:
        _, p = wilcoxon(a, b, zero_method="wilcox")
    except ValueError:
        p = 1.0
    r = rankdata(np.abs(nz))
    rb = float((r[nz > 0].sum() - r[nz < 0].sum()) / r.sum())
    return float(p), rb, med


def _holm(pvals):
    """Holm-Bonferroni adjusted p-values (same order as input)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    raw = {}   # per function: condition -> list of errors (paired by seed index)
    print(f"[ladder] {len(FUNCS)} funcs x {RUNS} runs, B={BUDGET}, DE+PSO "
          f"(F22 excluded)")
    for f in FUNCS:
        cols = {"C0_DE": [], "C0_PSO": [], "C1_div": [], "C1_island": [], "C3": []}
        for r in range(RUNS):
            s = 3000 + r                      # fresh seeds (confirmatory != diag)
            cols["C0_DE"].append(_isolated(DE, f, s, BUDGET))
            cols["C0_PSO"].append(_isolated(PSO, f, s, BUDGET))
            cols["C1_div"].append(_c1_div(f, s))
            cols["C1_island"].append(_coop(f, s, gate=False))
            cols["C3"].append(_coop(f, s, gate=True))
        raw[f"F{f}"] = cols

    # --- attribution contrasts (paired, per function) ------------------------
    CONTRASTS = [
        ("C1_div_vs_C0DE",       "C1_div",    "C0_DE"),     # portfolio vs full-B DE
        ("C1_div_vs_C0PSO",      "C1_div",    "C0_PSO"),    # portfolio vs full-B PSO
        ("C1island_vs_C1div",    "C1_island", "C1_div"),    # value of migrating
        ("C3_vs_C1island",       "C3",        "C1_island"), # value of gate/directed
    ]
    results = {}
    for name, A, B in CONTRASTS:
        per_f, praw = {}, []
        for f in FUNCS:
            p, rb, med = _paired(raw[f"F{f}"][A], raw[f"F{f}"][B])
            per_f[f"F{f}"] = {"p": p, "rank_biserial": rb, "median_diff": med,
                              "A_median": float(np.median(raw[f"F{f}"][A])),
                              "B_median": float(np.median(raw[f"F{f}"][B]))}
            praw.append(p)
        holm = _holm(praw)
        wins = 0
        for (f, h) in zip(FUNCS, holm):
            per_f[f"F{f}"]["p_holm"] = h
            if h < 0.05 and per_f[f"F{f}"]["rank_biserial"] > 0:
                per_f[f"F{f}"]["A_better_sig"] = True
                wins += 1
            else:
                per_f[f"F{f}"]["A_better_sig"] = False
        results[name] = {"per_function": per_f, "A_sig_wins": wins,
                         "n_funcs": len(FUNCS)}

    out = {"config": {"funcs": FUNCS, "dim": DIM, "budget": BUDGET, "runs": RUNS,
                      "pop": POP, "transfer_every": TRANSFER_EVERY,
                      "solvers": [s[0] for s in SPECS],
                      "note": "F22 excluded (anomalous); fresh seeds 3000+"},
           "raw_medians": {f: {c: float(np.median(v)) for c, v in cols.items()}
                           for f, cols in raw.items()},
           "contrasts": results, "provenance": provenance()}
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2)

    # --- report --------------------------------------------------------------
    print("\n=== MEDIANAS por condicion ===")
    print(f"{'Func':6s} {'C0_DE':>10s} {'C0_PSO':>10s} {'C1_div':>10s} "
          f"{'C1_island':>10s} {'C3':>10s}")
    for f in FUNCS:
        m = out["raw_medians"][f"F{f}"]
        print(f"F{f:<5d} {m['C0_DE']:10.3e} {m['C0_PSO']:10.3e} "
              f"{m['C1_div']:10.3e} {m['C1_island']:10.3e} {m['C3']:10.3e}")
    print("\n=== CONTRASTES (A mejor que B, Wilcoxon pareado + Holm) ===")
    for name, meta in results.items():
        print(f"  {name:22s}: A significativamente mejor en "
              f"{meta['A_sig_wins']}/{meta['n_funcs']} funcs")
    print(f"\n-> {OUT_PATH}")
    print("\nLECTURA: si C1_div ya gana a C0 => el 4/6 es PORTFOLIO (dividir+diversificar),")
    print("no transferencia. Si C1_island>C1_div => migrar aporta. Si C3>C1_island => gate/dirigido aporta.")


if __name__ == "__main__":
    main()
