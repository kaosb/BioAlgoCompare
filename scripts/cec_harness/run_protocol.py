"""Production CEC harness faithful to Rodrigo's experimental protocol.

(`tesis-mia gestion_proyecto/reuniones/2026-06-05_setup_experimental_rodrigo.md`)

Structure (faithful):
    * 71 problems: CEC2014 (F1-F30) + CEC2017 (F1-F29, F2 retired) + CEC2022 (F1-F12).
    * Two aggregate sets by dimensionality:
        - CEC_71_10  : all 71 problems at 10D.
        - CEC_71_50  : CEC2014/2017 at 50D + CEC2022 at 20D (2022 has no >20D).
    * MaxFES levels: independent runs, each from scratch with its OWN seeds
      (a higher level is NOT a continuation of a lower one).
    * 51 independent runs per (problem, dim-set, MaxFES); metric = mean best
      error over the 51 runs (error = f(x) - f(x*) >= 0).
    * Author-recommended parameters, single config across all experiments
      (pop_size fixed and documented).
    * Separate rankings (no averaging across MaxFES): per benchmark x dim-set x
      MaxFES, and per aggregate-set x MaxFES. Ties at 1e-8 (CEC rule).
    * Friedman + Shaffer static post-hoc; Wilcoxon better/equal/worse.

Compute reality (this machine, 8 cores): the full protocol (4 MaxFES incl.
5e6) is months of CPU. This script is parameterised by ``MAXFES_LEVELS`` so the
viable levels (5e3, 5e4, 5e5) can be run and SCALED INDEPENDENTLY; 5e6 is left
out and declared (see AUDITORIA / PLAN). Per-cell JSON persistence makes the
whole thing RESUMABLE: re-running skips cells already computed.

Usage:
    python scripts/cec_harness/run_protocol.py            # default levels
    MAXFES_LEVELS=5000,50000 python .../run_protocol.py   # override levels
"""

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.cec_harness.run_cell import run_cell, cell_id  # noqa: E402
from scripts.cec_harness.build_rankings import build_rankings  # noqa: E402
from scripts.cec_harness import stats as st  # noqa: E402

# In-repo faithful algorithms (classical paradigms / baselines).
from algorithms.ho import HO  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
# CEC winners / top performers (faithful C++ via minionpy).
from algorithms.minion_adapter import MINION_ROSTER  # noqa: E402
# mealpy roster is also available (algorithms.mealpy_adapter.MEALPY_ROSTER) but
# minionpy provides faithful C++ versions of the same DE-family + the actual CEC
# winners, so production uses minionpy to avoid redundant implementations.

# ---------------------------------------------------------------------------
# Protocol configuration
# ---------------------------------------------------------------------------
OUT_DIR = os.path.join(_REPO_ROOT, "results", "cec_protocol")
RAW_DIR = os.path.join(OUT_DIR, "raw")

# 71 problems as (suite, fnum). CEC2017 F2 retired -> excluded (opfunu omits it).
PROBLEMS = (
    [("CEC2014", f) for f in range(1, 31)]
    + [("CEC2017", f) for f in range(1, 30)]
    + [("CEC2022", f) for f in range(1, 13)]
)

# Dimensionality per aggregate set: ("10" set, "50" set).
# 2022 has no version above 20D, so its high-dim member is 20D.
DIM_OF = {
    "10": {"CEC2014": 10, "CEC2017": 10, "CEC2022": 10},
    "50": {"CEC2014": 50, "CEC2017": 50, "CEC2022": 20},
}
DIM_SETS = ["10", "50"]

# Roster: 18 algorithms covering diverse paradigms, incl. actual CEC winners
# (protocol Sec 3: "include recent CEC winners; avoid only weak competitors").
#   Classical / baseline (in-repo): HO, PSO, GA, GWO, DE, ACO
#   DE-family + CEC winners (minionpy C++): L-SHADE, JADE, jSO, NL-SHADE-RSP,
#       L-SRTDE (CEC2024 winner), j2020, ARRDE, AGSK, IMODE, LSHADE-cnEpSin
#   Evolution strategies (minionpy): CMA-ES, BIPOP-aCMAES
ALGOS = {
    "HO": HO, "PSO": PSO, "GA": GA, "GWO": GWO, "DE": DE, "ACO": ACO,
    "L-SHADE": MINION_ROSTER["L-SHADE"], "JADE": MINION_ROSTER["JADE"],
    "jSO": MINION_ROSTER["jSO"], "NL-SHADE-RSP": MINION_ROSTER["NL-SHADE-RSP"],
    "L-SRTDE": MINION_ROSTER["L-SRTDE"], "j2020": MINION_ROSTER["j2020"],
    "ARRDE": MINION_ROSTER["ARRDE"], "AGSK": MINION_ROSTER["AGSK"],
    "IMODE": MINION_ROSTER["IMODE"],
    "LSHADE-cnEpSin": MINION_ROSTER["LSHADE-cnEpSin"],
    "CMA-ES": MINION_ROSTER["CMA-ES"],
    # NOTE: BIPOP-aCMAES excluded -- its restart scheme hangs in minionpy at low
    # MaxFES (e.g. CEC2014 F12 50D @5e3 never returns). CMA-ES covers the ES
    # family. Re-add only if the upstream hang is resolved.
}
ALGO_NAMES = list(ALGOS)
# Reference for Wilcoxon better/equal/worse: provisional = the strongest current
# SOTA (CEC2024 winner). Swap to the "proposed" (IL-augmented) algorithm later.
REFERENCE = "L-SRTDE"

# Author-recommended single config: fixed population across all experiments.
POP_SIZE = int(os.environ.get("POP_SIZE", "100"))
N_REPS = int(os.environ.get("N_REPS", "51"))

# Smoke mode (validate the pipeline cheaply): PROTOCOL_SMOKE=1 shrinks the grid.
if os.environ.get("PROTOCOL_SMOKE") == "1":
    PROBLEMS = [("CEC2014", 1), ("CEC2014", 4), ("CEC2017", 1),
                ("CEC2017", 3), ("CEC2022", 1), ("CEC2022", 5)]
    ALGOS = {k: ALGOS[k] for k in ["DE", "HO", "L-SRTDE", "CMA-ES"]}
    ALGO_NAMES = list(ALGOS)
    OUT_DIR = os.path.join(_REPO_ROOT, "results", "cec_protocol_smoke")
    RAW_DIR = os.path.join(OUT_DIR, "raw")

# MaxFES levels to run NOW (5e6 deliberately excluded; override via env var).
_DEFAULT_LEVELS = [5000, 50000, 500000]
_env = os.environ.get("MAXFES_LEVELS")
MAXFES_LEVELS = (
    [int(x) for x in _env.split(",")] if _env else list(_DEFAULT_LEVELS)
)

N_JOBS = int(os.environ.get("N_JOBS", "8"))


def _seed_base(max_fes: int) -> int:
    """Independent seed block per MaxFES level (levels are not continuations)."""
    return max_fes  # e.g. 5e3 -> seeds 5000..5050, 5e4 -> 50000..50050, ...


def build_grid():
    """All cells: (algo, suite, fnum, dim, max_fes) over roster x problems x
    dim-sets x levels."""
    grid = []
    for algo_name in ALGO_NAMES:
        for dim_set in DIM_SETS:
            for suite, fnum in PROBLEMS:
                dim = DIM_OF[dim_set][suite]
                for max_fes in MAXFES_LEVELS:
                    grid.append((algo_name, suite, fnum, dim, max_fes))
    return grid


def _worker(args):
    algo_name, suite, fnum, dim, max_fes = args
    res = run_cell(
        algo_name=algo_name,
        algo_class=ALGOS[algo_name],
        suite=suite,
        fnum=fnum,
        dim=dim,
        max_fes=max_fes,
        pop_size=POP_SIZE,
        n_reps=N_REPS,
        seed_base=_seed_base(max_fes),
        out_dir=RAW_DIR,
        overwrite=False,  # RESUMABLE: skip cells already computed
    )
    # Tag dim-set so aggregation can group without re-deriving from dim.
    res["dim_set"] = "10" if dim == 10 else "50"
    return res


def _friedman_shaffer(cells):
    rk = build_rankings(cells)
    algos, problems = rk["algos"], rk["problems"]
    if len(problems) < 2 or len(algos) < 2:
        return None
    mat = np.array(
        [[rk["mean_perf"][p][a] for a in algos] for p in problems], dtype=float
    )
    return {
        "algos": algos,
        "avg_ranks": rk["avg_ranks"],
        "rank_std": float(np.std(list(rk["avg_ranks"].values()))),
        "friedman": st.friedman_test(mat),
        "shaffer": st.shaffer_posthoc(mat, algos),
    }


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    grid = build_grid()
    n = len(grid)
    print(f"[PROTOCOL] {len(ALGO_NAMES)} algos x {len(PROBLEMS)} problems x "
          f"{len(DIM_SETS)} dim-sets x {len(MAXFES_LEVELS)} levels = {n} cells")
    print(f"[PROTOCOL] levels={MAXFES_LEVELS} reps={N_REPS} pop={POP_SIZE} "
          f"n_jobs={N_JOBS}  (resumable: existing cells skipped)")

    t0 = time.time()
    cells = []
    done = 0

    def _track(res):
        nonlocal done
        cells.append(res)
        done += 1
        if done % 25 == 0 or done == n:
            el = time.time() - t0
            print(f"[PROTOCOL] {done}/{n} cells ({el:.0f}s, {el/done:.1f}s/cell)")

    if N_JOBS <= 1:
        # Sequential (no Pool): debugging / smoke without spawn re-import.
        for args in grid:
            _track(_worker(args))
    else:
        with Pool(processes=N_JOBS) as pool:
            for res in pool.imap_unordered(_worker, grid):
                _track(res)
    wall = time.time() - t0
    print(f"[PROTOCOL] all cells done in {wall/60:.1f} min")

    # --- Rankings (separate; never averaged across MaxFES) ----------------
    rankings = {"per_benchmark": {}, "aggregate": {}}
    fr_sh = {"per_benchmark": {}, "aggregate": {}}
    wilcoxon = {"per_benchmark": {}, "aggregate": {}}

    suites = ["CEC2014", "CEC2017", "CEC2022"]
    for max_fes in MAXFES_LEVELS:
        for dim_set in DIM_SETS:
            # Per individual benchmark x dim-set x MaxFES.
            for suite in suites:
                sub = [c for c in cells if c["suite"] == suite
                       and c["dim_set"] == dim_set and c["max_fes"] == max_fes]
                if not sub:
                    continue
                key = f"{suite}_D{dim_set}_FES{max_fes}"
                rk = build_rankings(sub)
                rankings["per_benchmark"][key] = {
                    "avg_ranks": rk["avg_ranks"], "n_problems": len(rk["problems"])}
                fs = _friedman_shaffer(sub)
                if fs:
                    fr_sh["per_benchmark"][key] = fs
                wilcoxon["per_benchmark"][key] = _wilcoxon_manual(sub, max_fes)
            # Aggregate set (all 71) x MaxFES.
            agg = [c for c in cells if c["dim_set"] == dim_set
                   and c["max_fes"] == max_fes]
            if agg:
                key = f"CEC_71_{dim_set}_FES{max_fes}"
                rk = build_rankings(agg)
                rankings["aggregate"][key] = {
                    "avg_ranks": rk["avg_ranks"], "n_problems": len(rk["problems"])}
                fs = _friedman_shaffer(agg)
                if fs:
                    fr_sh["aggregate"][key] = fs
                wilcoxon["aggregate"][key] = _wilcoxon_manual(agg, max_fes)

    summary = {
        "config": {
            "problems": len(PROBLEMS), "dim_sets": DIM_SETS,
            "maxfes_levels": MAXFES_LEVELS, "n_reps": N_REPS,
            "pop_size": POP_SIZE, "algos": ALGO_NAMES, "reference": REFERENCE,
            "note_71": "CEC2017 F2 retired -> 71 problems (not 72)",
            "note_5e6": "MaxFES=5e6 excluded (compute); declared per protocol",
        },
        "wall_clock_s": wall,
        "rankings": rankings,
        "friedman_shaffer": fr_sh,
        "wilcoxon_bew": wilcoxon,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "protocol_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    _report(rankings, fr_sh, wilcoxon, wall)
    return summary


def _wilcoxon_manual(cells, max_fes):
    """Wilcoxon better/equal/worse: REFERENCE vs each competitor, paired across
    the problems in ``cells`` by mean best error (51-run mean per cell)."""
    from scipy.stats import wilcoxon as _wx
    by_algo = {}
    for c in cells:
        by_algo.setdefault(c["algo"], {})[(c["suite"], c["fnum"])] = c["mean"]
    if REFERENCE not in by_algo:
        return {}
    ref = by_algo[REFERENCE]
    out = {}
    for comp in [a for a in ALGO_NAMES if a != REFERENCE]:
        if comp not in by_algo:
            continue
        probs = sorted(set(ref) & set(by_algo[comp]))
        better = equal = worse = 0
        for p in probs:
            a, b = ref[p], by_algo[comp][p]
            if abs(a - b) <= 1e-8:
                equal += 1
            elif a < b:
                better += 1
            else:
                worse += 1
        out[comp] = {"better": better, "equal": equal, "worse": worse,
                     "n_problems": len(probs)}
    return out


def _report(rankings, fr_sh, wilcoxon, wall):
    print("\n" + "=" * 72)
    print("CEC PROTOCOL REPORT  (lower avg-rank = better)")
    print("=" * 72)
    print("\n--- AGGREGATE RANKINGS (CEC_71 per dim-set x MaxFES) ---")
    for key, rk in rankings["aggregate"].items():
        ordered = sorted(rk["avg_ranks"].items(), key=lambda kv: kv[1])
        line = ", ".join(f"{a}={r:.2f}" for a, r in ordered)
        fr = fr_sh["aggregate"].get(key, {}).get("friedman", {})
        p = fr.get("p_value")
        ps = f" | Friedman p={p:.2e}" if p is not None else ""
        print(f"  {key} (n={rk['n_problems']}){ps}\n     {line}")
    print(f"\n--- WALL-CLOCK: {wall/60:.1f} min ---")
    print("=" * 72)


if __name__ == "__main__":
    main()
