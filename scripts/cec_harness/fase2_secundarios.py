"""Fase 2 — contrastes secundarios pre-registrados (v0.1 §8) sobre el piloto:
candidatos vs SBS del par, B vs C1_island (¿aporta la admisión/rollback sobre
la migración fija?), y actividad del mecanismo por brazo. Lee las celdas del
piloto y escribe results/cooperative/fase2_v05/piloto_secundarios.json"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
PIL = os.path.join(_REPO, "results", "cooperative", "fase2_v05", "piloto")
SBS = {"GWOGA": "SBS_A", "DEGA": "SBS_B", "PSOACO": "SBS_B"}   # GWO, GA, ACO


def holm(pv):
    m = len(pv); order = sorted(range(m), key=lambda i: pv[i]); adj = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pv[i]); adj[i] = min(1.0, run)
    return adj


def paired(a, b):
    a = np.where(np.asarray(a, float) < 1e-8, 0.0, np.asarray(a, float))
    b = np.where(np.asarray(b, float) < 1e-8, 0.0, np.asarray(b, float))
    d = a - b; dd = d[d != 0]
    if len(dd) == 0:
        return 1.0, 0.0
    _, p = wilcoxon(a, b, zero_method="wilcox")
    r = rankdata(np.abs(dd))
    return float(p), float((r[dd < 0].sum() - r[dd > 0].sum()) / r.sum())


def table(cells, A, B):
    pv, rs = [], []
    for c in cells:
        p, r = paired(c["errors"][A], c["errors"][B]); pv.append(p); rs.append(r)
    adj = holm(pv)
    return {"wins": sum(1 for h, r in zip(adj, rs) if h < 0.05 and r > 0),
            "losses": sum(1 for h, r in zip(adj, rs) if h < 0.05 and r < 0),
            "median_r": round(float(np.median(rs)), 2), "n": len(cells)}


out = {}
for d in sorted(glob.glob(os.path.join(PIL, "*"))):
    key = os.path.basename(d); pair = key.split("_")[0]
    cells = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(d, "*.json")))]
    if not cells:
        continue
    sbs = SBS[pair]
    res = {"vs_SBS": {arm: table(cells, arm, sbs) for arm in ["C1_div", "C1_shared", "C1_island", "A", "B", "C"]},
           "B_vs_C1_island": table(cells, "B", "C1_island"),
           "C1_island_vs_C1_shared": table(cells, "C1_island", "C1_shared"),
           "C1_shared_vs_C1_div": table(cells, "C1_shared", "C1_div"),
           "A_vs_C1_island": table(cells, "A", "C1_island"),
           "mech": {}}
    for arm in ["C1_island", "B", "C", "BENg", "BENn"]:
        agg = {}
        for c in cells:
            for k, v in c["mech_stats"].get(arm, {}).items():
                agg[k] = agg.get(k, 0) + v
        res["mech"][arm] = {k: round(v / (len(cells) * cells[0]["runs"]), 2) for k, v in agg.items()
                            if k in ("proposed", "accepted", "rejected", "rolled_back", "kept")}
    out[key] = res
    print(f"== {key} ==")
    print("  vs SBS:", {a: f"{t['wins']}/{t['losses']} r={t['median_r']}" for a, t in res["vs_SBS"].items()})
    print(f"  B vs C1_island: {res['B_vs_C1_island']['wins']}/{res['B_vs_C1_island']['losses']} r={res['B_vs_C1_island']['median_r']}"
          f" | A vs C1_island: {res['A_vs_C1_island']['wins']}/{res['A_vs_C1_island']['losses']} r={res['A_vs_C1_island']['median_r']}")
    print("  mech (por corrida):", {a: v for a, v in res["mech"].items() if a in ("C1_island", "B")})
with open(os.path.join(_REPO, "results", "cooperative", "fase2_v05", "piloto_secundarios.json"), "w") as fh:
    json.dump(out, fh, indent=1)
