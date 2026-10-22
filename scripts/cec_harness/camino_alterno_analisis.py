"""Análisis pre-registrado del camino alterno (enmienda v0.6) sobre
results/cooperative/camino_alterno_v06/. Por par × nivel, Holm sobre las 71
funciones, Wilcoxon de rangos con signo (errores < 1e-8 = 0), rank-biserial.

Claims (criterios fijados en v0.6 antes de correr):
  G1 protección   CTRLg vs CTRLn  y  CTRLg no inferior a C1_div (peor ≤ 7/71)
  G1b detección   entre las funciones donde el control daña (CTRLn_noSL peor que
                  C1_div con Holm), fracción donde CTRLg mejora a CTRLn
  G2 canal real   C3p vs C2p  y  C3p no inferior a C1_div
  G3 componentes  CTRLg vs CTRLg_noSL (stop-loss), CTRLg vs CTRLg_nomem (memoria),
                  CTRLn vs CTRLn_noSL (stop-loss sin admisión)
  G4 costo        BENg vs BENn (falsos positivos), MODg vs MODn (daño sutil)
  contexto        C2p/C3p vs C1_div, C3p vs ABL, C1_div vs SBS
Éxito G1 (gate validado como componente de seguridad): en ambos presupuestos,
CTRLg mejor>peor vs CTRLn con mediana r ≥ 0.3 y no inferior a C1_div, en ≥ 2 de 3 pares.
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
OUT = os.environ.get("CA_OUT", os.path.join(_REPO, "results", "cooperative", "camino_alterno_v06"))
PAIRS = ["GWO+GA", "DE+GA", "PSO+ACO"]
NONINF_MAX = 7


def holm(pv):
    m = len(pv); order = sorted(range(m), key=lambda i: pv[i]); adj = [0.0] * m; run = 0.0
    for k, i in enumerate(order):
        run = max(run, (m - k) * pv[i]); adj[i] = min(1.0, run)
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


def contrast(cells, A, B):
    pv, rs = zip(*[paired(c["errors"][A], c["errors"][B]) for c in cells])
    adj = holm(list(pv))
    better = [c["key"] for c, h, r in zip(cells, adj, rs) if h < 0.05 and r > 0]
    worse = [c["key"] for c, h, r in zip(cells, adj, rs) if h < 0.05 and r < 0]
    return {"better": len(better), "equal": len(cells) - len(better) - len(worse), "worse": len(worse),
            "median_r": round(float(np.median(rs)), 3), "n": len(cells), "better_set": better, "worse_set": worse}


CONTRASTS = {
    "G1_CTRLg_vs_CTRLn": ("CTRLg", "CTRLn"), "G1_CTRLg_vs_C1div": ("CTRLg", "C1_div"),
    "harm_CTRLn_noSL_vs_C1div": ("CTRLn_noSL", "C1_div"),
    "G2_C3p_vs_C2p": ("C3p", "C2p"), "G2_C3p_vs_C1div": ("C3p", "C1_div"),
    "G3_CTRLg_vs_CTRLg_noSL": ("CTRLg", "CTRLg_noSL"), "G3_CTRLg_vs_CTRLg_nomem": ("CTRLg", "CTRLg_nomem"),
    "G3_CTRLn_vs_CTRLn_noSL": ("CTRLn", "CTRLn_noSL"),
    "G4_BENg_vs_BENn": ("BENg", "BENn"), "G4_MODg_vs_MODn": ("MODg", "MODn"),
    "ctx_C2p_vs_C1div": ("C2p", "C1_div"), "ctx_C3p_vs_ABL": ("C3p", "ABL"), "ctx_C1div_vs_SBS": ("C1_div", "SBS"),
}


def analyse(pair, level):
    cells = []
    for f in sorted(glob.glob(os.path.join(OUT, f"{pair.replace('+', '')}_{level}", "*.json"))):
        c = json.load(open(f)); c["key"] = os.path.basename(f)[:-5]; cells.append(c)
    if not cells:
        return None
    med = np.array([[np.median(c["errors"]["C0_A"]), np.median(c["errors"]["C0_B"])] for c in cells])
    rk = np.vstack([rankdata(r) for r in med]).mean(0)
    sbs = "C0_A" if rk[0] <= rk[1] else "C0_B"
    for c in cells:
        c["errors"]["SBS"] = c["errors"][sbs]
    res = {"n": len(cells), "SBS": cells[0]["solvers"][0 if sbs == "C0_A" else 1],
           "contrasts": {k: contrast(cells, *v) for k, v in CONTRASTS.items()}}
    harm = set(res["contrasts"]["harm_CTRLn_noSL_vs_C1div"]["worse_set"])
    det = set(res["contrasts"]["G1_CTRLg_vs_CTRLn"]["better_set"])
    res["G1b_deteccion"] = {"n_funciones_daninas": len(harm), "detectadas": len(harm & det),
                            "tasa": round(len(harm & det) / len(harm), 3) if harm else None}
    # Omnibus del protocolo (v0.1 §8): Friedman + Iman-Davenport + Shaffer sobre
    # la mediana de 51 corridas por función (empate a 1e-8)
    arms = ["C0_A", "C0_B", "C1_div", "C2p", "C3p", "ABL", "CTRLn", "CTRLg"]
    names = [cells[0]["solvers"][0], cells[0]["solvers"][1]] + arms[2:]
    M = np.array([[float(np.median(c["errors"][x])) for x in arms] for c in cells])
    M = np.where(M < 1e-8, 0.0, M)
    fr = friedman_test(M); N, k = M.shape; chi2 = fr["statistic"]
    ff = (N - 1) * chi2 / (N * (k - 1) - chi2) if N * (k - 1) - chi2 > 0 else float("inf")
    res["friedman"] = {"chi2": round(chi2, 3), "df": fr["df"], "p": fr["p_value"], "iman_davenport_F": round(ff, 3),
                       "p_FF": float(f_dist.sf(ff, k - 1, (k - 1) * (N - 1))),
                       "mean_ranks": dict(zip(names, [round(x, 3) for x in fr["mean_ranks"]]))}
    res["shaffer"] = shaffer_posthoc(M, names)
    res["mech_por_corrida"] = {arm: {k: round(sum(c["mech_stats"][arm].get(k, 0) for c in cells) / (len(cells) * c["runs"]), 2)
                                     for k in ("proposed", "accepted", "rolled_back")}
                               for arm in ("C3p", "CTRLg", "CTRLg_noSL", "CTRLg_nomem", "BENg", "MODg")}
    return res


def main():
    levels = sorted({int(d.rsplit("_", 1)[1]) for d in glob.glob(os.path.join(OUT, "*_*")) if d.rsplit("_", 1)[1].isdigit()})
    out = {"levels": levels, "configs": {}, "G1_exito": {}}
    for pair in PAIRS:
        oks = []
        for lv in levels:
            r = analyse(pair, lv)
            if r is None:
                continue
            out["configs"][f"{pair}_{lv}"] = r
            a, b = r["contrasts"]["G1_CTRLg_vs_CTRLn"], r["contrasts"]["G1_CTRLg_vs_C1div"]
            oks.append(a["better"] > a["worse"] and a["median_r"] >= 0.3 and b["worse"] <= NONINF_MAX)
        out["G1_exito"][pair] = {"por_presupuesto": oks, "cumple": bool(oks) and all(oks)}
    out["G1_gate_validado"] = sum(v["cumple"] for v in out["G1_exito"].values()) >= 2
    out["provenance"] = provenance()
    with open(os.path.join(OUT, "analisis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    fmt = lambda t: f"{t['better']}/{t['equal']}/{t['worse']} ({t['median_r']})"
    cols = ["G1_CTRLg_vs_CTRLn", "G1_CTRLg_vs_C1div", "harm_CTRLn_noSL_vs_C1div", "G2_C3p_vs_C2p", "G2_C3p_vs_C1div",
            "G3_CTRLg_vs_CTRLg_noSL", "G3_CTRLg_vs_CTRLg_nomem", "G3_CTRLn_vs_CTRLn_noSL", "G4_BENg_vs_BENn",
            "G4_MODg_vs_MODn", "ctx_C2p_vs_C1div", "ctx_C3p_vs_ABL", "ctx_C1div_vs_SBS"]
    lines = ["# Camino alterno (v0.6) — mejor/igual/peor con Holm sobre funciones (mediana r)\n",
             "| celda | " + " | ".join(cols) + " | detección G1b |", "|" + "---|" * (len(cols) + 2)]
    for k, r in out["configs"].items():
        d = r["G1b_deteccion"]
        lines.append(f"| {k} (n={r['n']}) | " + " | ".join(fmt(r["contrasts"][c]) for c in cols)
                     + f" | {d['detectadas']}/{d['n_funciones_daninas']} |")
    lines += ["", "## Friedman + Iman-Davenport (rangos medios; menor = mejor)", ""]
    for k, r in out["configs"].items():
        fz = r["friedman"]
        lines.append(f"- {k}: F_F={fz['iman_davenport_F']} p={fz['p_FF']:.2g}; " + ", ".join(f"{a} {v}" for a, v in fz["mean_ranks"].items()))
    lines += ["", f"G1 por par: {out['G1_exito']}", f"**Gate validado como componente de seguridad (≥2/3 pares): {out['G1_gate_validado']}**"]
    open(os.path.join(OUT, "analisis.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
