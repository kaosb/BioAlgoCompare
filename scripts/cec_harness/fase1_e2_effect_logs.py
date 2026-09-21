"""Fase 1 (pre-registro fase positiva v0.2) — logs de efecto por triple (fila 4).

E2 (e5_discriminant.json) persistió solo totales de veto, no los efectos por
transferencia. Se re-ejecutan los brazos con intención de fuente (C2p y C3p) de
DE+GA @ 5e3 sobre las 6 funciones taxonómicas con ``log_transfers=True``,
elevando a 51 corridas (regla de Fase 0: 51 en toda celda que llegue a tabla).

Cota: estabilidad del signo del efecto por triple (fuente, destino, intención)
entre semillas — insumo del candidato C (régimen por efecto observado).

Salida: results/cooperative/fase1/e2_effect_logs.json
        {"config", "per_func": {F: {arm: {triple: {"per_seed_mean_effect": [..],
         "n_obs": [..]}}}}, "provenance"}
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402

from problems.continuous.cec_problem import CECProblem, FESLimitProblem  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from cooperative.orchestrator import CooperativeRunner  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
FUNCS = [1, 4, 6, 9, 15, 23]
DIM, POP, RUNS, BUDGET, TE, SEED0 = 10, 30, 51, 5000, 500, 8000   # SEED0 de E2
SPECS = [("DE", DE, {"population_size": POP, "max_iterations": 10**9}),
         ("GA", GA, {"population_size": POP, "max_iterations": 10**9})]
ARMS = {"C2p": False, "C3p": True}     # gate_enabled
OUT = os.path.join(_REPO, "results", "cooperative", "fase1", "e2_effect_logs.json")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    per_func = {}
    for f in FUNCS:
        per_func[f"F{f}"] = {}
        for arm, gate in ARMS.items():
            acc = defaultdict(lambda: {"per_seed_mean_effect": [], "n_obs": []})
            for r in range(RUNS):
                prob = FESLimitProblem(CECProblem("CEC2014", f, DIM), max_fes=BUDGET)
                runner = CooperativeRunner(prob, SPECS, transfer_every=TE,
                                           gate_enabled=gate, seed=SEED0 + r,
                                           transfer_mode="parametric",
                                           intent_mode="source",
                                           log_transfers=True)
                res = runner.run()
                assert res["fes_used"] == BUDGET
                by_triple = defaultdict(list)
                for t in res["transfers"]:
                    by_triple[f"{t['src']}->{t['tgt']}:{t['intent']}"].append(float(t["effect"]))
                for k in set(list(by_triple) + list(acc)):
                    v = by_triple.get(k, [])
                    acc[k]["per_seed_mean_effect"].append(float(np.mean(v)) if v else None)
                    acc[k]["n_obs"].append(len(v))
            per_func[f"F{f}"][arm] = dict(acc)
        print(f"  F{f} listo", flush=True)
    out = {"config": {"pair": "DE+GA", "funcs": FUNCS, "runs": RUNS,
                      "budget": BUDGET, "transfer_every": TE, "seed0": SEED0,
                      "arms": list(ARMS), "effect": "mediana_now - mediana_commit (>0 = daño)"},
           "per_func": per_func, "provenance": provenance()}
    tmp = OUT + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, OUT)
    print("->", OUT, flush=True)


if __name__ == "__main__":
    main()
