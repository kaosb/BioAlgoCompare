"""F1 pipeline: train a real IL (behavioral-cloning) policy and test it OOD.

The thesis experiment ("does IL improve optimization?") instantiated on the
two screened targets (PSO, DE), with the methodological guards that killed the
old HO+IL study baked in:

  * TRAIN / TEST SPLIT of functions: demos come ONLY from CEC2014 (30 funcs);
    evaluation happens ONLY on CEC2017 (29) + CEC2022 (12) -- never seen by
    the policy. Generalization, not memorization.
  * FES-FAIRNESS: at test time the policy consumes only free state features
    (utils/state_features.py); base and IL variants run under the SAME exact
    MaxFES budget (FESLimitProblem). Demo generation is an offline, declared
    training phase (oracle rollouts are not charged to any comparison budget).
  * NO CLAIRVOYANCE: demonstrations come from the ROBUST oracle
    (n_eval_samples>1, RNG-averaged), and features cannot see the future.
  * PAIRED EVALUATION: base vs IL share seeds; Wilcoxon signed-rank per
    function on 51 paired runs + better/equal/worse counts across functions.

Stages (resumable, each persists JSON):
  1. demos   -- robust-oracle runs on CEC2014 10D -> demo files
  2. train   -- BCPolicy per algorithm -> models/*.pkl
  3. eval    -- paired base-vs-IL on CEC2017+CEC2022 10D, 51 seeds
  4. report  -- per-function Wilcoxon + aggregate B/E/W + mean rel. improvement

Usage:
    python scripts/cec_harness/run_il_pipeline.py [demos|train|eval|report|all]
"""

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from problems.continuous.cec_problem import CECProblem, run_with_fes  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso_oracle import PSOOracle  # noqa: E402
from algorithms.de_oracle import DEOracle  # noqa: E402
from utils.bc_policy import BCPolicy  # noqa: E402

OUT = os.path.join(_REPO_ROOT, "results", "il_pipeline")
DEMO_DIR = os.path.join(OUT, "demos")
MODEL_DIR = os.path.join(_REPO_ROOT, "models")
EVAL_DIR = os.path.join(OUT, "eval")

# --- experimental configuration --------------------------------------------
TARGETS = {
    "PSO": {"base": PSO, "oracle": PSOOracle, "n_outputs": 3},
    "DE":  {"base": DE,  "oracle": DEOracle,  "n_outputs": 2},
}
# TRAIN: all of CEC2014 at 10D. TEST: all of CEC2017 + CEC2022 at 10D.
TRAIN_FUNCS = [("CEC2014", f) for f in range(1, 31)]
TEST_FUNCS = ([("CEC2017", f) for f in range(1, 30)]
              + [("CEC2022", f) for f in range(1, 13)])
DIM = 10
POP = 30
DEMO_ITERS = 100          # oracle decisions per demo run
DEMO_SEEDS = [11, 22, 33]  # 3 independent demo runs per function
N_EVAL_ROBUST = 3          # robust oracle samples (anti-clairvoyance)
EVAL_MAXFES = 5000         # test budget (protocol low-FES level)
EVAL_SEEDS = list(range(2000, 2051))  # 51 paired seeds
N_JOBS = int(os.environ.get("N_JOBS", "8"))


# --- stage 1: demo generation ----------------------------------------------
def _demo_worker(args):
    algo_name, suite, fnum, seed = args
    path = os.path.join(DEMO_DIR, f"{algo_name}__{suite}__F{fnum}__s{seed}.json")
    if os.path.exists(path):
        return path
    oracle_cls = TARGETS[algo_name]["oracle"]
    prob = CECProblem(suite, fnum, DIM)
    algo = oracle_cls(problem=prob, population_size=POP,
                      max_iterations=DEMO_ITERS, seed=seed,
                      n_eval_samples=N_EVAL_ROBUST, oracle_lookahead=1,
                      record_demos=True)
    algo.execute()
    with open(path, "w") as fh:
        json.dump(algo.demo_log, fh)
    return path


def stage_demos():
    os.makedirs(DEMO_DIR, exist_ok=True)
    grid = [(a, s, f, sd) for a in TARGETS for (s, f) in TRAIN_FUNCS
            for sd in DEMO_SEEDS]
    t0 = time.time()
    print(f"[demos] {len(grid)} oracle runs (train={len(TRAIN_FUNCS)} funcs x "
          f"{len(DEMO_SEEDS)} seeds x {len(TARGETS)} algos) n_jobs={N_JOBS}")
    with Pool(N_JOBS) as pool:
        done = 0
        for _ in pool.imap_unordered(_demo_worker, grid):
            done += 1
            if done % 20 == 0 or done == len(grid):
                print(f"[demos] {done}/{len(grid)} ({time.time()-t0:.0f}s)")
    print(f"[demos] done in {(time.time()-t0)/60:.1f} min")


# --- stage 2: train BC policies ---------------------------------------------
def stage_train():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for algo_name, spec in TARGETS.items():
        paths = sorted(
            os.path.join(DEMO_DIR, f)
            for f in os.listdir(DEMO_DIR)
            if f.startswith(f"{algo_name}__") and f.endswith(".json")
        )
        policy = BCPolicy.train_from_demo_files(
            paths, n_outputs=spec["n_outputs"], seed=0)
        out = os.path.join(MODEL_DIR, f"{algo_name.lower()}_il_cec2014_10d.pkl")
        policy.save(out)
        print(f"[train] {algo_name}: {policy.n_demos} demos from "
              f"{len(paths)} runs -> {out}")
        print(f"[train]   feature importances: "
              f"{ {k: round(v, 3) for k, v in policy.feature_importances().items()} }")


# --- stage 3: paired OOD evaluation ------------------------------------------
def _eval_worker(args):
    algo_name, suite, fnum = args
    path = os.path.join(EVAL_DIR, f"{algo_name}__{suite}__F{fnum}.json")
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    base_cls = TARGETS[algo_name]["base"]
    model = BCPolicy.load(
        os.path.join(MODEL_DIR, f"{algo_name.lower()}_il_cec2014_10d.pkl"))
    base_err, il_err = [], []
    for seed in EVAL_SEEDS:
        prob = CECProblem(suite, fnum, DIM)
        base_err.append(run_with_fes(base_cls, prob, pop_size=POP,
                                     max_fes=EVAL_MAXFES, seed=seed))
        prob2 = CECProblem(suite, fnum, DIM)
        il_err.append(run_with_fes(base_cls, prob2, pop_size=POP,
                                   max_fes=EVAL_MAXFES, seed=seed,
                                   algo_params={"use_il": True,
                                                "il_model": model}))
    rec = {"algo": algo_name, "suite": suite, "fnum": fnum,
           "base": base_err, "il": il_err}
    with open(path, "w") as fh:
        json.dump(rec, fh)
    return rec


def stage_eval():
    os.makedirs(EVAL_DIR, exist_ok=True)
    grid = [(a, s, f) for a in TARGETS for (s, f) in TEST_FUNCS]
    t0 = time.time()
    print(f"[eval] {len(grid)} cells x {len(EVAL_SEEDS)} paired seeds x 2 "
          f"variants | OOD test funcs (CEC2017+CEC2022 {DIM}D) "
          f"MaxFES={EVAL_MAXFES}")
    with Pool(N_JOBS) as pool:
        done = 0
        for _ in pool.imap_unordered(_eval_worker, grid):
            done += 1
            if done % 10 == 0 or done == len(grid):
                print(f"[eval] {done}/{len(grid)} ({time.time()-t0:.0f}s)")
    print(f"[eval] done in {(time.time()-t0)/60:.1f} min")


# --- stage 4: report ----------------------------------------------------------
def stage_report():
    from scipy.stats import wilcoxon
    out = {}
    print("\n" + "=" * 72)
    print(f"IL OOD EVALUATION -- {DIM}D, MaxFES={EVAL_MAXFES}, "
          f"{len(EVAL_SEEDS)} paired seeds, alpha=0.05")
    print("TRAIN: CEC2014 (never evaluated) | TEST: CEC2017 + CEC2022")
    print("=" * 72)
    for algo_name in TARGETS:
        rows = []
        for suite, fnum in TEST_FUNCS:
            path = os.path.join(EVAL_DIR, f"{algo_name}__{suite}__F{fnum}.json")
            if not os.path.exists(path):
                continue
            with open(path) as fh:
                r = json.load(fh)
            b = np.asarray(r["base"], dtype=float)
            i = np.asarray(r["il"], dtype=float)
            diff = b - i
            if np.allclose(diff, 0.0, atol=1e-12):
                verdict, p = "equal", 1.0
            else:
                try:
                    _, p = wilcoxon(b, i)
                except ValueError:
                    p = 1.0
                if p < 0.05:
                    verdict = "better" if np.mean(i) < np.mean(b) else "worse"
                else:
                    verdict = "equal"
            rel = float((np.mean(b) - np.mean(i)) / (abs(np.mean(b)) + 1e-12))
            rows.append({"suite": suite, "fnum": fnum, "p": float(p),
                         "verdict": verdict, "rel_improvement": rel})
        bett = sum(1 for r in rows if r["verdict"] == "better")
        eq = sum(1 for r in rows if r["verdict"] == "equal")
        wors = sum(1 for r in rows if r["verdict"] == "worse")
        mean_rel = float(np.mean([r["rel_improvement"] for r in rows])) if rows else 0.0
        med_rel = float(np.median([r["rel_improvement"] for r in rows])) if rows else 0.0
        out[algo_name] = {"rows": rows, "better": bett, "equal": eq,
                          "worse": wors, "mean_rel_improvement": mean_rel,
                          "median_rel_improvement": med_rel}
        print(f"\n{algo_name}+IL vs {algo_name}  (n={len(rows)} OOD functions)")
        print(f"  Wilcoxon B/E/W: {bett} / {eq} / {wors}")
        print(f"  mean rel. improvement:   {mean_rel*100:+.2f}%")
        print(f"  median rel. improvement: {med_rel*100:+.2f}%")
    with open(os.path.join(OUT, "il_ood_report.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nsaved {OUT}/il_ood_report.json")
    print("=" * 72)
    return out


STAGES = {"demos": stage_demos, "train": stage_train, "eval": stage_eval,
          "report": stage_report}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(OUT, exist_ok=True)
    if which == "all":
        for name in ("demos", "train", "eval", "report"):
            STAGES[name]()
    else:
        STAGES[which]()
