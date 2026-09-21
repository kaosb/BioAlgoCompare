"""Smoke test de los brazos de Fase 2 (enmienda v0.3 §E): 1 función × 3 semillas
@ 5e3, aserción de presupuesto exacto, sin excepciones, estadísticas de
mecanismo no triviales. El piloto no se lanza si esto falla."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from problems.continuous.cec_problem import CECProblem, FESLimitProblem  # noqa: E402
from algorithms.gwo import GWO  # noqa: E402
from algorithms.ga import GA  # noqa: E402
from algorithms.de import DE  # noqa: E402
from algorithms.pso import PSO  # noqa: E402
from algorithms.aco import ACO  # noqa: E402
from cooperative.orchestrator import CooperativeRunner  # noqa: E402
from cooperative.functional_intent import PRESETS_V2, RegimeController  # noqa: E402
from cooperative.candidates import (BudgetAllocRunner, StructuralGatedRunner,  # noqa: E402
                                    UCBRegimeRunner, BenignControlRunner)

_CLS = {"GWO": GWO, "GA": GA, "DE": DE, "PSO": PSO, "ACO": ACO}
LEVEL, POP, F = 5000, 30, 2
NEUTRAL_BENIGN = {"GWO": (1.0,), "GA": (1.0, 1.0), "DE": (1.0, 1.0),
                  "PSO": (1.0, 1.0, 1.0), "ACO": (1.0, 1.0)}


def specs(a, b):
    return [(a, _CLS[a], {"population_size": POP, "max_iterations": 10**9}),
            (b, _CLS[b], {"population_size": POP, "max_iterations": 10**9})]


def prob():
    return FESLimitProblem(CECProblem("CEC2014", F, 10), max_fes=LEVEL)


ok = True
for pair in ["GWO+GA", "DE+GA", "PSO+ACO"]:
    a, b = pair.split("+")
    for seed in (9000, 9001, 9002):
        arms = {
            "C1_island": CooperativeRunner(prob(), specs(a, b), transfer_every=500, gate_enabled=False, seed=seed, transfer_mode="structural"),
            "A": BudgetAllocRunner(prob(), specs(a, b), delta=500, seed=seed, log_transfers=True),
            "B": StructuralGatedRunner(prob(), specs(a, b), delta=500, seed=seed, log_transfers=True),
            "C": UCBRegimeRunner(prob(), specs(a, b), delta=500, seed=seed, log_transfers=True),
            "BENg": BenignControlRunner(prob(), specs(a, b), {a: NEUTRAL_BENIGN[a], b: NEUTRAL_BENIGN[b]}, delta=500, seed=seed, gate_enabled=True),
            "BENn": BenignControlRunner(prob(), specs(a, b), {a: NEUTRAL_BENIGN[a], b: NEUTRAL_BENIGN[b]}, delta=500, seed=seed, gate_enabled=False),
        }
        r = CooperativeRunner(prob(), specs(a, b), transfer_every=500, gate_enabled=True, seed=seed, transfer_mode="parametric")
        for e in r.solvers:
            ctrl = RegimeController(e["name"], presets=PRESETS_V2); e["solver"].il_model = ctrl; r._controllers[e["name"]] = ctrl
        arms["C3p_v2"] = r
        for name, runner in arms.items():
            try:
                res = runner.run()
            except Exception as ex:  # noqa: BLE001
                print(f"FAIL {pair} s={seed} {name}: {type(ex).__name__}: {ex}"); ok = False; continue
            st = res["transfer_stats"]
            fes_ok = res["fes_used"] == LEVEL
            if name == "A":
                nontriv = st["windows"] >= 8 and sum(st["fes_share"]) > 0
                detail = f"windows={st['windows']} reverts={st['reverts']} fes_share={st['fes_share']}"
            elif name == "B":
                nontriv = st["proposed"] > 0
                detail = f"prop={st['proposed']} acc={st['accepted']} rb={st['rolled_back']} kept={st['kept']}"
            elif name == "C":
                nontriv = st["proposed"] > 0 and all(sum(v.values()) > 0 for v in st["arm_counts"].values())
                detail = f"arms={st['arm_counts']}"
            else:
                nontriv = st.get("proposed", 0) > 0
                detail = f"prop={st.get('proposed')} acc={st.get('accepted')} rb={st.get('rolled_back')}"
            flag = "ok " if (fes_ok and nontriv) else "BAD"
            ok &= fes_ok and nontriv
            if seed == 9000:
                print(f"{flag} {pair:8s} {name:9s} best={res['best_fitness']:.4g} fes={res['fes_used']} {detail}")
print("SMOKE_OK" if ok else "SMOKE_FAIL")
