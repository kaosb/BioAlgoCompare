#!/usr/bin/env python3
"""Arm C: Can IL trained on IN-DOMAIN oracle demonstrations close the gap?

Pipeline:
  1. GENERATE: run the HO oracle on the dynamic QC-DVRP for a set of train
     seeds, logging (dynamic state features -> oracle-chosen alpha,beta,gamma)
     as in-domain demonstrations (no domain shift, unlike the static CVRPLIB
     demos used by the original model).
  2. TRAIN: fit the SimpleILModel (RandomForest) on those demos; report val R².
  3. EVALUATE on held-out test seeds: HO (neutral) vs HO+IL_v2 (oracle-demo
     model) vs HO+Oracle (ceiling), paired Wilcoxon.

Question: does HO+IL_v2 move from ~0% toward the oracle's ~3% ceiling?

Usage:
  python scripts/run_armC_oracle_il.py --train-seeds 42-46 --test-seeds 60-69
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

SIM_CONFIG = {
    "zone_size": 10.0, "n_dark_stores": 3, "n_vehicles": 25,
    "vehicle_capacity": 50, "poisson_lambda": 5.0,
    "time_window_min": 15.0, "time_window_max": 45.0,
    "rolling_horizon_window": 300.0, "simulation_horizon": 240.0,
    "service_time": 5.0, "avg_speed": 40.0,
    "omega_weights": (0.4, 0.4, 0.2), "max_fes": 50000, "population_size": 100,
}
EXCLUDE = ['instance', 'algorithm', 'demo_id', 'alpha', 'beta', 'gamma',
           'improvement', 'fitness_after', 'gain_vs_neutral']


def parse_seeds(spec):
    a, b = spec.split("-")
    return list(range(int(a), int(b) + 1))


def _run(cls, params, seed):
    sim = QCDVRPSimulator(seed=seed, **SIM_CONFIG)
    t = time.time()
    rr = sim.run_simulation(cls, params)
    return rr["fitness"], rr["dsr"], rr["wbi"], time.time() - t


@click.command()
@click.option("--train-seeds", default="42-46")
@click.option("--test-seeds", default="60-69")
@click.option("--output-dir", "-o", default=None)
def main(train_seeds, test_seeds, output_dir):
    train_s, test_s = parse_seeds(train_seeds), parse_seeds(test_seeds)
    if output_dir is None:
        output_dir = f"results/armC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    demos_path = os.path.join(output_dir, "oracle_demos_indomain.csv")
    model_path = os.path.join(output_dir, "ho_il_oracle.pkl")

    # ---- Phase 1: generate in-domain demos via the oracle ----
    print(f"[1/3] Generating in-domain oracle demos on seeds {train_s}...")
    for seed in train_s:
        t = time.time()
        _run(HOOracle, {"oracle_lookahead": 1, "demo_log_path": demos_path}, seed)
        print(f"  seed {seed} done ({time.time()-t:.0f}s)")
    df = pd.read_csv(demos_path)
    print(f"  -> {len(df)} demonstrations, {df.shape[1]} columns")

    # ---- Phase 2: train ----
    print("[2/3] Training IL model on in-domain oracle demos...")
    feat_cols = [c for c in df.columns if c not in EXCLUDE]
    df_train = df.sample(frac=0.8, random_state=42)
    df_val = df.drop(df_train.index)
    model = SimpleILModel(n_estimators=200, random_state=42)
    # train() uses prepare_features (its own exclude list); ensure our extra
    # column is dropped so it is not used as a feature.
    res = model.train(df_train.drop(columns=["gain_vs_neutral"], errors="ignore"),
                      df_val.drop(columns=["gain_vs_neutral"], errors="ignore"))
    r2 = {p: res[p].get("val_r2") for p in ("alpha", "beta", "gamma")}
    print(f"  Val R^2: alpha={r2['alpha']:.3f} beta={r2['beta']:.3f} gamma={r2['gamma']:.3f}")
    model.save(model_path)

    # ---- Phase 3: evaluate on held-out test seeds ----
    print(f"[3/3] Evaluating on held-out seeds {test_s}...")
    arms = {
        "HO": (HO, {}),
        "HO+IL_v2": (HO, {"use_il": True, "il_model_path": model_path}),
        "HO+Oracle": (HOOracle, {"oracle_lookahead": 1}),
    }
    fit = {a: [] for a in arms}
    for a, (cls, params) in arms.items():
        for seed in test_s:
            f, d, w, dt = _run(cls, params, seed)
            fit[a].append(f)
        print(f"  {a:10} mean Z={np.mean(fit[a]):.0f}")

    base = np.array(fit["HO"])
    print("\n=== Arm C result (held-out seeds) ===")
    print(f"{'Arm':10} {'Z mean':>8} {'vs HO':>10} {'Wilcoxon p':>12} {'better/N':>10}")
    out = {"r2_val": r2, "n_demos": len(df), "train_seeds": train_s, "test_seeds": test_s}
    for a in arms:
        v = np.array(fit[a])
        delta = v.mean() - base.mean()
        if a == "HO":
            print(f"{a:10} {v.mean():8.0f} {'--':>10} {'--':>12} {'--':>10}")
        else:
            p = stats.wilcoxon(base, v).pvalue
            better = int((v < base).sum())
            print(f"{a:10} {v.mean():8.0f} {delta:+9.1f}  {p:12.4f} {better:>4}/{len(v)}")
            out[a] = {"mean": float(v.mean()), "delta": float(delta),
                      "pct": float(100*delta/base.mean()), "wilcoxon_p": float(p),
                      "better": better}
    out["HO_mean"] = float(base.mean())
    out["fit_raw"] = {a: list(map(float, fit[a])) for a in arms}
    with open(os.path.join(output_dir, "armC_results.json"), "w") as fp:
        json.dump(out, fp, indent=2)
    print(f"\nSaved: {output_dir}/armC_results.json")


if __name__ == "__main__":
    main()
