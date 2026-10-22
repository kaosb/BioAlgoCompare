"""Fase 2 (enmienda v0.3 §C) — afinado del régimen BENIGN por (función, solver).

Corridas AISLADAS a B/2 con factores multiplicativos constantes (grilla dentro
de las regiones de convergencia), 11 semillas de tuning (seed0=12500, D20), elección
por mediana. Salida: results/cooperative/fase2_v05/benign_regimes.json
  {"<level>": {"F<n>": {"<solver>": {"factors": [...], "median": x}}}}
Uso: N_JOBS=10 python scripts/cec_harness/fase2_tuning_benigno.py
"""
import itertools
import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402

from problems.continuous.cec_problem import CECProblem, run_with_fes  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
FUNCS = [2, 3, 5, 8, 11, 14, 17, 18, 20, 24, 26, 29]
LEVELS = [int(x) for x in os.environ.get("LEVELS", "5000,50000").split(",")]
DIM, POP, TUNE_SEEDS, SEED0 = 10, 30, 11, 12500
N_JOBS = int(os.environ.get("N_JOBS", "10"))
GRIDS = {
    "DE":  [(f, cr) for f in (0.75, 1.00, 1.20) for cr in (0.67, 1.00)],
    "PSO": [(w, c1, c2) for w in (0.8, 1.0, 1.1) for (c1, c2) in ((1.0, 1.0), (0.8, 1.3), (1.3, 0.7))],
    "GWO": [(a,) for a in (0.5, 0.7, 1.0)],
    "GA":  [(cx, m) for cx in (0.9, 1.0, 1.1) for m in (0.4, 1.0, 1.5)],
    "ACO": [(xi, q) for xi in (0.7, 1.0, 1.15) for q in (0.5, 1.0, 1.8)],
}
OUT = os.path.join(_REPO, "results", "cooperative", "fase2_v05", "benign_regimes.json")


class _Const:
    """il_model constante: factores multiplicativos fijos (0 FES)."""
    def __init__(self, factors):
        self.f = tuple(float(x) for x in factors)
    def predict(self, algo, iteration):
        return self.f


def _cell(args):
    solver, level, f = args
    res = {}
    for factors in GRIDS[solver]:
        meds = []
        for s in range(TUNE_SEEDS):
            meds.append(float(run_with_fes(
                _CLS[solver], CECProblem("CEC2014", f, DIM), pop_size=POP,
                max_fes=level // 2, seed=SEED0 + s,
                algo_params={"use_il": True, "il_model": _Const(factors)})))
        res[str(factors)] = float(np.median(meds))
    best = min(res, key=res.get)
    return solver, level, f, {"factors": list(eval(best)), "median": res[best],
                              "grid_medians": res}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    jobs = [(s, lv, f) for lv in LEVELS for s in GRIDS for f in FUNCS]
    out = {str(lv): {f"F{f}": {} for f in FUNCS} for lv in LEVELS}
    print(f"[tuning-benigno] {len(jobs)} celdas (solver x nivel x funcion), N_JOBS={N_JOBS}", flush=True)
    with Pool(N_JOBS) as pool:
        for i, (s, lv, f, r) in enumerate(pool.imap_unordered(_cell, jobs), 1):
            out[str(lv)][f"F{f}"][s] = r
            if i % 10 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
    out["config"] = {"funcs": FUNCS, "levels": LEVELS, "tune_seeds": TUNE_SEEDS,
                     "seed0": SEED0, "pop": POP, "grids": {k: [list(x) for x in v] for k, v in GRIDS.items()},
                     "note": "regimen BENIGN = argmin mediana en 11 semillas de tuning; corrida aislada a B/2"}
    out["provenance"] = provenance()
    tmp = OUT + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh, indent=1)
    os.replace(tmp, OUT)
    print("->", OUT, flush=True)


if __name__ == "__main__":
    main()
