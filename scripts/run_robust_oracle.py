#!/usr/bin/env python3
"""Validation: is the oracle's gain REAL-achievable or RNG-clairvoyant?

The greedy oracle picks the params best for the ALREADY-REALIZED random draw
(info no deployable policy has). The robust oracle picks the params best on
AVERAGE over n independent stochastic continuations -- the ceiling a feature-based
policy could aspire to. If robust gain << greedy gain, the headline "~3% signal"
is mostly clairvoyance, and IL's failure to capture it is expected (not a model
deficiency). Same QC-DVRP config and seeds as the original oracle run.
"""
import json
import os
import sys
import time
from datetime import datetime

import click
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from problems.qc_dvrp import QCDVRPSimulator
from algorithms.ho import HO
from algorithms.ho_oracle import HOOracle

SIM_CONFIG = {
    "zone_size": 10.0, "n_dark_stores": 3, "n_vehicles": 25,
    "vehicle_capacity": 50, "poisson_lambda": 5.0,
    "time_window_min": 15.0, "time_window_max": 45.0,
    "rolling_horizon_window": 300.0, "simulation_horizon": 240.0,
    "service_time": 5.0, "avg_speed": 40.0,
    "omega_weights": (0.4, 0.4, 0.2), "max_fes": 50000, "population_size": 100,
}


def parse_seeds(spec):
    a, b = spec.split("-")
    return list(range(int(a), int(b) + 1))


def run(cls, params, seed):
    return QCDVRPSimulator(seed=seed, **SIM_CONFIG).run_simulation(cls, params)["fitness"]


@click.command()
@click.option("--test-seeds", default="60-64")
@click.option("--k", default=3, type=int, help="robust eval samples")
@click.option("--output-dir", "-o", default=None)
def main(test_seeds, k, output_dir):
    seeds = parse_seeds(test_seeds)
    if output_dir is None:
        output_dir = f"results/robustoracle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    arms = {
        "HO": (HO, {}),
        "Oracle_greedy": (HOOracle, {"oracle_lookahead": 1, "n_eval_samples": 1}),
        f"Oracle_robust_k{k}": (HOOracle, {"oracle_lookahead": 1, "n_eval_samples": k}),
    }
    fit = {a: [] for a in arms}
    for a, (cls, params) in arms.items():
        for s in seeds:
            t = time.time()
            fit[a].append(run(cls, params, s))
            print(f"  {a:18} seed {s}: Z={fit[a][-1]:.0f}  ({time.time()-t:.0f}s)")

    ho = np.array(fit["HO"])
    print("\n=== Clairvoyance check (vs HO, same seeds) ===")
    out = {"HO_mean": float(ho.mean()), "n": len(ho), "seeds": seeds, "k": k}
    for a in arms:
        if a == "HO":
            continue
        v = np.array(fit[a]); d = v.mean() - ho.mean()
        p = stats.wilcoxon(ho, v).pvalue if len(ho) > 1 else float("nan")
        print(f"{a:18} Z={v.mean():.0f}  delta={d:+.1f} ({100*d/ho.mean():+.2f}%)  p={p:.4f}  mejor={int((v<ho).sum())}/{len(ho)}")
        out[a] = {"mean": float(v.mean()), "pct": float(100*d/ho.mean()),
                  "wilcoxon_p": float(p), "better": int((v < ho).sum())}
    out["fit_raw"] = {a: list(map(float, v)) for a, v in fit.items()}
    json.dump(out, open(os.path.join(output_dir, "robustoracle_results.json"), "w"), indent=2)
    print(f"\nSaved: {output_dir}/robustoracle_results.json")


if __name__ == "__main__":
    main()
