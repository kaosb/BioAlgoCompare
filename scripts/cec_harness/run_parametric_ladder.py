"""
Parametric-transfer LADDER on a COMPLEMENTARY pair — Paso 3 (pre-registro v2).

Pool: GWO+GA, chosen by the complementarity screen (Paso 1): highest VBS-over-SBS
gain (0.19) with BALANCED wins (GWO 4 / GA 2) — unlike the dominated DE+PSO pair
that made the structural ladder unwinnable.

Conditions (all same total budget B, assert fes_used == B):
  C0_GWO / C0_GA : isolated, full B                       (references)
  C1_div         : both isolated at B/2, no comms, min    (portfolio floor)
  C2p            : parametric transfer (functional intent), gate OFF
  C3p            : parametric + gate ON (commit/rollback) (proposed)
  ABL            : parametric, gate ON, RANDOM intent     (cross-solver attribution)
  CTRLn / CTRLg  : ADVERSARIAL intents, gate OFF / ON     (positive control: does
                   the gate DETECT guaranteed-harmful transfer?)

Confirmatory contrasts (paired Wilcoxon + Holm, frozen family):
  1. C2p  vs C1_div   — does parametric transfer add over the no-comms portfolio?
  2. C3p  vs C2p      — does the gate help (or at least not hurt)?
  3. C3p  vs ABL      — is source knowledge better than random intent?
  4. CTRLg vs CTRLn   — does the gate protect against adversarial transfer? (H2 detection)

    RUNS=31 python scripts/cec_harness/run_parametric_ladder.py

Output: results/cooperative/parametric_ladder.json (+ provenance).
Fresh seeds 4000+ (screen used 3000+). F22 excluded (anomalous).
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
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from cooperative import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

FUNCS = [1, 4, 6, 9, 15, 23]
DIM = 10
BUDGET = int(os.environ.get("BUDGET", "5000"))
RUNS = int(os.environ.get("RUNS", "31"))
POP = 30
TRANSFER_EVERY = 500
SPECS = [("GWO", GWO, {"population_size": POP, "max_iterations": 10**9}),
         ("GA", GA, {"population_size": POP, "max_iterations": 10**9})]

OUT_DIR = os.path.join(_REPO_ROOT, "results", "cooperative")
OUT_PATH = os.path.join(OUT_DIR, "parametric_ladder.json")


def _isolated(cls, fnum, seed, budget):
    return float(run_with_fes(cls, CECProblem("CEC2014", fnum, DIM),
                              pop_size=POP, max_fes=budget, seed=seed))


def _coop(fnum, seed, gate, intent_mode):
    prob = FESLimitProblem(CECProblem("CEC2014", fnum, DIM), max_fes=BUDGET)
    runner = CooperativeRunner(prob, SPECS, transfer_every=TRANSFER_EVERY,
                               gate_enabled=gate, seed=seed,
                               transfer_mode="parametric",
                               intent_mode=intent_mode)
    res = runner.run()
    assert res["fes_used"] == BUDGET, (fnum, seed, gate, res["fes_used"])
    return res["best_fitness"], res["transfer_stats"]


def _paired(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a
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
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    raw, gate_stats = {}, {}
    print(f"[param-ladder] GWO+GA, {len(FUNCS)} funcs x {RUNS} runs, B={BUDGET}")
    for f in FUNCS:
        cols = {"C0_GWO": [], "C0_GA": [], "C1_div": [], "C2p": [], "C3p": [],
                "ABL": [], "CTRLn": [], "CTRLg": []}
        agg = {c: {"proposed": 0, "accepted": 0, "rejected": 0,
                   "rolled_back": 0, "kept": 0}
               for c in ["C2p", "C3p", "ABL", "CTRLn", "CTRLg"]}
        for r in range(RUNS):
            s = 4000 + r
            cols["C0_GWO"].append(_isolated(GWO, f, s, BUDGET))
            cols["C0_GA"].append(_isolated(GA, f, s, BUDGET))
            cols["C1_div"].append(min(_isolated(GWO, f, s, BUDGET // 2),
                                      _isolated(GA, f, s, BUDGET // 2)))
            for cname, gate, mode in [("C2p", False, "source"),
                                      ("C3p", True, "source"),
                                      ("ABL", True, "random"),
                                      ("CTRLn", False, "adversarial"),
                                      ("CTRLg", True, "adversarial")]:
                v, st = _coop(f, s, gate, mode)
                cols[cname].append(v)
                for k in agg[cname]:
                    agg[cname][k] += st.get(k, 0)
        raw[f"F{f}"] = cols
        gate_stats[f"F{f}"] = agg
        m = {c: float(np.median(v)) for c, v in cols.items()}
        print(f"  F{f:<3d} GWO={m['C0_GWO']:.2e} GA={m['C0_GA']:.2e} "
              f"C1div={m['C1_div']:.2e} C2p={m['C2p']:.2e} C3p={m['C3p']:.2e} "
              f"ABL={m['ABL']:.2e} CTRLn={m['CTRLn']:.2e} CTRLg={m['CTRLg']:.2e}")

    CONTRASTS = [
        ("C2p_vs_C1div",   "C2p",   "C1_div"),
        ("C3p_vs_C2p",     "C3p",   "C2p"),
        ("C3p_vs_ABL",     "C3p",   "ABL"),
        ("CTRLg_vs_CTRLn", "CTRLg", "CTRLn"),
        ("C3p_vs_C0SBS",   "C3p",   "C0_GWO"),   # SBS a-priori = GWO (screen)
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
        wins = losses = 0
        for (f, h) in zip(FUNCS, holm):
            e = per_f[f"F{f}"]
            e["p_holm"] = h
            e["A_better_sig"] = bool(h < 0.05 and e["rank_biserial"] > 0)
            e["A_worse_sig"] = bool(h < 0.05 and e["rank_biserial"] < 0)
            wins += e["A_better_sig"]; losses += e["A_worse_sig"]
        results[name] = {"per_function": per_f, "A_sig_wins": wins,
                         "A_sig_losses": losses, "n_funcs": len(FUNCS)}

    out = {"config": {"pair": "GWO+GA", "funcs": FUNCS, "dim": DIM,
                      "budget": BUDGET, "runs": RUNS, "pop": POP,
                      "transfer_every": TRANSFER_EVERY,
                      "note": "fresh seeds 4000+; F22 excluded; SBS=GWO (screen)"},
           "raw_medians": {f: {c: float(np.median(v)) for c, v in cols.items()}
                           for f, cols in raw.items()},
           "gate_stats": gate_stats,
           "contrasts": results, "provenance": provenance()}
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2)

    print("\n=== CONTRASTES (A mejor que B; Wilcoxon pareado + Holm) ===")
    for name, meta in results.items():
        print(f"  {name:16s}: A sig-mejor {meta['A_sig_wins']}/{meta['n_funcs']}, "
              f"A sig-peor {meta['A_sig_losses']}/{meta['n_funcs']}")
    print(f"\n-> {OUT_PATH}")


if __name__ == "__main__":
    main()
