"""Pre-registered expert-imitation study: JADE (teacher) -> DE (student).

Design and success criteria are FROZEN in
tesis-mia/gestion_proyecto/PREREGISTRO_IL_EXPERTO.md (committed 6 Jul 2026,
BEFORE any run). This pipeline implements exactly that design:

  Teacher : mealpy JADE (validated) with per-generation logging of
            (state features -> (miu_F, miu_CR)) on TRAIN functions only
            (CEC2014, 10D), at BOTH budgets (5e3, 5e4) -- horizon-matched.
  Policy  : BCPolicy, features -> ABSOLUTE (F, CR), clipped to demo hull.
  Variants: DE | DE+static-grid (train-tuned) | DE+static-teacher (mean demo)
            | DE+IL (cloned policy) | JADE (teacher reference).
  Eval    : 41 OOD functions (CEC2017+CEC2022, 10D), 51 paired seeds,
            exact MaxFES, v2 metrics (median-labelled Wilcoxon, Holm, A12).
  Verdict : pre-registered -- H confirmed iff DE+IL beats base AND BOTH
            statics after Holm at both budgets (else H refuted and reported).

Stages (resumable): demos | grid | train | eval | report
Usage: python scripts/cec_harness/run_expert_il.py [stage|all]
"""

import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from problems.continuous.cec_problem import CECProblem, run_with_fes  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.mealpy_adapter import MEALPY_ROSTER  # noqa: E402
from utils.bc_policy import BCPolicy  # noqa: E402

OUT = os.path.join(_REPO_ROOT, "results", "expert_il")
DEMO_DIR = os.path.join(OUT, "demos")
GRID_DIR = os.path.join(OUT, "grid")
EVAL_DIR = os.path.join(OUT, "eval")
MODEL_PATH = os.path.join(_REPO_ROOT, "models", "de_il_jade_cec2014_10d.pkl")

# --- frozen experimental configuration (see PREREGISTRO, do not edit) -------
TRAIN_FUNCS = [("CEC2014", f) for f in range(1, 31)]
TEST_FUNCS = ([("CEC2017", f) for f in range(1, 30)]
              + [("CEC2022", f) for f in range(1, 13)])
DIM = 10
POP = 30                       # teacher pop == student pop (state parity)
BUDGETS = [5000, 50000]
DEMO_SEEDS = [11, 22, 33]
GRID_F = [0.3, 0.45, 0.6, 0.75, 0.9]
GRID_CR = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
GRID_SEEDS = list(range(1000, 1011))    # 11 seeds (train tuning only)
EVAL_SEEDS = list(range(2000, 2051))    # 51 paired seeds (OOD)
BASE_F, BASE_CR = 0.8, 0.9
N_JOBS = int(os.environ.get("N_JOBS", "8"))


# --- policy adapters (module-level: workers rebuild from names) -------------
# AbsoluteToFactor now lives in utils.bc_policy so algorithms/de_il.py (the
# protocol variant) and this pipeline share one contract. Re-exported here so
# any pickles/workers referencing the old module path still resolve.
from utils.bc_policy import AbsoluteToFactor as _AbsoluteToFactor  # noqa: E402


class AbsoluteToFactor(_AbsoluteToFactor):
    """Thin subclass fixing the pipeline's BASE_F/BASE_CR (backwards compat)."""
    def __init__(self, policy):
        super().__init__(policy, base_f=BASE_F, base_cr=BASE_CR)


class StaticFCR:
    """Constant absolute (F, CR), expressed as factors for DE's hook."""
    n_outputs = 2

    def __init__(self, F, CR):
        self.F, self.CR = float(F), float(CR)

    def predict(self, algo, iteration):
        return (self.F / BASE_F, self.CR / BASE_CR)


# --- stage: demos (teacher trajectories) -------------------------------------
def _demo_worker(args):
    suite, fnum, seed, budget = args
    path = os.path.join(DEMO_DIR, f"JADE__{suite}__F{fnum}__s{seed}__fes{budget}.json")
    if os.path.exists(path):
        return path
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from mealpy import FloatVar
        from algorithms.jade_teacher import LoggingJADE
        prob = CECProblem(suite, fnum, DIM)
        lb = prob.get_lower_bounds().tolist()
        ub = prob.get_upper_bounds().tolist()
        pd = {"obj_func": lambda x: float(prob.evaluate(x)),
              "bounds": FloatVar(lb=lb, ub=ub), "minmax": "min", "log_to": None}
        epoch = max(1, min(100000, math.ceil(budget / POP) + 1))
        model = LoggingJADE(epoch=epoch, pop_size=POP, log_max_fe=budget)
        model.solve(pd, termination={"max_fe": budget}, seed=seed)
    with open(path, "w") as fh:
        json.dump(model.demo_log, fh)
    return path


def stage_demos():
    os.makedirs(DEMO_DIR, exist_ok=True)
    grid = [(s, f, sd, b) for (s, f) in TRAIN_FUNCS for sd in DEMO_SEEDS
            for b in BUDGETS]
    t0 = time.time()
    print(f"[demos] {len(grid)} teacher runs (30 funcs x {len(DEMO_SEEDS)} seeds"
          f" x {len(BUDGETS)} budgets)")
    with Pool(N_JOBS) as pool:
        done = 0
        for _ in pool.imap_unordered(_demo_worker, grid):
            done += 1
            if done % 20 == 0 or done == len(grid):
                print(f"[demos] {done}/{len(grid)} ({time.time()-t0:.0f}s)")
    print(f"[demos] done in {(time.time()-t0)/60:.1f} min")


# --- stage: static grid search (TRAIN only) ----------------------------------
def _grid_worker(args):
    F, CR, suite, fnum, budget = args
    cid = f"F{F}__CR{CR}__{suite}__F{fnum}__fes{budget}"
    path = os.path.join(GRID_DIR, cid + ".json")
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    errs = []
    for seed in GRID_SEEDS:
        prob = CECProblem(suite, fnum, DIM)
        e = run_with_fes(DE, prob, pop_size=POP, max_fes=budget, seed=seed,
                         algo_params={"use_il": True,
                                      "il_model": StaticFCR(F, CR)})
        errs.append(float(e))
    rec = {"F": F, "CR": CR, "suite": suite, "fnum": fnum, "budget": budget,
           "mean": float(np.mean(errs))}
    with open(path, "w") as fh:
        json.dump(rec, fh)
    return rec


def stage_grid():
    os.makedirs(GRID_DIR, exist_ok=True)
    combos = [(F, CR) for F in GRID_F for CR in GRID_CR]
    grid = [(F, CR, s, f, b) for (F, CR) in combos for (s, f) in TRAIN_FUNCS
            for b in BUDGETS]
    t0 = time.time()
    print(f"[grid] {len(grid)} cells ({len(combos)} combos x 30 train funcs x "
          f"{len(BUDGETS)} budgets, {len(GRID_SEEDS)} seeds each)")
    cells = []
    with Pool(N_JOBS) as pool:
        done = 0
        for rec in pool.imap_unordered(_grid_worker, grid):
            cells.append(rec)
            done += 1
            if done % 100 == 0 or done == len(grid):
                print(f"[grid] {done}/{len(grid)} ({(time.time()-t0)/60:.1f}m)")
    # Rank combos per (func, budget); best avg rank per budget wins.
    best = {}
    for b in BUDGETS:
        ranks = {c: [] for c in combos}
        for (s, f) in TRAIN_FUNCS:
            sub = [r for r in cells if r["suite"] == s and r["fnum"] == f
                   and r["budget"] == b]
            sub.sort(key=lambda r: r["mean"])
            for rank, r in enumerate(sub, 1):
                ranks[(r["F"], r["CR"])].append(rank)
        avg = {c: float(np.mean(v)) for c, v in ranks.items() if v}
        winner = min(avg, key=avg.get)
        best[str(b)] = {"F": winner[0], "CR": winner[1],
                        "avg_rank": avg[winner]}
        print(f"[grid] budget {b}: best static = F={winner[0]}, CR={winner[1]} "
              f"(avg rank {avg[winner]:.2f})")
    with open(os.path.join(OUT, "static_best.json"), "w") as fh:
        json.dump(best, fh, indent=2)


# --- stage: train policy ------------------------------------------------------
def stage_train():
    import glob
    paths = sorted(glob.glob(os.path.join(DEMO_DIR, "JADE__*.json")))
    acts = []
    for p in paths:
        acts += [r["action"] for r in json.load(open(p))]
    acts = np.array(acts)
    # Per-dimension demonstrated hull (independent F and CR ranges), not a
    # shared scalar hull (remediation from the implementation audit).
    lo = acts.min(axis=0)
    hi = acts.max(axis=0)
    policy = BCPolicy.train_from_demo_files(paths, n_outputs=2, seed=0,
                                            clip_lo=lo, clip_hi=hi)
    policy.save(MODEL_PATH)
    # Teacher-mean static (pre-registered baseline): overall mean action.
    teacher_mean = {"F": float(acts[:, 0].mean()), "CR": float(acts[:, 1].mean())}
    with open(os.path.join(OUT, "teacher_mean.json"), "w") as fh:
        json.dump(teacher_mean, fh)
    print(f"[train] {policy.n_demos} demos from {len(paths)} teacher runs")
    print(f"[train] action hull=[{lo:.3f},{hi:.3f}]  teacher-mean F={teacher_mean['F']:.3f} CR={teacher_mean['CR']:.3f}")
    print(f"[train] feature importances: "
          f"{ {k: round(v,3) for k, v in policy.feature_importances().items()} }")
    print(f"[train] saved {MODEL_PATH}")


# --- stage: eval (5 variants, OOD) --------------------------------------------
def _make_variant(name, budget):
    """Return (algo_class, algo_params) for a variant name."""
    if name == "base":
        return DE, None
    if name == "static_grid":
        best = json.load(open(os.path.join(OUT, "static_best.json")))[str(budget)]
        return DE, {"use_il": True, "il_model": StaticFCR(best["F"], best["CR"])}
    if name == "static_teacher":
        tm = json.load(open(os.path.join(OUT, "teacher_mean.json")))
        return DE, {"use_il": True, "il_model": StaticFCR(tm["F"], tm["CR"])}
    if name == "il":
        return DE, {"use_il": True,
                    "il_model": AbsoluteToFactor(BCPolicy.load(MODEL_PATH))}
    if name == "jade":
        return MEALPY_ROSTER["JADE"], None
    raise ValueError(name)


VARIANTS = ["base", "static_grid", "static_teacher", "il", "jade"]


def _eval_worker(args):
    variant, suite, fnum, budget = args
    path = os.path.join(EVAL_DIR, f"{variant}__{suite}__F{fnum}__fes{budget}.json")
    if os.path.exists(path):
        return path
    cls, params = _make_variant(variant, budget)
    errs = []
    for seed in EVAL_SEEDS:
        prob = CECProblem(suite, fnum, DIM)
        errs.append(float(run_with_fes(cls, prob, pop_size=POP, max_fes=budget,
                                       seed=seed, algo_params=params)))
    with open(path, "w") as fh:
        json.dump({"variant": variant, "suite": suite, "fnum": fnum,
                   "budget": budget, "errors": errs}, fh)
    return path


def stage_eval():
    os.makedirs(EVAL_DIR, exist_ok=True)
    grid = [(v, s, f, b) for v in VARIANTS for (s, f) in TEST_FUNCS
            for b in BUDGETS]
    t0 = time.time()
    print(f"[eval] {len(grid)} cells ({len(VARIANTS)} variants x 41 OOD funcs x "
          f"{len(BUDGETS)} budgets, {len(EVAL_SEEDS)} paired seeds)")
    with Pool(N_JOBS) as pool:
        done = 0
        for _ in pool.imap_unordered(_eval_worker, grid):
            done += 1
            if done % 25 == 0 or done == len(grid):
                print(f"[eval] {done}/{len(grid)} ({(time.time()-t0)/60:.1f}m)")
    print(f"[eval] done in {(time.time()-t0)/60:.1f} min")


# --- stage: report (v2 metrics + PRE-REGISTERED verdict) -----------------------
def _load_errors(variant, suite, fnum, budget):
    p = os.path.join(EVAL_DIR, f"{variant}__{suite}__F{fnum}__fes{budget}.json")
    return np.asarray(json.load(open(p))["errors"], dtype=float)


def _holm(pvals, alpha=0.05):
    p = np.asarray(pvals)
    order = np.argsort(p)
    reject = np.zeros(len(p), dtype=bool)
    for rank, idx in enumerate(order):
        if p[idx] <= alpha / (len(p) - rank):
            reject[idx] = True
        else:
            break
    return reject


def _a12(x, y):
    x = np.asarray(x)[:, None]
    y = np.asarray(y)[None, :]
    return float(((x < y).sum() + 0.5 * (x == y).sum()) / (x.shape[0] * y.shape[1]))


def _compare(variant, ref, budget):
    """Paired v2 comparison of `variant` against `ref` across OOD functions."""
    from scipy.stats import wilcoxon
    rows = []
    for suite, fnum in TEST_FUNCS:
        a = _load_errors(ref, suite, fnum, budget)      # reference
        v = _load_errors(variant, suite, fnum, budget)  # candidate
        diff = a - v
        med = float(np.median(diff))
        if np.allclose(diff, 0.0, atol=1e-12):
            p = 1.0
        else:
            try:
                _, p = wilcoxon(a, v)
            except ValueError:
                p = 1.0
        rows.append({"p": p, "med": med, "a12": _a12(v, a)})
    rej = _holm([r["p"] for r in rows])
    def label(r, sig):
        if not sig or r["med"] == 0:
            return "equal"
        return "better" if r["med"] > 0 else "worse"
    raw = [label(r, r["p"] < 0.05) for r in rows]
    hol = [label(r, s) for r, s in zip(rows, rej)]
    return {
        "bew_raw": {k: raw.count(k) for k in ("better", "equal", "worse")},
        "bew_holm": {k: hol.count(k) for k in ("better", "equal", "worse")},
        "median_a12": float(np.median([r["a12"] for r in rows])),
    }


def stage_report():
    out = {}
    print("\n" + "=" * 76)
    print("EXPERT-IL (JADE->DE) -- pre-registered report (v2 metrics, n=41 OOD)")
    print("=" * 76)
    for budget in BUDGETS:
        print(f"\n--- MaxFES = {budget} ---")
        res = {}
        for variant in ["static_grid", "static_teacher", "il", "jade"]:
            res[variant + "_vs_base"] = _compare(variant, "base", budget)
        res["il_vs_static_grid"] = _compare("il", "static_grid", budget)
        res["il_vs_static_teacher"] = _compare("il", "static_teacher", budget)
        res["il_vs_jade"] = _compare("il", "jade", budget)
        for k, r in res.items():
            print(f"  {k:24} raw={r['bew_raw']['better']}/{r['bew_raw']['equal']}"
                  f"/{r['bew_raw']['worse']}  holm={r['bew_holm']['better']}/"
                  f"{r['bew_holm']['equal']}/{r['bew_holm']['worse']}  "
                  f"A12={r['median_a12']:.3f}")
        out[str(budget)] = res

    # --- PRE-REGISTERED VERDICT (frozen criteria; see PREREGISTRO doc) ------
    # H confirmed iff, at BOTH budgets, DE+IL beats base AND both statics:
    # better > worse after Holm, and median A12 > 0.5 against each static.
    print("\n--- PRE-REGISTERED VERDICT ---")
    confirmed = True
    for budget in BUDGETS:
        r = out[str(budget)]
        checks = [("il_vs_base", False),
                  ("il_vs_static_grid", True),
                  ("il_vs_static_teacher", True)]
        for key, need_a12 in checks:
            bh = r[key]["bew_holm"]
            ok = bh["better"] > bh["worse"]
            if need_a12:
                ok = ok and r[key]["median_a12"] > 0.5
            print(f"  {budget} {key}: Holm {bh['better']}/{bh['equal']}/"
                  f"{bh['worse']}, A12={r[key]['median_a12']:.3f} "
                  f"-> {'OK' if ok else 'FAIL'}")
            confirmed &= ok
    print(f"\n  H {'CONFIRMADA' if confirmed else 'REFUTADA (para esta operacionalizacion)'}")
    out["_verdict"] = {"H_confirmada": bool(confirmed)}
    try:
        from utils.provenance import provenance
        out["_provenance"] = provenance()
    except Exception as exc:  # pragma: no cover
        out["_provenance"] = {"error": f"provenance unavailable: {exc}"}
    with open(os.path.join(OUT, "expert_il_report.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nsaved {OUT}/expert_il_report.json")
    return out


STAGES = {"demos": stage_demos, "grid": stage_grid, "train": stage_train,
          "eval": stage_eval, "report": stage_report}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(OUT, exist_ok=True)
    if which == "all":
        for name in ("demos", "grid", "train", "eval", "report"):
            STAGES[name]()
    else:
        STAGES[which]()
