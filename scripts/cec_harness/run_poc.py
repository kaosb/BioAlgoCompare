"""Reduced Proof-of-Concept harness for CEC continuous benchmarks.

PoC grid:
    suite  = CEC2022
    funcs  = F1..F12
    dims   = {10, 20}
    MaxFES = {5000, 50000}
    reps   = 11
    algos  = {HO, PSO, GA, GWO}

Parallelism is at the *cell* level (one cell = one algo x problem x MaxFES,
i.e. n_reps replicas run sequentially inside the worker) using a
multiprocessing pool with ``n_jobs`` workers.

Outputs (under results/cec_poc/):
    raw/*.json          one summary per cell (written by run_cell)
    rankings.json       4 aggregated avg-rank tables (2 dims x 2 MaxFES)
    friedman_shaffer.json   Friedman omnibus + Shaffer post-hoc per config
    wilcoxon_bew.json   HO-vs-{PSO,GA,GWO} better/equal/worse per config
    poc_summary.json    everything + wall-clock
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

from scripts.cec_harness.run_cell import run_cell, RAW_DIR  # noqa: E402
from scripts.cec_harness.build_rankings import build_rankings, filter_cells  # noqa: E402
from scripts.cec_harness import stats as st  # noqa: E402

from algorithms.ho import HO  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.aco import ACO  # noqa: E402

OUT_DIR = os.path.join(_REPO_ROOT, "results", "cec_poc")

# --- PoC configuration ----------------------------------------------------
SUITE = "CEC2022"
FUNCS = list(range(1, 13))          # F1..F12
DIMS = [10, 20]
MAXFES = [5000, 50000]
N_REPS = 11
POP_SIZE = 20
SEED_BASE = 1000
N_JOBS = 8

# Algorithm registry (name -> class). Worker resolves the class by name to keep
# pickled payloads small and robust across the process boundary.
ALGOS = {"HO": HO, "PSO": PSO, "GA": GA, "GWO": GWO, "DE": DE, "ACO": ACO}
REFERENCE = "HO"
COMPETITORS = ["PSO", "GA", "GWO", "DE", "ACO"]


def _worker(args):
    """Module-level worker (picklable) running a single cell."""
    algo_name, suite, fnum, dim, max_fes = args
    algo_class = ALGOS[algo_name]
    res = run_cell(
        algo_name=algo_name,
        algo_class=algo_class,
        suite=suite,
        fnum=fnum,
        dim=dim,
        max_fes=max_fes,
        pop_size=POP_SIZE,
        n_reps=N_REPS,
        seed_base=SEED_BASE,
        out_dir=RAW_DIR,
        overwrite=True,
    )
    return res


def build_cell_grid():
    grid = []
    for algo_name in ALGOS:
        for dim in DIMS:
            for max_fes in MAXFES:
                for fnum in FUNCS:
                    grid.append((algo_name, SUITE, fnum, dim, max_fes))
    return grid


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    grid = build_cell_grid()
    n_cells = len(grid)
    print(f"[PoC] {n_cells} cells | {N_REPS} reps each | n_jobs={N_JOBS}")
    print(f"[PoC] grid: {SUITE} F1..F12 x {DIMS} dims x {MAXFES} MaxFES x {list(ALGOS)}")

    t0 = time.time()
    with Pool(processes=N_JOBS) as pool:
        cells = []
        done = 0
        for res in pool.imap_unordered(_worker, grid):
            cells.append(res)
            done += 1
            if done % 10 == 0 or done == n_cells:
                print(f"[PoC] {done}/{n_cells} cells done "
                      f"({time.time() - t0:.0f}s elapsed)")
    wall = time.time() - t0
    print(f"[PoC] all cells done in {wall:.1f}s")

    # --- Rankings: one aggregated table per (dim, max_fes) config ---------
    rankings = {}
    for dim in DIMS:
        for max_fes in MAXFES:
            sub = filter_cells(cells, dim, max_fes)
            rk = build_rankings(sub)
            key = f"D{dim}_FES{max_fes}"
            rankings[key] = {
                "avg_ranks": rk["avg_ranks"],
                "n_problems": len(rk["problems"]),
            }

    # --- Friedman + Shaffer per config ------------------------------------
    friedman_shaffer = {}
    for dim in DIMS:
        for max_fes in MAXFES:
            sub = filter_cells(cells, dim, max_fes)
            rk = build_rankings(sub)
            algos = rk["algos"]
            problems = rk["problems"]
            mat = np.array(
                [[rk["mean_perf"][p][a] for a in algos] for p in problems],
                dtype=float,
            )
            fr = st.friedman_test(mat)
            sh = st.shaffer_posthoc(mat, algos)
            key = f"D{dim}_FES{max_fes}"
            friedman_shaffer[key] = {
                "algos": algos,
                "friedman": fr,
                "shaffer": sh,
            }

    # --- Wilcoxon B/E/W HO vs competitors per config ----------------------
    wilcoxon_table = {}
    for dim in DIMS:
        for max_fes in MAXFES:
            key = f"D{dim}_FES{max_fes}"
            wilcoxon_table[key] = st.wilcoxon_bew(
                cells, REFERENCE, COMPETITORS, dim, max_fes
            )

    # --- Persist ----------------------------------------------------------
    with open(os.path.join(OUT_DIR, "rankings.json"), "w") as fh:
        json.dump(rankings, fh, indent=2)
    with open(os.path.join(OUT_DIR, "friedman_shaffer.json"), "w") as fh:
        json.dump(friedman_shaffer, fh, indent=2)
    with open(os.path.join(OUT_DIR, "wilcoxon_bew.json"), "w") as fh:
        json.dump(wilcoxon_table, fh, indent=2)

    summary = {
        "config": {
            "suite": SUITE, "funcs": FUNCS, "dims": DIMS, "maxfes": MAXFES,
            "n_reps": N_REPS, "pop_size": POP_SIZE, "n_jobs": N_JOBS,
            "algos": list(ALGOS), "n_cells": n_cells,
        },
        "wall_clock_s": wall,
        "rankings": rankings,
        "friedman_shaffer": friedman_shaffer,
        "wilcoxon_bew": wilcoxon_table,
    }
    with open(os.path.join(OUT_DIR, "poc_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    _print_report(rankings, friedman_shaffer, wilcoxon_table, wall)
    return summary


def _print_report(rankings, friedman_shaffer, wilcoxon_table, wall):
    print("\n" + "=" * 70)
    print("CEC PoC REPORT")
    print("=" * 70)

    print("\n--- AVERAGE RANKS (lower = better) ---")
    for key, rk in rankings.items():
        ordered = sorted(rk["avg_ranks"].items(), key=lambda kv: kv[1])
        line = ", ".join(f"{a}={r:.3f}" for a, r in ordered)
        print(f"  {key} (n={rk['n_problems']}): {line}")

    print("\n--- FRIEDMAN OMNIBUS ---")
    for key, fs in friedman_shaffer.items():
        fr = fs["friedman"]
        print(f"  {key}: chi2={fr['statistic']:.3f}, df={fr['df']}, "
              f"p={fr['p_value']:.3e}, N={fr['n_problems']}")

    print("\n--- SHAFFER POST-HOC (significant pairs, p<0.05) ---")
    for key, fs in friedman_shaffer.items():
        sig = [pp for pp in fs["shaffer"]["pairs"] if pp["significant"]]
        print(f"  {key}: {len(sig)} significant pairs")
        for pp in sorted(sig, key=lambda d: d["p_shaffer"]):
            print(f"      {pp['a']} vs {pp['b']}: "
                  f"p_shaffer={pp['p_shaffer']:.3e} (z={pp['z']:.2f})")

    print("\n--- WILCOXON HO vs competitors (Better/Equal/Worse) ---")
    for key, tbl in wilcoxon_table.items():
        print(f"  {key}:")
        for comp, r in tbl.items():
            print(f"      HO vs {comp}: B={r['better']} E={r['equal']} "
                  f"W={r['worse']} (n={r['n_problems']})")

    print(f"\n--- WALL-CLOCK: {wall:.1f}s ({wall/60:.2f} min) ---")
    print("=" * 70)


if __name__ == "__main__":
    main()
