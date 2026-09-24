"""Fase 3 (enmienda v0.5) — confirmatorio bajo protocolo CEC.

v0.5 (revisión interna del 23-Sep-2026): benchmark OFICIAL (minionpy = código C
de Suganthan, 142/142 verificado), numeración oficial (71 problemas: CEC2014
F1–F30, CEC2017 F1,F3–F30, CEC2022 F1–F12), semillas independientes por
solver (`solver_seed`), reparto del presupuesto cooperativo por evaluaciones,
migrante absorbido por GWO/PSO, mejor = mínimo evaluado, brazo de control
C1_shared (runner compartido SIN migración) para atribuir la ganancia.
Salida en results/cooperative/fase3_v05/ (lo de fase3/ es inválido: opfunu).

Mecanismo bajo prueba: C1_island (migración fija de una élite cada Δ=500 FES,
sin admisión ni rollback), con B (élite bajo admisión, v0.3) como variante.
Baselines por celda: C0 de cada solver a presupuesto completo (SBS/VBS),
C1_div (reparto igual), C1_shared (mismo runner que C1_island, sin migrar). Referencia externa: L-SHADE aislado (minionpy, parámetros
de Tanabe & Fukunaga 2014), una celda por (dimset, nivel, función), independiente
del par.

Matriz: 71 problemas oficiales; dimset 10 (todo a 10D) y 50 (2014/2017 a 50D,
2022 a 20D, su máximo); 51 corridas CRN (seed0 = 11000); cada nivel parte de
cero. A 5·10⁶ la matriz se restringe a las 12 funciones del piloto (v0.4).

Celdas resumibles (un JSON por celda, escritura atómica) con tiempo de pared.

Uso:
  DIMSET=10 LEVELS=5000,50000 N_JOBS=12 python scripts/cec_harness/run_fase3_confirmatorio.py run
  ONLY_PAIR=DE+GA  limita el plan a un par;  ONLY_FUNCS=CEC2014:2,CEC2017:5  limita funciones
"""
import json
import os
import platform
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from cooperative.orchestrator import CooperativeRunner, solver_seed  # noqa: E402
from cooperative.candidates import StructuralGatedRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
PAIRS = ["GWO+GA", "DE+GA", "PSO+ACO"]
PROBLEMS = ([("CEC2014", f) for f in range(1, 31)]
            + [("CEC2017", f) for f in range(1, 31) if f != 2]
            + [("CEC2022", f) for f in range(1, 13)])
PILOT_FUNCS = [("CEC2014", f) for f in [2, 3, 5, 8, 11, 14, 17, 18, 20, 24, 26, 29]]
DIMSETS = {"10": {"CEC2014": 10, "CEC2017": 10, "CEC2022": 10},
           "50": {"CEC2014": 50, "CEC2017": 50, "CEC2022": 20}}
DIMSET = os.environ.get("DIMSET", "10")
LEVELS = [int(x) for x in os.environ.get("LEVELS", "5000,50000").split(",")]
POP, RUNS, SEED0, DELTA = 30, int(os.environ.get("RUNS", "51")), 11000, 500
NO_MIGRATION = 10**12
N_JOBS = int(os.environ.get("N_JOBS", "12"))
OUT_DIR = os.path.join(os.environ.get("FASE3_OUT", os.path.join(_REPO, "results", "cooperative", "fase3_v05")),
                       f"dim{DIMSET}")
ARMS = ["C0_A", "C0_B", "C1_div", "C1_shared", "C1_island", "B"]

if os.environ.get("ONLY_PAIR"):
    PAIRS = [p for p in PAIRS if p == os.environ["ONLY_PAIR"]]
if os.environ.get("ONLY_FUNCS"):
    _sel = [(s, int(f)) for s, f in (x.split(":") for x in os.environ["ONLY_FUNCS"].split(","))]
    PROBLEMS = [p for p in PROBLEMS if p in _sel]
    PILOT_FUNCS = [p for p in PILOT_FUNCS if p in _sel]


def lshade_options(dim):
    """L-SHADE per Tanabe & Fukunaga (2014): N_init = 18·D, H = 6, r_arc = 2.6,
    N_min = 4, reducción lineal; sin parada por tolerancia (solo MaxFES)."""
    return {"population_size": 18 * dim, "memory_size": 6, "archive_size_ratio": 2.6,
            "minimum_population_size": 4, "reduction_strategy": "linear",
            "x_tol": 0.0, "f_tol": -1.0, "bound_strategy": "random"}


def _specs(a, b):
    return [(a, _CLS[a], {"population_size": POP, "max_iterations": 10**9}),
            (b, _CLS[b], {"population_size": POP, "max_iterations": 10**9})]


def _funcs_for(level):
    return PILOT_FUNCS if level >= 5_000_000 else PROBLEMS


def _dim(suite):
    return DIMSETS[DIMSET][suite]


def _run_arm(arm, a, b, suite, f, level, seed):
    dim = _dim(suite)
    sa, sb = solver_seed(seed, 0), solver_seed(seed, 1)   # same mapping as the cooperative runner (CRN)
    if arm == "C0_A":
        return float(run_with_fes(_CLS[a], CECProblem(suite, f, dim), pop_size=POP, max_fes=level, seed=sa)), {}
    if arm == "C0_B":
        return float(run_with_fes(_CLS[b], CECProblem(suite, f, dim), pop_size=POP, max_fes=level, seed=sb)), {}
    if arm == "C1_div":
        return float(min(run_with_fes(_CLS[a], CECProblem(suite, f, dim), pop_size=POP, max_fes=level // 2, seed=sa),
                         run_with_fes(_CLS[b], CECProblem(suite, f, dim), pop_size=POP, max_fes=level - level // 2, seed=sb))), {}
    prob = FESLimitProblem(CECProblem(suite, f, dim), max_fes=level)
    if arm == "C1_shared":
        r = CooperativeRunner(prob, _specs(a, b), transfer_every=NO_MIGRATION, gate_enabled=False,
                              seed=seed, transfer_mode="structural")
    elif arm == "C1_island":
        r = CooperativeRunner(prob, _specs(a, b), transfer_every=DELTA, gate_enabled=False,
                              seed=seed, transfer_mode="structural")
    elif arm == "B":
        r = StructuralGatedRunner(prob, _specs(a, b), delta=DELTA, seed=seed)
    else:
        raise ValueError(arm)
    res = r.run()
    if res["fes_used"] != level:
        raise AssertionError((arm, a, b, suite, f, level, seed, res["fes_used"]))
    st = dict(res.get("transfer_stats", {}))
    st.update({f"fes_{k}": v for k, v in res.get("fes_per_solver", {}).items()})
    return float(res["best_fitness"]), st


def _cell_path(pair, level, suite, f):
    d = os.path.join(OUT_DIR, f"{pair.replace('+', '')}_{level}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{suite}_F{f}.json")


def _lshade_path(level, suite, f):
    d = os.path.join(OUT_DIR, f"LSHADE_{level}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{suite}_F{f}.json")


def _write(path, out):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, path)


def _cell(args):
    pair, level, suite, f = args
    path = _cell_path(pair, level, suite, f)
    if os.path.exists(path):
        return path, "skip", 0.0
    a, b = pair.split("+")
    t0 = time.time()
    errors = {arm: [] for arm in ARMS}
    stats = {arm: {} for arm in ARMS}
    for r in range(RUNS):
        for arm in ARMS:
            e, st = _run_arm(arm, a, b, suite, f, level, SEED0 + r)
            errors[arm].append(e)
            for k, v in st.items():
                if isinstance(v, (int, float)):
                    stats[arm][k] = stats[arm].get(k, 0) + v
    wall = time.time() - t0
    _write(path, {"pair": pair, "solvers": [a, b], "level": level, "suite": suite, "fnum": f,
                  "dim": _dim(suite), "dimset": DIMSET, "runs": RUNS, "seed0": SEED0,
                  "delta": DELTA, "pop": POP, "errors": errors, "mech_stats": stats,
                  "wall_s": wall})
    return path, "done", wall


def _lshade_cell(args):
    level, suite, f = args
    path = _lshade_path(level, suite, f)
    if os.path.exists(path):
        return path, "skip", 0.0
    from algorithms.minion_adapter import LSHADE_M
    dim = _dim(suite)
    t0 = time.time()
    errs, used = [], []
    for r in range(RUNS):
        algo = LSHADE_M(FESLimitProblem(CECProblem(suite, f, dim), max_fes=level),
                        population_size=18 * dim, max_iterations=10**9, seed=SEED0 + r,
                        minion_options=lshade_options(dim))
        algo.execute()
        if algo.fes_used > level:
            raise AssertionError(("LSHADE", suite, f, level, SEED0 + r, algo.fes_used))
        errs.append(float(algo.get_best_solution().fitness()))
        used.append(int(algo.fes_used))
    wall = time.time() - t0
    _write(path, {"algo": "L-SHADE", "backend": "minionpy", "options": lshade_options(dim),
                  "level": level, "suite": suite, "fnum": f, "dim": dim, "dimset": DIMSET,
                  "runs": RUNS, "seed0": SEED0, "errors": {"LSHADE": errs}, "fes_used": used,
                  "wall_s": wall})
    return path, "done", wall


def stage_run():
    cells = [(p, lv, s, f) for lv in LEVELS for p in PAIRS for (s, f) in _funcs_for(lv)]
    lcells = [(lv, s, f) for lv in LEVELS for (s, f) in _funcs_for(lv)]
    todo = [c for c in cells if not os.path.exists(_cell_path(*c))]
    ltodo = [c for c in lcells if not os.path.exists(_lshade_path(*c))]
    print(f"[fase3 dim{DIMSET}] niveles={LEVELS} celdas par={len(cells)} ({len(todo)} pendientes) "
          f"celdas L-SHADE={len(lcells)} ({len(ltodo)} pendientes) N_JOBS={N_JOBS}", flush=True)
    t0 = time.time()
    with Pool(N_JOBS) as pool:
        for i, (path, st, w) in enumerate(pool.imap_unordered(_lshade_cell, ltodo), 1):
            print(f"  LSHADE {i}/{len(ltodo)} {os.path.relpath(path, OUT_DIR)} {st} {w:.0f}s", flush=True)
        for i, (path, st, w) in enumerate(pool.imap_unordered(_cell, todo), 1):
            print(f"  {i}/{len(todo)} {os.path.relpath(path, OUT_DIR)} {st} {w:.0f}s "
                  f"[{(time.time() - t0) / 3600:.2f} h]", flush=True)
    meta = {"dimset": DIMSET, "levels": LEVELS, "pairs": PAIRS, "n_problems": len(PROBLEMS),
            "runs": RUNS, "seed0": SEED0, "delta": DELTA, "n_jobs": N_JOBS,
            "wall_s_this_invocation": time.time() - t0,
            "machine": {"cpu": platform.processor(), "ncpu": os.cpu_count(),
                        "platform": platform.platform()},
            "provenance": provenance()}
    _write(os.path.join(OUT_DIR, f"run_meta_{'_'.join(map(str, LEVELS))}_{int(time.time())}.json"), meta)
    print(f"[fase3 dim{DIMSET}] hecho en {(time.time() - t0) / 3600:.2f} h", flush=True)


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "run"
    if stage == "run":
        stage_run()
    else:
        raise SystemExit(f"stage desconocido: {stage}")
