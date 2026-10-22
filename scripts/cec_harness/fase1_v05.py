"""Fase 1 re-ejecutada sobre el benchmark OFICIAL (enmienda v0.5, D27).

La Fase 1 original (v0.2) se calculó con opfunu 1.0.1 y con el C1_div de la
campaña inválida. Aquí se recalcula todo desde cero con las MISMAS definiciones
de las cuatro cotas y los MISMOS umbrales de v0.2 §A (sin ajustar nada):

  (1) VBS por función vs C1_div                          umbral: mejor ≥ 20 con Holm y mediana r ≥ 0.3
  (2a) reparto estático óptimo (clarividente) vs C1_div   ídem
  (2b) conmutación clarividente por mejora absoluta       ídem (definición pre-registrada)
  (2c) ídem por mejora relativa (EXPLORATORIO, la señal que nombra H1)
  (3) cribado 71 × 7: cambio de ganador                   umbral: ≥ 40 %
  (4) estabilidad del signo del efecto por triple         umbral: ≥ 70 % en triples con ≥ 30 observaciones
Corte 1: continuar si (1) o (2b) supera en alguna celda.

Datos: C0 con curvas (grilla Δ = 500) de 7 solvers a presupuesto completo; C0
a B/2 de cada solver de cada par (C1_div = mejor de los dos); E2 = DE+GA @ 5e3
con intención de fuente (C2p, C3p) y vocabulario PRESETS_V2 sobre las 6
funciones taxonómicas. Semillas CRN con el mapeo de v0.5 (`solver_seed`):
índice 0 = GWO/DE/PSO/SSA/WOA, índice 1 = GA/ACO.

Uso: N_JOBS=12 LEVELS=5000,50000 python scripts/cec_harness/fase1_v05.py curves
     N_JOBS=12 python scripts/cec_harness/fase1_v05.py e2
     python scripts/cec_harness/fase1_v05.py cotas
     (GWO+GA a 5e5: SOLVERS=GWO,GA LEVELS=500000 ... curves)

Orden obligatorio: curves (5e3, 5e4 y GWO+GA a 5e5) → e2 → cotas. Las curvas C0
no se versionan (D31). Si falta alguna celda de las cotas (1) o (3), `cotas`
termina con código distinto de 0 sin decidir el Corte 1 y sin escribir
cotas_fase1.{json,md}; F1_PARTIAL=1 permite un cálculo parcial explícito.
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from cooperative.curves import run_with_curve  # noqa: E402
from cooperative.orchestrator import CooperativeRunner, solver_seed  # noqa: E402
from cooperative.functional_intent import PRESETS_V2  # noqa: E402
from scripts.cec_harness.fase1_cotas import _static_opt, _greedy_clairvoyant, _greedy_relative  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from algorithms.ssa import SSA  # noqa: E402
from algorithms.woa import WOA  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.environ.get("F1_OUT", os.path.join(_REPO, "results", "cooperative", "fase1_v05"))
_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO, "SSA": SSA, "WOA": WOA}
IDX = {"GWO": 0, "DE": 0, "PSO": 0, "SSA": 0, "WOA": 0, "GA": 1, "ACO": 1}
SOLVERS7 = ["DE", "PSO", "GWO", "GA", "ACO", "SSA", "WOA"]
PAIRS = {"GWOGA": ("GWO", "GA", [5000, 50000, 500000]),
         "DEGA": ("DE", "GA", [5000, 50000]),
         "PSOACO": ("PSO", "ACO", [5000, 50000])}
PROBLEMS = ([("CEC2014", f) for f in range(1, 31)]
            + [("CEC2017", f) for f in range(1, 31) if f != 2]
            + [("CEC2022", f) for f in range(1, 13)])
DIM, POP, DELTA = 10, 30, 500
RUNS = int(os.environ.get("RUNS", "51"))
SEED0, E2_SEED0 = 14000, 14500
E2_FUNCS = [1, 4, 6, 9, 15, 23]
TH = {"wins_min": 20, "median_r_min": 0.3, "winner_change_min": 0.40,
      "stability_min": 0.70, "stability_min_seeds": 30, "alpha": 0.05}
N_JOBS = int(os.environ.get("N_JOBS", "12"))
LEVELS = [int(x) for x in os.environ.get("LEVELS", "5000,50000").split(",")]
SOLVERS = os.environ.get("SOLVERS", ",".join(SOLVERS7)).split(",")


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh)
    os.replace(tmp, path)


def _key(s, f):
    return f"{s}_F{f}"


# ------------------------------------------------------------- stage: curves --
def _curve_path(solver, level, s, f):
    return os.path.join(OUT, "c0_curves", f"{solver}_{level}", _key(s, f) + ".json")


def _half_path(solver, level, s, f):
    return os.path.join(OUT, "c0_half", f"{solver}_{level}", _key(s, f) + ".json")


def _curve_cell(args):
    solver, level, s, f = args
    p = _curve_path(solver, level, s, f)
    if not os.path.exists(p):
        finals, curves = [], []
        for r in range(RUNS):
            best, curve = run_with_curve(_CLS[solver], CECProblem(s, f, DIM), pop_size=POP, max_fes=level,
                                         seed=solver_seed(SEED0 + r, IDX[solver]), delta=DELTA)
            finals.append(float(best)); curves.append([float(v) for v in curve])
        _write(p, {"solver": solver, "level": level, "suite": s, "fnum": f, "seed0": SEED0, "runs": RUNS,
                   "delta": DELTA, "finals": finals, "curves": curves})
    # mitad del presupuesto (componente de C1_div) solo para solvers de algún par
    if any(solver in (a, b) and level in lv for a, b, lv in PAIRS.values()):
        hp = _half_path(solver, level, s, f)
        if not os.path.exists(hp):
            idx = IDX[solver]
            half = level // 2 if idx == 0 else level - level // 2
            finals = [float(run_with_fes(_CLS[solver], CECProblem(s, f, DIM), pop_size=POP, max_fes=half,
                                         seed=solver_seed(SEED0 + r, idx))) for r in range(RUNS)]
            _write(hp, {"solver": solver, "level": level, "budget": half, "finals": finals})
    return p


def stage_curves():
    jobs = [(so, lv, s, f) for lv in LEVELS for so in SOLVERS for (s, f) in PROBLEMS
            if not (lv == 500000 and so not in ("GWO", "GA"))]
    if os.environ.get("ONLY_FUNCS"):
        sel = [(s, int(f)) for s, f in (x.split(":") for x in os.environ["ONLY_FUNCS"].split(","))]
        jobs = [j for j in jobs if (j[2], j[3]) in sel]
    print(f"[fase1_v05 curves] {len(jobs)} celdas, N_JOBS={N_JOBS}", flush=True)
    with Pool(N_JOBS) as pool:
        for i, _ in enumerate(pool.imap_unordered(_curve_cell, jobs), 1):
            if i % 50 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)


# ----------------------------------------------------------------- stage: e2 --
def _e2_cell(args):
    f, arm, gate = args
    acc = defaultdict(lambda: {"per_seed_mean_effect": [], "n_obs": []})
    specs = [("DE", DE, {"population_size": POP}), ("GA", GA, {"population_size": POP})]
    for r in range(RUNS):
        res = CooperativeRunner(FESLimitProblem(CECProblem("CEC2014", f, DIM), max_fes=5000), specs,
                                transfer_every=DELTA, gate_enabled=gate, seed=E2_SEED0 + r,
                                transfer_mode="parametric", intent_mode="source", presets=PRESETS_V2,
                                log_transfers=True).run()
        assert res["fes_used"] == 5000
        by = defaultdict(list)
        for t in res["transfers"]:
            by[f"{t['src']}->{t['tgt']}:{t['intent']}"].append(float(t["effect"]))
        for k in set(list(by) + list(acc)):
            v = by.get(k, [])
            acc[k]["per_seed_mean_effect"].append(float(np.mean(v)) if v else None)
            acc[k]["n_obs"].append(len(v))
    return f, arm, dict(acc)


def stage_e2():
    jobs = [(f, arm, gate) for f in (E2_FUNCS if not os.environ.get("E2_FUNCS") else [int(x) for x in os.environ["E2_FUNCS"].split(",")]) for arm, gate in (("C2p", False), ("C3p", True))]
    per = defaultdict(dict)
    with Pool(min(N_JOBS, len(jobs))) as pool:
        for f, arm, acc in pool.imap_unordered(_e2_cell, jobs):
            per[f"F{f}"][arm] = acc
    _write(os.path.join(OUT, "e2_effect_logs.json"),
           {"config": {"pair": "DE+GA", "funcs": E2_FUNCS, "runs": RUNS, "budget": 5000, "delta": DELTA,
                       "seed0": E2_SEED0, "arms": ["C2p", "C3p"], "vocab": "PRESETS_V2",
                       "effect": "mediana_now - mediana_commit (>0 = daño)"},
            "per_func": per, "provenance": provenance()})


# -------------------------------------------------------------- stage: cotas --
def paired(a, b):
    a = np.where(np.asarray(a, float) < 1e-8, 0.0, np.asarray(a, float))
    b = np.where(np.asarray(b, float) < 1e-8, 0.0, np.asarray(b, float))
    d = a - b; dd = d[d != 0]
    if len(dd) == 0:
        return 1.0, 0.0
    _, p = wilcoxon(a, b, zero_method="wilcox")
    r = rankdata(np.abs(dd))
    return float(p), float((r[dd < 0].sum() - r[dd > 0].sum()) / r.sum())


def contrast(rows):
    ps, rs = zip(*[paired(a, b) for a, b in rows]) if rows else ((), ())
    m = len(ps); order = sorted(range(m), key=lambda i: ps[i]); adj = [0.0] * m; run = 0.0
    for k, i in enumerate(order):
        run = max(run, (m - k) * ps[i]); adj[i] = min(1.0, run)
    w = sum(1 for h, r in zip(adj, rs) if h < TH["alpha"] and r > 0)
    l = sum(1 for h, r in zip(adj, rs) if h < TH["alpha"] and r < 0)
    med = float(np.median(rs)) if rs else 0.0
    return {"wins": w, "losses": l, "n": m, "median_r": round(med, 3),
            "pass": bool(w >= TH["wins_min"] and med >= TH["median_r_min"])}


def _load(kind, solver, level):
    d = os.path.join(OUT, kind, f"{solver}_{level}")
    return {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(d, "*.json"))}


def stage_cotas():
    res = {"thresholds": TH, "cota1_vbs": {}, "cota2_oraculo": {}, "cota3_cribado": {}}
    for pdir, (A, B, levels) in PAIRS.items():
        for lv in levels:
            ca, cb = _load("c0_curves", A, lv), _load("c0_curves", B, lv)
            ha, hb = _load("c0_half", A, lv), _load("c0_half", B, lv)
            keys = sorted(set(ca) & set(cb) & set(ha) & set(hb))
            if len(keys) < len(PROBLEMS) and not os.environ.get("F1_PARTIAL"):
                res["cota1_vbs"][f"{pdir}_{lv}"] = {"status": f"incompleto ({len(keys)}/{len(PROBLEMS)})"}
                continue
            c1div = {k: np.minimum(ha[k]["finals"], hb[k]["finals"]) for k in keys}
            rows1, choice = [], Counter()
            for k in keys:
                ea, eb = ca[k]["finals"], cb[k]["finals"]
                use_a = np.median(ea) <= np.median(eb)
                choice[A if use_a else B] += 1
                rows1.append((ea if use_a else eb, c1div[k]))
            t = contrast(rows1); t["vbs_choice"] = dict(choice)
            res["cota1_vbs"][f"{pdir}_{lv}"] = t
            rows_s, rows_g, rows_r = [], [], []
            for k in keys:
                CA, CB = ca[k]["curves"], cb[k]["curves"]
                rows_s.append(([_static_opt(CA[r], CB[r]) for r in range(RUNS)], c1div[k]))
                rows_g.append(([_greedy_clairvoyant(CA[r], CB[r]) for r in range(RUNS)], c1div[k]))
                rows_r.append(([_greedy_relative(CA[r], CB[r]) for r in range(RUNS)], c1div[k]))
            res["cota2_oraculo"][f"{pdir}_{lv}"] = {"2a_asignacion_estatica_optima": contrast(rows_s),
                                                  "2b_conmutacion_clarividente": contrast(rows_g),
                                                  "2c_exploratorio_mejora_relativa": contrast(rows_r)}
    for lv in (5000, 50000):
        finals = {so: {k: v["finals"] for k, v in _load("c0_curves", so, lv).items()} for so in SOLVERS7}
        names = sorted(set.intersection(*[set(v) for v in finals.values()]))
        if len(names) < len(PROBLEMS) and not os.environ.get("F1_PARTIAL"):
            res["cota3_cribado"][str(lv)] = {"status": f"incompleto ({len(names)})"}
            continue
        winners = Counter(min(SOLVERS7, key=lambda so: np.median(finals[so][n])) for n in names)
        modal, fm = winners.most_common(1)[0]
        change = 1 - fm / len(names)
        res["cota3_cribado"][str(lv)] = {"n_funcs": len(names), "winner_counts": dict(winners), "modal": modal,
                                         "winner_change": round(change, 3),
                                         "pass": bool(change >= TH["winner_change_min"])}
    # Sin curvas C0 completas no hay Corte 1: abortar ANTES de decidir y de escribir
    # cotas_fase1.{json,md} (con celdas "incompleto" la regla daría CAMINO ALTERNO
    # por omisión y sobrescribiría los resultados versionados). F1_PARTIAL lo desactiva.
    faltan = [f"cota1_vbs[{k}]" for k, v in res["cota1_vbs"].items()
              if str(v.get("status", "")).startswith("incompleto")]
    faltan += [f"cota3_cribado[{k}]" for k, v in res["cota3_cribado"].items()
               if str(v.get("status", "")).startswith("incompleto")]
    if faltan:
        sys.exit("Faltan curvas C0: ejecutar primero `fase1_v05.py curves` y `e2` "
                 f"(celdas incompletas: {', '.join(faltan)}). "
                 "No se decide el Corte 1 ni se escribe cotas_fase1.{json,md}.")
    e2p = os.path.join(OUT, "e2_effect_logs.json")
    res["cota4_estabilidad"] = {}
    if os.path.exists(e2p):
        d = json.load(open(e2p))
        for arm in d["config"]["arms"]:
            agg = defaultdict(list)
            for f, arms in d["per_func"].items():
                for triple, v in arms.get(arm, {}).items():
                    agg[triple] += [np.sign(m) for m in v["per_seed_mean_effect"] if m is not None]
            rows = {}
            for triple, s in agg.items():
                s = np.asarray(s); maj = 1.0 if (s > 0).sum() >= (s < 0).sum() else -1.0
                rows[triple] = {"n_seed_obs": int(len(s)), "majority_sign": "daño" if maj > 0 else "beneficio",
                                "stability": round(float((s == maj).mean()), 3) if len(s) else 0.0}
            elig = [r for r in rows.values() if r["n_seed_obs"] >= TH["stability_min_seeds"]]
            ok = sum(1 for r in elig if r["stability"] >= TH["stability_min"])
            res["cota4_estabilidad"][arm] = {"triples": rows, "n_eligible": len(elig), "n_stable": ok,
                                             "pass": bool(elig and ok >= (len(elig) + 1) // 2)}
    any1 = any(v.get("pass") for v in res["cota1_vbs"].values())
    any2 = any(v.get("2b_conmutacion_clarividente", {}).get("pass") for v in res["cota2_oraculo"].values())
    res["corte1"] = {"cota1_supera": any1, "cota2b_supera": any2,
                     "decision": "CONTINUAR a Fase 2" if (any1 or any2) else "CAMINO ALTERNO"}
    res["provenance"] = provenance()
    _write(os.path.join(OUT, "cotas_fase1.json"), res)
    f = lambda t: f"{t['wins']}/{t['losses']} (r={t['median_r']}){' ✓' if t['pass'] else ''}" if "wins" in t else t.get("status", "")
    L = ["# Fase 1 re-ejecutada (benchmark oficial, v0.5) — cotas\n", f"Umbrales (v0.2 §A): {TH}\n",
         "| celda | (1) VBS | (2a) estático óptimo | (2b) conmutación | (2c) exploratorio |", "|---|---|---|---|---|"]
    for k, t in res["cota1_vbs"].items():
        o = res["cota2_oraculo"].get(k, {})
        L.append(f"| {k} | {f(t)} | {f(o.get('2a_asignacion_estatica_optima', {}))} | "
                 f"{f(o.get('2b_conmutacion_clarividente', {}))} | {f(o.get('2c_exploratorio_mejora_relativa', {}))} |")
    L += ["", "## (3) cribado 71 × 7", ""] + [f"- {k}: {v}" for k, v in res["cota3_cribado"].items()]
    L += ["", "## (4) estabilidad por triple", ""]
    for arm, v in res["cota4_estabilidad"].items():
        L.append(f"- {arm}: {v['n_stable']}/{v['n_eligible']} estables " + str({t: (r['majority_sign'], r['stability'], r['n_seed_obs']) for t, r in v['triples'].items()}))
    L += ["", f"**Corte 1: {res['corte1']['decision']}** ({res['corte1']})"]
    open(os.path.join(OUT, "cotas_fase1.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    {"curves": stage_curves, "e2": stage_e2, "cotas": stage_cotas}[sys.argv[1]]()
