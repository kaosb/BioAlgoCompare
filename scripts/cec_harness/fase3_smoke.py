"""Fase 3 — smoke + estimación de costo ANTES de lanzar (v0.1 §6: "estimar con
el planificador del protocolo antes de lanzar").

Corre cada brazo en 1 función × 3 semillas por (dimset, nivel ∈ {5e3, 5e4}) con
aserción de presupuesto exacto, mide segundos por corrida y extrapola a la
matriz completa. Escribe results/cooperative/fase3/costo_estimado.json.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

os.environ.setdefault("RUNS", "3")
import scripts.cec_harness.run_fase3_confirmatorio as F  # noqa: E402
from problems.continuous.cec_problem import CECProblem, FESLimitProblem  # noqa: E402
from algorithms.minion_adapter import LSHADE_M  # noqa: E402

N_FULL, N_PILOT, RUNS_FULL, N_PAIRS = 70, 12, 51, 3
out = {"per_run_s": {}, "estimate_core_h": {}, "note": "1 funcion (CEC2014 F4) x 3 semillas; extrapolado"}
for dimset in ("10", "50"):
    F.DIMSET = dimset
    for level in (5000, 50000):
        per = {}
        for arm in F.ARMS:
            t = time.time()
            for s in range(3):
                F._run_arm(arm, "DE", "GA", "CEC2014", 4, level, 10000 + s)
            per[arm] = (time.time() - t) / 3
        t = time.time()
        for s in range(3):
            algo = LSHADE_M(FESLimitProblem(CECProblem("CEC2014", 4, F._dim("CEC2014")), max_fes=level),
                            seed=10000 + s, minion_options=F.lshade_options(F._dim("CEC2014")))
            algo.execute()
            assert algo.fes_used <= level, algo.fes_used
        per["LSHADE"] = (time.time() - t) / 3
        per["LSHADE_fes_used"] = algo.fes_used
        out["per_run_s"][f"dim{dimset}_{level}"] = per
        pair_s = sum(per[a] for a in F.ARMS)
        print(f"dim{dimset} {level}: " + " ".join(f"{a}={per[a]:.2f}s" for a in F.ARMS + ["LSHADE"]), flush=True)
        # extrapolación lineal en FES a 5e5 y 5e6 (12 funcs)
        base = level
        for lv, nf in ((5000, N_FULL), (50000, N_FULL), (500000, N_FULL), (5000000, N_PILOT)):
            scale = lv / base
            core_h = (pair_s * N_PAIRS + per["LSHADE"]) * scale * nf * RUNS_FULL / 3600
            out["estimate_core_h"].setdefault(f"dim{dimset}_{lv}", {})[f"from_{base}"] = round(core_h, 1)
print(json.dumps(out["estimate_core_h"], indent=1))
os.makedirs(os.path.join(F._REPO, "results", "cooperative", "fase3_v05"), exist_ok=True)
with open(os.path.join(F._REPO, "results", "cooperative", "fase3_v05", "costo_estimado.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("SMOKE_OK")
