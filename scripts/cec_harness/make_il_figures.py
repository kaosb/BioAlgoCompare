"""Figures + LaTeX tables for the IL cross-algorithm study (Paper 2).

Reads:
  results/il_pipeline/il_ood_report.json          (5e3 cross-algo table)
  results/il_pipeline/il_ood_report_fes50000.json (5e4, if present)
  results/oracle_screen/oracle_screen.json        (screening)
  results/cec_protocol/protocol_summary.json      (DE-IL ranking)

Writes under results/il_pipeline/figures/:
  fig_il_bew.(pdf|png)          stacked B/E/W bars per algorithm (per budget)
  fig_oracle_vs_realized.(pdf|png)  screening headroom vs realized median gain
  table_il_cross.tex            cross-algorithm results (LaTeX, protocol style)
  table_deil_wilcoxon.tex       DE-IL vs each competitor (10D & 50D)
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IL_DIR = os.path.join(_REPO, "results", "il_pipeline")
OUT = os.path.join(IL_DIR, "figures")

ORDER = ["DE", "PSO", "GA", "GWO", "ACO", "HO"]


def _load(path):
    p = os.path.join(_REPO, path)
    return json.load(open(p)) if os.path.exists(p) else None


def fig_bew(rep5e3, rep5e4):
    reports = [("MaxFES = 5×10³", rep5e3)]
    if rep5e4:
        reports.append(("MaxFES = 5×10⁴", rep5e4))
    fig, axes = plt.subplots(1, len(reports), figsize=(5.2 * len(reports), 3.6),
                             sharey=True)
    axes = np.atleast_1d(axes)
    colors = {"better": "#2ca02c", "equal": "#d9d9d9", "worse": "#d62728"}
    for ax, (title, rep) in zip(axes, reports):
        algos = [a for a in ORDER if a in rep]
        y = np.arange(len(algos))
        b = np.array([rep[a]["better"] for a in algos])
        e = np.array([rep[a]["equal"] for a in algos])
        w = np.array([rep[a]["worse"] for a in algos])
        ax.barh(y, b, color=colors["better"], label="better")
        ax.barh(y, e, left=b, color=colors["equal"], label="equal")
        ax.barh(y, w, left=b + e, color=colors["worse"], label="worse")
        for yi, (bb, ee, ww) in enumerate(zip(b, e, w)):
            ax.text(bb / 2, yi, str(bb), va="center", ha="center", fontsize=8,
                    color="white", fontweight="bold")
            ax.text(bb + ee + ww / 2, yi, str(ww), va="center", ha="center",
                    fontsize=8, color="white", fontweight="bold")
        ax.set_yticks(y)
        ax.set_yticklabels([f"{a}+IL" for a in algos], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("# funciones OOD (de 41)", fontsize=8)
        ax.set_title(title, fontsize=10, fontweight="bold")
    axes[0].legend(loc="lower right", fontsize=7, frameon=False)
    fig.suptitle("IL vs algoritmo base — Wilcoxon por función (51 semillas pareadas)",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"fig_il_bew.{ext}"), dpi=150)
    plt.close(fig)


def fig_oracle_vs_realized(rep5e3, screen):
    """Screening headroom (a-priori) vs realized median improvement (posterior)."""
    if not screen:
        return
    # screening: mean headroom per algo (records averaged)
    from collections import defaultdict
    head = defaultdict(list)
    for r in screen["records"]:
        head[r["algo"]].append(r.get("headroom", r.get("rel_gain", 0.0)))
    algos = [a for a in ORDER if a in rep5e3 and a in head]
    x = [float(np.mean(head[a])) * 100 for a in algos]
    y = [rep5e3[a]["median_rel_improvement"] * 100 for a in algos]
    frac_b = [rep5e3[a]["better"] / 41 for a in algos]

    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    sc = ax.scatter(x, y, s=[200 * f + 30 for f in frac_b],
                    c=["#2ca02c" if yy > 5 else ("#d62728" if yy < -2 else "#7f7f7f")
                       for yy in y], zorder=3, edgecolor="black", linewidth=0.6)
    for xi, yi, a in zip(x, y, algos):
        ax.annotate(a, (xi, yi), textcoords="offset points", xytext=(7, 4),
                    fontsize=9)
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_xlabel("Techo del oráculo robusto (headroom per-step, %)", fontsize=9)
    ax.set_ylabel("Mejora realizada por IL (mediana OOD, %)", fontsize=9)
    ax.set_title("El cribado anticipa dónde IL ayuda\n(tamaño = fracción de funciones better)",
                 fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"fig_oracle_vs_realized.{ext}"), dpi=150)
    plt.close(fig)


def table_il_cross(rep5e3, rep5e4, screen):
    """Audited v2 table: median-labelled B/E/W with raw and Holm-corrected
    counts, Vargha-Delaney A12 and median relative improvement, per budget."""
    from collections import defaultdict
    head = defaultdict(lambda: float("nan"))
    if screen:
        acc = defaultdict(list)
        for r in screen["records"]:
            acc[r["algo"]].append(r.get("headroom", 0.0))
        for a, v in acc.items():
            head[a] = float(np.mean(v)) * 100

    def fmt(rep, a):
        if not rep or a not in rep:
            return "--", "--", "--", "--"
        r = rep[a]
        raw = "{better}/{equal}/{worse}".format(**r["bew_raw"])
        hol = "{better}/{equal}/{worse}".format(**r["bew_holm"])
        a12 = f"{r['median_a12']:.2f}"
        med = f"{r['median_rel_mean']*100:+.1f}\\%"
        return raw, hol, a12, med

    lines = [
        "% Cross-algorithm IL results, audited v2 (median-labelled Wilcoxon,",
        "% raw and Holm-corrected counts, Vargha-Delaney A12).",
        "\\begin{tabular}{lrrrrrrrr}", "\\hline",
        " & Oracle & \\multicolumn{4}{c}{MaxFES $=5{\\times}10^3$} & "
        "\\multicolumn{3}{c}{MaxFES $=5{\\times}10^4$} \\\\",
        "Algorithm & headroom & B/E/W & Holm & $A_{12}$ & Median & "
        "B/E/W & Holm & $A_{12}$ \\\\", "\\hline",
    ]
    for a in ORDER:
        if a not in rep5e3:
            continue
        raw3, hol3, a123, med3 = fmt(rep5e3, a)
        raw4, hol4, a124, _ = fmt(rep5e4, a)
        h = f"{head[a]:+.1f}\\%" if not np.isnan(head[a]) else "--"
        lines.append(f"{a}+IL & {h} & {raw3} & {hol3} & {a123} & {med3} & "
                     f"{raw4} & {hol4} & {a124} \\\\")
    lines += ["\\hline", "\\end{tabular}"]
    with open(os.path.join(OUT, "table_il_cross.tex"), "w") as fh:
        fh.write("\n".join(lines))


def table_deil_wilcoxon(summary):
    if not summary:
        return
    lines = ["% DE-IL (proposed) vs each competitor (auto-generated)",
             "\\begin{tabular}{lrr}", "\\hline",
             "Competidor & B/E/W (10D) & B/E/W (50D/20D) \\\\", "\\hline"]
    t10 = summary["wilcoxon_bew"]["aggregate"].get("CEC_71_10_FES5000", {})
    t50 = summary["wilcoxon_bew"]["aggregate"].get("CEC_71_50_FES5000", {})
    comps = sorted(t10, key=lambda c: -t10[c]["better"])
    for c in comps:
        a = t10[c]
        b = t50.get(c, {})
        s10 = f"{a['better']}/{a['equal']}/{a['worse']}"
        s50 = f"{b.get('better','-')}/{b.get('equal','-')}/{b.get('worse','-')}"
        lines.append(f"{c} & {s10} & {s50} \\\\")
    lines += ["\\hline", "\\end{tabular}"]
    with open(os.path.join(OUT, "table_deil_wilcoxon.tex"), "w") as fh:
        fh.write("\n".join(lines))


def _v2_compat(rep):
    """Adapt an audited v2 report to the {better,equal,worse,median_rel_improvement}
    shape the figures consume (raw counts; Holm shown in the table)."""
    if rep is None:
        return None
    out = {}
    for a, r in rep.items():
        out[a] = {**r["bew_raw"],
                  "median_rel_improvement": r["median_rel_mean"]}
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    # Audited v2 reports (median-labelled, Holm available); fall back to v1.
    rep3v2 = _load("results/il_pipeline/il_ood_report_v2.json")
    rep4v2 = _load("results/il_pipeline/il_ood_report_v2_fes50000.json")
    rep3 = _v2_compat(rep3v2) or _load("results/il_pipeline/il_ood_report.json")
    rep4 = _v2_compat(rep4v2) or _load("results/il_pipeline/il_ood_report_fes50000.json")
    # Prefer the leak-free CEC2014 (train-only) screening when available (C2).
    screen = (_load("results/oracle_screen/oracle_screen_cec2014.json")
              or _load("results/oracle_screen/oracle_screen.json"))
    summary = _load("results/cec_protocol/protocol_summary.json")
    fig_bew(rep3, rep4)
    fig_oracle_vs_realized(rep3, screen)
    table_il_cross(rep3v2 or rep3, rep4v2 or rep4, screen)
    table_deil_wilcoxon(summary)
    print(f"Artefactos IL en {OUT}/")
    for f in sorted(os.listdir(OUT)):
        print("  ", f)


if __name__ == "__main__":
    main()
