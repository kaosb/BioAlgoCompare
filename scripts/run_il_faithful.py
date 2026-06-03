#!/usr/bin/env python3
"""Regenerate HO+IL with the FAITHFUL HO: in-domain oracle demos -> train -> run.

Demos on train seeds (disjoint from eval), train SimpleILModel, then run HO+IL on
the SAME eval seeds as the 6-algorithm faithful N=30 run (42-71) so HO vs HO+IL is
paired. Outputs HO+IL summary + Wilcoxon/A12 vs HO.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from problems.qc_dvrp import QCDVRPSimulator
from algorithms.ho import HO
from algorithms.ho_oracle import HOOracle
from utils.train_il_simple import SimpleILModel

CFG = {
    "zone_size": 10.0, "n_dark_stores": 3, "n_vehicles": 25, "vehicle_capacity": 50,
    "poisson_lambda": 5.0, "time_window_min": 15.0, "time_window_max": 45.0,
    "rolling_horizon_window": 300.0, "simulation_horizon": 240.0, "service_time": 5.0,
    "avg_speed": 40.0, "omega_weights": (0.4, 0.4, 0.2), "max_fes": 50000, "population_size": 100,
}
EXCLUDE = ['instance', 'algorithm', 'demo_id', 'alpha', 'beta', 'gamma',
           'improvement', 'fitness_after', 'gain_vs_neutral']
OUT = "results/dvrp_faithful_n30"
DEMOS = os.path.join(OUT, "il_demos_faithful.csv")
MODEL = os.path.join(OUT, "ho_il_faithful.pkl")
TRAIN_SEEDS = list(range(100, 105))   # disjoint from eval
EVAL_SEEDS = list(range(42, 72))      # same as 6-algo N=30 run


def run(cls, params, seed, key="fitness"):
    return QCDVRPSimulator(seed=seed, **CFG).run_simulation(cls, params)[key]


def main():
    # 1) demos via faithful-HO oracle
    print(f"[1/3] Demos (faithful HO oracle) seeds {TRAIN_SEEDS}...")
    for s in TRAIN_SEEDS:
        t = time.time()
        run(HOOracle, {"oracle_lookahead": 1, "demo_log_path": DEMOS}, s)
        print(f"  seed {s} ({time.time()-t:.0f}s)")
    df = pd.read_csv(DEMOS)
    print(f"  -> {len(df)} demos")

    # 2) train
    print("[2/3] Train SimpleILModel...")
    df_tr = df.sample(frac=0.8, random_state=42)
    df_va = df.drop(df_tr.index)
    model = SimpleILModel(n_estimators=200, random_state=42)
    res = model.train(df_tr.drop(columns=["gain_vs_neutral"], errors="ignore"),
                      df_va.drop(columns=["gain_vs_neutral"], errors="ignore"))
    print("  Val R2:", {p: round(res[p].get("val_r2", float('nan')), 3) for p in ("alpha", "beta", "gamma")})
    model.save(MODEL)

    # 3) run HO+IL N=30 (paired with HO from the 6-algo run)
    print(f"[3/3] HO+IL N=30 (eval seeds {EVAL_SEEDS[0]}-{EVAL_SEEDS[-1]})...")
    il = []
    for s in EVAL_SEEDS:
        il.append(run(HO, {"use_il": True, "il_model_path": MODEL}, s))
    il = np.array(il)

    # HO baseline from the 6-algo detailed CSV (same seeds order = Run 1..30)
    det = pd.read_csv(os.path.join(OUT, "results_detailed.csv"))
    ho = det[det.Algorithm == "HO"].sort_values("Run")["Fitness"].values
    delta = il.mean() - ho.mean()
    p = stats.wilcoxon(ho, il).pvalue

    print("\n=== HO+IL (faithful HO) vs HO, N=30 ===")
    print(f"HO     Z={ho.mean():.0f}")
    print(f"HO+IL  Z={il.mean():.0f}  delta={delta:+.1f} ({100*delta/ho.mean():+.2f}%)  "
          f"Wilcoxon p={p:.4f}  mejor={int((il<ho).sum())}/30")

    json.dump({"HO_mean": float(ho.mean()), "HOIL_mean": float(il.mean()),
               "delta_pct": float(100*delta/ho.mean()), "wilcoxon_p": float(p),
               "il_raw": list(map(float, il)),
               "val_r2": {p_: res[p_].get("val_r2") for p_ in ("alpha", "beta", "gamma")}},
              open(os.path.join(OUT, "ho_il_faithful_results.json"), "w"), indent=2)
    print(f"\nSaved: {OUT}/ho_il_faithful_results.json")


if __name__ == "__main__":
    main()
