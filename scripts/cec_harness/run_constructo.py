"""
Constructo K — reproducible runner for the CENTRAL finding of the IL study.

Question: is the hindsight-optimal (F, CR) control for DE of LEVEL or of
SCHEDULE? We optimize the end-to-end (robust over M seeds) block schedule for
K in {1, 2, 4, 8} and compare the relative gain over the neutral baseline. If
K=1 (a single best constant) already captures essentially the same gain as
K=8 (a temporal schedule), there is NO schedule signal to learn -> dynamic IL
has no foundation for this algorithm.

This is the runner that regenerates the table in
``tesis-mia/gestion_proyecto/DISENO_IL_RIGUROSO.md`` (VEREDICTO DEL CONSTRUCTO).
It was previously run ad hoc and never committed; committing it closes the
reproducibility gap flagged by the July-2026 meta-audit (finding C2).

Usage:
    python scripts/cec_harness/run_constructo.py            # frozen config
    CMA_BUDGET=800 python .../run_constructo.py             # robustness check
    CMA_SCALE_K=1 python .../run_constructo.py              # CMA budget ~ 2K

Output: results/constructo/constructo_K.json (with provenance) + a printed table.
"""

import json
import os
import sys
import time

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from algorithms.hindsight_oracle import optimize_hindsight  # noqa: E402
from utils.provenance import provenance  # noqa: E402

# --- frozen configuration (reproduces DISENO_IL_RIGUROSO VEREDICTO) ----------
FUNCS = [("CEC2014", 1), ("CEC2014", 6), ("CEC2014", 9), ("CEC2014", 17)]
DIM = 10
BUDGET = 5000
K_VALUES = [1, 2, 4, 8]
M = 3                # robust seeds averaged inside the oracle
POP = 30
SEED = 0             # CMA-ES seed (deterministic)
# CMA budget: frozen at 400 to reproduce the original table. The audit (1b)
# noted 400 is tight for K=8 (2K=16 vars); CMA_SCALE_K scales it as a robustness
# check, and the saturation argument (K=1 already caps the margin) holds either way.
CMA_BUDGET = int(os.environ.get("CMA_BUDGET", "400"))
CMA_SCALE_K = os.environ.get("CMA_SCALE_K") == "1"

OUT_DIR = os.path.join(_REPO_ROOT, "results", "constructo")
OUT_PATH = os.path.join(OUT_DIR, "constructo_K.json")


def _cma_budget(K: int) -> int:
    # Scale ~ per-dimension budget when requested (100 evals per block-dim).
    return max(CMA_BUDGET, 100 * 2 * K) if CMA_SCALE_K else CMA_BUDGET


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    rows = {}
    print(f"[constructo] {len(FUNCS)} funcs x K in {K_VALUES}, "
          f"budget={BUDGET}, M={M}, pop={POP}, cma_scale_k={CMA_SCALE_K}")
    for suite, fnum in FUNCS:
        key = f"{suite}-F{fnum}"
        rows[key] = {}
        for K in K_VALUES:
            _, info = optimize_hindsight(
                suite, fnum, DIM, BUDGET, K=K, M=M,
                cma_budget=_cma_budget(K), pop=POP, seed=SEED)
            rows[key][f"K{K}"] = {
                "rel_gain_pct": round(100.0 * info["rel_gain"], 2),
                "best_err": info["best_err"],
                "neutral_err": info["neutral_err"],
                "F_range": info["F_range"],
                "CR_range": info["CR_range"],
                "F_traj": info["F_traj"],
                "CR_traj": info["CR_traj"],
                "cma_budget": _cma_budget(K),
            }
            print(f"  {key:16s} K={K}: gain={100*info['rel_gain']:6.2f}%  "
                  f"F_range={info['F_range']:.3f}")

    # Verdict: for each func, does the best static (K=1) match/beat the best
    # schedule (max over K>1)? "level, not schedule" iff K1 >= max(K>1) - eps.
    EPS = 0.5  # percentage points tolerance
    verdict = {}
    for key, ks in rows.items():
        k1 = ks["K1"]["rel_gain_pct"]
        kdyn = max(ks[f"K{K}"]["rel_gain_pct"] for K in K_VALUES if K > 1)
        verdict[key] = {
            "static_K1_pct": k1,
            "best_schedule_pct": kdyn,
            "dynamics_delta_pct": round(kdyn - k1, 2),
            "level_not_schedule": bool(k1 >= kdyn - EPS),
        }

    n_level = sum(v["level_not_schedule"] for v in verdict.values())
    out = {
        "config": {
            "funcs": FUNCS, "dim": DIM, "budget": BUDGET, "K_values": K_VALUES,
            "M": M, "pop": POP, "cma_seed": SEED, "cma_scale_k": CMA_SCALE_K,
            "eps_pp": EPS,
        },
        "results": rows,
        "verdict": verdict,
        "summary": {
            "n_funcs": len(FUNCS),
            "n_level_not_schedule": n_level,
            "unanimous_level": n_level == len(FUNCS),
        },
        "provenance": provenance(),
    }
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2)

    print("\n=== VEREDICTO CONSTRUCTO ===")
    print(f"{'Funcion':16s} {'K=1(static)':>12s} {'best sched':>11s} "
          f"{'delta':>7s} {'level?':>7s}")
    for key, v in verdict.items():
        print(f"{key:16s} {v['static_K1_pct']:11.1f}% {v['best_schedule_pct']:10.1f}% "
              f"{v['dynamics_delta_pct']:+6.1f} {str(v['level_not_schedule']):>7s}")
    print(f"\n{n_level}/{len(FUNCS)} funciones: NIVEL no SCHEDULE  "
          f"(unanime={n_level == len(FUNCS)})")
    print(f"written {OUT_PATH}  ({(time.time()-t0)/60:.1f} min)")


if __name__ == "__main__":
    main()
