"""Fase 2 (enmienda v0.3 §D) — piloto de candidatos A, B, C.

12 funciones CEC2014-10D × 51 corridas CRN (seed0=9000) × {5e3, 5e4} × 3 pares.
Brazos por celda: SBS_A, SBS_B, C1_div, C1_island, C3p_v2, A, B, C, BENg, BENn.
Resumible por celda (un JSON por (par, nivel, función)); `aggregate` emite la
tabla de criterios de éxito por candidato (v0.1 §5).

Uso:  N_JOBS=10 python scripts/cec_harness/run_fase2_piloto.py run
      python scripts/cec_harness/run_fase2_piloto.py aggregate
Requiere results/cooperative/fase2/benign_regimes.json (fase2_tuning_benigno.py).
"""
import glob
import json
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from cooperative.orchestrator import CooperativeRunner  # noqa: E402
from cooperative.functional_intent import PRESETS_V2  # noqa: E402
from cooperative.candidates import (BudgetAllocRunner, StructuralGatedRunner,  # noqa: E402
                                    UCBRegimeRunner, BenignControlRunner)
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
PAIRS = ["GWO+GA", "DE+GA", "PSO+ACO"]
FUNCS = [2, 3, 5, 8, 11, 14, 17, 18, 20, 24, 26, 29]
LEVELS = [int(x) for x in os.environ.get("LEVELS", "5000,50000").split(",")]
DIM, POP, RUNS, SEED0, DELTA = 10, 30, int(os.environ.get("RUNS", "51")), 9000, 500
N_JOBS = int(os.environ.get("N_JOBS", "10"))
OUT_DIR = os.path.join(_REPO, "results", "cooperative", "fase2", "piloto")
BENIGN = os.path.join(_REPO, "results", "cooperative", "fase2", "benign_regimes.json")
ARMS = ["SBS_A", "SBS_B", "C1_div", "C1_island", "C3p_v2", "A", "B", "C", "BENg", "BENn"]
CANDIDATES = ["A", "B", "C"]


def _specs(a, b):
    return [(a, _CLS[a], {"population_size": POP, "max_iterations": 10**9}),
            (b, _CLS[b], {"population_size": POP, "max_iterations": 10**9})]


def _prob(f, level):
    return FESLimitProblem(CECProblem("CEC2014", f, DIM), max_fes=level)


def _run_arm(arm, a, b, f, level, seed, benign):
    specs = _specs(a, b)
    if arm == "SBS_A":
        return float(run_with_fes(_CLS[a], CECProblem("CEC2014", f, DIM), pop_size=POP, max_fes=level, seed=seed)), {}
    if arm == "SBS_B":
        return float(run_with_fes(_CLS[b], CECProblem("CEC2014", f, DIM), pop_size=POP, max_fes=level, seed=seed)), {}
    if arm == "C1_div":
        return float(min(run_with_fes(_CLS[a], CECProblem("CEC2014", f, DIM), pop_size=POP, max_fes=level // 2, seed=seed),
                         run_with_fes(_CLS[b], CECProblem("CEC2014", f, DIM), pop_size=POP, max_fes=level // 2, seed=seed))), {}
    if arm == "C1_island":
        r = CooperativeRunner(_prob(f, level), specs, transfer_every=DELTA, gate_enabled=False,
                              seed=seed, transfer_mode="structural")
    elif arm == "C3p_v2":
        r = CooperativeRunner(_prob(f, level), specs, transfer_every=DELTA, gate_enabled=True,
                              seed=seed, transfer_mode="parametric", intent_mode="source")
        from cooperative.functional_intent import RegimeController
        for e in r.solvers:
            ctrl = RegimeController(e["name"], presets=PRESETS_V2)
            e["solver"].il_model = ctrl; r._controllers[e["name"]] = ctrl
    elif arm == "A":
        r = BudgetAllocRunner(_prob(f, level), specs, delta=DELTA, seed=seed)
    elif arm == "B":
        r = StructuralGatedRunner(_prob(f, level), specs, delta=DELTA, seed=seed)
    elif arm == "C":
        r = UCBRegimeRunner(_prob(f, level), specs, delta=DELTA, seed=seed)
    elif arm in ("BENg", "BENn"):
        r = BenignControlRunner(_prob(f, level), specs, benign, delta=DELTA, seed=seed,
                                gate_enabled=(arm == "BENg"))
    else:
        raise ValueError(arm)
    res = r.run()
    if res["fes_used"] != level:
        raise AssertionError((arm, a, b, f, level, seed, res["fes_used"]))
    return float(res["best_fitness"]), res.get("transfer_stats", {})


def _cell_path(pair, level, f):
    d = os.path.join(OUT_DIR, f"{pair.replace('+', '')}_{level}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"CEC2014_F{f}.json")


def _cell(args):
    pair, level, f = args
    path = _cell_path(pair, level, f)
    if os.path.exists(path):
        return path, "skip"
    a, b = pair.split("+")
    ben_all = json.load(open(BENIGN))[str(level)][f"F{f}"]
    benign = {a: ben_all[a]["factors"], b: ben_all[b]["factors"]}
    errors = {arm: [] for arm in ARMS}
    stats = {arm: {} for arm in ARMS}
    for r in range(RUNS):
        for arm in ARMS:
            e, st = _run_arm(arm, a, b, f, level, SEED0 + r, benign)
            errors[arm].append(e)
            for k, v in st.items():
                if isinstance(v, (int, float)):
                    stats[arm][k] = stats[arm].get(k, 0) + v
    out = {"pair": pair, "level": level, "fnum": f, "dim": DIM, "runs": RUNS,
           "seed0": SEED0, "delta": DELTA, "benign": benign, "errors": errors,
           "mech_stats": stats}
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, path)
    return path, "done"


def _holm(pv):
    m = len(pv); order = sorted(range(m), key=lambda i: pv[i]); adj = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pv[i]); adj[i] = min(1.0, run)
    return adj


def _paired(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); d = a - b; dd = d[d != 0]
    if len(dd) == 0:
        return 1.0, 0.0
    _, p = wilcoxon(a, b, zero_method="wilcox")
    r = np.argsort(np.argsort(np.abs(dd))) + 1.0
    return float(p), float((r[dd < 0].sum() - r[dd > 0].sum()) / r.sum())


def stage_run():
    cells = [(p, lv, f) for p in PAIRS for lv in LEVELS for f in FUNCS]
    todo = [c for c in cells if not os.path.exists(_cell_path(*c))]
    print(f"[piloto] {len(cells)} celdas, {len(todo)} pendientes, N_JOBS={N_JOBS}", flush=True)
    with Pool(N_JOBS) as pool:
        for i, (path, st) in enumerate(pool.imap_unordered(_cell, todo), 1):
            print(f"  {i}/{len(todo)} {os.path.basename(os.path.dirname(path))}/{os.path.basename(path)} {st}", flush=True)


def stage_aggregate():
    summary = {"criteria": "v0.1 §5: mejor>peor en ambos presupuestos; mediana r>=0.3; peor<=2/12; en >=2 de 3 pares",
               "contrasts": {}, "success": {}}
    per_pair_ok = {c: {} for c in CANDIDATES}
    for pair in PAIRS:
        for lv in LEVELS:
            cells = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT_DIR, f"{pair.replace('+', '')}_{lv}", "*.json")))]
            if not cells:
                continue
            key = f"{pair}_{lv}"
            summary["contrasts"][key] = {}
            for arm in ["C1_island", "C3p_v2", "A", "B", "C", "BENg", "BENn"]:
                pv, rs = [], []
                for c in cells:
                    p, r = _paired(c["errors"][arm], c["errors"]["C1_div"]); pv.append(p); rs.append(r)
                adj = _holm(pv)
                summary["contrasts"][key][f"{arm}_vs_C1div"] = {
                    "wins": sum(1 for h, r in zip(adj, rs) if h < 0.05 and r > 0),
                    "losses": sum(1 for h, r in zip(adj, rs) if h < 0.05 and r < 0),
                    "median_r": float(np.median(rs)), "n": len(cells)}
            # falsos positivos del gate: BENg vs BENn
            pv, rs = [], []
            for c in cells:
                p, r = _paired(c["errors"]["BENg"], c["errors"]["BENn"]); pv.append(p); rs.append(r)
            adj = _holm(pv)
            summary["contrasts"][key]["BENg_vs_BENn"] = {
                "wins": sum(1 for h, r in zip(adj, rs) if h < 0.05 and r > 0),
                "losses": sum(1 for h, r in zip(adj, rs) if h < 0.05 and r < 0),
                "median_r": float(np.median(rs)), "n": len(cells)}
        # criterio por candidato y par (ambos presupuestos)
        for cand in CANDIDATES:
            oks = []
            for lv in LEVELS:
                key = f"{pair}_{lv}"
                t = summary["contrasts"].get(key, {}).get(f"{cand}_vs_C1div")
                if t is None:
                    oks.append(False); continue
                oks.append(t["wins"] > t["losses"] and t["median_r"] >= 0.3 and t["losses"] <= 2)
            per_pair_ok[cand][pair] = bool(all(oks))
    for cand in CANDIDATES:
        n_ok = sum(per_pair_ok[cand].values())
        summary["success"][cand] = {"pairs_ok": per_pair_ok[cand], "n_pairs_ok": n_ok,
                                    "cumple_criterio": n_ok >= 2}
    winners = [c for c in CANDIDATES if summary["success"][c]["cumple_criterio"]]
    summary["corte2"] = ("CONTINUAR a Fase 3 con " + ", ".join(winners)) if winners else "CAMINO ALTERNO (ningun candidato cumple)"
    summary["provenance"] = provenance()
    out = os.path.join(_REPO, "results", "cooperative", "fase2", "piloto_summary.json")
    with open(out, "w") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "provenance"}, indent=1))
    print("->", out)


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "run"
    stage_run() if stage == "run" else stage_aggregate()
