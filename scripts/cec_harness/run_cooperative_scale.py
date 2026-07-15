"""
Confirmatory study at SCALE — cooperative parametric transfer (pre-registro v2).

Full-rigor run on the principal pair, parallelized and RESUMABLE (a ~1-day job
must survive interruption). Escala (decision 15 Jul, "rigor pleno par principal"):
  * Principal pair GWO+GA @10D: 70 funcs, 51 runs, 3 MaxFES {5e3,5e4,5e5}.
  * Secondary pairs DE+GA, PSO+ACO @10D: 70 funcs, 51 runs, {5e3,5e4} (cheap
    robustness).
  * MaxFES=5e6 declared OUT OF SCOPE (~7 CPU-days/pair; see pre-registro §2).
  * 70 funcs = CEC2014 (1-30, minus F22 anomalous) + CEC2017 (1-29, F2 retired)
    + CEC2022 (1-12).

Each CELL = (pair, level, suite, fnum): 51 paired runs x 8 conditions, written to
its own JSON so re-running SKIPS finished cells. Cells run in parallel.

    python scripts/cec_harness/run_cooperative_scale.py run       # compute cells
    python scripts/cec_harness/run_cooperative_scale.py aggregate # stats + report
    N_JOBS=8 python .../run_cooperative_scale.py run

Output: results/cooperative/scale/<A><B>_<level>/<suite>_F<fnum>.json (cells)
        results/cooperative/scale/summary_<A><B>.json (aggregate)
"""

import json
import os
import sys
from multiprocessing import Pool

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from cooperative import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
DIM = 10
POP = 30
RUNS = int(os.environ.get("RUNS", "51"))
N_JOBS = int(os.environ.get("N_JOBS", "8"))
SEED0 = 5000                       # fresh seeds (pilot used 3000/4000)

# 70 problems (F22 of CEC2014 excluded: anomalous, DE err==0 in 10/10)
PROBLEMS = ([("CEC2014", f) for f in range(1, 31) if f != 22]
            + [("CEC2017", f) for f in range(1, 30)]
            + [("CEC2022", f) for f in range(1, 13)])

# experiment plan: pair -> (levels, sbs)
PLAN = {
    "GWO+GA":  ([5000, 50000, 500000], "GWO"),
    "DE+GA":   ([5000, 50000],          "GA"),
    "PSO+ACO": ([5000, 50000],          "ACO"),
}

OUT_DIR = os.path.join(_REPO_ROOT, "results", "cooperative", "scale")

CONDS = ["C2p", "C3p", "ABL", "CTRLn", "CTRLg"]
_COOP_SPEC = {"C2p": (False, "source"), "C3p": (True, "source"),
             "ABL": (True, "random"), "CTRLn": (False, "adversarial"),
             "CTRLg": (True, "adversarial")}


def _pair_specs(pair):
    a, b = pair.split("+")
    return a, b, [(a, _CLS[a], {"population_size": POP, "max_iterations": 10**9}),
                  (b, _CLS[b], {"population_size": POP, "max_iterations": 10**9})]


def _cell_path(pair, level, suite, fnum):
    a, b = pair.split("+")
    d = os.path.join(OUT_DIR, f"{a}{b}_{level}")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{suite}_F{fnum}.json")


def _compute_cell(args):
    """One cell: 51 paired runs x 8 conditions. Idempotent (skips if present)."""
    pair, level, suite, fnum = args
    path = _cell_path(pair, level, suite, fnum)
    if os.path.exists(path):
        return (path, "skip")
    a, b, specs = _pair_specs(pair)
    te = max(500, level // 10)
    cols = {f"C0_{a}": [], f"C0_{b}": [], "C1_div": [],
            "C2p": [], "C3p": [], "ABL": [], "CTRLn": [], "CTRLg": []}
    agg = {c: {"proposed": 0, "accepted": 0, "rejected": 0,
               "rolled_back": 0, "kept": 0} for c in CONDS}
    for r in range(RUNS):
        s = SEED0 + r
        cols[f"C0_{a}"].append(float(run_with_fes(
            _CLS[a], CECProblem(suite, fnum, DIM), pop_size=POP,
            max_fes=level, seed=s)))
        cols[f"C0_{b}"].append(float(run_with_fes(
            _CLS[b], CECProblem(suite, fnum, DIM), pop_size=POP,
            max_fes=level, seed=s)))
        cols["C1_div"].append(min(
            float(run_with_fes(_CLS[a], CECProblem(suite, fnum, DIM),
                               pop_size=POP, max_fes=level // 2, seed=s)),
            float(run_with_fes(_CLS[b], CECProblem(suite, fnum, DIM),
                               pop_size=POP, max_fes=level // 2, seed=s))))
        for cname in CONDS:
            gate, mode = _COOP_SPEC[cname]
            prob = FESLimitProblem(CECProblem(suite, fnum, DIM), max_fes=level)
            runner = CooperativeRunner(prob, specs, transfer_every=te,
                                       gate_enabled=gate, seed=s,
                                       transfer_mode="parametric",
                                       intent_mode=mode)
            res = runner.run()
            if res["fes_used"] != level:
                raise AssertionError((pair, level, suite, fnum, s, cname,
                                      res["fes_used"]))
            cols[cname].append(res["best_fitness"])
            for k in agg[cname]:
                agg[cname][k] += res["transfer_stats"].get(k, 0)
    out = {"pair": pair, "level": level, "suite": suite, "fnum": fnum,
           "dim": DIM, "runs": RUNS, "seed0": SEED0,
           "errors": cols, "gate_stats": agg}
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, path)
    return (path, "done")


def _all_cells():
    cells = []
    for pair, (levels, _) in PLAN.items():
        for level in levels:
            for suite, fnum in PROBLEMS:
                cells.append((pair, level, suite, fnum))
    return cells


def stage_run():
    cells = _all_cells()
    todo = [c for c in cells if not os.path.exists(_cell_path(*c))]
    print(f"[scale] {len(cells)} celdas totales, {len(todo)} pendientes "
          f"(N_JOBS={N_JOBS})")
    done = 0
    with Pool(N_JOBS) as pool:
        for path, status in pool.imap_unordered(_compute_cell, todo):
            done += 1
            if status == "done" and (done % 10 == 0 or done == len(todo)):
                print(f"[scale] {done}/{len(todo)} celdas listas "
                      f"(ultima {os.path.basename(path)})")
    print("[scale] run completo")


# --- aggregation ------------------------------------------------------------
def _paired(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a
    nz = d[d != 0]
    if nz.size == 0:
        return 1.0, 0.0
    try:
        _, p = wilcoxon(a, b, zero_method="wilcox")
    except ValueError:
        p = 1.0
    r = rankdata(np.abs(nz))
    rb = float((r[nz > 0].sum() - r[nz < 0].sum()) / r.sum())
    return float(p), rb


def _holm(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, run = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pvals[i])
        adj[i] = min(1.0, run)
    return adj


def stage_aggregate():
    for pair, (levels, sbs) in PLAN.items():
        a, b = pair.split("+")
        summary = {"pair": pair, "sbs": sbs, "dim": DIM, "runs": RUNS,
                   "levels": {}, "provenance": provenance()}
        for level in levels:
            cells = []
            for suite, fnum in PROBLEMS:
                p = _cell_path(pair, level, suite, fnum)
                if os.path.exists(p):
                    with open(p) as fh:
                        cells.append(json.load(fh))
            if not cells:
                continue
            contrasts = {
                "C2p_vs_C1div":   ("C2p", "C1_div"),
                "C3p_vs_C2p":     ("C3p", "C2p"),
                "C3p_vs_ABL":     ("C3p", "ABL"),
                "CTRLg_vs_CTRLn": ("CTRLg", "CTRLn"),
                "C3p_vs_C0SBS":   ("C3p", f"C0_{sbs}"),
            }
            res = {}
            for cname, (A, B) in contrasts.items():
                pv, rbs = [], []
                for c in cells:
                    p, rb = _paired(c["errors"][A], c["errors"][B])
                    pv.append(p); rbs.append(rb)
                holm = _holm(pv)
                wins = sum(1 for h, rb in zip(holm, rbs) if h < 0.05 and rb > 0)
                losses = sum(1 for h, rb in zip(holm, rbs) if h < 0.05 and rb < 0)
                res[cname] = {"A_sig_wins": wins, "A_sig_losses": losses,
                              "n_funcs": len(cells)}
            summary["levels"][str(level)] = {"n_funcs": len(cells),
                                             "contrasts": res}
        out_path = os.path.join(OUT_DIR, f"summary_{a}{b}.json")
        with open(out_path, "w") as fh:
            json.dump(summary, fh, indent=2)
        print(f"\n=== {pair} {DIM}D ===")
        for lv, d in summary["levels"].items():
            print(f"  MaxFES={lv} ({d['n_funcs']} funcs):")
            for cn, m in d["contrasts"].items():
                print(f"    {cn:16s}: A mejor {m['A_sig_wins']}/{m['n_funcs']}, "
                      f"peor {m['A_sig_losses']}/{m['n_funcs']}")
        print(f"  -> {out_path}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "run"
    if stage == "run":
        stage_run()
    elif stage == "aggregate":
        stage_aggregate()
    else:
        print("uso: run | aggregate")
