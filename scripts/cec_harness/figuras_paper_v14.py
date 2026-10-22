"""Figuras del artículo a partir de las cifras ya calculadas por el generador de
tablas (tablas_v13.json de tablas_paper_v13.py); no lee los datos crudos.

  fig2_rangos_10D   rangos medios de Friedman (Tabla 11): 8 brazos por par y presupuesto, 10D
  fig1_g1_10D       mejor/igual/peor de los contrastes del criterio G1 (Tabla 7), 10D

Uso: .venv/bin/python scripts/cec_harness/figuras_paper_v14.py --tablas DIR [--salida DIR]
     (salida por defecto: DIR/figs)
Escala de grises apta para impresión; los pies de figura van en el artículo.
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))  # las cifras se pasan con --tablas (salida de tablas_paper_v13.py)
PAIRS = [("GWOGA", "GWO+GA"), ("DEGA", "DE+GA"), ("PSOACO", "PSO+ACO")]
LEVELS = [(5000, "5·10³"), (50000, "5·10⁴")]
ARMS8 = ["C0_A", "C0_B", "C1_div", "C2p", "C3p", "ABL", "CTRLn", "CTRLg"]
NONINF_MAX, UMBRAL_MEJOR = 7, 20

plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42})


def etiqueta(arm, par):
    a, b = par.split("+")
    return {"C0_A": f"C0_A ({a})", "C0_B": f"C0_B ({b})"}.get(arm, arm)


def fig_rangos(js, out):
    fig, axes = plt.subplots(len(PAIRS), len(LEVELS), figsize=(6.6, 6.4), sharey=True)
    greys = ["0.15", "0.35", "0.55", "0.70", "0.80", "0.90"]
    for i, (pdir, par) in enumerate(PAIRS):
        for j, (lv, lvlab) in enumerate(LEVELS):
            ax = axes[i, j]
            mr = js[f"{pdir}_{lv}"]["friedman"]["mean_ranks"]
            vals = [mr[a] for a in ARMS8]
            best = min(vals)
            for k, (a, v) in enumerate(zip(ARMS8, vals)):
                ctrl = a.startswith("CTRL")
                ax.bar(k, v, width=0.72, color="white" if ctrl else greys[k], edgecolor="black", linewidth=0.6,
                       hatch="////" if ctrl else None)
                if v == best:
                    ax.text(k, v + 0.08, "▼", ha="center", va="bottom", fontsize=7)
            ax.set_xticks(range(len(ARMS8)))
            ax.set_xticklabels([etiqueta(a, par) for a in ARMS8], rotation=60, ha="right", fontsize=7)
            ax.set_ylim(0, 8)
            ax.set_yticks([1, 3, 5, 7])
            ax.set_title(f"{par}, {lvlab} evaluaciones", fontsize=9)
            if j == 0:
                ax.set_ylabel("rango medio (menor es mejor)")
    fig.legend(handles=[Patch(facecolor="0.55", edgecolor="black", label="brazos reales"),
                        Patch(facecolor="white", edgecolor="black", hatch="////", label="controles adversariales (CTRLn, CTRLg)")],
               loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"fig2_rangos_10D.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def fig_g1(js, out):
    rows = []
    for pdir, par in PAIRS:
        for lv, lvlab in LEVELS:
            c = js[f"{pdir}_{lv}"]
            rows.append((f"{par}, {lvlab}", "CTRLg vs CTRLn", c["det"]))
            rows.append((f"{par}, {lvlab}", "CTRLg vs C1_div", c["noninf"]))
    n = len(rows)
    fig, ax = plt.subplots(figsize=(6.6, 5.2))
    ys = []
    y = 0
    for idx, (cfg, lab, t) in enumerate(rows):
        if idx % 2 == 0 and idx:
            y += 0.6
        ys.append(y)
        b, e, w = t["better"], t["equal"], t["worse"]
        ax.barh(y, b, color="0.25", edgecolor="black", linewidth=0.5, height=0.8)
        ax.barh(y, e, left=b, color="0.85", edgecolor="black", linewidth=0.5, height=0.8)
        ax.barh(y, w, left=b + e, color="white", edgecolor="black", linewidth=0.5, height=0.8, hatch="////")
        ax.text(72, y, f"{b}/{e}/{w}", va="center", fontsize=7.5)
        y += 1
    labels = [f"{cfg}\n{lab}" for cfg, lab, _ in rows]
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 84)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 71])
    ax.set_xlabel("funciones (de 71)")
    ax.axvline(UMBRAL_MEJOR, color="black", linestyle="--", linewidth=0.8)
    ax.text(UMBRAL_MEJOR + 0.5, ys[0] - 0.9, "umbral: mejor ≥ 20\n(CTRLg vs CTRLn)", fontsize=7, va="bottom")
    ax.axvline(71 - NONINF_MAX, color="black", linestyle=":", linewidth=0.8)
    ax.text(71 - NONINF_MAX + 0.5, ys[0] - 0.9, "tope: peor ≤ 7\n(CTRLg vs C1_div)", fontsize=7, va="bottom")
    ax.legend(handles=[Patch(facecolor="0.25", edgecolor="black", label="mejor"),
                       Patch(facecolor="0.85", edgecolor="black", label="igual"),
                       Patch(facecolor="white", edgecolor="black", hatch="////", label="peor")],
              loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"fig1_g1_10D.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tablas", required=True, help="directorio con tablas_v13.json (salida de tablas_paper_v13.py)")
    ap.add_argument("--salida", default=None, help="directorio de salida (por defecto, <tablas>/figs)")
    a = ap.parse_args(argv)
    a.salida = a.salida or os.path.join(a.tablas, "figs")
    js = json.load(open(os.path.join(a.tablas, "tablas_v13.json")))["alterno_10"]
    os.makedirs(a.salida, exist_ok=True)
    fig_rangos(js, a.salida)
    fig_g1(js, a.salida)
    print(f"figuras escritas en {a.salida}: fig2_rangos_10D, fig1_g1_10D (pdf y png)")


if __name__ == "__main__":
    main()
