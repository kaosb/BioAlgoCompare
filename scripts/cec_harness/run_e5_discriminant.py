"""
E5/E4 discriminant run — living memory + subtle-harm gate test (18 Jul audit).

After fixing the effect metric (population median, harm-sensitive) the gate's
memory-veto is ALIVE (verified: effects>0 recorded, triples vetoed). Questions:
  E5: with the living memory, do C3p / CTRL+ outcomes change vs the dead-memory
      results? Does the gate now do better than its 2 static rules?
  E4: does the gate discriminate MODERATE (subtle, non-freezing) harm — the
      realistic use case — or only catastrophic freezing?

Pair DE+GA @5e3 (where parametric transfer actively harms), 6 taxonomy funcs,
fresh seeds 8000+, conditions:
  C1_div (no-comms portfolio floor), C2p/C3p (source, gate OFF/ON),
  CTRLn/CTRLg (catastrophic adversarial), MODn/MODg (moderate harm).

    RUNS=31 python scripts/cec_harness/run_e5_discriminant.py
Output: results/cooperative/e5_discriminant.json
"""

import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem, run_with_fes  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from cooperative import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

FUNCS = [1, 4, 6, 9, 15, 23]
DIM = 10
BUDGET = 5000
RUNS = int(os.environ.get("RUNS", "31"))
POP = 30
SPECS = [("DE", DE, {"population_size": POP, "max_iterations": 10**9}),
         ("GA", GA, {"population_size": POP, "max_iterations": 10**9})]
SEED0 = 8000

CONDS = {"C2p": (False, "source"), "C3p": (True, "source"),
         "CTRLn": (False, "adversarial"), "CTRLg": (True, "adversarial"),
         "MODn": (False, "moderate"), "MODg": (True, "moderate")}

OUT = os.path.join(_REPO_ROOT, "results", "cooperative", "e5_discriminant.json")


def _coop(f, seed, gate, mode):
    prob = FESLimitProblem(CECProblem("CEC2014", f, DIM), max_fes=BUDGET)
    r = CooperativeRunner(prob, SPECS, transfer_every=500, gate_enabled=gate,
                          seed=seed, transfer_mode="parametric",
                          intent_mode=mode)
    res = r.run()
    assert res["fes_used"] == BUDGET
    vetoed = sum(1 for k in r.memory._effects
                 if len(k) == 3 and r.memory.is_harmful_triple(*k))
    return res["best_fitness"], res["transfer_stats"], vetoed


def _paired(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = b - a; nz = d[d != 0]
    if nz.size == 0:
        return 1.0, 0.0
    try:
        _, p = wilcoxon(a, b)
    except ValueError:
        p = 1.0
    r = rankdata(np.abs(nz))
    return float(p), float((r[nz > 0].sum() - r[nz < 0].sum()) / r.sum())


def _holm(ps):
    m = len(ps); o = sorted(range(m), key=lambda i: ps[i])
    adj, run = [0.0] * m, 0.0
    for k, i in enumerate(o):
        run = max(run, (m - k) * ps[i]); adj[i] = min(1.0, run)
    return adj


def main():
    raw, gate_info = {}, {}
    print(f"[E5] DE+GA @5e3, {len(FUNCS)} funcs x {RUNS} runs, memoria VIVA")
    for f in FUNCS:
        cols = {"C1_div": []}
        info = {c: {"accepted": 0, "rejected": 0, "rolled_back": 0, "vetoed": 0}
                for c in CONDS}
        for r in range(RUNS):
            s = SEED0 + r
            cols["C1_div"].append(min(
                float(run_with_fes(DE, CECProblem("CEC2014", f, DIM),
                                   pop_size=POP, max_fes=BUDGET // 2, seed=s)),
                float(run_with_fes(GA, CECProblem("CEC2014", f, DIM),
                                   pop_size=POP, max_fes=BUDGET // 2, seed=s))))
            for cname, (gate, mode) in CONDS.items():
                v, st, vetoed = _coop(f, s, gate, mode)
                cols.setdefault(cname, []).append(v)
                for k in ("accepted", "rejected", "rolled_back"):
                    info[cname][k] += st.get(k, 0)
                info[cname]["vetoed"] += vetoed
        raw[f"F{f}"] = cols
        gate_info[f"F{f}"] = info

    CONTRASTS = [("C3p_vs_C2p", "C3p", "C2p"),
                 ("C3p_vs_C1div", "C3p", "C1_div"),
                 ("C2p_vs_C1div", "C2p", "C1_div"),
                 ("CTRLg_vs_CTRLn", "CTRLg", "CTRLn"),
                 ("MODg_vs_MODn", "MODg", "MODn"),
                 ("MODn_vs_C1div", "MODn", "C1_div")]
    results = {}
    for name, A, B in CONTRASTS:
        ps, rbs = [], []
        for f in FUNCS:
            p, rb = _paired(raw[f"F{f}"][A], raw[f"F{f}"][B])
            ps.append(p); rbs.append(rb)
        holm = _holm(ps)
        wins = sum(1 for h, rb in zip(holm, rbs) if h < 0.05 and rb > 0)
        losses = sum(1 for h, rb in zip(holm, rbs) if h < 0.05 and rb < 0)
        results[name] = {"wins": wins, "losses": losses, "n": len(FUNCS)}

    veto_tot = {c: sum(gate_info[f][c]["vetoed"] for f in gate_info)
                for c in CONDS}
    out = {"config": {"pair": "DE+GA", "budget": BUDGET, "runs": RUNS,
                      "funcs": FUNCS, "seed0": SEED0,
                      "note": "metrica de efecto = mediana poblacional (fix 18 Jul)"},
           "contrasts": results, "veto_totals": veto_tot,
           "gate_info": gate_info,
           "raw_medians": {f: {c: float(np.median(v)) for c, v in cols.items()}
                           for f, cols in raw.items()},
           "provenance": provenance()}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)

    print("\n=== E5/E4 (A mejor que B; Wilcoxon+Holm) ===")
    for n, m in results.items():
        print(f"  {n:16s}: mejor {m['wins']}/{m['n']}, peor {m['losses']}/{m['n']}")
    print("\n=== triples vetados (memoria viva actuando) ===")
    for c, v in veto_tot.items():
        print(f"  {c:6s}: {v}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
