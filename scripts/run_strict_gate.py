#!/usr/bin/env python3
"""Rodrigo-aligned test: HO+IL with STRICT neutral fallback at a real budget.

Rodrigo (26 Mar 2026): "no puede funcionar peor que el que no tiene mejora".
Since HO+IL with (1,1,1) == HO, a well-designed IL must be able to fall back to
neutral and never underperform HO. We enforce this with a high-confidence gate:
modulate only when P(modulation helps) >= threshold; else neutral.

Regime: ~25 iters/solve (where the optimizer actually matters). Reuses the
in-domain 25-iter oracle demos. Sweeps the gate threshold and reports whether any
setting yields HO+IL >= HO with a net improvement.

Usage:
  python scripts/run_strict_gate.py --demos results/fairtest_i25/demos.csv \
      --iters 25 --test-seeds 60-64 --thresholds 0.5,0.7,0.85
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
@click.option("--demos", default="results/fairtest_i25/demos.csv")
@click.option("--iters", default=25, type=int)
@click.option("--test-seeds", default="60-64")
@click.option("--thresholds", default="0.5,0.7,0.85")
@click.option("--output-dir", "-o", default=None)
def main(demos, iters, test_seeds, thresholds, output_dir):
    seeds = parse_seeds(test_seeds)
    thr_list = [float(t) for t in thresholds.split(",")]
    max_fes = iters * BASE["population_size"] * 48 * BASE["n_dark_stores"]
    cfg = {**BASE, "max_fes": max_fes}
    if output_dir is None:
        output_dir = f"results/strict_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "gated_model.pkl")

    # ---- train gate + regressors ----
    df = pd.read_csv(demos)
    feats = [c for c in df.columns if c not in EXCLUDE]
    scaler = StandardScaler().fit(df[feats].values)
    X = scaler.transform(df[feats].values)
    y = (df["gain_vs_neutral"] > 1e-9).astype(int).values
    gate = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1).fit(X, y)
    mod = y == 1
    Xm = scaler.transform(df.loc[mod, feats].values)
    regs = {p: RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1
                                     ).fit(Xm, df.loc[mod, p].values)
            for p in ("alpha", "beta", "gamma")}
    pickle.dump({"gate": gate, "reg_alpha": regs["alpha"], "reg_beta": regs["beta"],
                 "reg_gamma": regs["gamma"], "scaler": scaler, "feature_names": feats},
                open(model_path, "wb"))
    print(f"Regime ~{iters} iters/solve | demos={len(df)} | modulate base rate={y.mean():.3f}")

    def run(cls, params, seed):
        return QCDVRPSimulator(seed=seed, **cfg).run_simulation(cls, params)["fitness"]

    # ---- baseline HO ----
    ho = np.array([run(HO, {}, s) for s in seeds])
    print(f"HO          Z={ho.mean():.0f}")

    out = {"iters": iters, "HO_mean": float(ho.mean()), "thresholds": {},
           "HO_raw": list(map(float, ho))}
    for thr in thr_list:
        t0 = time.time()
        il = np.array([run(HOGatedIL, {"gated_model_path": model_path, "gate_threshold": thr}, s)
                       for s in seeds])
        delta = il.mean() - ho.mean()
        p = stats.wilcoxon(ho, il).pvalue if len(ho) > 1 else float("nan")
        better = int((il < ho).sum()); notworse = int((il <= ho + 1e-9).sum())
        print(f"HO+IL thr={thr:.2f}  Z={il.mean():.0f}  delta={delta:+.1f} ({100*delta/ho.mean():+.2f}%)  "
              f"p={p:.4f}  mejor={better}/{len(ho)}  no-peor={notworse}/{len(ho)}  ({time.time()-t0:.0f}s)")
        out["thresholds"][str(thr)] = {"mean": float(il.mean()), "delta": float(delta),
                                       "pct": float(100*delta/ho.mean()), "wilcoxon_p": float(p),
                                       "better": better, "not_worse": notworse,
                                       "raw": list(map(float, il))}

    json.dump(out, open(os.path.join(output_dir, "strict_results.json"), "w"), indent=2)
    print(f"\nSaved: {output_dir}/strict_results.json")


if __name__ == "__main__":
    main()
