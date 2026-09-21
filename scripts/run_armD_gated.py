#!/usr/bin/env python3
"""Arm D: does a GATED IL model (modulate-or-neutral) close the gap?

Reuses the in-domain oracle demos from Arm C. Trains:
  - gate: RandomForestClassifier predicting whether modulation helps (gain>0)
  - regressors: alpha/beta/gamma RFs fit ONLY on states where modulation helped
Then evaluates HO vs HO+GatedIL on held-out seeds, paired Wilcoxon, and compares
against the oracle ceiling.

Usage:
  python scripts/run_armD_gated.py --demos results/armC_full/oracle_demos_indomain.csv \
      --test-seeds 60-69 -o results/armD_gated
"""
import json
import os
import pickle
import sys
import time
from datetime import datetime

import click
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from problems.qc_dvrp import QCDVRPSimulator
from algorithms.ho import HO
from algorithms.ho_gated import HOGatedIL

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
    rr = sim.run_simulation(cls, params)
    return rr["fitness"]


@click.command()
@click.option("--demos", default="results/armC_full/oracle_demos_indomain.csv")
@click.option("--test-seeds", default="60-69")
@click.option("--output-dir", "-o", default=None)
def main(demos, test_seeds, output_dir):
    test_s = parse_seeds(test_seeds)
    if output_dir is None:
        output_dir = f"results/armD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "ho_gated_model.pkl")

    # ---- Train gate + regressors ----
    df = pd.read_csv(demos)
    feats = [c for c in df.columns if c not in EXCLUDE]
    scaler = StandardScaler().fit(df[feats].values)
    X = scaler.transform(df[feats].values)
    y_gate = (df["gain_vs_neutral"] > 1e-9).astype(int).values

    gate = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1).fit(X, y_gate)

    mod = df["gain_vs_neutral"] > 1e-9  # train regressors on helpful states only
    Xmod = scaler.transform(df.loc[mod, feats].values)
    regs = {}
    for p in ("alpha", "beta", "gamma"):
        regs[p] = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1
                                        ).fit(Xmod, df.loc[mod, p].values)

    with open(model_path, "wb") as f:
        pickle.dump({"gate": gate, "reg_alpha": regs["alpha"], "reg_beta": regs["beta"],
                     "reg_gamma": regs["gamma"], "scaler": scaler, "feature_names": feats}, f)
    print(f"Trained gated model | demos={len(df)} | modulate_frac={y_gate.mean():.3f}")

    # ---- Evaluate ----
    print(f"Evaluating on held-out seeds {test_s}...")
    fit = {"HO": [], "HO+GatedIL": []}
    for seed in test_s:
        fit["HO"].append(_run(HO, {}, seed))
        t = time.time()
        fit["HO+GatedIL"].append(_run(HOGatedIL, {"gated_model_path": model_path}, seed))
        print(f"  seed {seed}: HO={fit['HO'][-1]:.0f}  Gated={fit['HO+GatedIL'][-1]:.0f}  ({time.time()-t:.0f}s)")

    base = np.array(fit["HO"]); gated = np.array(fit["HO+GatedIL"])
    p = stats.wilcoxon(base, gated).pvalue
    delta = gated.mean() - base.mean()

    # Oracle reference from Arm C (same seeds)
    oracle_ref = None
    armc = "results/armC_full/armC_results.json"
    if os.path.exists(armc):
        oracle_ref = json.load(open(armc)).get("HO+Oracle", {})

    print("\n=== Arm D: gated IL on held-out seeds ===")
    print(f"HO          Z={base.mean():.0f}")
    print(f"HO+GatedIL  Z={gated.mean():.0f}  delta={delta:+.1f} ({100*delta/base.mean():+.2f}%)  "
          f"Wilcoxon p={p:.4f}  better={int((gated<base).sum())}/{len(base)}")
    if oracle_ref:
        print(f"[ref] Oracle ceiling (Arm C, same seeds): {oracle_ref.get('pct'):+.2f}%")

    json.dump({
        "HO_mean": float(base.mean()),
        "gated_mean": float(gated.mean()), "gated_delta": float(delta),
        "gated_pct": float(100*delta/base.mean()), "wilcoxon_p": float(p),
        "better": int((gated < base).sum()), "n": len(base),
        "modulate_frac_train": float(y_gate.mean()),
        "oracle_ref_pct": oracle_ref.get("pct") if oracle_ref else None,
        "fit_raw": {k: list(map(float, v)) for k, v in fit.items()},
    }, open(os.path.join(output_dir, "armD_results.json"), "w"), indent=2)
    print(f"\nSaved: {output_dir}/armD_results.json")


if __name__ == "__main__":
    main()
