"""Camino alterno (pre-registro v0.1 §2; enmienda v0.6) — el gate como componente
de seguridad, re-ejecutado sobre el benchmark OFICIAL (v0.5).

Escalera por celda (par × nivel × función), 51 corridas CRN:
  baselines    C0_A, C0_B, C1_div
  canal real   C2p (intención de la fuente, sin gate), C3p (con gate), ABL (azar, con gate)
  control +    CTRLn (adversarial, sin gate), CTRLn_noSL (sin gate ni stop-loss),
               CTRLg (con gate), CTRLg_noSL (gate sin stop-loss), CTRLg_nomem (gate sin memoria)
  daño sutil   MODn / MODg
  benigno      BENn / BENg (régimen afinado por función en semillas separadas)
Parámetros: Δ = 500 FES, PRESETS_V2, población 30, memoria por mediana.

Uso:  N_JOBS=12 python scripts/cec_harness/run_camino_alterno.py tune   # régimen benigno
      N_JOBS=12 LEVELS=5000,50000 python scripts/cec_harness/run_camino_alterno.py run
Env: ONLY_PAIR, ONLY_FUNCS=CEC2014:1,..., CA_OUT (directorio de salida),
     DIMSET=10|50 (50: CEC2014/2017 a 50D, CEC2022 a 20D; salida *_dim50).
"""
import json
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from cooperative.orchestrator import CooperativeRunner, solver_seed  # noqa: E402
from cooperative.candidates import BenignControlRunner  # noqa: E402
from cooperative.functional_intent import PRESETS_V2  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
PAIRS = ["GWO+GA", "DE+GA", "PSO+ACO"]
PROBLEMS = ([("CEC2014", f) for f in range(1, 31)]
            + [("CEC2017", f) for f in range(1, 31) if f != 2]
            + [("CEC2022", f) for f in range(1, 13)])
POP, DELTA = 30, 500
DIMSET = os.environ.get("DIMSET", "10")
DIMSETS = {"10": {"CEC2014": 10, "CEC2017": 10, "CEC2022": 10},
           "50": {"CEC2014": 50, "CEC2017": 50, "CEC2022": 20}}


def _dim(suite):
    return DIMSETS[DIMSET][suite]

RUNS = int(os.environ.get("RUNS", "51"))
SEED0, TUNE_SEED0, TUNE_SEEDS = 13000, 13500, 11
LEVELS = [int(x) for x in os.environ.get("LEVELS", "5000,50000").split(",")]
N_JOBS = int(os.environ.get("N_JOBS", "12"))
OUT = os.environ.get("CA_OUT", os.path.join(_REPO, "results", "cooperative", "camino_alterno_v06" + ("" if DIMSET == "10" else f"_dim{DIMSET}")))
BENIGN = os.path.join(OUT, "benign_regimes.json")

# arm -> (gate, intent_mode, stop_loss, memory)
PARAM_ARMS = {
    "C2p": (False, "source", True, True),
    "C3p": (True, "source", True, True),
    "ABL": (True, "random", True, True),
    "CTRLn": (False, "adversarial", True, True),
    "CTRLn_noSL": (False, "adversarial", False, True),
    "CTRLg": (True, "adversarial", True, True),
    "CTRLg_noSL": (True, "adversarial", False, True),
    "CTRLg_nomem": (True, "adversarial", True, False),
    "MODn": (False, "moderate", True, True),
    "MODg": (True, "moderate", True, True),
}
ARMS = ["C0_A", "C0_B", "C1_div"] + list(PARAM_ARMS) + ["BENn", "BENg"]
if os.environ.get("ONLY_PAIR"):
    PAIRS = [p for p in PAIRS if p == os.environ["ONLY_PAIR"]]
if os.environ.get("ONLY_FUNCS"):
    _sel = [(s, int(f)) for s, f in (x.split(":") for x in os.environ["ONLY_FUNCS"].split(","))]
    PROBLEMS = [p for p in PROBLEMS if p in _sel]
GRIDS = {
    "DE":  [(f, cr) for f in (0.75, 1.00, 1.20) for cr in (0.67, 1.00)],
    "PSO": [(w, c1, c2) for w in (0.8, 1.0, 1.1) for (c1, c2) in ((1.0, 1.0), (0.8, 1.3), (1.3, 0.7))],
    "GWO": [(a,) for a in (0.5, 0.7, 1.0)],
    "GA":  [(cx, m) for cx in (0.9, 1.0, 1.1) for m in (0.4, 1.0, 1.5)],
    "ACO": [(xi, q) for xi in (0.7, 1.0, 1.15) for q in (0.5, 1.0, 1.8)],
}


class _Const:
    def __init__(self, factors):
        self.f = tuple(float(x) for x in factors)

    def predict(self, algo, iteration):
        return self.f


def _key(suite, f):
    return f"{suite}_F{f}"


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


# ----------------------------------------------------------------- tuning --
def _tune_cell(args):
    solver, level, suite, f = args
    res = {}
    for factors in GRIDS[solver]:
        meds = [float(run_with_fes(_CLS[solver], CECProblem(suite, f, _dim(suite)), pop_size=POP,
                                   max_fes=level // 2, seed=TUNE_SEED0 + s,
                                   algo_params={"use_il": True, "il_model": _Const(factors)}))
                for s in range(TUNE_SEEDS)]
        res[str(factors)] = float(np.median(meds))
    best = min(res, key=res.get)
    return solver, level, _key(suite, f), {"factors": list(eval(best)), "median": res[best]}


def stage_tune():
    solvers = sorted({s for p in PAIRS for s in p.split("+")})
    jobs = [(s, lv, su, f) for lv in LEVELS for s in solvers for (su, f) in PROBLEMS]
    out = json.load(open(BENIGN)) if os.path.exists(BENIGN) else {}
    todo = [j for j in jobs if j[0] not in out.get(str(j[1]), {}).get(_key(j[2], j[3]), {})]
    print(f"[tune] {len(todo)}/{len(jobs)} celdas pendientes", flush=True)
    with Pool(N_JOBS) as pool:
        for i, (s, lv, k, r) in enumerate(pool.imap_unordered(_tune_cell, todo), 1):
            out.setdefault(str(lv), {}).setdefault(k, {})[s] = r
            if i % 50 == 0:
                _write(BENIGN, out); print(f"  {i}/{len(todo)}", flush=True)
    out["config"] = {"tune_seed0": TUNE_SEED0, "tune_seeds": TUNE_SEEDS, "grids": {k: [list(x) for x in v] for k, v in GRIDS.items()},
                     "note": "BENIGN = argmin mediana (11 semillas separadas, corrida aislada a B/2)"}
    out["provenance"] = provenance()
    _write(BENIGN, out)


# ------------------------------------------------------------------- runs --
def _specs(a, b):
    return [(a, _CLS[a], {"population_size": POP}), (b, _CLS[b], {"population_size": POP})]


def _run_arm(arm, a, b, suite, f, level, seed, benign):
    sa, sb = solver_seed(seed, 0), solver_seed(seed, 1)
    if arm == "C0_A":
        return float(run_with_fes(_CLS[a], CECProblem(suite, f, _dim(suite)), pop_size=POP, max_fes=level, seed=sa)), {}
    if arm == "C0_B":
        return float(run_with_fes(_CLS[b], CECProblem(suite, f, _dim(suite)), pop_size=POP, max_fes=level, seed=sb)), {}
    if arm == "C1_div":
        return float(min(run_with_fes(_CLS[a], CECProblem(suite, f, _dim(suite)), pop_size=POP, max_fes=level // 2, seed=sa),
                         run_with_fes(_CLS[b], CECProblem(suite, f, _dim(suite)), pop_size=POP, max_fes=level - level // 2, seed=sb))), {}
    prob = FESLimitProblem(CECProblem(suite, f, _dim(suite)), max_fes=level)
    if arm in ("BENn", "BENg"):
        r = BenignControlRunner(prob, _specs(a, b), benign, delta=DELTA, seed=seed,
                                gate_enabled=(arm == "BENg"), presets=PRESETS_V2)
    else:
        gate, mode, sl, mem = PARAM_ARMS[arm]
        r = CooperativeRunner(prob, _specs(a, b), transfer_every=DELTA, gate_enabled=gate, seed=seed,
                              transfer_mode="parametric", intent_mode=mode, stop_loss=sl,
                              presets=PRESETS_V2, memory_enabled=mem)
    res = r.run()
    if res["fes_used"] != level:
        raise AssertionError((arm, a, b, suite, f, level, seed, res["fes_used"]))
    st = {k: v for k, v in res.get("transfer_stats", {}).items() if isinstance(v, (int, float))}
    st.update({f"fes_{k}": v for k, v in res.get("fes_per_solver", {}).items()})
    return float(res["best_fitness"]), st


def _cell_path(pair, level, suite, f):
    return os.path.join(OUT, f"{pair.replace('+', '')}_{level}", f"{_key(suite, f)}.json")


def _cell(args):
    pair, level, suite, f = args
    path = _cell_path(pair, level, suite, f)
    if os.path.exists(path):
        return path, "skip", 0.0
    a, b = pair.split("+")
    ben = json.load(open(BENIGN))[str(level)][_key(suite, f)]
    benign = {a: ben[a]["factors"], b: ben[b]["factors"]}
    t0 = time.time()
    errors = {arm: [] for arm in ARMS}
    stats = {arm: {} for arm in ARMS}
    for r in range(RUNS):
        for arm in ARMS:
            e, st = _run_arm(arm, a, b, suite, f, level, SEED0 + r, benign)
            errors[arm].append(e)
            for k, v in st.items():
                stats[arm][k] = stats[arm].get(k, 0) + v
    _write(path, {"pair": pair, "solvers": [a, b], "level": level, "suite": suite, "fnum": f, "dim": _dim(suite), "dimset": DIMSET,
                  "runs": RUNS, "seed0": SEED0, "delta": DELTA, "benign": benign, "errors": errors,
                  "mech_stats": stats, "wall_s": time.time() - t0})
    return path, "done", time.time() - t0


def stage_run():
    cells = [(p, lv, s, f) for lv in LEVELS for p in PAIRS for (s, f) in PROBLEMS]
    todo = [c for c in cells if not os.path.exists(_cell_path(*c))]
    print(f"[camino-alterno] {len(cells)} celdas, {len(todo)} pendientes, N_JOBS={N_JOBS}", flush=True)
    t0 = time.time()
    with Pool(N_JOBS) as pool:
        for i, (path, st, w) in enumerate(pool.imap_unordered(_cell, todo), 1):
            print(f"  {i}/{len(todo)} {os.path.relpath(path, OUT)} {st} {w:.0f}s [{(time.time() - t0) / 3600:.2f} h]", flush=True)
    _write(os.path.join(OUT, f"run_meta_{int(time.time())}.json"),
           {"levels": LEVELS, "pairs": PAIRS, "n_problems": len(PROBLEMS), "runs": RUNS, "seed0": SEED0,
            "wall_s": time.time() - t0, "provenance": provenance()})


if __name__ == "__main__":
    {"tune": stage_tune, "run": stage_run}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
