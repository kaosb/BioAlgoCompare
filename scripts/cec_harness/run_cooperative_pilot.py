"""
Cooperative-transfer PILOT — C0/C2/C3 on a CEC2014 10D subset (Fase 3).

Quick-signal experiment for the transfer line (see
tesis-mia/gestion_proyecto/DISENO_TRANSFERENCIA_MHS.md §8): does gated cooperation
(C3) beat the best isolated solver (C0) and the no-gate ablation (C2), at an
equal shared FES budget?

    python scripts/cec_harness/run_cooperative_pilot.py            # frozen pilot
    RUNS=31 BUDGET=5000 python .../run_cooperative_pilot.py        # override

Output: results/cooperative/pilot_C0C2C3.json (with provenance) + printed table.
"""

import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from cooperative import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

# --- frozen pilot configuration (see DISENO §8) ------------------------------
FUNCS = [1, 4, 6, 9, 15, 22]        # uni / multimodal / hybrid / composition
DIM = 10
BUDGET = int(os.environ.get("BUDGET", "5000"))
RUNS = int(os.environ.get("RUNS", "15"))
POP = 30
TRANSFER_EVERY = 500
SPECS = [("DE", DE, {"population_size": POP, "max_iterations": 10**9}),
         ("PSO", PSO, {"population_size": POP, "max_iterations": 10**9})]

OUT_DIR = os.path.join(_REPO_ROOT, "results", "cooperative")
OUT_PATH = os.path.join(OUT_DIR, "pilot_C0C2C3.json")


def _isolated(cls, kwargs, fnum, seed):
    # run_with_fes wraps the raw problem itself and returns the best error.
    prob = CECProblem("CEC2014", fnum, DIM)
    return float(run_with_fes(cls, prob, pop_size=POP, max_fes=BUDGET, seed=seed))


def _coop(fnum, seed, gate):
    prob = FESLimitProblem(CECProblem("CEC2014", fnum, DIM), max_fes=BUDGET)
    runner = CooperativeRunner(prob, SPECS, transfer_every=TRANSFER_EVERY,
                               gate_enabled=gate, seed=seed)
    res = runner.run()
    return res["best_fitness"], res["transfer_stats"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = {}
    print(f"[pilot] {len(FUNCS)} funcs x {RUNS} runs, B={BUDGET} (shared), DE+PSO")
    for f in FUNCS:
        c0_de, c0_pso, c2, c3 = [], [], [], []
        acc_c3 = rej_c3 = 0
        for r in range(RUNS):
            s = 2000 + r
            c0_de.append(_isolated(DE, SPECS[0][2], f, s))
            c0_pso.append(_isolated(PSO, SPECS[1][2], f, s))
            v2, _ = _coop(f, s, gate=False); c2.append(v2)
            v3, st = _coop(f, s, gate=True); c3.append(v3)
            acc_c3 += st["accepted"]; rej_c3 += st["rejected"]
        best_iso = [min(a, b) for a, b in zip(c0_de, c0_pso)]
        rows[f"F{f}"] = {
            "C0_DE_median": float(np.median(c0_de)),
            "C0_PSO_median": float(np.median(c0_pso)),
            "C0_bestiso_median": float(np.median(best_iso)),
            "C2_nogate_median": float(np.median(c2)),
            "C3_gated_median": float(np.median(c3)),
            "gate_accepted": acc_c3, "gate_rejected": rej_c3,
            "C3_beats_bestiso": bool(np.median(c3) < np.median(best_iso)),
            "C3_beats_C2": bool(np.median(c3) <= np.median(c2)),
        }
        r_ = rows[f"F{f}"]
        print(f"  F{f:<2} bestiso={r_['C0_bestiso_median']:.3e} "
              f"C2={r_['C2_nogate_median']:.3e} C3={r_['C3_gated_median']:.3e} "
              f"| C3<iso={r_['C3_beats_bestiso']} C3<=C2={r_['C3_beats_C2']} "
              f"| gate {acc_c3}acc/{rej_c3}rej")

    summary = {
        "n_funcs": len(FUNCS),
        "C3_beats_bestiso": sum(v["C3_beats_bestiso"] for v in rows.values()),
        "C3_beats_C2": sum(v["C3_beats_C2"] for v in rows.values()),
    }
    out = {"config": {"funcs": FUNCS, "dim": DIM, "budget": BUDGET, "runs": RUNS,
                      "pop": POP, "transfer_every": TRANSFER_EVERY,
                      "solvers": [s[0] for s in SPECS]},
           "results": rows, "summary": summary, "provenance": provenance()}
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n[pilot] C3<bestiso {summary['C3_beats_bestiso']}/{len(FUNCS)}, "
          f"C3<=C2 {summary['C3_beats_C2']}/{len(FUNCS)}  -> {OUT_PATH}")


if __name__ == "__main__":
    main()
