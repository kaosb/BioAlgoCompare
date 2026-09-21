"""Fase 1 (pre-registro fase positiva v0.2) — re-instrumentación de C0 con curvas.

Re-ejecuta las corridas AISLADAS (C0) de los 7 solvers del cribado sobre las 70
funciones del protocolo, con las MISMAS semillas de la campaña (seed0=5000, 51
corridas, pop=30), registrando el mejor error en cada múltiplo de Δ=500 FES.

  * No es una condición experimental nueva: para los 5 solvers de la campaña se
    verifica que el error final es BIT-IDÉNTICO al almacenado en las celdas
    (sanity del entorno); SSA y WOA solo existían sobre 6 funciones.
  * Alimenta las cotas de Fase 1: oráculo de conmutación por Δ (fila 2) y
    cribado de complementariedad 70 × 7 (fila 3). Declarado en deviations-log.

Salida: results/cooperative/fase1/c0_curves/<SOLVER>_<level>/<suite>_F<n>.json
        {"solver","level","suite","fnum","seed0","runs","delta",
         "finals":[51], "curves":[51][level/delta], "bitmatch_hist": bool|null}

Uso:  N_JOBS=10 LEVELS=5000,50000 python scripts/cec_harness/fase1_c0_curves.py
"""
import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402

from problems.continuous.cec_problem import CECProblem  # noqa: E402
from cooperative.curves import run_with_curve  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from algorithms.ssa import SSA  # noqa: E402
from algorithms.woa import WOA  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO,
        "SSA": SSA, "WOA": WOA}
SOLVERS = os.environ.get("SOLVERS", "GWO,GA,DE,PSO,ACO,SSA,WOA").split(",")
LEVELS = [int(x) for x in os.environ.get("LEVELS", "5000,50000").split(",")]
N_JOBS = int(os.environ.get("N_JOBS", "10"))
DIM, POP, RUNS, SEED0, DELTA = 10, 30, 51, 5000, 500
PROBLEMS = ([("CEC2014", f) for f in range(1, 31) if f != 22]
            + [("CEC2017", f) for f in range(1, 30)]
            + [("CEC2022", f) for f in range(1, 13)])
OUT_DIR = os.path.join(_REPO, "results", "cooperative", "fase1", "c0_curves")
SCALE = os.path.join(_REPO, "results", "cooperative", "scale")
# celda histórica donde vive el C0 de cada solver (para el bitmatch)
_HIST = {"GWO": "GWOGA", "GA": "GWOGA", "DE": "DEGA", "PSO": "PSOACO",
         "ACO": "PSOACO"}


def _path(solver, level, suite, fnum):
    d = os.path.join(OUT_DIR, f"{solver}_{level}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{suite}_F{fnum}.json")


def _cell(args):
    solver, level, suite, fnum = args
    path = _path(solver, level, suite, fnum)
    if os.path.exists(path):
        return path, "skip"
    finals, curves = [], []
    for r in range(RUNS):
        best, curve = run_with_curve(
            _CLS[solver], CECProblem(suite, fnum, DIM), pop_size=POP,
            max_fes=level, seed=SEED0 + r, delta=DELTA)
        finals.append(float(best))
        curves.append([float(v) for v in curve])
    match = None
    if solver in _HIST:
        hp = os.path.join(SCALE, f"{_HIST[solver]}_{level}", f"{suite}_F{fnum}.json")
        if os.path.exists(hp):
            hist = json.load(open(hp))["errors"][f"C0_{solver}"]
            match = bool(np.array_equal(np.asarray(hist, float),
                                        np.asarray(finals, float)))
    out = {"solver": solver, "level": level, "suite": suite, "fnum": fnum,
           "dim": DIM, "pop": POP, "runs": RUNS, "seed0": SEED0, "delta": DELTA,
           "finals": finals, "curves": curves, "bitmatch_hist": match}
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, path)
    return path, ("done" if match in (True, None) else "MISMATCH")


def main():
    cells = [(s, lv, suite, f) for s in SOLVERS for lv in LEVELS
             for suite, f in PROBLEMS]
    todo = [c for c in cells if not os.path.exists(_path(*c))]
    print(f"[fase1-c0] {len(cells)} celdas, {len(todo)} pendientes, "
          f"N_JOBS={N_JOBS}", flush=True)
    done = mism = 0
    with Pool(N_JOBS) as pool:
        for path, st in pool.imap_unordered(_cell, todo):
            done += 1
            if st == "MISMATCH":
                mism += 1
                print(f"  !! MISMATCH {path}", flush=True)
            if done % 20 == 0:
                print(f"  {done}/{len(todo)} (mismatches={mism})", flush=True)
    print(f"[fase1-c0] listo: {done} celdas, mismatches={mism}", flush=True)


if __name__ == "__main__":
    main()
