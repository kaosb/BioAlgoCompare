#!/usr/bin/env python3
"""Fair test: does HO+IL help when HO has a REAL optimization trajectory?

The Paper-2 dynamic config gives HO only ~3 iterations per sub-VRP solve
(50K FES / 144 sub-problems / 100 pop), leaving no trajectory for per-iteration
adaptive control. Here we raise the FES budget so each solve runs ~N iterations,
train an IN-DOMAIN IL model (oracle demos in this regime), and compare HO vs
HO+IL directly (paired Wilcoxon).

Usage:
  python scripts/run_fairtest_traj.py --iters 25 --train-seeds 42-43 --test-seeds 60-64
"""
import json
import os
import sys
import time
from datetime import datetime

import click
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from problems.qc_dvrp import QCDVRPSimulator
from algorithms.ho import HO
from algorithms.ho_oracle import HOOracle
from utils.train_il_simple import SimpleILModel

BASE = {
    "zone_size": 10.0, "n_dark_stores": 3, "n_vehicles": 25,
    "vehicle_capacity": 50, "poisson_lambda": 5.0,
    "time_window_min": 15.0, "time_window_max": 45.0,
    "rolling_horizon_window": 300.0, "simulation_horizon": 240.0,
    "service_time": 5.0, "avg_speed": 40.0,
    "omega_weights": (0.4, 0.4, 0.2), "population_size": 100,
}
EXCLUDE = ['instance', 'algorithm', 'demo_id', 'alpha', 'beta', 'gamma',
           'improvement', 'fitness_after', 'gain_vs_neutral']


def parse_seeds(spec):
    a, b = spec.split("-")
    return list(range(int(a), int(b) + 1))


@click.command()
@click.option("--iters", default=25, type=int, help="Target HO iterations per sub-VRP solve")
@click.option("--train-seeds", default="42-43")
@click.option("--test-seeds", default="60-64")
@click.option("--output-dir", "-o", default=None)
def main(iters, train_seeds, test_seeds, output_dir):
    # n_windows=48, stores=3 -> 144 sub-problems. max_fes = iters*pop*144
    n_sub = 48 * BASE["n_dark_stores"]
    max_fes = iters * BASE["population_size"] * n_sub
    cfg = {**BASE, "max_fes": max_fes}
    print(f"Regime: ~{iters} iters/solve (max_fes={max_fes})")

    train_s, test_s = parse_seeds(train_seeds), parse_seeds(test_seeds)
    if output_dir is None:
        output_dir = f"results/fairtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    demos_path = os.path.join(output_dir, "demos.csv")
    model_path = os.path.join(output_dir, "model.pkl")

    def run(cls, params, seed):
        return QCDVRPSimulator(seed=seed, **cfg).run_simulation(cls, params)["fitness"]

    # 1) generate in-domain demos in THIS regime
    print(f"[1/3] Generating oracle demos (seeds {train_s})...")
    for seed in train_s:
        t = time.time()
        run(HOOracle, {"oracle_lookahead": 1, "demo_log_path": demos_path}, seed)
        print(f"  seed {seed} ({time.time()-t:.0f}s)")
    df = pd.read_csv(demos_path)
    print(f"  -> {len(df)} demos")

    # 2) train
    print("[2/3] Training IL model...")
    df_tr = df.sample(frac=0.8, random_state=42)
    df_va = df.drop(df_tr.index)
    model = SimpleILModel(n_estimators=200, random_state=42)
    res = model.train(df_tr.drop(columns=["gain_vs_neutral"], errors="ignore"),
                      df_va.drop(columns=["gain_vs_neutral"], errors="ignore"))
    r2 = {p: round(res[p].get("val_r2", float("nan")), 3) for p in ("alpha", "beta", "gamma")}
    print(f"  Val R^2: {r2}")
    model.save(model_path)

    # 3) eval HO vs HO+IL (no oracle)
    print(f"[3/3] Eval HO vs HO+IL (seeds {test_s})...")
    fit = {"HO": [], "HO+IL": []}
    for seed in test_s:
        fit["HO"].append(run(HO, {}, seed))
        fit["HO+IL"].append(run(HO, {"use_il": True, "il_model_path": model_path}, seed))
        print(f"  seed {seed}: HO={fit['HO'][-1]:.0f}  HO+IL={fit['HO+IL'][-1]:.0f}")

    base, il = np.array(fit["HO"]), np.array(fit["HO+IL"])
    delta = il.mean() - base.mean()
    p = stats.wilcoxon(base, il).pvalue if len(base) > 1 else float("nan")
    print(f"\n=== Fair test (~{iters} iters/solve) ===")
    print(f"HO     Z={base.mean():.0f}")
    print(f"HO+IL  Z={il.mean():.0f}  delta={delta:+.1f} ({100*delta/base.mean():+.2f}%)  "
          f"Wilcoxon p={p:.4f}  better={int((il<base).sum())}/{len(base)}")
    json.dump({"iters": iters, "max_fes": max_fes, "r2_val": r2, "n_demos": len(df),
               "HO_mean": float(base.mean()), "IL_mean": float(il.mean()),
               "delta": float(delta), "pct": float(100*delta/base.mean()),
               "wilcoxon_p": float(p), "better": int((il < base).sum()), "n": len(base),
               "fit_raw": {k: list(map(float, v)) for k, v in fit.items()}},
              open(os.path.join(output_dir, "fairtest_results.json"), "w"), indent=2)
    print(f"\nSaved: {output_dir}/fairtest_results.json")


if __name__ == "__main__":
    main()
