#!/usr/bin/env python3
"""Arm B: positive control -- does parameter modulation help PSO?

Compares PSO vs PSO+Oracle on the dynamic QC-DVRP, same held-out seeds as the
HO study. If the PSO oracle gain >> the HO oracle gain (~3%), it supports that
HO's parameter-free design leaves little room for modulation, whereas parametric
algorithms benefit more.
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


def _run(cls, params, seed):
    sim = QCDVRPSimulator(seed=seed, **SIM_CONFIG)
    return sim.run_simulation(cls, params)["fitness"]


@click.command()
@click.option("--test-seeds", default="60-69")
@click.option("--output-dir", "-o", default=None)
def main(test_seeds, output_dir):
    seeds = parse_seeds(test_seeds)
    if output_dir is None:
        output_dir = f"results/armB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    fit = {"PSO": [], "PSO+Oracle": []}
    for seed in seeds:
        fit["PSO"].append(_run(PSO, {}, seed))
        t = time.time()
        fit["PSO+Oracle"].append(_run(PSOOracle, {"oracle_lookahead": 1}, seed))
        print(f"  seed {seed}: PSO={fit['PSO'][-1]:.0f}  PSO+Oracle={fit['PSO+Oracle'][-1]:.0f}  ({time.time()-t:.0f}s)")

    base = np.array(fit["PSO"]); orc = np.array(fit["PSO+Oracle"])
    delta = orc.mean() - base.mean()
    p = stats.wilcoxon(base, orc).pvalue
    print("\n=== Arm B: PSO positive control (held-out seeds) ===")
    print(f"PSO         Z={base.mean():.0f}")
    print(f"PSO+Oracle  Z={orc.mean():.0f}  delta={delta:+.1f} ({100*delta/base.mean():+.2f}%)  "
          f"Wilcoxon p={p:.4f}  better={int((orc<base).sum())}/{len(base)}")
    print("[ref] HO oracle gain on same seeds: -3.20% (Arm C)")

    json.dump({
        "PSO_mean": float(base.mean()), "oracle_mean": float(orc.mean()),
        "delta": float(delta), "pct": float(100*delta/base.mean()),
        "wilcoxon_p": float(p), "better": int((orc < base).sum()), "n": len(base),
        "fit_raw": {k: list(map(float, v)) for k, v in fit.items()},
    }, open(os.path.join(output_dir, "armB_results.json"), "w"), indent=2)
    print(f"\nSaved: {output_dir}/armB_results.json")


if __name__ == "__main__":
    main()
