"""Calcula las tablas de resultados de la fase positiva (v13) desde los
datos crudos de results/cooperative/ (benchmark oficial, enmiendas v0.5 y v0.6).

Solo calcula y escribe las salidas: no contiene ni modifica el texto del paper.
Cada tabla se identifica por su marcador (FASE1, PILOTO, ..., CANAL_50); el mapa
tabla -> datos -> script está en README_FASE_POSITIVA.md, sección 6.

Fuentes (crudos por celda, 51 corridas), relativas a results/cooperative/:
  fase1_v05/cotas_fase1.json, fase1_v05/e2_effect_logs.json   (Fase 1)
  fase2_v05/piloto/<PAR>_<B>/*.json                           (piloto)
  camino_alterno_v06{,_dim50}/<PAR>_<B>/*.json                (camino alterno)
  camino_alterno_v06{,_dim50}/analisis.json                   (post-hoc de Shaffer
      y control cruzado de SBS, contexto C1_div vs SBS, G1 y Friedman)
Los enunciados de H1-H5 se verifican contra
docs/preregistro_fase_positiva/PREREGISTRO_v0.1_rodrigo.md (sección 2).

Estadística: Wilcoxon de rangos con signo por función (scipy.stats.wilcoxon,
zero_method='wilcox', method='auto': con 51 corridas es la aproximación asintótica
salvo que queden <= 50 pares no nulos sin empates; errores < 1e-8 = 0, empates
descartados), Holm sobre la familia de funciones, rank-biserial pareado
con rangos promedio sobre los pares no empatados; Friedman (χ², gl = k − 1) con
corrección de Iman-Davenport sobre la mediana de 51 corridas. SBS por
configuración: el solver aislado con menor rango medio de las medianas (empate:
primer solver del par), como en camino_alterno_analisis.py.

Salidas (en --salida):
  tablas_v13.json                     cifras de todas las tablas
  tablas_v13_preview.md               todas las tablas renderizadas (Markdown)
  tablas_v13_supl.json / .md          material suplementario: S0 contenido; S1-S7
                                      (Shaffer, ómnibus a 50D y sin controles,
                                      mecanismo a 50D, ómnibus por banco); S8
                                      sensibilidad de los contrastes, S9 robustez
                                      por banco y sin repetidas, S10 seis brazos con
                                      Shaffer por banco (D36)
  suplementario_v13_estadisticos.csv  media, mediana y desviación por celda y brazo

Uso (desde la raíz del repositorio):
  .venv/bin/python scripts/cec_harness/tablas_paper_v13.py --salida DIR
      [--resultados RUTA]   (por defecto, results/cooperative del repositorio)
"""
import argparse
import csv
import glob
import json
import math
import os
import re
from itertools import combinations

import numpy as np
from scipy.stats import f as f_dist
from scipy.stats import binomtest, friedmanchisquare, norm, rankdata, wilcoxon

_REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RESULTS = os.path.join(_REPO, "results", "cooperative")
PAIRS = [("GWOGA", "GWO+GA"), ("DEGA", "DE+GA"), ("PSOACO", "PSO+ACO")]
LEVELS = [5000, 50000]
LV = {5000: "5·10^3^", 50000: "5·10^4^", 500000: "5·10^5^"}
NONINF_MAX = 7
MENOS = "−"
# Orden de las tablas en el artículo (la numeración la fija la prosa; aquí solo
# se usa para la vista previa).
ORDEN = ["FASE1", "PILOTO", "PILOTO_SEC", "HIPOTESIS", "G1_10", "COMP_10", "MECH_10", "CANAL_10", "FRIED_10",
         "TAX_10", "G1_50", "COMP_50", "CANAL_50"]
PRIMERA_TABLA = 3
ARMS8 = ["C0_A", "C0_B", "C1_div", "C2p", "C3p", "ABL", "CTRLn", "CTRLg"]
ARMS_REALES = ["C0_A", "C0_B", "C1_div", "C2p", "C3p", "ABL"]
MECH_ARMS = [("CTRLg", "CTRLg (adversarial)"), ("CTRLg_nomem", "CTRLg_nomem (adversarial, sin memoria)"),
             ("MODg", "MODg (moderado)"), ("BENg", "BENg (benigno)"), ("C3p", "C3p (canal real)"),
             ("ABL", "ABL (azar)")]
ARM_LABEL = {"C0_A": "C0_A (primer solver aislado)", "C0_B": "C0_B (segundo solver aislado)"}
# Enunciados copiados literalmente de
# docs/preregistro_fase_positiva/PREREGISTRO_v0.1_rodrigo.md §2 (los exponentes
# Unicode ³ ⁴ ⁵ del original se escriben con la sintaxis de superíndice de pandoc).
ENUNCIADOS = {
    "H1": "Un controlador reactivo de presupuesto guiado por mejora relativa supera a C1_div en más funciones "
          "de las que pierde, a 5·10^3^ y 5·10^4^ en 10D.",
    "H2": "La migración de élite admitida por estado y revertida por stop-loss supera a la migración fija "
          "(C1_island) y a C1_div.",
    "H3": "La selección de régimen por efecto observado supera a la selección por intención fija (C3p) y no es "
          "inferior a C1_div.",
    "H4": "La ventaja de H1 o H2 se mantiene a 5·10^5^ con Δ fijo y en 50D.",
    "H5": "La cooperación no es inferior a L-SHADE aislado a igual presupuesto. Si se rechaza, el claim se acota "
          "al portafolio de los mismos solvers.",
}
PREREG = "docs/preregistro_fase_positiva/PREREGISTRO_v0.1_rodrigo.md"  # relativo a la raíz del repositorio


# ------------------------------------------------------------------ estadística --
def _t(x):
    x = np.asarray(x, float)
    return np.where(x < 1e-8, 0.0, x)


def paired(a, b):
    a, b = _t(a), _t(b)
    d = a - b; dd = d[d != 0]
    if len(dd) == 0:
        return 1.0, 0.0
    _, p = wilcoxon(a, b, zero_method="wilcox")
    r = rankdata(np.abs(dd))
    return float(p), float((r[dd < 0].sum() - r[dd > 0].sum()) / r.sum())


def holm(pv):
    m = len(pv); order = sorted(range(m), key=lambda i: pv[i]); adj = [0.0] * m; run = 0.0
    for k, i in enumerate(order):
        run = max(run, (m - k) * pv[i]); adj[i] = min(1.0, run)
    return adj


def contrast(cells, A, B, sel=None, runs=None):
    """Contraste pareado por función. sel filtra funciones; runs (índices) restringe las corridas usadas."""
    cells = [c for c in cells if sel is None or sel(c)]
    if not cells:
        return None
    if runs is None:
        pv, rs = zip(*[paired(c["errors"][A], c["errors"][B]) for c in cells])
    else:
        pv, rs = zip(*[paired(np.asarray(c["errors"][A], float)[runs], np.asarray(c["errors"][B], float)[runs])
                       for c in cells])
    adj = holm(list(pv))
    better = [c["key"] for c, h, r in zip(cells, adj, rs) if h < 0.05 and r > 0]
    worse = [c["key"] for c, h, r in zip(cells, adj, rs) if h < 0.05 and r < 0]
    return {"better": len(better), "worse": len(worse), "equal": len(cells) - len(better) - len(worse),
            "n": len(cells), "median_r": float(np.median(rs)), "better_set": better, "worse_set": worse,
            "r_por_funcion": dict(zip([c["key"] for c in cells], rs))}


def crit_piloto(t):
    """Criterio pre-registrado del piloto en un presupuesto: mejor > peor, r ≥ 0.3 y peor ≤ 2."""
    return t["better"] > t["worse"] and t["median_r"] >= 0.3 and t["worse"] <= 2


def sg(x, nd=2):
    """Número con signo explícito y signo menos tipográfico (U+2212)."""
    return f"{x:+.{nd}f}".replace("-", MENOS)


def fmt(t, eq=True, short=False):
    if t is None:
        return "—"
    core = f"{t['better']}/{t['equal']}/{t['worse']}" if eq else f"{t['better']}/{t['worse']}"
    return core if short else f"{core} ({sg(t['median_r'])})"


def fmt_p(p):
    """p en la forma a·10^b^ (superíndice de pandoc) con signo menos tipográfico."""
    if p >= 1e-3:
        s = f"{p:.3f}"
        # que el redondeo no cruce el umbral de significación (p. ej., 0.0497 → «0.050»)
        return s if (p < 0.05) == (float(s) < 0.05) else f"{p:.4f}"
    m, e = f"{p:.1e}".split("e")
    return f"{m}·10^{str(int(e)).replace('-', MENOS)}^"


# Los p de Shaffer de analisis.json se calculan como 2·(1 − Φ(|z|)), que en doble
# precisión no baja de 2.2·10^−16 (y vale 0 por debajo): bajo este piso solo se
# reporta la cota.
PISO_P_SHAFFER = 1e-10


def fmt_p_shaffer(p):
    return f"p < 10^{MENOS}10^" if p < PISO_P_SHAFFER else f"p = {fmt_p(p)}"


def bold(s, cond):
    return f"**{s}**" if cond else s


UMBRAL_MEJOR, UMBRAL_R = 20, 0.3


def gana(t):
    """Umbral sobre 71 funciones (v0.2 §A, G1): mejor ≥ 20 y mediana del rank-biserial ≥ 0.3."""
    return t is not None and t["better"] >= UMBRAL_MEJOR and t["median_r"] >= UMBRAL_R


def fmtb(t):
    return bold(fmt(t), gana(t))


def friedman(cells, arms):
    M = _t(np.array([[np.median(c["errors"][a]) for a in arms] for c in cells]))
    chi2, p = friedmanchisquare(*[M[:, j] for j in range(M.shape[1])])
    N, k = M.shape
    ff = (N - 1) * chi2 / (N * (k - 1) - chi2)
    ranks = np.vstack([rankdata(r) for r in M]).mean(0)
    return {"chi2": float(chi2), "df": int(k - 1), "p_chi2": float(p), "F_F": float(ff),
            "df_FF": [int(k - 1), int((k - 1) * (N - 1))], "p_FF": float(f_dist.sf(ff, k - 1, (k - 1) * (N - 1))),
            "N": int(N), "k": int(k), "sd_rangos_medios": float(np.std(ranks, ddof=1)),
            "mean_ranks": dict(zip(arms, map(float, ranks)))}


def sbs_de(cells, a="C0_A", b="C0_B"):
    """SBS por configuración: menor rango medio de las medianas (empate: el primer solver)."""
    med = np.array([[np.median(c["errors"][a]), np.median(c["errors"][b])] for c in cells])
    rk = np.vstack([rankdata(r) for r in med]).mean(0)
    return (a if rk[0] <= rk[1] else b), (0 if rk[0] <= rk[1] else 1), [float(x) for x in rk]


def mech(cells, arms):
    """Propuestas, aceptadas y revertidas por corrida; tasas de admisión y de reversión."""
    R = sum(c["runs"] for c in cells)
    out = {}
    for a in arms:
        s = {k: sum(c["mech_stats"][a].get(k, 0) for c in cells) for k in ("proposed", "accepted", "rolled_back", "kept")}
        out[a] = {"propuestas": s["proposed"] / R, "aceptadas": s["accepted"] / R, "revertidas": s["rolled_back"] / R,
                  "conservadas": s["kept"] / R, "admision": s["accepted"] / s["proposed"],
                  "reversion": s["rolled_back"] / (s["rolled_back"] + s["kept"]) if s["rolled_back"] + s["kept"] else float("nan")}
    return out


# ---------------------------------------------------------------------- datos --
TAX = {"CEC2014": lambda f: "U" if f <= 3 else "M" if f <= 16 else "H" if f <= 22 else "C",
       "CEC2017": lambda f: "U" if f <= 3 else "M" if f <= 10 else "H" if f <= 20 else "C",
       "CEC2022": lambda f: "U" if f == 1 else "M" if f <= 5 else "H" if f <= 8 else "C"}


def load(root, pdir, lv):
    out = []
    for p in sorted(glob.glob(os.path.join(root, f"{pdir}_{lv}", "*.json"))):
        c = json.load(open(p))
        c["key"] = os.path.basename(p)[:-5]
        suite, f = c["key"].rsplit("_F", 1)
        c["tax"] = TAX[suite](int(f))
        out.append(c)
    return out


def table(header, rows, sep=None):
    return "\n".join(["| " + " | ".join(header) + " |", sep or ("|" + "---|" * len(header))]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def ttable(first, cols, rows):
    """Tabla traspuesta: una fila por contraste o brazo, una columna por configuración."""
    return table([first] + cols, rows, sep="|" + "-" * 6 + "|" + "---|" * len(cols))


def sin_sets(t):
    return {k: v for k, v in t.items() if not k.endswith("_set") and k != "r_por_funcion"}


def configs():
    return [(pdir, name, lv) for pdir, name in PAIRS for lv in LEVELS]


def col_labels():
    return [f"{name} {LV[lv]}" for _, name, lv in configs()]


# --------------------------------------------------------------------- tablas --
def t_fase1(bac):
    d = json.load(open(os.path.join(bac, "fase1_v05", "cotas_fase1.json")))
    e2 = json.load(open(os.path.join(bac, "fase1_v05", "e2_effect_logs.json")))["config"]
    th = d["thresholds"]

    def f(t):
        s = f"{t['wins']}/{t['n'] - t['wins'] - t['losses']}/{t['losses']} ({sg(t['median_r'])})"
        return bold(s, t.get("pass"))
    rows = []
    for pdir, name in PAIRS:
        for lv in (5000, 50000, 500000):
            k = f"{pdir}_{lv}"
            if k not in d["cota1_vbs"] or "wins" not in d["cota1_vbs"][k]:
                continue
            o = d["cota2_oraculo"][k]
            rows.append([name, LV[lv], f(d["cota1_vbs"][k]), f(o["2a_asignacion_estatica_optima"]),
                         f(o["2b_conmutacion_clarividente"]), f(o["2c_exploratorio_mejora_relativa"])])
    cr = d["cota3_cribado"]; st = d["cota4_estabilidad"]
    nf = {t["n"] for t in d["cota1_vbs"].values() if "n" in t}
    assert len(nf) == 1, nf
    nf = nf.pop()
    dec = d["corte1"]["decision"]
    dec_txt = {"CONTINUAR a Fase 2": "continuar a la Fase 2"}.get(dec, dec[:1].lower() + dec[1:])
    lv_e2 = {5000: "5·10^3^", 50000: "5·10^4^"}[e2["budget"]]
    txt = table(["Par", "Presupuesto", "(1) VBS", "(2a) Mejor reparto fijo por corrida (a posteriori)",
                 "(2b) Conmutación por mejora absoluta (pre-registrada)", "(2c) Por mejora relativa (exploratoria)"], rows)
    txt += (f"\n\n*Mejor/igual/peor que el portafolio C1_div con Holm sobre {nf} funciones (mediana del rank-biserial);"
            f" en negrita, las celdas que superan el umbral pre-registrado (mejor ≥ {th['wins_min']} y r ≥ {th['median_r_min']}). "
            f"(3) Cribado de complementariedad {nf} × 7: cambio de ganador (1 {MENOS} fracción de funciones que gana el "
            f"solver más frecuente) {cr['5000']['winner_change']:.2f} a 5·10^3^ y {cr['50000']['winner_change']:.2f} a 5·10^4^ "
            f"(umbral {th['winner_change_min']:.2f}; a 5·10^4^ DE gana {cr['50000']['winner_counts'].get('DE', 0)} de {nf}). "
            f"(4) Estabilidad del signo del efecto por triple (fuente, destino, intención), por observación función × "
            f"semilla (operacionalización congelada en el código de v0.2), medida en {e2['pair']} a {lv_e2} sobre "
            f"{len(e2['funcs'])} funciones: {st['C3p']['n_stable']}/{st['C3p']['n_eligible']} triples estables con "
            f"gate y {st['C2p']['n_stable']}/{st['C2p']['n_eligible']} sin gate (umbral {th['stability_min']:.2f} en "
            f"triples con ≥ {th['stability_min_seeds']} observaciones). Corte 1: {dec_txt}.*")
    return txt, d


def t_piloto(bac):
    root = os.path.join(bac, "fase2_v05", "piloto")
    rows1, js = [], {}
    crit = {c: {} for c in ("C1_island", "A", "B", "C")}
    sec_rows = {k: [] for k in ("shared_vs_div", "same", "isl_vs_shared", "B_vs_isl", "C_vs_C3p", "BENg_vs_BENn",
                                "SBS", "C1_div", "C1_island", "A", "B", "C")}
    agg_iguales = True
    for pdir, name, lv in configs():
        cells = load(root, pdir, lv)
        r = {a: contrast(cells, a, "C1_div") for a in ("C1_island", "A", "B", "C")}
        for a, t in r.items():
            crit[a].setdefault(name, []).append(crit_piloto(t))
        same = np.mean([np.mean(np.asarray(c["errors"]["C1_shared"]) == np.asarray(c["errors"]["C1_div"])) for c in cells])
        sbs, idx, rk = sbs_de(cells, "SBS_A", "SBS_B")
        sname = name.split("+")[idx]
        sec = {"shared_vs_div": contrast(cells, "C1_shared", "C1_div"),
               "isl_vs_shared": contrast(cells, "C1_island", "C1_shared"), "B_vs_isl": contrast(cells, "B", "C1_island"),
               "C_vs_C3p": contrast(cells, "C", "C3p_v2"), "BENg_vs_BENn": contrast(cells, "BENg", "BENn"),
               "vs_SBS": {a: contrast(cells, a, sbs) for a in ("C1_div", "C1_island", "A", "B", "C")}}
        iv, isd = sec["isl_vs_shared"], r["C1_island"]
        agg_iguales &= all(iv[k] == isd[k] for k in ("better", "equal", "worse")) and fmt(iv) == fmt(isd)
        r_distintos = sum(1 for k in iv["r_por_funcion"] if round(iv["r_por_funcion"][k], 12) != round(isd["r_por_funcion"][k], 12))
        rows1.append([name, LV[lv]] + [bold(fmt(r[a]), crit_piloto(r[a])) for a in ("C1_island", "A", "B", "C")])
        for k in ("shared_vs_div", "isl_vs_shared", "B_vs_isl", "C_vs_C3p", "BENg_vs_BENn"):
            sec_rows[k].append(bold(fmt(sec[k]), crit_piloto(sec[k])))
        sec_rows["same"].append(f"{100 * same:.0f} %")
        sec_rows["SBS"].append(sname + (" (empate)" if rk[0] == rk[1] else ""))
        for a in ("C1_div", "C1_island", "A", "B", "C"):
            sec_rows[a].append(bold(fmt(sec["vs_SBS"][a]), crit_piloto(sec["vs_SBS"][a])))
        js[f"{pdir}_{lv}"] = {"primario": {a: sin_sets(t) | {"cumple": crit_piloto(t)} for a, t in r.items()},
                              "secundarios": {k: (sin_sets(v) if k != "vs_SBS" else {a: sin_sets(u) for a, u in v.items()})
                                              for k, v in sec.items()},
                              "shared_eq_div": same,
                              "SBS": {"brazo": sbs, "solver": sname, "rangos_medios": rk, "empate": rk[0] == rk[1]},
                              "isl_vs_shared_r_distintos_de_isl_vs_div": r_distintos}
    ok = {a: sum(all(v) for v in crit[a].values()) for a in crit}
    txt1 = table(["Par", "Presupuesto", "C1_island (migración)", "A (reparto por desempeño)", "B (élite con admisión)",
                  "C (régimen por efecto)"], rows1)
    txt1 += ("\n\n*Mejor/igual/peor que C1_div con Holm sobre las 12 funciones del piloto (mediana del rank-biserial). "
             "Criterio pre-registrado por par: en ambos presupuestos, mejor > peor, r ≥ 0.3 y peor ≤ 2; éxito en ≥ 2 de 3 "
             "pares. En negrita, las celdas que cumplen el criterio en ese presupuesto. "
             f"Pares que cumplen: A {ok['A']}, B {ok['B']}, C {ok['C']} (C1_island, referencia: {ok['C1_island']}). "
             f"Corte 2: {'ningún candidato cumple' if max(ok['A'], ok['B'], ok['C']) < 2 else 'hay candidato'}.*")
    lab = [("shared_vs_div", "C1_shared vs C1_div"), ("same", "C1_shared = C1_div (corridas idénticas)"),
           ("isl_vs_shared", "C1_island vs C1_shared"), ("B_vs_isl", "B vs C1_island"), ("C_vs_C3p", "C vs C3p (H3)"),
           ("BENg_vs_BENn", "BENg vs BENn"), ("SBS", "SBS (solver aislado)"), ("C1_div", "C1_div vs SBS"),
           ("C1_island", "C1_island vs SBS"), ("A", "A vs SBS"), ("B", "B vs SBS"), ("C", "C vs SBS")]
    txt2 = ttable("Contraste", col_labels(), [[l] + sec_rows[k] for k, l in lab])
    n_rdif = sum(1 for v in js.values() if v["isl_vs_shared_r_distintos_de_isl_vs_div"] > 0)
    emp = [(name, lv, js[f"{pdir}_{lv}"]["SBS"]) for pdir, name, lv in configs() if js[f"{pdir}_{lv}"]["SBS"]["empate"]]
    emp_txt = "".join(f" En {n} a {LV[lv]} los rangos medios empatan ({s['rangos_medios'][0]:.2f} y "
                      f"{s['rangos_medios'][1]:.2f}) y se toma {s['solver']}, el primer solver del par, como en el análisis "
                      "del camino alterno." for n, lv, s in emp)
    txt2 += ("\n\n*Contrastes secundarios pre-registrados del piloto: mejor/igual/peor con Holm sobre las 12 funciones "
             "(mediana del rank-biserial); en negrita, las celdas en que la primera condición cumple el criterio del "
             "piloto (mejor > peor, r ≥ 0.3 y peor ≤ 2). C1_shared vs C1_div es el control de atribución (enmienda v0.5); la fila "
             "siguiente es el porcentaje de corridas en que el runner cooperativo sin transferencia reproduce bit a bit "
             "al portafolio. SBS: el solver aislado (con el presupuesto completo) de menor rango medio de las medianas "
             f"en cada configuración.{emp_txt}"
             + (" C1_island vs C1_shared coincide en el agregado con C1_island vs C1_div (contraste primario); los r "
                f"por función difieren en {n_rdif} de {len(js)} configuraciones." if agg_iguales else "") + "*")
    return txt1, txt2, js, ok


def _cross_check(an, name, lv, sname, c, fr):
    """Control cruzado con analisis.json del repositorio (si existe)."""
    if an is None:
        return
    a = an["configs"][f"{name}_{lv}"]
    assert a["SBS"] == sname, (name, lv, a["SBS"], sname)
    for k_an, k_me in (("ctx_C1div_vs_SBS", "c1div_sbs"), ("G1_CTRLg_vs_CTRLn", "det"), ("G1_CTRLg_vs_C1div", "noninf"),
                       ("G2_C3p_vs_C2p", "c3c2"), ("ctx_C3p_vs_ABL", "c3abl")):
        assert all(a["contrasts"][k_an][x] == c[k_me][x] for x in ("better", "equal", "worse")), (name, lv, k_an)
    assert abs(a["friedman"]["chi2"] - fr["chi2"]) < 1e-3 and abs(a["friedman"]["iman_davenport_F"] - fr["F_F"]) < 1e-3
    sr = a["shaffer"]["mean_ranks"]
    assert all(abs(x - y) < 1e-9 for x, y in zip(sr.values(), fr["mean_ranks"].values())), (name, lv)


def t_alterno(root, dimtag, ref_shaffer="en la sección S1 del material suplementario"):
    pth = os.path.join(root, "analisis.json")
    an = json.load(open(pth)) if os.path.exists(pth) else None
    rows_g1, rows_comp, js = [], [], {}
    can = {k: [] for k in ("c2", "c3", "c3c2", "c3abl", "SBS", "c1div_sbs", "c3p_sbs", "bendiv", "benn_sbs", "beng_abl")}
    fr_rows = {k: [] for k in ["chi2", "p_chi2", "F_F", "p_FF", "sd"] + ARMS8}
    mech_cols, g1, ident, memnt = [], {}, [], {}
    for pdir, name, lv in configs():
        cells = load(root, pdir, lv)
        if not cells:
            continue
        sbs, idx, rk = sbs_de(cells)
        sname = cells[0]["solvers"][idx]
        for cc in cells:
            cc["errors"]["SBS"] = cc["errors"][sbs]
        c = {k: contrast(cells, a, b) for k, (a, b) in {
            "det": ("CTRLg", "CTRLn"), "noninf": ("CTRLg", "C1_div"), "harm": ("CTRLn_noSL", "C1_div"),
            "sl": ("CTRLg", "CTRLg_noSL"), "mem": ("CTRLg", "CTRLg_nomem"), "slsa": ("CTRLn", "CTRLn_noSL"),
            "ben": ("BENg", "BENn"), "mod": ("MODg", "MODn"), "c2": ("C2p", "C1_div"), "c3": ("C3p", "C1_div"),
            "c3c2": ("C3p", "C2p"), "c3abl": ("C3p", "ABL"), "bendiv": ("BENn", "C1_div"),
            "c1div_sbs": ("C1_div", "SBS"), "benn_sbs": ("BENn", "SBS"), "c3p_sbs": ("C3p", "SBS"),
            "beng_abl": ("BENg", "ABL"), "ctrln_div": ("CTRLn", "C1_div"), "abl_div": ("ABL", "C1_div"),
            "modg_div": ("MODg", "C1_div")}.items()}
        harm = set(c["harm"]["worse_set"]); det = set(c["det"]["better_set"])
        rate = len(harm & det) / len(harm) if harm else float("nan")
        ok = c["det"]["better"] > c["det"]["worse"] and c["det"]["median_r"] >= 0.3 and c["noninf"]["worse"] <= NONINF_MAX
        g1.setdefault(name, []).append(ok)
        rows_g1.append([name, LV[lv], fmt(c["det"]), f"{len(harm & det)}/{len(harm)} ({100 * rate:.0f} %)",
                        f"{c['noninf']['better']}", f"{c['noninf']['worse']}", bold("sí", ok) if ok else "no"])
        rows_comp.append([name, LV[lv], fmtb(c["sl"]), fmtb(c["mem"]), fmtb(c["slsa"]), fmtb(c["ben"]), fmtb(c["mod"])])
        for k in can:
            can[k].append(sname if k == "SBS" else fmtb(c[k]))
        fr = friedman(cells, ARMS8)
        _cross_check(an, name, lv, sname, c, fr)
        fr6 = friedman(cells, ARMS_REALES)
        mr = fr["mean_ranks"]; best = min(mr.values())
        fr_rows["chi2"].append(f"{fr['chi2']:.1f}"); fr_rows["p_chi2"].append(fmt_p(fr["p_chi2"]))
        fr_rows["F_F"].append(f"{fr['F_F']:.1f}"); fr_rows["p_FF"].append(fmt_p(fr["p_FF"]))
        fr_rows["sd"].append(f"{fr['sd_rangos_medios']:.2f}")
        for a in ARMS8:
            fr_rows[a].append(bold(f"{mr[a]:.2f}", mr[a] == best))
        mc = mech(cells, [a for a, _ in MECH_ARMS])
        mech_cols.append(mc)
        ident.append((sum(int(np.sum(np.asarray(x["errors"]["CTRLn"]) == np.asarray(x["errors"]["CTRLn_noSL"]))) for x in cells),
                      sum(len(x["errors"]["CTRLn"]) for x in cells)))
        memnt[f"{pdir}_{lv}"] = float(np.median([np.sum(_t(x["errors"]["CTRLg"]) != _t(x["errors"]["CTRLg_nomem"])) for x in cells]))
        tax = {t: contrast(cells, "CTRLg", "C1_div", lambda x, t=t: x["tax"] == t) for t in "UMHC"}
        js[f"{pdir}_{lv}"] = {k: sin_sets(v) for k, v in c.items()}
        js[f"{pdir}_{lv}"]["deteccion"] = {"daninas": len(harm), "detectadas": len(harm & det)}
        js[f"{pdir}_{lv}"]["G1_por_presupuesto"] = ok
        js[f"{pdir}_{lv}"]["residual_por_clase"] = {t: (v["worse"], v["n"]) if v else None for t, v in tax.items()}
        js[f"{pdir}_{lv}"]["SBS"] = {"brazo": sbs, "solver": sname, "rangos_medios": rk}
        js[f"{pdir}_{lv}"]["friedman"] = fr
        js[f"{pdir}_{lv}"]["friedman_sin_controles"] = fr6
        js[f"{pdir}_{lv}"]["mecanismo"] = mc
        js[f"{pdir}_{lv}"]["memoria_pares_no_empatados_mediana"] = memnt[f"{pdir}_{lv}"]
        js[f"{pdir}_{lv}"]["CTRLn_igual_CTRLn_noSL"] = {"corridas_identicas": ident[-1][0], "corridas": ident[-1][1]}
        if an is not None:
            js[f"{pdir}_{lv}"]["shaffer"] = an["configs"][f"{name}_{lv}"]["shaffer"]["pairs"]
    n_ok = sum(all(v) and len(v) == 2 for v in g1.values())
    cols = col_labels()
    pares_txt = "; ".join(f"{n} {'sí' if all(v) else 'no'}" for n, v in g1.items())
    t1 = table(["Par", "Presupuesto", "CTRLg vs CTRLn", "Mitigación G1b (mejora sobre las funciones dañinas)",
                "CTRLg mejor que C1_div", "CTRLg peor que C1_div (máx. 7)", "Cumple por presupuesto"], rows_g1)
    t1 += (f"\n\n*{dimtag}. CTRLg vs CTRLn: mejor/igual/peor con Holm sobre 71 funciones (mediana del rank-biserial). "
           "Funciones dañinas: aquellas donde el control adversarial sin gate ni stop-loss es peor que el portafolio "
           "(Holm); la mitigación G1b («detección» en la enmienda v0.6) es la fracción de ellas en que la condición con "
           "gate mejora a la condición sin gate: una medida de resultado, no de discriminación evento a evento. Las dos "
           "columnas siguientes cuentan las funciones en que CTRLg es mejor o peor que C1_div (Holm). Por presupuesto se "
           "exige CTRLg mejor > peor frente a CTRLn con r ≥ 0.3 y CTRLg peor que C1_div en a lo sumo "
           f"{NONINF_MAX} funciones (tope pre-registrado de pérdidas significativas); en negrita, los presupuestos que "
           "cumplen. "
           f"G1 por par (ambos presupuestos): {pares_txt}. G1 exige ≥ 2 de 3 pares: se cumple en {n_ok} de 3.*")
    ej = memnt["DEGA_5000"]
    todo_ident = all(a == b for a, b in ident)
    t2 = table(["Par", "Presupuesto", "Stop-loss (CTRLg vs sin stop-loss)", "Memoria (CTRLg vs sin memoria)",
                "Stop-loss sin admisión (CTRLn vs sin stop-loss)", "Costo: BENg vs BENn", "Daño sutil: MODg vs MODn"],
               rows_comp)
    t2 += (f"\n\n*{dimtag}. Mejor/igual/peor con Holm sobre 71 funciones (mediana del rank-biserial); en negrita, las "
           f"celdas en que la primera condición supera el umbral (mejor ≥ {UMBRAL_MEJOR} y r ≥ {UMBRAL_R}). El rank-biserial se "
           "calcula sobre los pares no empatados; con muchos empates es inestable (p. ej., Memoria en DE+GA a "
           f"5·10^3^: mediana de {ej:.0f} pares no empatados de 51 por función). "
           + ("La columna «Stop-loss sin admisión» es idéntica por construcción: CTRLn y CTRLn sin stop-loss coinciden "
              "bit a bit en todas las corridas, porque sin admisión el régimen revertido se reaplica en el mismo punto "
              "de control (verificación de construcción, no resultado empírico).*" if todo_ident else
              "La columna «Stop-loss sin admisión» compara CTRLn con CTRLn sin stop-loss.*"))
    lab = [("c2", "C2p vs C1_div"), ("c3", "C3p vs C1_div"), ("c3c2", "C3p vs C2p"), ("c3abl", "C3p vs ABL"),
           ("SBS", "SBS (solver aislado)"), ("c1div_sbs", "C1_div vs SBS (contexto)"), ("c3p_sbs", "C3p vs SBS"),
           ("bendiv", "BENn vs C1_div (exploratorio: cota de configuración por instancia)"),
           ("benn_sbs", "BENn vs SBS (exploratorio)"), ("beng_abl", "BENg vs ABL (mismo gate)")]
    t3 = ttable("Contraste", cols, [[l] + can[k] for k, l in lab])
    t3 += (f"\n\n*{dimtag}. Mejor/igual/peor con Holm sobre 71 funciones (mediana del rank-biserial); en negrita, las "
           f"celdas en que la primera condición supera el umbral (mejor ≥ {UMBRAL_MEJOR} y r ≥ {UMBRAL_R}). Canal real de "
           "transferencia paramétrica: C2p sin gate y C3p con gate; ABL elige la intención al azar, con gate. SBS: el "
           "solver aislado (con el presupuesto completo) de menor rango medio de las medianas en cada configuración; "
           "C1_div vs SBS es el contraste de contexto pre-registrado (enmienda v0.6). BENn y BENg aplican a cada solver "
           "su mejor régimen estático por función, afinado en semillas separadas, sin y con gate: las filas de BENn son "
           "exploratorias (una cota de configuración por instancia, no un mecanismo cooperativo), y BENg vs ABL compara "
           "el régimen afinado con el azar bajo el mismo gate.*")
    N = {js[k]["friedman"]["N"] for k in js}; dff = {tuple(js[k]["friedman"]["df_FF"]) for k in js}
    assert len(N) == 1 and len(dff) == 1, (N, dff)
    N = N.pop(); dff = dff.pop(); k8 = len(ARMS8)
    labf = [("chi2", f"χ² (gl = {dff[0]})"), ("p_chi2", "p (χ²)"), ("F_F", f"F~F~ (gl = {dff[0]} y {dff[1]})"),
            ("p_FF", "p (F~F~)"), ("sd", "σ de los rangos medios")] + [(a, ARM_LABEL.get(a, a)) for a in ARMS8]
    t4 = ttable("Estadístico o condición", cols, [[l] + fr_rows[k] for k, l in labf])
    t4 += (f"\n\n*{dimtag}. Friedman sobre la mediana de 51 corridas por función (N = {N} funciones, k = {k8} "
           f"condiciones). χ²: estadístico de Friedman, con k {MENOS} 1 = {dff[0]} grados de libertad; F~F~: corrección "
           f"de Iman-Davenport, con (k {MENOS} 1, (k {MENOS} 1)(N {MENOS} 1)) = ({dff[0]}, {dff[1]}) grados de libertad; "
           f"σ: desviación estándar muestral de los {k8} rangos medios. C0_A y C0_B: primer y segundo solver del par, "
           "aislados con el presupuesto completo. Rangos medios (menor = mejor); en negrita, el menor rango medio de "
           f"cada configuración. Los pares significativos del post-hoc de Shaffer están {ref_shaffer}.*")
    t5 = mech_table(mech_cols, cols, dimtag)
    return {"g1": t1, "comp": t2, "canal": t3, "fried": t4, "mech": t5}, js, n_ok


def mech_table(mech_cols, cols, dimtag):
    rows = [["Propuestas por corrida"] + [f"{m['CTRLg']['propuestas']:.1f}" for m in mech_cols]]
    assert all(len({round(v["propuestas"], 9) for v in m.values()}) == 1 for m in mech_cols)
    rows.append(["*Aceptadas por corrida (tasa de admisión)*"] + [""] * len(cols))
    rows += [[l] + [f"{m[a]['aceptadas']:.2f} ({100 * m[a]['admision']:.1f} %)" for m in mech_cols] for a, l in MECH_ARMS]
    rows.append(["*Revertidas por corrida (tasa de reversión)*"] + [""] * len(cols))
    rows += [[l] + [f"{m[a]['revertidas']:.2f} ({100 * m[a]['reversion']:.1f} %)" for m in mech_cols] for a, l in MECH_ARMS]
    n_mas = sum(m["CTRLg"]["reversion"] > m["BENg"]["reversion"] for m in mech_cols)
    t = ttable("Brazo", cols, rows)
    t += (f"\n\n*{dimtag}. Promedios por corrida sobre las 71 funciones y 51 corridas de cada configuración. Propuestas: "
          "regímenes que el canal propone (iguales en todos los brazos de una configuración). Aceptadas: regímenes que "
          "el gate admite; entre paréntesis, la tasa de admisión (aceptadas / propuestas). Revertidas: regímenes "
          "admitidos que el stop-loss revierte; entre paréntesis, la tasa de reversión sobre los compromisos resueltos "
          "(revertidos / (revertidos + conservados)), que excluye los que siguen abiertos al agotarse el presupuesto. "
          f"El stop-loss revierte una fracción mayor de regímenes adversariales (CTRLg) que benignos (BENg) en {n_mas} "
          f"de {len(mech_cols)} configuraciones.*")
    return t


TAXN = {"U": "Unimodales", "M": "Multimodales", "H": "Híbridas", "C": "Composición"}


def t_taxonomia(root):
    rows = []
    for pdir, name, lv in configs():
        cells = load(root, pdir, lv)
        r = [name, LV[lv]]
        for t in "UMHC":
            a = contrast(cells, "CTRLg", "CTRLn", lambda x, t=t: x["tax"] == t)
            b = contrast(cells, "CTRLg", "C1_div", lambda x, t=t: x["tax"] == t)
            r.append(f"{a['better']}/{a['n']} ({b['worse']})")
        rows.append(r)
    txt = table(["Par", "Presupuesto"] + [f"{TAXN[t]}" for t in "UMHC"], rows)
    txt += ("\n\n*10D, exploratorio (pre-registro §8). En cada celda: funciones donde el gate supera al control sin "
            "gate / funciones de la clase; entre paréntesis, funciones donde la condición con gate queda peor que el "
            "portafolio (daño residual). Holm se aplica dentro de cada clase, por lo que estos conteos no son "
            "comparables con los del criterio G1 (Holm sobre las 71 funciones) ni suman sus totales.*")
    return txt


def _verificar_enunciados():
    """Comprueba que ENUNCIADOS coincide literalmente con la sección 2 del pre-registro."""
    p = os.path.join(_REPO, PREREG)
    if not os.path.exists(p):
        raise SystemExit(f"falta {PREREG}: no se pueden verificar los enunciados de H1-H5")
    with open(p, encoding="utf-8") as fh:
        txt = fh.read()
    sec = txt[txt.index("2\\. Pregunta"):txt.index("3\\. Fase 0")]
    sec = sec.translate(str.maketrans({"³": "^3^", "⁴": "^4^", "⁵": "^5^"}))
    sec = re.sub(r"\s+", " ", sec)
    for h, e in ENUNCIADOS.items():
        assert e in sec, f"{h}: el enunciado no coincide literalmente con {PREREG}"
    return PREREG


def t_hipotesis(f1js, pjs, ok_piloto):
    fuente = _verificar_enunciados()
    o = f1js["cota2_oraculo"]
    names = dict(PAIRS)

    def clasif(clave):
        peor = [names[p] for p, _ in PAIRS if all(o[f"{p}_{lv}"][clave]["losses"] > o[f"{p}_{lv}"][clave]["wins"] for lv in LEVELS)]
        supera = [names[p] for p, _ in PAIRS if all(o[f"{p}_{lv}"][clave]["pass"] for lv in LEVELS)]
        return peor, supera
    peor2b, sup2b = clasif("2b_conmutacion_clarividente")
    peor2c, sup2c = clasif("2c_exploratorio_mejora_relativa")
    assert len(peor2b) == 2 and len(sup2b) == 1, (peor2b, sup2b)
    coincide = (peor2b, sup2b) == (peor2c, sup2c)
    h1 = ("No contrastada directamente por su mecanismo: el candidato A se diseñó en v0.3 para repartir por desempeño "
          "del incumbente («por nivel»), no por mejora relativa, y no se evaluó un controlador guiado por mejora. La cota "
          "pre-registrada (2b, conmutación clarividente por mejora; "
          + ("la 2c por mejora relativa, exploratoria, coincide en dirección" if coincide else "la 2c por mejora relativa es exploratoria")
          + f") va en contra en {' y '.join(peor2b)} y a favor en {sup2b[0]}, en 10D a 5·10^3^ y 5·10^4^.")
    bwin = sum(pjs[k]["secundarios"]["B_vs_isl"]["better"] for k in pjs)
    bloss = sum(pjs[k]["secundarios"]["B_vs_isl"]["worse"] for k in pjs)
    assert bwin == 0 and ok_piloto["B"] == 0, (bwin, ok_piloto)
    h2 = ("Refutada en el piloto (12 funciones), en su forma pre-registrada (la reformulación de v0.4 quedó anulada): "
          f"B no supera a la migración fija en ninguna función ({bwin} mejor y {bloss} peor en las 6 configuraciones) y no cumple "
          f"el criterio frente a C1_div en ningún par ({ok_piloto['B']} de 3).")
    c3_cells = [k for k in pjs if pjs[k]["secundarios"]["C_vs_C3p"]["better"] > pjs[k]["secundarios"]["C_vs_C3p"]["worse"]]
    c3_pares = [names[p] for p, _ in PAIRS if all(crit_piloto(pjs[f"{p}_{lv}"]["secundarios"]["C_vs_C3p"]) for lv in LEVELS)]
    c3_pares_celdas = sorted({names[k.split("_")[0]] for k in c3_cells})
    assert len(c3_pares) == 1 and c3_pares_celdas == c3_pares, (c3_pares, c3_pares_celdas)
    pdir_c3 = {v: k for k, v in names.items()}[c3_pares[0]]
    vs_sbs = [pjs[f"{pdir_c3}_{lv}"]["secundarios"]["vs_SBS"]["C"] for lv in LEVELS]
    assert all(t["better"] <= t["worse"] for t in vs_sbs), vs_sbs
    max_peor = max(pjs[k]["primario"]["C"]["worse"] for k in pjs)
    assert max_peor <= 2
    h3 = (f"No soportada con el criterio de consistencia (cumple solo en {c3_pares[0]}): C supera a C3p en "
          f"{len(c3_cells)} de {len(pjs)} configuraciones ({len(c3_pares)} de 3 pares con el criterio del piloto), donde no supera "
          f"al mejor solver aislado ({' y '.join(fmt(t, short=True) for t in vs_sbs)}); frente a C1_div queda peor en a "
          f"lo sumo {max_peor} de 12 funciones en todas las configuraciones. Señal exploratoria.")
    corte2_confirmatorio = max(ok_piloto["A"], ok_piloto["B"], ok_piloto["C"]) >= 2
    assert not corte2_confirmatorio
    h4 = "No aplica: el Corte 2 no habilitó el confirmatorio."
    h5 = ("No evaluada (el Corte 2 no habilitó el confirmatorio); sin la referencia externa, los claims se acotan al "
          "portafolio de los mismos solvers, la acotación que el pre-registro prevé si H5 se rechaza.")
    rows = [["H1 (asignación)", ENUNCIADOS["H1"], h1], ["H2 (estructural)", ENUNCIADOS["H2"], h2],
            ["H3 (régimen por efecto)", ENUNCIADOS["H3"], h3], ["H4 (escala)", ENUNCIADOS["H4"], h4],
            ["H5 (referencia externa)", ENUNCIADOS["H5"], h5]]
    for r in rows:
        assert r[1].endswith(".") and r[2].endswith("."), r
    t = table(["Hipótesis", "Enunciado pre-registrado", "Veredicto con los datos de este estudio"], rows,
              sep="|------|----------|--------------------|")
    info = {"enunciados_verificados_contra": fuente, "H1": {"cota_2b_peor": peor2b, "cota_2b_supera": sup2b,
                                                            "cota_2c_coincide": coincide},
            "H2": {"B_vs_island_mejor": bwin, "B_vs_island_peor": bloss, "B_pares_criterio": ok_piloto["B"]},
            "H3": {"celdas_C_supera_C3p": len(c3_cells), "pares_criterio": c3_pares,
                   "C_vs_SBS": [sin_sets(t) for t in vs_sbs], "C_vs_C1div_max_peor": max_peor},
            "veredictos": {"H1": "No contrastada directamente por su mecanismo", "H2": "Refutada en el piloto",
                           "H3": "No soportada con el criterio de consistencia",
                           "H4": "No aplica", "H5": "No evaluada"}}
    return t, info


def suplementario(bac):
    rows = []
    for camp, root, dim in [("piloto", os.path.join(bac, "fase2_v05", "piloto"), "10"),
                            ("alterno", os.path.join(bac, "camino_alterno_v06"), "10"),
                            ("alterno", os.path.join(bac, "camino_alterno_v06_dim50"), "50")]:
        for pdir, name in PAIRS:
            for lv in LEVELS:
                for c in load(root, pdir, lv):
                    for arm, e in c["errors"].items():
                        e = _t(e)
                        rows.append([camp, dim, name, lv, c["key"], arm, f"{e.mean():.6g}", f"{np.median(e):.6g}",
                                     f"{e.std(ddof=1):.6g}", len(e)])
    return rows


# --------------------------------------------------------------- suplementario --
def supl_shaffer(js, solvers_por_par, dimtag):
    """Pares significativos del post-hoc de Shaffer (leídos de analisis.json) y % de competidores."""
    cols = col_labels()
    pct = {a: [] for a in ARMS8}
    lista, data = [], {}
    for (pdir, name, lv), col in zip(configs(), cols):
        pairs = js[f"{pdir}_{lv}"].get("shaffer")
        if pairs is None:
            continue
        sA, sB = solvers_por_par[name]
        alias = {sA: "C0_A", sB: "C0_B"}
        mr = js[f"{pdir}_{lv}"]["friedman"]["mean_ranks"]
        sig = [p for p in pairs if p["significant"]]
        k = len(ARMS8)
        for a in ARMS8:
            n = sum(1 for p in sig if a in (alias.get(p["a"], p["a"]), alias.get(p["b"], p["b"])))
            pct[a].append(f"{100 * n / (k - 1):.0f} % ({n}/{k - 1})")
        items, reg = [], []
        lab = lambda x: f"{x} ({sA if x == 'C0_A' else sB})" if x in ("C0_A", "C0_B") else x
        for p in sorted(sig, key=lambda p: p["p_shaffer"]):
            a, b = alias.get(p["a"], p["a"]), alias.get(p["b"], p["b"])
            mejor, peor = (a, b) if mr[a] < mr[b] else (b, a)
            items.append(f"{lab(mejor)} mejor que {lab(peor)} ({fmt_p_shaffer(p['p_shaffer'])})")
            reg.append({"mejor": mejor, "peor": peor, "p_shaffer": p["p_shaffer"]})
        lista.append(f"- {name} a {LV[lv]} ({len(sig)} de {len(pairs)} pares): " + "; ".join(items) + ".")
        data[f"{pdir}_{lv}"] = {"significativos": len(sig), "pares": len(pairs), "lista": reg,
                                "pct_competidores": {a: pct[a][-1] for a in ARMS8}}
    t = ttable("Condición", cols, [[ARM_LABEL.get(a, a)] + pct[a] for a in ARMS8])
    t += (f"\n\n*{dimtag}. Porcentaje de competidores (de {len(ARMS8) - 1}) de los que cada condición difiere "
          "significativamente según el post-hoc de Shaffer (estático, α = 0.05) sobre los rangos de Friedman de la "
          "tabla ómnibus; leído de analisis.json del repositorio (camino_alterno_analisis.py). En la lista, los p "
          "ajustados menores que 10^−10^ se reportan como cota, porque la implementación pierde precisión en ese "
          "rango.*")
    return t, "\n".join(lista), data


def supl_sin_controles(js, dimtag):
    cols = col_labels()
    rows = {k: [] for k in ("chi2", "p_chi2", "F_F", "p_FF")}
    dff = None
    for pdir, name, lv in configs():
        fr = js[f"{pdir}_{lv}"]["friedman_sin_controles"]
        dff = fr["df_FF"]
        rows["chi2"].append(f"{fr['chi2']:.1f}"); rows["p_chi2"].append(fmt_p(fr["p_chi2"]))
        rows["F_F"].append(f"{fr['F_F']:.1f}"); rows["p_FF"].append(fmt_p(fr["p_FF"]))
    lab = [("chi2", f"χ² (gl = {dff[0]})"), ("p_chi2", "p (χ²)"), ("F_F", f"F~F~ (gl = {dff[0]} y {dff[1]})"),
           ("p_FF", "p (F~F~)")]
    t = ttable("Estadístico", cols, [[l] + rows[k] for k, l in lab])
    t += (f"\n\n*{dimtag}. Friedman con corrección de Iman-Davenport sobre los {len(ARMS_REALES)} brazos reales "
          f"({', '.join(ARMS_REALES)}), sin los controles adversariales CTRLn y CTRLg.*")
    return t


# Bancos del conjunto de 71 funciones: (prefijo de la celda, nombre, funciones).
BANCOS = [("CEC2014", "CEC 2014", "F1–F30"), ("CEC2017", "CEC 2017", "F1 y F3–F30"),
          ("CEC2022", "CEC 2022", "F1–F12")]


def omnibus_por_banco(root):
    """Friedman e Iman-Davenport por banco (pre-registro §8: banco × dimensión × presupuesto).

    Misma matriz que el ómnibus agregado (mediana de 51 corridas por función, errores
    < 1e-8 = 0, los 8 brazos de ARMS8), restringida a las funciones de cada banco.
    """
    out = {}
    for pdir, name, lv in configs():
        cells = load(root, pdir, lv)
        por = {b: [c for c in cells if c["key"].rsplit("_F", 1)[0] == b] for b, _, _ in BANCOS}
        assert sum(map(len, por.values())) == len(cells) and all(por.values()), (root, pdir, lv)
        out[f"{pdir}_{lv}"] = {b: friedman(cs, ARMS8) for b, cs in por.items()}
    return out


def menor_rango(fr):
    mr = fr["mean_ranks"]; best = min(mr.values())
    return [a for a in ARMS8 if mr[a] == best]


def dim_banco(dim, b):
    """(sufijo del título, prefijo del pie) de la tabla de un banco en un conjunto de dimensión."""
    if dim == "10D":
        return "a 10D", "10D"
    if b == "CEC2022":
        return "a 20D, conjunto de 50D (exploratorio)", "20D (CEC 2022 en el conjunto de 50D), exploratorio"
    return "a 50D (exploratorio)", "50D, exploratorio"


def supl_por_banco(fb, dim):
    """Una tabla traspuesta por banco, con el formato de la tabla ómnibus."""
    cols = col_labels()
    partes = []
    for b, lab, rango in BANCOS:
        frs = [fb[f"{pdir}_{lv}"][b] for pdir, _, lv in configs()]
        N = {f["N"] for f in frs}; dff = {tuple(f["df_FF"]) for f in frs}
        assert len(N) == 1 and len(dff) == 1, (b, N, dff)
        N = N.pop(); dff = dff.pop(); k8 = len(ARMS8)
        rows = {k: [] for k in ["chi2", "p_chi2", "F_F", "p_FF", "sd"] + ARMS8}
        for fr in frs:
            mr = fr["mean_ranks"]; best = min(mr.values())
            rows["chi2"].append(f"{fr['chi2']:.1f}"); rows["p_chi2"].append(fmt_p(fr["p_chi2"]))
            rows["F_F"].append(f"{fr['F_F']:.1f}"); rows["p_FF"].append(fmt_p(fr["p_FF"]))
            rows["sd"].append(f"{fr['sd_rangos_medios']:.2f}")
            for a in ARMS8:
                rows[a].append(bold(f"{mr[a]:.2f}", mr[a] == best))
        labf = [("chi2", f"χ² (gl = {dff[0]})"), ("p_chi2", "p (χ²)"), ("F_F", f"F~F~ (gl = {dff[0]} y {dff[1]})"),
                ("p_FF", "p (F~F~)"), ("sd", "σ de los rangos medios")] + [(a, ARM_LABEL.get(a, a)) for a in ARMS8]
        tit, pie = dim_banco(dim, b)
        t = ttable("Estadístico o condición", cols, [[l] + rows[k] for k, l in labf])
        t += (f"\n\n*{pie}. {lab} ({rango}): N = {N} funciones, k = {k8} condiciones. Friedman sobre la mediana de 51 "
              f"corridas por función, con {dff[0]} grados de libertad; F~F~: corrección de Iman-Davenport, con "
              f"({dff[0]}, {dff[1]}) grados de libertad. Rangos medios (menor = mejor); en negrita, el menor rango "
              "medio de cada configuración."
              + (f" Con solo N = {N} funciones, la aproximación asintótica de ambos estadísticos es más gruesa y la "
                 "potencia del ómnibus es baja: un p no significativo en este banco no indica ausencia de diferencias."
                 if N < 20 else "") + "*")
        partes.append((f"{lab} {tit}", t))
    return partes


def resumen_por_banco(fb10, fb50, a10js, a50js):
    """Cifras para la prosa: significación del ómnibus por banco y brazo de menor rango frente al agregado."""
    filas = []
    for dim, fb, agg in (("10D", fb10, a10js), ("50D", fb50, a50js)):
        for pdir, name, lv in configs():
            k = f"{pdir}_{lv}"
            for b, lab, _ in BANCOS:
                fr = fb[k][b]
                filas.append({"config": f"{dim} {lab} {name} {lv}", "dim": dim, "banco": lab, "N": fr["N"],
                              "p_chi2": fr["p_chi2"], "p_FF": fr["p_FF"], "menor_rango": menor_rango(fr),
                              "menor_rango_agregado": menor_rango(agg[k]["friedman"])})
    p_holm = holm([f["p_FF"] for f in filas])
    sig = lambda f: f["p_FF"] < 0.05
    coin = [f for f in filas if f["menor_rango"] == f["menor_rango_agregado"]]
    emp = [f for f in filas if f not in coin and set(f["menor_rango_agregado"]) <= set(f["menor_rango"])]
    return {"configuraciones": len(filas), "alfa": 0.05,
            "significativas_F_F": sum(map(sig, filas)),
            "significativas_chi2": sum(f["p_chi2"] < 0.05 for f in filas),
            "significativas_F_F_holm_sobre_36": sum(p < 0.05 for p in p_holm),
            "significativas_F_F_por_banco": {lab: f"{sum(sig(f) for f in filas if f['banco'] == lab)}/"
                                                  f"{sum(f['banco'] == lab for f in filas)}" for _, lab, _ in BANCOS},
            "significativas_F_F_por_dimension": {d: f"{sum(sig(f) for f in filas if f['dim'] == d)}/"
                                                    f"{sum(f['dim'] == d for f in filas)}" for d in ("10D", "50D")},
            "no_significativas_F_F": {f["config"]: f["p_FF"] for f in filas if not sig(f)},
            "menor_rango_coincide_con_agregado": len(coin),
            "menor_rango_empata_con_el_del_agregado": [f["config"] for f in emp],
            "menor_rango_no_coincide": {f["config"]: {"banco": f["menor_rango"], "agregado": f["menor_rango_agregado"]}
                                        for f in filas if f not in coin},
            "menor_rango_por_brazo": {a: sum(a in f["menor_rango"] for f in filas) for a in ARMS8},
            "nota": "F_F: Iman-Davenport; sin corrección por multiplicidad salvo el conteo con Holm sobre las 36; "
                    "coincidencia = mismo conjunto de brazos con el menor rango medio (banco vs 71 funciones)"}


def seccion_por_banco(fb10, fb50, res):
    """Sección S7: introducción, una tabla por banco y dimensión, y resumen."""
    n = res["configuraciones"]
    txt = [f"Desglose por banco del ómnibus de la Tabla 11 del artículo (10D) y de S3 (50D), según la unidad de "
           "análisis del pre-registro (§8: banco × dimensión × presupuesto). La matriz es la misma del ómnibus "
           f"agregado (mediana de 51 corridas por función, errores menores que 10^{MENOS}8^ truncados a 0, los mismos "
           f"{len(ARMS8)} brazos y promedio de rangos en los empates), restringida a las funciones de cada banco: "
           + "; ".join(f"{lab} {rango} ({fb10[next(iter(fb10))][b]['N']})" for b, lab, rango in BANCOS)
           + f". Sin post-hoc de Shaffer por banco (solo sobre el agregado, en S1 y S4); los p no se corrigen por "
           f"multiplicidad entre las {n} configuraciones (3 bancos × 3 pares × 2 presupuestos × 2 dimensiones).", ""]
    j = 0
    for dim, fb in (("10D", fb10), ("50D", fb50)):
        for tit, t in supl_por_banco(fb, dim):
            j += 1
            txt += [f"### S7.{j}. {tit}", "", t, ""]
    lv_lab = {str(lv): LV[lv] for lv in LEVELS}
    nosig = [f"{c.rsplit(' ', 1)[0]} a {lv_lab[c.rsplit(' ', 1)[1]]} (p = {fmt_p(p)})"
             for c, p in res["no_significativas_F_F"].items()]
    txt.append(f"*Resumen: el ómnibus de Iman-Davenport es significativo (α = 0.05) en {res['significativas_F_F']} de "
               f"{n} configuraciones ({res['significativas_chi2']} de {n} con el χ² de Friedman; "
               f"{res['significativas_F_F_holm_sobre_36']} de {n} con Holm sobre las {n}); por banco, "
               + ", ".join(f"{lab} {v}" for lab, v in res["significativas_F_F_por_banco"].items())
               + (f". No significativas: {'; '.join(nosig)}" if nosig else "")
               + f". El brazo de menor rango medio coincide con el del agregado de 71 funciones en "
               f"{res['menor_rango_coincide_con_agregado']} de {n} configuraciones"
               + "".join(f"; en {c.rsplit(' ', 1)[0]} a {lv_lab[c.rsplit(' ', 1)[1]]}, el del agregado empata en el "
                         "menor rango con otro brazo" for c in res["menor_rango_empata_con_el_del_agregado"])
               + ".*")
    return "\n".join(txt).rstrip()


def calcular_supl(a10, a10js, a50, a50js, solvers, fb10, fb50, res_banco, root10):
    md = [f"# Material suplementario de «{TITULO_PAPER}»", "", f"*{AUTORES}. Generado por script.*", "",
          "## S0. Contenido y archivos", "", S0_TEXTO, ""]
    out = {}
    secciones = []
    for js, tag, dimtag, tit in ((a10js, "10", "10D", "a 10D"),
                                 (a50js, "50", "50D (CEC 2022 a 20D), exploratorio", "a 50D (exploratorio)")):
        t_pct, lista, data = supl_shaffer(js, solvers, dimtag)
        out[f"shaffer_{tag}"] = data
        out[f"friedman_sin_controles_{tag}"] = {k: v["friedman_sin_controles"] for k, v in js.items()}
        secciones.append((f"Post-hoc de Shaffer {tit}", t_pct + "\n\nPares con diferencia significativa:\n\n" + lista))
        secciones.append((f"Ómnibus sin controles adversariales {tit}", supl_sin_controles(js, dimtag)))
    secciones.insert(2, ("Ómnibus a 50D (exploratorio)", a50["fried"]))
    secciones.append(("Mecanismo del gate a 50D (exploratorio)", a50["mech"]))
    out["friedman_50"] = {k: v["friedman"] for k, v in a50js.items()}
    out["mecanismo_50"] = {k: v["mecanismo"] for k, v in a50js.items()}
    out["mecanismo_10"] = {k: v["mecanismo"] for k, v in a10js.items()}
    secciones.append(("Ómnibus por banco", seccion_por_banco(fb10, fb50, res_banco)))
    out["omnibus_por_banco"] = {"10D": fb10, "50D": fb50, "resumen": res_banco}
    p8, n8, out["sensibilidad_10"] = supl_sensibilidad(root10, a10js)
    secciones.append(("Sensibilidad de los contrastes pareados a 10D",
                      "\n\n".join(f"{t}\n\n{c}" for t, c in p8) + "\n\n" + n8))
    t9, out["robustez_G1_10"] = supl_robustez(root10, a10js)
    secciones.append(("Robustez de G1 por banco y sin funciones repetidas a 10D", t9))
    p10, n10, out["seis_brazos_10"] = supl_seis_brazos(root10, a10js, solvers)
    secciones.append(("Ómnibus y post-hoc de Shaffer con los seis brazos reales a 10D",
                      "\n\n".join(f"{t}\n\n{c}" for t, c in p10) + "\n\n" + n10))
    for i, (tit, cont) in enumerate(secciones, 1):
        md += [f"## S{i}. {tit}", "", cont, ""]
    return out, "\n".join(md)

# ------------------------------------------------- suplementario: S0, S8, S9, S10 --
TITULO_PAPER = ("Mitigar no es neutralizar: evaluación pre-registrada de una salvaguarda en línea contra la "
                "transferencia negativa entre metaheurísticas heterogéneas concurrentes")
AUTORES = "Felipe González y Rodrigo Olivares (Universidad de Valparaíso)"
RUTA_REGISTRO = "docs/preregistro_fase_positiva/deviations-log.md"
REPO_URL = "https://github.com/kaosb/BioAlgoCompare"

S0_TEXTO = f"""Suplementario de «{TITULO_PAPER}» ({AUTORES}). Todas las cifras se calculan por script desde los
datos crudos del repositorio {REPO_URL} (`results/cooperative/`; script `scripts/cec_harness/tablas_paper_v13.py`,
que también compone las tablas del artículo); el post-hoc de Shaffer de S1 y S4 se lee de `analisis.json` del
camino alterno (10D y 50D). Contenido:

- `suplementario_v13_estadisticos.csv`: media, mediana y desviación estándar de las 51 corridas de cada condición,
  por campaña (`piloto`: Tablas 4 y 5; `alterno`: Tablas 7, 8, 10, 11, 13, 14 y 15), dimensión (`dimset`: 10 o 50), par,
  presupuesto, función y condición (`brazo`). Columnas: `campana`, `dimset`, `par`, `presupuesto`, `funcion`,
  `brazo`, `media`, `mediana`, `desv_est`, `corridas`. Errores menores que 10^{MENOS}8^ truncados a 0 antes de
  calcular. Equivalencia de rótulos con la Tabla 2: en el piloto, `SBS_A` y `SBS_B` son C0_A y C0_B (el primer y el
  segundo solver del par, aislados con el presupuesto completo) y `C3p_v2` es C3p; los demás rótulos coinciden.
  Las Tablas 3 (cotas de la Fase 1, calculadas sobre `fase1_v05/`), 6 (hipótesis), 9 (mecanismo, de `mech_stats`)
  y 12 (conteos por clase) no tienen estadísticos por condición en el CSV.
- S1 a S7: post-hoc de Shaffer y ómnibus sin controles a 10D y 50D, ómnibus a 50D, mecanismo del gate a 50D y
  ómnibus por banco.
- S8 a S10 (añadidos en el análisis, descriptivos; registro D36): sensibilidad de los contrastes pareados a 10D,
  robustez de G1 por banco y sin funciones repetidas, y ómnibus de los seis brazos reales con post-hoc de Shaffer
  por banco.
- Registro de desviaciones del pre-registro: `{RUTA_REGISTRO}` en el repositorio (etiquetas
  `preregistro-fase-positiva-v0.2` a `v0.6`)."""

# Funciones básicas cuya función base ya aparece en un banco anterior (informes técnicos CEC 2014, 2017 y 2022);
# se conserva la primera aparición por orden de banco. (banco, F): (función base, copia conservada).
DUPLICADAS = {("CEC2017", 1): ("Bent Cigar", "CEC 2014 F2"), ("CEC2017", 4): ("Rosenbrock", "CEC 2014 F4"),
              ("CEC2017", 5): ("Rastrigin", "CEC 2014 F9"), ("CEC2017", 10): ("Schwefel", "CEC 2014 F11"),
              ("CEC2022", 1): ("Zakharov", "CEC 2017 F3"), ("CEC2022", 2): ("Rosenbrock", "CEC 2014 F4"),
              ("CEC2022", 3): ("Schaffer F7 expandida", "CEC 2017 F6"),
              ("CEC2022", 4): ("Rastrigin no continua", "CEC 2017 F8"), ("CEC2022", 5): ("Levy", "CEC 2017 F9")}


def es_duplicada(c):
    suite, f = c["key"].rsplit("_F", 1)
    return (suite, int(f)) in DUPLICADAS


def contrast_sens(cells, A, B):
    """Sensibilidad de un contraste pareado: conteo sin corrección (α = 0.05), Wilcoxon entre funciones sobre
    las medianas (Derrac et al. 2011) con rank-biserial, y prueba de signos sobre las medianas."""
    out = [paired(c["errors"][A], c["errors"][B]) for c in cells]
    raw_b = sum(1 for p, r in out if p < 0.05 and r > 0)
    raw_w = sum(1 for p, r in out if p < 0.05 and r < 0)
    ma = np.array([np.median(_t(c["errors"][A])) for c in cells])
    mb = np.array([np.median(_t(c["errors"][B])) for c in cells])
    d = ma - mb; dd = d[d != 0]
    if len(dd):
        _, p_ef = wilcoxon(ma, mb, zero_method="wilcox")
        rk = rankdata(np.abs(dd)); r_ef = float((rk[dd < 0].sum() - rk[dd > 0].sum()) / rk.sum())
    else:
        p_ef, r_ef = 1.0, 0.0
    n_mas, n_menos = int(np.sum(d < 0)), int(np.sum(d > 0))
    p_sig = float(binomtest(n_mas, n_mas + n_menos).pvalue) if n_mas + n_menos else 1.0
    return {"sin_corregir": {"better": raw_b, "equal": len(cells) - raw_b - raw_w, "worse": raw_w, "n": len(cells)},
            "entre_funciones": {"p": float(p_ef), "r": r_ef, "n_distintas": int(len(dd))},
            "signos": {"n_mas": n_mas, "n_menos": n_menos, "p": p_sig}}


S8_GRUPOS = [("Tabla 7", [("det", "CTRLg vs CTRLn"), ("noninf", "CTRLg vs C1_div"),
                          ("harm", "CTRLn sin stop-loss vs C1_div (funciones dañinas)")]),
             ("Tabla 8", [("sl", "Stop-loss: CTRLg vs CTRLg sin stop-loss"), ("mem", "Memoria: CTRLg vs CTRLg sin memoria"),
                          ("ben", "Costo: BENg vs BENn"), ("mod", "Daño sutil: MODg vs MODn")]),
             ("Tabla 10", [("c2", "C2p vs C1_div"), ("c3", "C3p vs C1_div"), ("c3c2", "C3p vs C2p"),
                           ("c3abl", "C3p vs ABL"), ("c1div_sbs", "C1_div vs SBS"), ("c3p_sbs", "C3p vs SBS"),
                           ("bendiv", "BENn vs C1_div"), ("benn_sbs", "BENn vs SBS"), ("beng_abl", "BENg vs ABL")])]
S8_PARES = {"det": ("CTRLg", "CTRLn"), "noninf": ("CTRLg", "C1_div"), "harm": ("CTRLn_noSL", "C1_div"),
            "sl": ("CTRLg", "CTRLg_noSL"), "mem": ("CTRLg", "CTRLg_nomem"), "ben": ("BENg", "BENn"),
            "mod": ("MODg", "MODn"), "c2": ("C2p", "C1_div"), "c3": ("C3p", "C1_div"), "c3c2": ("C3p", "C2p"),
            "c3abl": ("C3p", "ABL"), "c1div_sbs": ("C1_div", "SBS"), "c3p_sbs": ("C3p", "SBS"),
            "bendiv": ("BENn", "C1_div"), "benn_sbs": ("BENn", "SBS"), "beng_abl": ("BENg", "ABL")}


S8_SEP = "|" + "-" * 22 + "|" + "-" * 9 + "|" + "-" * 11 + "|" + "-" * 11 + "|" + "-" * 10 + "|" + "-" * 9 + "|" + "-" * 6 + "|" + "-" * 10 + "|" + "-" * 9 + "|"


def supl_sensibilidad(root, a10js):
    """S8: para cada contraste de las Tablas 7, 8 y 10 (10D), el conteo con Holm del artículo, el conteo sin
    corrección, el Wilcoxon entre funciones y la prueba de signos."""
    partes, data = [], {}
    cache = {}
    for pdir, name, lv in configs():
        cells = load(root, pdir, lv)
        sbs = a10js[f"{pdir}_{lv}"]["SBS"]["brazo"]
        for c in cells:
            c["errors"]["SBS"] = c["errors"][sbs]
        cache[(pdir, lv)] = cells
    for j, (tabla, items) in enumerate(S8_GRUPOS, 1):
        rows = []
        for key, lab in items:
            A, B = S8_PARES[key]
            for pdir, name, lv in configs():
                h = a10js[f"{pdir}_{lv}"][key]
                s = contrast_sens(cache[(pdir, lv)], A, B)
                data.setdefault(key, {})[f"{pdir}_{lv}"] = {"holm": sin_sets(h)} | s
                sc, ef, sg_ = s["sin_corregir"], s["entre_funciones"], s["signos"]
                rows.append([lab, name, LV[lv], fmt(h), f"{sc['better']}/{sc['equal']}/{sc['worse']}",
                             fmt_p(ef["p"]), sg(ef["r"]), f"{sg_['n_mas']}/{sg_['n_menos']}", fmt_p(sg_["p"])])
        t = table(["Contraste", "Par", "Presupuesto", "Holm (artículo)", "Sin corrección", "Entre funciones: p",
                   "r", "Signos: a favor/en contra", "p"], rows, sep=S8_SEP)
        partes.append((f"### S8.{j}. Contrastes de la {tabla}", t))
    # S8.4: admisión x stop-loss (los dos componentes del gate por separado y juntos)
    rows = []
    for key, lab, A, B in (("adm_sola", "Admisión sin stop-loss: CTRLg sin stop-loss vs CTRLn sin stop-loss",
                            "CTRLg_noSL", "CTRLn_noSL"),
                           ("sl_con_adm", "Stop-loss con admisión: CTRLg vs CTRLg sin stop-loss", "CTRLg", "CTRLg_noSL"),
                           ("adm_sola_div", "Admisión sin stop-loss vs portafolio: CTRLg sin stop-loss vs C1_div",
                            "CTRLg_noSL", "C1_div"),
                           ("gate_div", "Gate completo vs portafolio: CTRLg vs C1_div", "CTRLg", "C1_div")):
        for pdir, name, lv in configs():
            h = contrast(cache[(pdir, lv)], A, B)
            s = contrast_sens(cache[(pdir, lv)], A, B)
            data.setdefault(key, {})[f"{pdir}_{lv}"] = {"holm": sin_sets(h)} | s
            sc, ef, sg_ = s["sin_corregir"], s["entre_funciones"], s["signos"]
            rows.append([lab, name, LV[lv], fmt(h), f"{sc['better']}/{sc['equal']}/{sc['worse']}",
                         fmt_p(ef["p"]), sg(ef["r"]), f"{sg_['n_mas']}/{sg_['n_menos']}", fmt_p(sg_["p"])])
    t = table(["Contraste", "Par", "Presupuesto", "Holm", "Sin corrección", "Entre funciones: p",
               "r", "Signos: a favor/en contra", "p"], rows, sep=S8_SEP)
    t += ("\n\n*Admisión y stop-loss por separado y juntos, bajo transferencia adversarial. CTRLn sin stop-loss "
          "y CTRLn coinciden bit a bit, por lo que «stop-loss sin admisión» no se contrasta. La columna Holm sigue "
          "el formato de las Tablas 7 y 8.*")
    partes.append(("### S8.4. Admisión y stop-loss por separado", t))
    # S8.5: G1b con validación por mitades de las corridas
    h1, h2 = np.arange(0, 25), np.arange(25, 51)
    rows = []
    for pdir, name, lv in configs():
        cells = cache[(pdir, lv)]
        H = set(contrast(cells, "CTRLn_noSL", "C1_div")["worse_set"])
        D = set(contrast(cells, "CTRLg", "CTRLn")["better_set"])
        fila = [name, LV[lv], f"{len(H & D)}/{len(H)}"]
        rec = {"completo": [len(H & D), len(H)]}
        for hs, hd, lab in ((h1, h1, "mismo_A"), (h1, h2, "A_B"), (h2, h2, "mismo_B"), (h2, h1, "B_A")):
            Hh = set(contrast(cells, "CTRLn_noSL", "C1_div", runs=hs)["worse_set"])
            Dh = set(contrast(cells, "CTRLg", "CTRLn", runs=hd)["better_set"])
            fila.append(f"{len(Hh & Dh)}/{len(Hh)}")
            rec[lab] = [len(Hh & Dh), len(Hh)]
        data.setdefault("g1b_mitades", {})[f"{pdir}_{lv}"] = rec
        rows.append(fila)
    t = table(["Par", "Presupuesto", "G1b (51 corridas)", "Daño y mitigación en la mitad A",
               "Daño en A, mitigación en B", "Daño y mitigación en la mitad B", "Daño en B, mitigación en A"], rows)
    t += ("\n\n*Mitad A: corridas 1–25; mitad B: corridas 26–51. Las funciones dañinas y la mitigación se "
          "determinan con Holm sobre la mitad indicada (como en la Tabla 7). Cuando el daño y la mitigación se "
          "determinan en mitades distintas, la tasa no usa las mismas corridas para ambas, y se compara con la "
          "tasa de la misma mitad.*")
    partes.append(("### S8.5. Mitigación G1b con validación por mitades", t))
    nota = (f"*10D, 71 funciones. Holm (artículo): mejor/igual/peor con Holm sobre las 71 funciones y mediana del "
            "rank-biserial, como en las Tablas 7, 8 y 10. Sin corrección: el mismo conteo con α = 0.05 por función. "
            "Entre funciones: Wilcoxon de rangos con signo sobre las 71 medianas (una observación por función, como "
            "en Derrac et al. 2011), con rank-biserial sobre las funciones con medianas distintas (r > 0: la primera "
            "condición tiene menor error). Signos: funciones en que la mediana de la primera condición es menor / "
            "mayor que la de la segunda, con el p bilateral de la prueba binomial de signos. La columna «Stop-loss "
            "sin admisión» de la Tabla 8 no se incluye: CTRLn y CTRLn sin stop-loss coinciden bit a bit. Análisis "
            "descriptivo añadido tras los resultados (D36): no modifica los veredictos pre-registrados.*")
    return partes, nota, data


def supl_robustez(root, a10js):
    """S9: contrastes de G1 por banco y sobre el conjunto sin funciones repetidas (10D)."""
    rows, data = [], {}
    subsets = [(lab, (lambda c, b=b: c["key"].rsplit("_F", 1)[0] == b)) for b, lab, _ in BANCOS]
    subsets.append(("Sin repetidas", lambda c: not es_duplicada(c)))
    excede, cumple = 0, 0
    for pdir, name, lv in configs():
        cells = load(root, pdir, lv)
        for lab, sel in subsets:
            a = contrast(cells, "CTRLg", "CTRLn", sel); b = contrast(cells, "CTRLg", "C1_div", sel)
            c3 = contrast(cells, "C3p", "C1_div", sel)
            tope = NONINF_MAX * a["n"] / 71
            ok = a["better"] > a["worse"] and a["median_r"] >= 0.3 and b["worse"] <= tope
            excede += b["worse"] > tope; cumple += ok
            rows.append([name, LV[lv], f"{lab} ({a['n']})", fmt(a), f"{b['better']}", f"{b['worse']} ({tope:.1f})",
                         fmt(c3), "sí" if ok else "no"])
            data.setdefault(f"{pdir}_{lv}", {})[lab] = {"N": a["n"], "CTRLg_vs_CTRLn": sin_sets(a),
                                                        "CTRLg_vs_C1div": sin_sets(b), "C3p_vs_C1div": sin_sets(c3),
                                                        "tope_proporcional": tope, "cumple": ok}
    t = table(["Par", "Presupuesto", "Subconjunto (N)", "CTRLg vs CTRLn", "CTRLg mejor que C1_div",
               "CTRLg peor que C1_div (tope 7·N/71)", "C3p vs C1_div", "Cumple"], rows)
    n_dup = len(DUPLICADAS)
    lista = "; ".join(f"{b.replace('CEC', 'CEC ')} F{f} ({base}; se conserva {keep})"
                      for (b, f), (base, keep) in DUPLICADAS.items())
    t += (f"\n\n*10D. Los contrastes de la Tabla 7 y C3p vs C1_div (Tabla 10) recalculados dentro de cada banco y "
          f"sobre las {71 - n_dup} funciones que quedan al excluir las {n_dup} funciones básicas cuya función base ya "
          f"aparece en un banco anterior (se conserva la primera aparición): {lista}. Mejor/igual/peor con Holm dentro "
          "de cada subconjunto (mediana del rank-biserial). Cumple: CTRLg mejor > peor que CTRLn con r ≥ 0.3 y CTRLg "
          f"peor que C1_div en a lo sumo 7·N/71 funciones (el tope de 7 de 71 de la enmienda v0.6, en proporción). "
          f"Resultado: el tope proporcional se excede en {excede} de {len(rows)} filas y el criterio por presupuesto se "
          f"cumple en {cumple} de {len(rows)}. El criterio G1 se definió sobre las 71 funciones; esta tabla es un "
          "análisis de robustez descriptivo (D36).*")
    return t, data


def _shaffer_s(k):
    cache = {0: {0}, 1: {0}}

    def S(m):
        if m not in cache:
            cache[m] = {j * (j - 1) // 2 + s for j in range(1, m + 1) for s in S(m - j)}
        return cache[m]
    return sorted(S(k))


def shaffer(M, arms, alpha=0.05):
    """Post-hoc de Shaffer (estático) sobre los rangos de Friedman; misma implementación que
    scripts/cec_harness/stats.py (shaffer_posthoc), sin el control cruzado de Conover."""
    N, k = M.shape
    ranks = np.vstack([rankdata(r) for r in M]); mr = ranks.mean(0)
    se = math.sqrt(k * (k + 1) / (6.0 * N))
    raw = []
    for a, b in combinations(range(k), 2):
        z = (mr[a] - mr[b]) / se
        raw.append({"a": arms[a], "b": arms[b], "z": float(z), "p_raw": float(2.0 * (1.0 - norm.cdf(abs(z))))})
    m = len(raw); svals = _shaffer_s(k)
    thr = [max(s for s in svals if s <= m - i + 1) for i in range(1, m + 1)]
    order = sorted(range(m), key=lambda i: raw[i]["p_raw"])
    adj = [0.0] * m; run = 0.0
    for i, idx in enumerate(order):
        run = max(run, min(1.0, thr[i] * raw[idx]["p_raw"])); adj[idx] = run
    return {"mean_ranks": dict(zip(arms, map(float, mr))),
            "pairs": [r | {"p_shaffer": adj[i], "significant": bool(adj[i] < alpha)} for i, r in enumerate(raw)]}


def tabla_friedman(frs, arms, pie):
    """Tabla traspuesta de Friedman e Iman-Davenport con rangos medios (negrita: el menor)."""
    cols = col_labels()
    N = {f["N"] for f in frs}; dff = {tuple(f["df_FF"]) for f in frs}
    assert len(N) == 1 and len(dff) == 1, (N, dff)
    N = N.pop(); dff = dff.pop()
    rows = {k: [] for k in ["chi2", "p_chi2", "F_F", "p_FF", "sd"] + arms}
    for fr in frs:
        mr = fr["mean_ranks"]; best = min(mr.values())
        rows["chi2"].append(f"{fr['chi2']:.1f}"); rows["p_chi2"].append(fmt_p(fr["p_chi2"]))
        rows["F_F"].append(f"{fr['F_F']:.1f}"); rows["p_FF"].append(fmt_p(fr["p_FF"]))
        rows["sd"].append(f"{fr['sd_rangos_medios']:.2f}")
        for a in arms:
            rows[a].append(bold(f"{mr[a]:.2f}", mr[a] == best))
    labf = [("chi2", f"χ² (gl = {dff[0]})"), ("p_chi2", "p (χ²)"), ("F_F", f"F~F~ (gl = {dff[0]} y {dff[1]})"),
            ("p_FF", "p (F~F~)"), ("sd", "σ de los rangos medios")] + [(a, ARM_LABEL.get(a, a)) for a in arms]
    t = ttable("Estadístico o condición", cols, [[l] + rows[k] for k, l in labf])
    t += (f"\n\n*{pie} N = {N} funciones, k = {len(arms)} condiciones. Friedman sobre la mediana de 51 corridas por "
          f"función, con {dff[0]} grados de libertad; F~F~: corrección de Iman-Davenport, con ({dff[0]}, {dff[1]}) "
          "grados de libertad. Rangos medios (menor = mejor); en negrita, el menor rango medio de cada configuración.*")
    return t


def lista_shaffer(sh_por_cfg, solvers_por_par):
    items = []
    for (pdir, name, lv) in configs():
        sh = sh_por_cfg[f"{pdir}_{lv}"]; mr = sh["mean_ranks"]
        sA, sB = solvers_por_par[name]
        lab = lambda x: f"{x} ({sA if x == 'C0_A' else sB})" if x in ("C0_A", "C0_B") else x
        sig = sorted([p for p in sh["pairs"] if p["significant"]], key=lambda p: p["p_shaffer"])
        txt = "; ".join(f"{lab(a)} mejor que {lab(b)} ({fmt_p_shaffer(p['p_shaffer'])})"
                        for p in sig for a, b in [((p["a"], p["b"]) if mr[p["a"]] < mr[p["b"]] else (p["b"], p["a"]))])
        items.append(f"- {name} a {LV[lv]} ({len(sig)} de {len(sh['pairs'])} pares): {txt}." if sig
                     else f"- {name} a {LV[lv]} (0 de {len(sh['pairs'])} pares).")
    return "\n".join(items)


def supl_seis_brazos(root, a10js, solvers_por_par):
    """S10: Friedman, Iman-Davenport y Shaffer con los seis brazos reales, agregado y por banco (10D)."""
    partes, data = [], {}
    grupos = [("Agregado (71 funciones)", None)] + [(lab, b) for b, lab, _ in BANCOS]
    for j, (lab, b) in enumerate(grupos, 1):
        frs, shs = [], {}
        for pdir, name, lv in configs():
            cells = [c for c in load(root, pdir, lv) if b is None or c["key"].rsplit("_F", 1)[0] == b]
            fr = friedman(cells, ARMS_REALES)
            if b is None:
                ref = a10js[f"{pdir}_{lv}"]["friedman_sin_controles"]
                assert abs(ref["chi2"] - fr["chi2"]) < 1e-9 and abs(ref["F_F"] - fr["F_F"]) < 1e-9
            M = _t(np.array([[np.median(c["errors"][a]) for a in ARMS_REALES] for c in cells]))
            sh = shaffer(M, ARMS_REALES)
            assert all(abs(sh["mean_ranks"][a] - fr["mean_ranks"][a]) < 1e-9 for a in ARMS_REALES)
            frs.append(fr); shs[f"{pdir}_{lv}"] = sh
            data.setdefault(lab, {})[f"{pdir}_{lv}"] = {"friedman": fr, "shaffer": sh["pairs"]}
        pie = "10D." if b is None else f"10D, {lab}."
        t = tabla_friedman(frs, ARMS_REALES, pie)
        sig_tot = sum(sum(p["significant"] for p in sh["pairs"]) for sh in shs.values())
        partes.append((f"### S10.{j}. {lab}", t + "\n\nPares con diferencia significativa (post-hoc de Shaffer, "
                       f"estático, α = 0.05; {sig_tot} en las 6 configuraciones):\n\n" + lista_shaffer(shs, solvers_por_par)))
    nota = (f"*Ómnibus y post-hoc sobre los {len(ARMS_REALES)} brazos reales ({', '.join(ARMS_REALES)}), sin los "
            "controles adversariales CTRLn y CTRLg, que por construcción son los brazos de mayor rango y hacen "
            "trivial el ómnibus de 8 brazos de la Tabla 11 y de S7. El agregado repite el ómnibus de S2 y añade su "
            "post-hoc; el post-hoc por banco responde al protocolo (Friedman + Shaffer por banco). El post-hoc se "
            "calcula aquí con la misma implementación que S1 (Shaffer estático sobre los rangos de Friedman); los p "
            f"ajustados menores que 10^{MENOS}10^ se reportan como cota. Análisis descriptivo añadido tras los "
            "resultados (D36).*")
    return partes, nota, data


def cifras_prosa(a10js, a50js):
    """Cifras derivadas que la prosa cita (todas desde los mismos cálculos de las tablas)."""
    out = {}
    for tag, js in (("10D", a10js), ("50D", a50js)):
        d = {}
        cel = [(f"{n} {lv}", js[f"{p}_{lv}"]) for p, n, lv in configs()]
        d["CTRLg_rango_menor_que_C1div"] = [k for k, v in cel if v["friedman"]["mean_ranks"]["CTRLg"] < v["friedman"]["mean_ranks"]["C1_div"]]
        d["CTRLn_mejor_que_C1div"] = {k: v["ctrln_div"]["better"] for k, v in cel}
        d["reversion_CTRLg_mayor_que_BENg"] = sum(v["mecanismo"]["CTRLg"]["reversion"] > v["mecanismo"]["BENg"]["reversion"] for _, v in cel)
        d["deteccion_G1b_rango_pct"] = [min(100 * v["deteccion"]["detectadas"] / v["deteccion"]["daninas"] for _, v in cel),
                                        max(100 * v["deteccion"]["detectadas"] / v["deteccion"]["daninas"] for _, v in cel)]
        d["ABL_vs_C1div"] = {k: fmt(v["abl_div"], short=True) for k, v in cel}
        d["MODg_vs_C1div"] = {k: fmt(v["modg_div"], short=True) for k, v in cel}
        d["CTRLg_vs_C1div"] = {k: fmt(v["noninf"], short=True) for k, v in cel}
        d["sin_controles_p_FF"] = {k: v["friedman_sin_controles"]["p_FF"] for k, v in cel}
        d["sin_controles_p_chi2"] = {k: v["friedman_sin_controles"]["p_chi2"] for k, v in cel}
        out[tag] = d
    return out


# ------------------------------------------------------------------ orquestación --
def calcular(bac):
    """Calcula todas las tablas. No escribe nada."""
    f1, f1js = t_fase1(bac)
    p1, p2, pjs, ok_piloto = t_piloto(bac)
    a10, a10js, g1_10 = t_alterno(os.path.join(bac, "camino_alterno_v06"), "10D")
    a50, a50js, g1_50 = t_alterno(os.path.join(bac, "camino_alterno_v06_dim50"), "50D (CEC 2022 a 20D), exploratorio",
                                  ref_shaffer="en la sección S4 de este suplementario")
    tax = t_taxonomia(os.path.join(bac, "camino_alterno_v06"))
    hip, hip_info = t_hipotesis(f1js, pjs, ok_piloto)
    tablas = {"FASE1": f1, "PILOTO": p1, "PILOTO_SEC": p2, "HIPOTESIS": hip, "G1_10": a10["g1"],
              "COMP_10": a10["comp"], "MECH_10": a10["mech"], "CANAL_10": a10["canal"], "FRIED_10": a10["fried"],
              "TAX_10": tax, "G1_50": a50["g1"], "COMP_50": a50["comp"], "CANAL_50": a50["canal"]}
    assert list(tablas) == ORDEN
    solvers = {name: tuple(name.split("+")) for _, name in PAIRS}
    fb10 = omnibus_por_banco(os.path.join(bac, "camino_alterno_v06"))
    fb50 = omnibus_por_banco(os.path.join(bac, "camino_alterno_v06_dim50"))
    res_banco = resumen_por_banco(fb10, fb50, a10js, a50js)
    supl_js, supl_md = calcular_supl(a10, a10js, a50, a50js, solvers, fb10, fb50, res_banco,
                                     os.path.join(bac, "camino_alterno_v06"))
    payload = {"fase1_corte1": f1js["corte1"], "piloto": pjs, "piloto_pares_cumplen": ok_piloto, "hipotesis": hip_info,
               "alterno_10": a10js, "alterno_50": a50js, "G1_10_pares": g1_10, "G1_50_pares": g1_50,
               "cifras_prosa": cifras_prosa(a10js, a50js), "omnibus_por_banco_S7": res_banco}
    return {"tablas": tablas, "json": payload, "supl": suplementario(bac), "supl_json": supl_js,
            "supl_md": supl_md, "g1": (g1_10, g1_50)}


def escribir_salidas(res, outdir):
    os.makedirs(outdir, exist_ok=True)
    json.dump(res["json"], open(os.path.join(outdir, "tablas_v13.json"), "w"), indent=1, default=float, ensure_ascii=False)
    json.dump(res["supl_json"], open(os.path.join(outdir, "tablas_v13_supl.json"), "w"), indent=1, default=float,
              ensure_ascii=False)
    open(os.path.join(outdir, "tablas_v13_supl.md"), "w").write(res["supl_md"] + "\n")
    with open(os.path.join(outdir, "suplementario_v13_estadisticos.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["campana", "dimset", "par", "presupuesto", "funcion", "brazo", "media", "mediana", "desv_est", "corridas"])
        w.writerows(res["supl"])
    prev = ["# Tablas del borrador v13 (vista previa generada por script)", "",
            "Cada sección corresponde a un marcador <!-- TABLA:NOMBRE --> del borrador, en el orden del documento.", ""]
    for i, name in enumerate(ORDEN):
        prev += [f"## Tabla {PRIMERA_TABLA + i} — {name}", "", res["tablas"][name], ""]
    open(os.path.join(outdir, "tablas_v13_preview.md"), "w").write("\n".join(prev))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", required=True, help="directorio de salida de JSON, CSV y vistas previas")
    ap.add_argument("--resultados", default=RESULTS,
                    help="ruta a results/cooperative (por defecto, la del repositorio)")
    a = ap.parse_args(argv)
    res = calcular(a.resultados)
    escribir_salidas(res, a.salida)
    g1_10, g1_50 = res["g1"]
    print(f"tablas calculadas en {a.salida}; G1 10D {g1_10}/3, 50D {g1_50}/3; "
          f"suplementario {len(res['supl'])} filas")


if __name__ == "__main__":
    main()
