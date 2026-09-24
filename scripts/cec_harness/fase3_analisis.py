"""Fase 3 — análisis pre-registrado (v0.1 §8-9, enmiendas v0.4/v0.5) sobre las
celdas crudas de results/cooperative/fase3_v05/dim{10,50}/.

Por configuración (dimset × nivel) y par:
  * primario:   C1_island vs C1_div   (Wilcoxon signo por función, Holm, r-biserial)
  * atribución (v0.5, co-primario): C1_island vs C1_shared (mismo runner sin migrar)
  * secundarios: C1_island vs SBS, vs VBS (cota), vs L-SHADE (H5); B vs C1_island;
                 C1_div vs SBS (efecto portafolio, contexto)
  * Friedman + Iman-Davenport + Shaffer sobre {C0_A, C0_B, C1_div, C1_island, B, LSHADE}
    con la mediana de 51 corridas por función
  * exploratorio (etiquetado): por clase taxonómica
Decisión §9: por dimset, C1_island mejor>peor vs C1_div con Holm en ≥3 de 4
presupuestos (10D); H5: no inferior a L-SHADE (wins ≥ losses) en ≥2 presupuestos.

Uso: python scripts/cec_harness/fase3_analisis.py [10|50]
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon, rankdata, f as f_dist  # noqa: E402

from scripts.cec_harness.stats import friedman_test, shaffer_posthoc  # noqa: E402
from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DIMSET = sys.argv[1] if len(sys.argv) > 1 else "10"
ROOT = os.environ.get("FASE3_OUT", os.path.join(_REPO, "results", "cooperative", "fase3_v05"))
BASE = os.path.join(ROOT, f"dim{DIMSET}")
PAIRS = ["GWO+GA", "DE+GA", "PSO+ACO"]
TAX = {"CEC2014": {**{f: "unimodal" for f in range(1, 4)}, **{f: "multimodal" for f in range(4, 17)},
                   **{f: "hibrida" for f in range(17, 23)}, **{f: "composicion" for f in range(23, 31)}},
       "CEC2017": {**{f: "unimodal" for f in range(1, 4)}, **{f: "multimodal" for f in range(4, 11)},
                   **{f: "hibrida" for f in range(11, 21)}, **{f: "composicion" for f in range(21, 31)}},
       "CEC2022": {1: "unimodal", **{f: "multimodal" for f in range(2, 6)},
                   **{f: "hibrida" for f in range(6, 9)}, **{f: "composicion" for f in range(9, 13)}}}


def holm(pv):
    m = len(pv); order = sorted(range(m), key=lambda i: pv[i]); adj = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pv[i]); adj[i] = min(1.0, run)
    return adj


def paired(a, b):
    """Wilcoxon de rangos con signo (empates descartados, CEC: error < 1e-8 = 0)
    y rank-biserial pareado con rangos promedio; r > 0 = `a` mejor."""
    a = np.where(np.asarray(a, float) < 1e-8, 0.0, np.asarray(a, float))
    b = np.where(np.asarray(b, float) < 1e-8, 0.0, np.asarray(b, float))
    d = a - b; dd = d[d != 0]
    if len(dd) == 0:
        return 1.0, 0.0
    _, p = wilcoxon(a, b, zero_method="wilcox")
    r = rankdata(np.abs(dd))
    return float(p), float((r[dd < 0].sum() - r[dd > 0].sum()) / r.sum())


def contrast(cells, A, B, sel=None):
    cells = [c for c in cells if sel is None or sel(c)]
    pv, rs = [], []
    for c in cells:
        p, r = paired(c["err"][A], c["err"][B]); pv.append(p); rs.append(r)
    adj = holm(pv)
    w = sum(1 for h, r in zip(adj, rs) if h < 0.05 and r > 0)
    l = sum(1 for h, r in zip(adj, rs) if h < 0.05 and r < 0)
    return {"better": w, "equal": len(cells) - w - l, "worse": l,
            "median_r": round(float(np.median(rs)), 3) if rs else None, "n": len(cells)}


def load(pair, level):
    d = os.path.join(BASE, f"{pair.replace('+', '')}_{level}")
    ls = os.path.join(BASE, f"LSHADE_{level}")
    cells = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        c = json.load(open(f))
        key = f"{c['suite']}_F{c['fnum']}"
        lp = os.path.join(ls, key + ".json")
        if not os.path.exists(lp):
            continue
        err = dict(c["errors"])
        err["LSHADE"] = json.load(open(lp))["errors"]["LSHADE"]
        # VBS = todo el presupuesto al mejor solver DE ESA FUNCIÓN (mediana), no
        # el mínimo por corrida (eso sería un oráculo con 2B)
        va, vb = np.median(err["C0_A"]), np.median(err["C0_B"])
        err["VBS"] = list(err["C0_A"] if va <= vb else err["C0_B"])
        cells.append({"key": key, "suite": c["suite"], "fnum": c["fnum"], "tax": TAX[c["suite"]][c["fnum"]],
                      "solvers": c["solvers"], "err": err, "mech": c["mech_stats"], "wall_s": c.get("wall_s")})
    return cells


def analyse(pair, level):
    cells = load(pair, level)
    if not cells:
        return None
    a, b = cells[0]["solvers"]
    # SBS por configuración: el C0 con menor rango medio (mediana por función)
    med = {arm: [float(np.median(c["err"][arm])) for c in cells] for arm in ["C0_A", "C0_B"]}
    rk = np.vstack([rankdata([med["C0_A"][i], med["C0_B"][i]]) for i in range(len(cells))]).mean(0)
    sbs = "C0_A" if rk[0] <= rk[1] else "C0_B"
    for c in cells:
        c["err"]["SBS"] = c["err"][sbs]
    out = {"pair": pair, "level": level, "n_funcs": len(cells), "SBS": {"arm": sbs, "solver": a if sbs == "C0_A" else b},
           "primario": {"C1_island_vs_C1_div": contrast(cells, "C1_island", "C1_div"),
                        "atribucion_C1_island_vs_C1_shared": contrast(cells, "C1_island", "C1_shared")},
           "secundarios": {k: contrast(cells, x, y) for k, (x, y) in {
               "C1_shared_vs_C1_div": ("C1_shared", "C1_div"),
               "C1_island_vs_SBS": ("C1_island", "SBS"), "C1_island_vs_VBS": ("C1_island", "VBS"),
               "C1_island_vs_LSHADE": ("C1_island", "LSHADE"), "B_vs_C1_island": ("B", "C1_island"),
               "B_vs_C1_div": ("B", "C1_div"), "C1_div_vs_SBS": ("C1_div", "SBS"),
               "C1_div_vs_LSHADE": ("C1_div", "LSHADE"), "SBS_vs_LSHADE": ("SBS", "LSHADE")}.items()},
           "exploratorio_taxonomia": {t: contrast(cells, "C1_island", "C1_div", lambda c, t=t: c["tax"] == t)
                                      for t in ["unimodal", "multimodal", "hibrida", "composicion"]}}
    # Friedman + Iman-Davenport + Shaffer sobre medianas
    algos = ["C0_A", "C0_B", "C1_div", "C1_shared", "C1_island", "B", "LSHADE"]
    names = [a, b, "C1_div", "C1_shared", "C1_island", "B", "LSHADE"]
    M = np.array([[float(np.median(c["err"][x])) for x in algos] for c in cells])
    M = np.where(M < 1e-8, 0.0, M)
    fr = friedman_test(M)
    N, k = M.shape
    chi2 = fr["statistic"]
    ff = (N - 1) * chi2 / (N * (k - 1) - chi2) if N * (k - 1) - chi2 > 0 else float("inf")
    p_ff = float(f_dist.sf(ff, k - 1, (k - 1) * (N - 1)))
    sh = shaffer_posthoc(M, names)
    out["friedman"] = {"chi2": round(chi2, 3), "df": fr["df"], "p": fr["p_value"],
                       "iman_davenport_F": round(ff, 3), "p_FF": p_ff,
                       "mean_ranks": dict(zip(names, [round(x, 3) for x in fr["mean_ranks"]]))}
    out["shaffer"] = sh
    out["mech_por_corrida"] = {arm: {kk: round(sum(c["mech"][arm].get(kk, 0) for c in cells) / (len(cells) * 51), 2)
                                     for kk in ("proposed", "accepted", "rejected", "rolled_back", "kept")}
                               for arm in ["C1_island", "B"]}
    runs = len(cells[0]["err"]["C1_div"])
    for arm in out["mech_por_corrida"]:
        out["mech_por_corrida"][arm] = {kk: round(v * 51 / runs, 2) for kk, v in out["mech_por_corrida"][arm].items()}
    out["wall_h_total"] = round(sum(c["wall_s"] or 0 for c in cells) / 3600, 2)
    return out


def main():
    levels = sorted({int(os.path.basename(d).split("_")[1]) for d in glob.glob(os.path.join(BASE, "LSHADE_*"))})
    res = {"dimset": DIMSET, "levels": levels, "configs": {}, "decision": {}}
    for pair in PAIRS:
        for lv in levels:
            r = analyse(pair, lv)
            if r:
                res["configs"][f"{pair}_{lv}"] = r
        # decisión §9 por par
        prim = [res["configs"][f"{pair}_{lv}"]["primario"]["C1_island_vs_C1_div"]
                for lv in levels if f"{pair}_{lv}" in res["configs"]]
        h5 = [res["configs"][f"{pair}_{lv}"]["secundarios"]["C1_island_vs_LSHADE"]
              for lv in levels if f"{pair}_{lv}" in res["configs"]]
        attr = [res["configs"][f"{pair}_{lv}"]["primario"]["atribucion_C1_island_vs_C1_shared"]
                for lv in levels if f"{pair}_{lv}" in res["configs"]]
        n_ok = sum(1 for t in prim if t["better"] > t["worse"])
        n_attr = sum(1 for t, u in zip(prim, attr) if t["better"] > t["worse"] and u["better"] > u["worse"])
        res["decision"][pair] = {
            "presupuestos_evaluados": len(prim), "mejor_que_peor_vs_C1_div": n_ok,
            "y_atribuible_a_migracion": n_attr,
            "criterio_10D_3_de_4": n_attr >= 3 if len(prim) >= 4 else None,
            "criterio_parcial_todos": n_attr == len(prim) if prim else None,
            "H5_no_inferior_LSHADE_n_presupuestos": sum(1 for t in h5 if t["better"] >= t["worse"]),
        }
    res["provenance"] = provenance()
    os.makedirs(ROOT, exist_ok=True)
    outp = os.path.join(ROOT, f"analisis_dim{DIMSET}.json")
    with open(outp, "w") as fh:
        json.dump(res, fh, indent=1)
    # tabla markdown
    lines = [f"# Fase 3 (v0.5, benchmark oficial) — dim{DIMSET} (n funcs, better/equal/worse, mediana r)\n",
             "| celda | SBS | C1_island vs C1_div | vs C1_shared (atribución) | C1_shared vs C1_div | vs SBS | vs VBS | vs L-SHADE | B vs C1_island | C1_div vs SBS | rangos Friedman (p_FF) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    fmt = lambda t: f"{t['better']}/{t['equal']}/{t['worse']} ({t['median_r']})"
    for key, r in res["configs"].items():
        s = r["secundarios"]
        rk = ", ".join(f"{k} {v}" for k, v in r["friedman"]["mean_ranks"].items())
        lines.append(f"| {key} (n={r['n_funcs']}) | {r['SBS']['solver']} | {fmt(r['primario']['C1_island_vs_C1_div'])} | "
                     f"{fmt(r['primario']['atribucion_C1_island_vs_C1_shared'])} | {fmt(s['C1_shared_vs_C1_div'])} | "
                     f"{fmt(s['C1_island_vs_SBS'])} | {fmt(s['C1_island_vs_VBS'])} | {fmt(s['C1_island_vs_LSHADE'])} | "
                     f"{fmt(s['B_vs_C1_island'])} | {fmt(s['C1_div_vs_SBS'])} | {rk} (p={r['friedman']['p_FF']:.2g}) |")
    lines.append("\n## Decisión (v0.1 §9)\n")
    for p, d in res["decision"].items():
        lines.append(f"- {p}: {d}")
    with open(outp.replace(".json", ".md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
