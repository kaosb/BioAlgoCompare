#!/usr/bin/env python3
"""Arm A: Oracle upper-bound study for HO parameter modulation in QC-DVRP.

Compares, on the dynamic QC-DVRP simulator (in-domain), three HO variants:
    - HO            : neutral, unmodulated (baseline)
    - HO+IL         : real trained Random Forest model (the thesis/Paper-2 model)
    - HO+Oracle     : greedy per-iteration oracle over the IL-reachable (alpha,
                      beta, gamma) grid -- the BEST any IL policy could achieve.

Decisive question: if even HO+Oracle does not beat neutral HO, then no IL model
(however good) can help -- the negative result is fundamental, not a pipeline
artifact. The oracle also logs, per decision, the achievable gain of the best
IL-reachable modulation vs. neutral.

Usage:
    python scripts/run_oracle_experiment.py --runs 3            # feasibility
    python scripts/run_oracle_experiment.py --runs 30 -o results/oracle_full
"""
import json
import os
import sys
import time
from datetime import datetime

import click
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from problems.qc_dvrp import QCDVRPSimulator
from algorithms.ho import HO
from algorithms.ho_oracle import HOOracle

IL_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "ho_il_model.pkl")

SIM_CONFIG = {
    "zone_size": 10.0, "n_dark_stores": 3, "n_vehicles": 25,
    "vehicle_capacity": 50, "poisson_lambda": 5.0,
    "time_window_min": 15.0, "time_window_max": 45.0,
    "rolling_horizon_window": 300.0, "simulation_horizon": 240.0,
    "service_time": 5.0, "avg_speed": 40.0,
    "omega_weights": (0.4, 0.4, 0.2), "max_fes": 50000, "population_size": 100,
}

ARMS = {
    "HO":        (HO,       {}),
    "HO+IL":     (HO,       {"use_il": True, "il_model_path": IL_MODEL_PATH}),
    "HO+Oracle": (HOOracle, {"oracle_lookahead": 1}),
}


@click.command()
@click.option("--runs", "-r", default=3, type=int, help="Independent runs (seeds)")
@click.option("--arms", "-a", default=None, help="Comma-separated arm subset")
@click.option("--output-dir", "-o", default=None)
def main(runs, arms, output_dir):
    arm_dict = ARMS if not arms else {a: ARMS[a] for a in arms.split(",") if a in ARMS}
    seeds = list(range(42, 42 + runs))
    if output_dir is None:
        output_dir = f"results/oracle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 64)
    print(f"Arm A: Oracle upper-bound study (QC-DVRP) | runs={runs}")
    print(f"Arms: {', '.join(arm_dict)}")
    print("=" * 64)

    results = {name: {"fitness": [], "dsr": [], "wbi": [], "time": [],
                      "oracle": []} for name in arm_dict}

    for name, (cls, params) in arm_dict.items():
        print(f"\n--- {name} ---")
        for run, seed in enumerate(seeds):
            t = time.time()
            sim = QCDVRPSimulator(seed=seed, **SIM_CONFIG)
            rr = sim.run_simulation(cls, params)
            dt = time.time() - t
            results[name]["fitness"].append(rr["fitness"])
            results[name]["dsr"].append(rr["dsr"])
            results[name]["wbi"].append(rr["wbi"])
            results[name]["time"].append(dt)
            print(f"  run {run+1}/{runs} seed={seed}  Z={rr['fitness']:.0f} "
                  f"DSR={rr['dsr']:.1f}% WBI={rr['wbi']:.1f}  ({dt:.1f}s)")

    # Summary
    print("\n" + "=" * 64)
    print(f"{'Arm':12} {'Fitness Z (mean+/-std)':24} {'DSR%':8} {'WBI':8} {'T(s)':8}")
    print("-" * 64)
    summary = {}
    for name in arm_dict:
        f = np.array(results[name]["fitness"])
        d = np.array(results[name]["dsr"]); w = np.array(results[name]["wbi"])
        tm = np.array(results[name]["time"])
        summary[name] = {
            "fitness_mean": float(f.mean()), "fitness_std": float(f.std(ddof=1) if len(f) > 1 else 0),
            "dsr_mean": float(d.mean()), "wbi_mean": float(w.mean()),
            "time_mean": float(tm.mean()), "runs": len(f),
        }
        print(f"{name:12} {f.mean():8.0f} +/- {summary[name]['fitness_std']:<10.0f} "
              f"{d.mean():7.1f} {w.mean():7.1f} {tm.mean():7.1f}")

    # Headline deltas vs neutral HO
    if "HO" in summary:
        base = summary["HO"]["fitness_mean"]
        print("\nFitness Z vs neutral HO (negative = better):")
        for name in arm_dict:
            if name == "HO":
                continue
            d = summary[name]["fitness_mean"] - base
            print(f"  {name:12} {d:+.1f}  ({100*d/base:+.2f}%)")

    with open(os.path.join(output_dir, "oracle_results.json"), "w") as fp:
        json.dump({"summary": summary, "raw": results,
                   "config": {**SIM_CONFIG, "omega_weights": list(SIM_CONFIG["omega_weights"]),
                              "seeds": seeds}}, fp, indent=2)
    print(f"\nSaved: {output_dir}/oracle_results.json")


if __name__ == "__main__":
    main()
