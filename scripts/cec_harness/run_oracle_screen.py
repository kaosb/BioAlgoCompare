"""Oracle screening: achievable parameter-modulation ceiling per algorithm.

Diagnostic, NOT the headline comparison (see tesis-mia
gestion_proyecto/AUDITORIA_PERTINENCIA_ORACULO.md). Runs the robust oracle on a
small CEC subset for each algorithm whose control parameters are real and
multiplicatively modulable, to answer:

    "Which algorithms have a learnable margin (ceiling > 0), and how much?"

For each (algorithm, function, dim) it reports:
    * relative_ceiling (robust)  -- the defensible IL upper bound
    * relative_ceiling (greedy)  -- clairvoyant, reported only as EVPI
    * EVPI = greedy - robust     -- how much of the apparent ceiling was just
                                    RNG clairvoyance (must be small for the
                                    robust number to be trustworthy)

Runs on the RAW CECProblem (no FES wrapper): these diagnostic evaluations are
deliberately NOT charged against any MaxFES comparison budget.
"""

import json
import os
import sys
import time

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from problems.continuous.cec_problem import CECProblem  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.ho import HO  # noqa: E402
from algorithms.de_oracle import DEOracle  # noqa: E402
from algorithms.aco_oracle import ACOOracle  # noqa: E402
from algorithms.pso_oracle import PSOOracle  # noqa: E402
from algorithms.gwo_oracle import GWOOracle  # noqa: E402
from algorithms.ga_oracle import GAOracle  # noqa: E402
from algorithms.ho_oracle import HOOracle  # noqa: E402

OUT_DIR = os.path.join(_REPO_ROOT, "results", "oracle_screen")

# Fixed-parameter classical algorithms = the real IL candidates (per the
# positioning doc: modern adaptive DEs already self-tune, so little IL margin).
# HO kept as an invented-parameter reference.
ORACLES = {
    "PSO": (PSOOracle, PSO, "real (w, c1, c2) -- Kennedy-Eberhart (FIXED)"),
    "GWO": (GWOOracle, GWO, "real (a coeff) -- Mirjalili (FIXED schedule)"),
    "DE":  (DEOracle,  DE,  "real (F, CR) -- Storn-Price (FIXED)"),
    "ACO": (ACOOracle, ACO, "real (xi, q) -- Socha-Dorigo (FIXED)"),
    "GA":  (GAOracle,  GA,  "real (crossover, mutation rate) -- RKGA (FIXED)"),
    "HO":  (HOOracle,  HO,  "INVENTED (alpha, beta, gamma) -- not in Amiri 2024"),
}

# Screening suite/functions. IMPORTANT (audit finding C2): screening must be
# performed on TRAIN functions only (CEC2014 = the demo suite), never on the
# held-out test suites, so the "a-priori" claim stays clean. Representative
# CEC2014 subset: F1 unimodal (rotated), F4 multimodal, F17 hybrid, F23
# composition. Override via env SCREEN_SUITE / SCREEN_FUNCS.
SUITE = os.environ.get("SCREEN_SUITE", "CEC2014")
_f = os.environ.get("SCREEN_FUNCS")
FUNCS = [int(x) for x in _f.split(",")] if _f else [1, 4, 17, 23]
DIMS = [10]
POP = 20
ITERS = 20
N_EVAL_ROBUST = 5
SEEDS = [42, 7, 123]  # multi-seed to tame single-trajectory variance


def _one_seed(oracle_cls, base_cls, fnum, dim, seed):
    """Single seed: per-step robust headroom + diagnostic + end-to-end ceiling.

    The oracle's rollout evaluations are diagnostic only (raw problem, not
    FES-charged). Two views are returned:
      * headroom -- mean over steps of max(0, gain)/neutral: how much optimal
        robust modulation COULD help per step (the policy keeps neutral
        otherwise). This is the stable ceiling proxy (matches the prior HO
        analysis) and is non-negative by construction.
      * end_ceiling -- end-to-end (neutral_final - mod_final)/neutral_final of
        the committed trajectory. HIGH VARIANCE at a single seed; reported only
        averaged across seeds, with std, as a secondary view.
    """
    prob = CECProblem(SUITE, fnum, dim)
    oracle = oracle_cls(problem=prob, population_size=POP, max_iterations=ITERS,
                        seed=seed, n_eval_samples=N_EVAL_ROBUST,
                        oracle_lookahead=1)
    oracle.execute()
    mod_final = float(oracle.best_solution.fitness())

    base = base_cls(problem=prob, population_size=POP, max_iterations=ITERS,
                    seed=seed, use_il=False)
    base.execute()
    neutral_final = float(base.best_solution.fitness())
    end_ceiling = ((neutral_final - mod_final) / neutral_final
                   if neutral_final > 1e-12 else 0.0)

    log = oracle.oracle_log
    if log:
        gains = np.array([r["gain_vs_neutral"] for r in log], dtype=float)
        neutral = np.array([r["neutral_fit"] for r in log], dtype=float)
        evpi = np.array([r.get("evpi", 0.0) for r in log], dtype=float)
        denom = np.where(neutral > 1e-12, neutral, np.nan)
        headroom = float(np.nanmean(np.maximum(0.0, gains) / denom))
        frac_help = float((gains > 1e-9).mean())
        rel_evpi = float(np.nanmean(np.maximum(0.0, evpi) / denom))
    else:
        headroom = frac_help = rel_evpi = 0.0
    return dict(headroom=headroom, frac_help=frac_help, rel_evpi=rel_evpi,
                end_ceiling=float(end_ceiling))


def _run_cell(oracle_cls, base_cls, fnum, dim):
    """Average a cell over SEEDS to tame single-trajectory variance."""
    runs = [_one_seed(oracle_cls, base_cls, fnum, dim, s) for s in SEEDS]
    agg = {k: float(np.mean([r[k] for r in runs])) for k in runs[0]}
    agg["end_ceiling_std"] = float(np.std([r["end_ceiling"] for r in runs]))
    return agg


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    records = []
    print("=" * 72)
    print("ORACLE SCREEN -- achievable parameter-modulation ceiling")
    print(f"{SUITE} F{FUNCS} x {DIMS}D | pop={POP} iters={ITERS} | "
          f"robust n_eval={N_EVAL_ROBUST} | seeds={SEEDS}")
    print("=" * 72)

    for name, (oracle_cls, base_cls, provenance) in ORACLES.items():
        heads, helps, evpis, ends = [], [], [], []
        for dim in DIMS:
            for fnum in FUNCS:
                s = _run_cell(oracle_cls, base_cls, fnum, dim)
                heads.append(s["headroom"])
                helps.append(s["frac_help"])
                evpis.append(s["rel_evpi"])
                ends.append(s["end_ceiling"])
                records.append({"algo": name, "func": fnum, "dim": dim, **s})
        mh = float(np.mean(heads))
        print(f"\n{name}  [{provenance}]")
        print(f"  mean per-step ROBUST headroom = {mh*100:+.2f}%   "
              f"(per-func: {', '.join(f'{h*100:.1f}' for h in heads)})")
        print(f"  mean frac iters modulation helps = {np.mean(helps)*100:.0f}%")
        print(f"  median end-to-end ceiling (noisy)= {np.median(ends)*100:+.1f}%"
              f"  [high-variance, see JSON]")
        print(f"  mean EVPI (clairvoyance gap)     = {np.mean(evpis)*100:+.2f}%")

    wall = time.time() - t0
    out = {
        "config": {"funcs": FUNCS, "dims": DIMS, "pop": POP, "iters": ITERS,
                   "n_eval_robust": N_EVAL_ROBUST, "seeds": SEEDS},
        "records": records, "wall_clock_s": wall,
    }
    out_name = f"oracle_screen_{SUITE.lower()}.json" if SUITE != "CEC2022" else "oracle_screen.json"
    with open(os.path.join(OUT_DIR, out_name), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n--- wall-clock {wall:.1f}s | saved {OUT_DIR}/{out_name} ---")
    print("INTERPRETATION: robust ceiling > 0 => learnable margin (IL may help).")
    print("                robust ~0 => algorithm robust to modulation (IL cannot).")
    print("                small EVPI => the robust number is not clairvoyant.")
    return out


if __name__ == "__main__":
    main()
