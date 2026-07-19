"""
E1 — positive control of the ACTION SPACE (18 Jul audit, the key discriminant).

The audit showed "source intent = random" (0/70) is confounded: both drew from
the SAME hand-made 2-preset vocabulary, and C2p (upper bound of exploiting that
vocabulary) did not beat the portfolio either -> the vocabulary may simply lack
a winning action. This experiment asks: does a RICH regime space contain ANY
winning action at all, when chosen with HINDSIGHT (per-function best static
regime, tuned on held-out seeds)?

  * If hindsight-best rich regimes BEAT the neutral portfolio -> the space is
    rich and our 2 presets were the limitation -> the negative claim must be
    scoped to the vocabulary ("estos presets no portan señal").
  * If even hindsight-best regimes DON'T beat neutral -> no static regime
    modulation helps at this budget -> the negative deepens: the author-default
    parameters are already at the level optimum (echoes the IL finding
    "nivel, no schedule"), and no intent vocabulary OF THIS FORM could win.

Pair GWO+GA @5e3 (isolated at B/2 each, mirroring C1_div structure). Grid:
GWO a_factor x7; GA (cx_f, mut_f) 3x4. Tuning seeds 9000+ (11), eval seeds
9500+ (31, fresh). Paired Wilcoxon + Holm per function.

    python scripts/cec_harness/run_e1_action_space.py
Output: results/cooperative/e1_action_space.json
"""

import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata  # noqa: E402

from problems.continuous.cec_problem import CECProblem, run_with_fes  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from utils.provenance import provenance  # noqa: E402

FUNCS = [1, 4, 6, 9, 15, 23]
DIM = 10
BUDGET = 5000                      # total; each solver gets B/2 (C1_div mirror)
POP = 30
TUNE_SEEDS = list(range(9000, 9011))    # 11
EVAL_SEEDS = list(range(9500, 9531))    # 31 fresh

GRID_GWO = [(a,) for a in (0.3, 0.5, 0.7, 1.0, 1.3, 1.7, 2.2)]
GRID_GA = [(cx, mut) for cx in (0.6, 0.9, 1.1)
           for mut in (0.3, 1.0, 2.5, 5.0)]

OUT = os.path.join(_REPO_ROOT, "results", "cooperative", "e1_action_space.json")


class StaticFactors:
    """Constant multiplicative regime through the il_model hook."""
    def __init__(self, factors):
        self.factors = tuple(float(x) for x in factors)
        self.n_outputs = len(self.factors)

    def predict(self, algo, iteration):
        return self.factors


def _run(cls, f, seed, factors):
    params = {}
    if factors is not None:
        params = {"use_il": True, "il_model": StaticFactors(factors)}
    return float(run_with_fes(cls, CECProblem("CEC2014", f, DIM), pop_size=POP,
                              max_fes=BUDGET // 2, seed=seed,
                              algo_params=params))


def _paired(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a; nz = d[d != 0]
    if nz.size == 0:
        return 1.0, 0.0
    try:
        _, p = wilcoxon(a, b)
    except ValueError:
        p = 1.0
    r = rankdata(np.abs(nz))
    return float(p), float((r[nz > 0].sum() - r[nz < 0].sum()) / r.sum())


def main():
    print(f"[E1] GWO+GA @B/2={BUDGET//2}, grid {len(GRID_GWO)}x{len(GRID_GA)}, "
          f"{len(FUNCS)} funcs, tune n={len(TUNE_SEEDS)}, eval n={len(EVAL_SEEDS)}")
    best, rows, ps, rbs = {}, {}, [], []
    for f in FUNCS:
        # --- hindsight tuning (held-out seeds) ---
        gwo_meds = {g: float(np.median([_run(GWO, f, s, g) for s in TUNE_SEEDS]))
                    for g in GRID_GWO}
        ga_meds = {g: float(np.median([_run(GA, f, s, g) for s in TUNE_SEEDS]))
                   for g in GRID_GA}
        bg = min(gwo_meds, key=gwo_meds.get)
        ba = min(ga_meds, key=ga_meds.get)
        best[f"F{f}"] = {"GWO_a": bg, "GA_cxmut": ba,
                         "GWO_neutral_med_tune": gwo_meds[(1.0,)],
                         "GWO_best_med_tune": gwo_meds[bg],
                         "GA_neutral_med_tune": ga_meds[(0.9, 1.0)]
                         if (0.9, 1.0) in ga_meds else None,
                         "GA_best_med_tune": ga_meds[ba]}
        # --- fresh evaluation: hindsight portfolio vs neutral portfolio ---
        hind, neut = [], []
        for s in EVAL_SEEDS:
            hind.append(min(_run(GWO, f, s, bg), _run(GA, f, s, ba)))
            neut.append(min(_run(GWO, f, s, None), _run(GA, f, s, None)))
        p, rb = _paired(hind, neut)
        ps.append(p); rbs.append(rb)
        rows[f"F{f}"] = {"hind_median": float(np.median(hind)),
                         "neutral_median": float(np.median(neut)),
                         "p": p, "rank_biserial": rb}
        print(f"  F{f:<3d} best GWO a={bg[0]:.1f} GA cx/mut={ba} | "
              f"hind={rows[f'F{f}']['hind_median']:.3e} "
              f"neut={rows[f'F{f}']['neutral_median']:.3e} p={p:.3f} rb={rb:+.2f}")

    # Holm
    m = len(ps); o = sorted(range(m), key=lambda i: ps[i])
    adj, run = [0.0] * m, 0.0
    for k, i in enumerate(o):
        run = max(run, (m - k) * ps[i]); adj[i] = min(1.0, run)
    wins = sum(1 for h, rb in zip(adj, rbs) if h < 0.05 and rb > 0)
    losses = sum(1 for h, rb in zip(adj, rbs) if h < 0.05 and rb < 0)
    for (f, h) in zip(FUNCS, adj):
        rows[f"F{f}"]["p_holm"] = h

    out = {"config": {"pair": "GWO+GA", "budget_total": BUDGET, "funcs": FUNCS,
                      "grid_gwo": GRID_GWO, "grid_ga": GRID_GA,
                      "tune_seeds": [TUNE_SEEDS[0], TUNE_SEEDS[-1]],
                      "eval_seeds": [EVAL_SEEDS[0], EVAL_SEEDS[-1]]},
           "verdict": {"hindsight_beats_neutral": wins,
                       "hindsight_worse": losses, "n_funcs": len(FUNCS)},
           "per_function": rows, "best_regimes": best,
           "provenance": provenance()}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n[E1] hindsight-rico bate neutral: {wins}/{len(FUNCS)} "
          f"(peor {losses}/{len(FUNCS)}) -> {OUT}")
    print("LECTURA: wins>0 => el espacio rico SI tiene acciones ganadoras (el "
          "vocabulario de 2 presets era la limitacion). wins=0 => ni el mejor "
          "regimen estatico con clarividencia ayuda (params de autor ya en el "
          "optimo de nivel; eco de 'nivel no schedule').")


if __name__ == "__main__":
    main()
