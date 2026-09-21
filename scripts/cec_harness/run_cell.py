"""Run a single PoC *cell*: (algorithm, CEC problem, MaxFES) x n_reps replicas.

A "cell" is one experimental condition. Each replica runs the given algorithm
on a fresh ``CECProblem`` instance under an exact MaxFES budget (via
``run_with_fes``) using a deterministic seed (``seed_base + rep``).

The cell result (per-replica best_error plus mean/median/std) is persisted as a
JSON file under ``results/cec_poc/raw/`` so that downstream ranking and stats
scripts can consume it without re-running the (expensive) optimizations.
"""

import json
import os
from typing import Optional, Type

import numpy as np

# Make the repo root importable when this module runs in a worker process.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
import sys

if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from problems.continuous.cec_problem import CECProblem, run_with_fes  # noqa: E402

RAW_DIR = os.path.join(_REPO_ROOT, "results", "cec_poc", "raw")


def cell_id(algo_name: str, suite: str, fnum: int, dim: int, max_fes: int) -> str:
    """Stable identifier / filename stem for a cell."""
    return f"{algo_name}__{suite}__F{fnum}__D{dim}__FES{max_fes}"


def run_cell(
    algo_name: str,
    algo_class: Type,
    suite: str,
    fnum: int,
    dim: int,
    max_fes: int,
    pop_size: int = 20,
    n_reps: int = 11,
    seed_base: int = 1000,
    algo_params: Optional[dict] = None,
    out_dir: str = RAW_DIR,
    overwrite: bool = True,
) -> dict:
    """Run ``n_reps`` replicas of one cell and persist/return the summary.

    Seeds are deterministic: replica ``rep`` (0-based) uses ``seed_base + rep``.
    A fresh ``CECProblem`` is built per replica so internal FES counters never
    leak across runs.
    """
    cid = cell_id(algo_name, suite, fnum, dim, max_fes)
    out_path = os.path.join(out_dir, f"{cid}.json")

    if not overwrite and os.path.exists(out_path):
        with open(out_path, "r") as fh:
            return json.load(fh)

    best_errors = []
    seeds = []
    for rep in range(n_reps):
        seed = seed_base + rep
        problem = CECProblem(suite, fnum, dim)
        err = run_with_fes(
            algo_class,
            problem,
            pop_size=pop_size,
            max_fes=max_fes,
            seed=seed,
            algo_params=algo_params,
        )
        best_errors.append(float(err))
        seeds.append(seed)

    arr = np.asarray(best_errors, dtype=float)
    result = {
        "cell_id": cid,
        "algo": algo_name,
        "suite": suite,
        "fnum": int(fnum),
        "dim": int(dim),
        "max_fes": int(max_fes),
        "pop_size": int(pop_size),
        "n_reps": int(n_reps),
        "seed_base": int(seed_base),
        "seeds": seeds,
        "best_errors": best_errors,
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)
    return result
