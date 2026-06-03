#!/usr/bin/env python3
"""Is PSO's parameter-modulation headroom REAL or clairvoyant?

Same clairvoyance test as HO, but on PSO (parametric). If PSO's robust oracle gain
is substantial (unlike HO's ~0.3%), then IL for PSO parameter control is a viable
path to a genuine positive result; if it also collapses, the whole IL-for-VRP
parameter-control idea is futile in this setting.
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
from algorithms.pso import PSO
from algorithms.pso_oracle import PSOOracle

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
@click.option("--k", default=3, type=int)
@click.option("--output-dir", "-o", default=None)
def main(test_seeds, k, output_dir):
    seeds = parse_seeds(test_seeds)
    if output_dir is None:
        output_dir = f"results/robustpso_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    arms = {
        "PSO": (PSO, {}),
        "PSO_Oracle_greedy": (PSOOracle, {"oracle_lookahead": 1, "n_eval_samples": 1}),
        f"PSO_Oracle_robust_k{k}": (PSOOracle, {"oracle_lookahead": 1, "n_eval_samples": k}),
    }
    fit = {a: [] for a in arms}
    for a, (cls, params) in arms.items():
        for s in seeds:
            t = time.time()
            fit[a].append(run(cls, params, s))
            print(f"  {a:24} seed {s}: Z={fit[a][-1]:.0f}  ({time.time()-t:.0f}s)")
    base = np.array(fit["PSO"])
    print("\n=== PSO clairvoyance check (vs PSO) ===")
    out = {"PSO_mean": float(base.mean()), "n": len(base), "k": k}
    for a in arms:
        if a == "PSO":
            continue
        v = np.array(fit[a]); d = v.mean() - base.mean()
        p = stats.wilcoxon(base, v).pvalue if len(base) > 1 else float("nan")
        print(f"{a:24} Z={v.mean():.0f}  {100*d/base.mean():+.2f}%  p={p:.4f}  mejor={int((v<base).sum())}/{len(base)}")
        out[a] = {"mean": float(v.mean()), "pct": float(100*d/base.mean()),
                  "wilcoxon_p": float(p), "better": int((v < base).sum())}
    out["fit_raw"] = {a: list(map(float, v)) for a, v in fit.items()}
    json.dump(out, open(os.path.join(output_dir, "robustpso_results.json"), "w"), indent=2)
    print(f"\nSaved: {output_dir}/robustpso_results.json")


if __name__ == "__main__":
    main()
