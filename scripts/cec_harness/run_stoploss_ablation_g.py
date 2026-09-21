"""Ablación del stop-loss.

El brazo CTRLn de la campaña (sin gate, intención adversarial) TAMBIÉN ejecuta
rollback, por lo que CTRLg vs CTRLn valida las reglas de admisión, no el
stop-loss. Este experimento aísla el stop-loss:

  CTRLn      = sin gate, adversarial, CON rollback  (re-corrido; debe ser
               bit-idéntico al de las celdas históricas — sanity de entorno)
  CTRLn_noRB = sin gate, adversarial, SIN rollback  (stop_loss=False)

Contraste CTRLn vs CTRLn_noRB (Wilcoxon pareado + Holm, CRN): si CTRLn gana,
el stop-loss corta daño adversarial por sí mismo.

3 pares × 6 funciones taxonómicas × 51 corridas × B=5e3. Δ=500 (igual campaña).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from cooperative.orchestrator import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
PAIRS = [("GWO", "GA"), ("DE", "GA"), ("PSO", "ACO")]
FUNCS = [1, 4, 6, 9, 15, 23]          # taxonomy set (= cribado / E1 / E2 / E3)
DIM, POP, RUNS, LEVEL, TE, SEED0 = 10, 30, 51, 5000, 500, 5000
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results",
                   "cooperative", "stoploss_ablation_conadmision.json")
CELLS = os.path.join(os.path.dirname(__file__), "..", "..", "results",
                     "cooperative", "scale")


def _holm(pv):
    m = len(pv)
    order = sorted(range(m), key=lambda i: pv[i])
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pv[i])
        adj[i] = min(1.0, run)
    return adj


def _rb(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    r = np.argsort(np.argsort(np.abs(d))) + 1.0
    return float((r[d < 0].sum() - r[d > 0].sum()) / r.sum())


def _arm(a, b, suite, fnum, seed, stop_loss):
    specs = [(a, _CLS[a], {"population_size": POP, "max_iterations": 10**9}),
             (b, _CLS[b], {"population_size": POP, "max_iterations": 10**9})]
    prob = FESLimitProblem(CECProblem(suite, fnum, DIM), max_fes=LEVEL)
    runner = CooperativeRunner(prob, specs, transfer_every=TE,
                               gate_enabled=True, seed=seed,
                               transfer_mode="parametric",
                               intent_mode="adversarial", stop_loss=stop_loss)
    res = runner.run()
    assert res["fes_used"] == LEVEL, res["fes_used"]
    return float(res["best_fitness"])


def main():
    out = {"config": {"pairs": [f"{a}+{b}" for a, b in PAIRS], "funcs": FUNCS,
                      "dim": DIM, "pop": POP, "runs": RUNS, "level": LEVEL,
                      "transfer_every": TE, "seed0": SEED0,
                      "arms": ["CTRLg (rollback)", "CTRLg_noRB (sin rollback)"]},
           "sanity_bitmatch": {}, "per_pair": {}}
    for a, b in PAIRS:
        pair = f"{a}+{b}"
        print(f"[{pair}] 6 funcs x {RUNS} runs x 2 brazos ...", flush=True)
        rows = {}
        pvals, rbs = [], []
        for f in FUNCS:
            ctrl = [_arm(a, b, "CEC2014", f, SEED0 + r, True) for r in range(RUNS)]
            norb = [_arm(a, b, "CEC2014", f, SEED0 + r, False) for r in range(RUNS)]
            # sanity: CTRLn re-corrido vs celda historica
            cell_p = os.path.join(CELLS, f"{a}{b}_{LEVEL}", f"CEC2014_F{f}.json")
            match = None
            if os.path.exists(cell_p):
                hist = json.load(open(cell_p))["errors"]["CTRLg"]
                match = bool(np.allclose(hist, ctrl, rtol=0, atol=0))
            d = np.asarray(ctrl) - np.asarray(norb)
            if np.all(d == 0):
                p = 1.0
            else:
                _, p = wilcoxon(ctrl, norb, zero_method="wilcox")
            pvals.append(float(p))
            rbs.append(_rb(ctrl, norb))
            rows[f"F{f}"] = {"median_CTRLn": float(np.median(ctrl)),
                             "median_noRB": float(np.median(norb)),
                             "p": float(p), "rank_biserial": rbs[-1],
                             "bitmatch_hist": match}
        adj = _holm(pvals)
        wins = sum(1 for h, r in zip(adj, rbs) if h < 0.05 and r > 0)
        loss = sum(1 for h, r in zip(adj, rbs) if h < 0.05 and r < 0)
        for (fk, row), h in zip(rows.items(), adj):
            row["p_holm"] = float(h)
        out["per_pair"][pair] = {"funcs": rows,
                                 "stoploss_wins": wins, "stoploss_losses": loss,
                                 "n_funcs": len(FUNCS)}
        out["sanity_bitmatch"][pair] = all(
            r["bitmatch_hist"] in (True, None) for r in rows.values())
        print(f"  {pair}: stop-loss mejor en {wins}/{len(FUNCS)}, "
              f"peor en {loss}/{len(FUNCS)} | bitmatch={out['sanity_bitmatch'][pair]}",
              flush=True)
    out["provenance"] = provenance()
    tmp = OUT + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh, indent=1)
    os.replace(tmp, OUT)
    print("->", OUT)


if __name__ == "__main__":
    main()
