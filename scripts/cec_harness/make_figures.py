"""Generate protocol Section-8 artefacts from protocol_summary.json:

  * fig_ranks_aggregate.(pdf|png)  -- avg-rank bar charts, CEC_71_10 vs _50
  * fig_ranks_per_benchmark.(pdf|png) -- 2x3 grid (benchmark x dim-set)
  * table_positions.(md|tex)       -- final position of each algo per ranking
  * table_wilcoxon.(md)            -- REFERENCE better/equal/worse vs each
  * table_shaffer.(md)             -- % significant pairs per config

Lightweight (matplotlib). Outputs under results/cec_protocol/figures/.
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SUMMARY = os.path.join(_REPO, "results", "cec_protocol", "protocol_summary.json")
OUT = os.path.join(_REPO, "results", "cec_protocol", "figures")

# Algorithm family -> colour (to make the structural pattern visible).
FAMILY = {
    "DE": ("DE classic", "#9ecae1"),
    "L-SHADE": ("DE adaptive", "#3182bd"), "JADE": ("DE adaptive", "#3182bd"),
    "jSO": ("DE adaptive", "#3182bd"), "NL-SHADE-RSP": ("DE adaptive", "#3182bd"),
    "L-SRTDE": ("DE adaptive", "#3182bd"), "j2020": ("DE adaptive", "#3182bd"),
    "ARRDE": ("DE adaptive", "#3182bd"), "IMODE": ("DE adaptive", "#3182bd"),
    "LSHADE-cnEpSin": ("DE adaptive", "#3182bd"),
    "AGSK": ("GSK", "#31a354"),
    "CMA-ES": ("CMA-ES", "#e6550d"), "BIPOP-aCMAES": ("CMA-ES", "#e6550d"),
    "PSO": ("Swarm", "#fdae6b"), "GWO": ("Swarm", "#fdae6b"),
    "ACO": ("Swarm", "#fdae6b"),
    "GA": ("GA", "#756bb1"),
    "HO": ("Bio (HO)", "#969696"),
}


def _colour(algo):
    return FAMILY.get(algo, ("Other", "#cccccc"))[1]


def _bar(ax, avg_ranks, title):
    items = sorted(avg_ranks.items(), key=lambda kv: kv[1])
    names = [a for a, _ in items]
    vals = [v for _, v in items]
    colours = [_colour(a) for a in names]
    y = np.arange(len(names))
    ax.barh(y, vals, color=colours, edgecolor="black", linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("avg rank (lower = better)", fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold")
    for yi, v in zip(y, vals):
        ax.text(v + 0.1, yi, f"{v:.2f}", va="center", fontsize=6)
    ax.grid(axis="x", alpha=0.3)


def fig_aggregate(s):
    agg = s["rankings"]["aggregate"]
    keys = sorted(agg)  # CEC_71_10_*, CEC_71_50_*
    fig, axes = plt.subplots(1, len(keys), figsize=(4.2 * len(keys), 5.5))
    if len(keys) == 1:
        axes = [axes]
    for ax, k in zip(axes, keys):
        _bar(ax, agg[k]["avg_ranks"], k.replace("_FES", " FES"))
    _legend(fig)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"fig_ranks_aggregate.{ext}"), dpi=150)
    plt.close(fig)


def fig_per_benchmark(s):
    pb = s["rankings"]["per_benchmark"]
    keys = list(pb)
    n = len(keys)
    ncol = 3
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 5.0 * nrow))
    axes = np.atleast_1d(axes).flatten()
    for ax, k in zip(axes, keys):
        _bar(ax, pb[k]["avg_ranks"], k.replace("_FES", " FES"))
    for ax in axes[n:]:
        ax.axis("off")
    _legend(fig)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"fig_ranks_per_benchmark.{ext}"), dpi=150)
    plt.close(fig)


def _legend(fig):
    seen = {}
    for algo, (fam, col) in FAMILY.items():
        seen[fam] = col
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, ec="black", lw=0.4)
               for c in seen.values()]
    fig.legend(handles, list(seen), loc="lower center", ncol=len(seen),
               fontsize=7, frameon=False)


def table_positions(s):
    """Final position (1=best) of each algo in every ranking -> md + tex."""
    rankings = {}
    rankings.update({k: v["avg_ranks"] for k, v in
                     s["rankings"]["per_benchmark"].items()})
    rankings.update({k: v["avg_ranks"] for k, v in
                     s["rankings"]["aggregate"].items()})
    cols = list(rankings)
    algos = s["config"]["algos"]

    # position per ranking (rank by avg-rank value)
    pos = {a: {} for a in algos}
    for k in cols:
        order = sorted(rankings[k].items(), key=lambda kv: kv[1])
        for i, (a, _) in enumerate(order, 1):
            pos[a][k] = i
    # sort algos by mean position
    mean_pos = {a: np.mean([pos[a][k] for k in cols]) for a in algos}
    algos_sorted = sorted(algos, key=lambda a: mean_pos[a])

    short = [c.replace("_FES5000", "").replace("CEC", "") for c in cols]
    # markdown
    md = ["| Algoritmo | " + " | ".join(short) + " | media |",
          "|" + "---|" * (len(cols) + 2)]
    for a in algos_sorted:
        row = [a] + [str(pos[a][k]) for k in cols] + [f"{mean_pos[a]:.1f}"]
        md.append("| " + " | ".join(row) + " |")
    with open(os.path.join(OUT, "table_positions.md"), "w") as fh:
        fh.write("\n".join(md))
    # latex
    tex = ["\\begin{tabular}{l" + "c" * (len(cols) + 1) + "}", "\\hline",
           "Algoritmo & " + " & ".join(short) + " & media \\\\", "\\hline"]
    for a in algos_sorted:
        row = [a] + [str(pos[a][k]) for k in cols] + [f"{mean_pos[a]:.1f}"]
        tex.append(" & ".join(row) + " \\\\")
    tex += ["\\hline", "\\end{tabular}"]
    with open(os.path.join(OUT, "table_positions.tex"), "w") as fh:
        fh.write("\n".join(tex))
    return algos_sorted, mean_pos


def table_wilcoxon(s):
    ref = s["config"]["reference"]
    md = [f"# Wilcoxon better/equal/worse ({ref} vs cada competidor)\n"]
    for scope in ("aggregate",):
        for key, tbl in s["wilcoxon_bew"][scope].items():
            md.append(f"\n## {key}\n")
            md.append("| competidor | B | E | W |")
            md.append("|---|---|---|---|")
            for comp, r in sorted(tbl.items(), key=lambda kv: -kv[1]["better"]):
                md.append(f"| {comp} | {r['better']} | {r['equal']} | {r['worse']} |")
    with open(os.path.join(OUT, "table_wilcoxon.md"), "w") as fh:
        fh.write("\n".join(md))


def table_shaffer(s):
    md = ["# Shaffer: % de pares significativos (p<0.05)\n",
          "| config | pares signif. | total | % |", "|---|---|---|---|"]
    for scope in ("aggregate", "per_benchmark"):
        for key, fr in s["friedman_shaffer"][scope].items():
            pairs = fr["shaffer"]["pairs"]
            sig = sum(1 for p in pairs if p["significant"])
            md.append(f"| {key} | {sig} | {len(pairs)} | "
                      f"{100*sig/len(pairs):.0f}% |")
    with open(os.path.join(OUT, "table_shaffer.md"), "w") as fh:
        fh.write("\n".join(md))


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(SUMMARY) as fh:
        s = json.load(fh)
    fig_aggregate(s)
    fig_per_benchmark(s)
    algos_sorted, mean_pos = table_positions(s)
    table_wilcoxon(s)
    table_shaffer(s)
    print(f"Artefactos en {OUT}/")
    print("  fig_ranks_aggregate.pdf/png, fig_ranks_per_benchmark.pdf/png")
    print("  table_positions.md/tex, table_wilcoxon.md, table_shaffer.md")
    print("\nRanking global por posicion media (todos los rankings):")
    for a in algos_sorted:
        print(f"  {a:16s} {mean_pos[a]:.2f}")


if __name__ == "__main__":
    main()
