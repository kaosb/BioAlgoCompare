"""Fase 1 (pre-registro fase positiva v0.2) — cálculo de las 4 cotas y Corte 1.

Lee crudos (celdas históricas, curvas C0 re-instrumentadas, logs de efecto de
E2), aplica las definiciones operacionales y umbrales FIJADOS en
docs/preregistro_fase_positiva/ENMIENDA_v0.2.md, y emite:

  results/cooperative/fase1/cotas_fase1.json     (todos los números + decisión)
  results/cooperative/fase1/cotas_fase1.md       (tablas para el registro)

Uso: python scripts/cec_harness/fase1_cotas.py
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np  # noqa: E402
from scipy.stats import wilcoxon  # noqa: E402

from utils.provenance import provenance  # noqa: E402

_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SCALE = os.path.join(_REPO, "results", "cooperative", "scale")
F1 = os.path.join(_REPO, "results", "cooperative", "fase1")
CURVES = os.path.join(F1, "c0_curves")
E2LOG = os.path.join(F1, "e2_effect_logs.json")

# ---- umbrales FIJADOS (ENMIENDA_v0.2 §A) -------------------------------------
TH = {"wins_min": 20, "n_funcs": 70, "median_r_min": 0.3,
      "winner_change_min": 0.40, "stability_min": 0.70,
      "stability_min_seeds": 30, "alpha": 0.05}
PAIRS = {"GWOGA": ("GWO", "GA", [5000, 50000, 500000]),
         "DEGA": ("DE", "GA", [5000, 50000]),
         "PSOACO": ("PSO", "ACO", [5000, 50000])}
SOLVERS7 = ["DE", "PSO", "GWO", "GA", "ACO", "SSA", "WOA"]
DELTA = 500


def holm(pv):
    m = len(pv); order = sorted(range(m), key=lambda i: pv[i])
    adj = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * pv[i]); adj[i] = min(1.0, run)
    return adj


def paired(a, b):
    """p de Wilcoxon (empates descartados) y rank-biserial pareado; >0 = a mejor."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = a - b; dd = d[d != 0]
    if len(dd) == 0:
        return 1.0, 0.0
    _, p = wilcoxon(a, b, zero_method="wilcox")
    r = np.argsort(np.argsort(np.abs(dd))) + 1.0
    return float(p), float((r[dd < 0].sum() - r[dd > 0].sum()) / r.sum())


def contrast_table(pairs_of_arrays):
    """pairs_of_arrays: lista de (A, B) por función -> wins, losses, mediana r."""
    ps, rs = [], []
    for a, b in pairs_of_arrays:
        p, r = paired(a, b); ps.append(p); rs.append(r)
    adj = holm(ps)
    wins = sum(1 for h, r in zip(adj, rs) if h < TH["alpha"] and r > 0)
    loss = sum(1 for h, r in zip(adj, rs) if h < TH["alpha"] and r < 0)
    return {"wins": wins, "losses": loss, "n": len(ps),
            "median_r": float(np.median(rs)) if rs else 0.0}


def load_cells(pair_dir):
    return {os.path.basename(f): json.load(open(f))
            for f in sorted(glob.glob(os.path.join(SCALE, pair_dir, "*.json")))}


def load_curves(solver, level):
    d = os.path.join(CURVES, f"{solver}_{level}")
    return {os.path.basename(f): json.load(open(f))
            for f in sorted(glob.glob(os.path.join(d, "*.json")))}


# ---- (1) VBS por función --------------------------------------------------------
def cota_vbs():
    out = {}
    for pdir, (A, B, levels) in PAIRS.items():
        for lv in levels:
            cells = load_cells(f"{pdir}_{lv}")
            if not cells:
                continue
            rows, chosen = [], Counter()
            for name, c in cells.items():
                ea, eb = c["errors"][f"C0_{A}"], c["errors"][f"C0_{B}"]
                vbs = ea if np.median(ea) <= np.median(eb) else eb
                chosen[A if vbs is ea else B] += 1
                rows.append((vbs, c["errors"]["C1_div"]))
            t = contrast_table(rows)
            t["vbs_choice"] = dict(chosen)
            t["pass"] = bool(t["wins"] >= TH["wins_min"] and t["median_r"] >= TH["median_r_min"])
            out[f"{pdir}_{lv}"] = t
    return out


# ---- (2) oráculo de conmutación -------------------------------------------------
def _static_opt(ca, cb):
    K = len(ca)                      # ventanas de Δ; x_A = k*Δ, x_B = (K-k)*Δ
    best = float("inf")
    for k in range(1, K):            # k ventanas a A, K-k a B
        best = min(best, min(ca[k - 1], cb[K - k - 1]))
    return best


def _greedy_clairvoyant(ca, cb):
    K = len(ca); ia = ib = 0          # ventanas consumidas por cada solver
    def gain(c, i):
        if i >= len(c):
            return -float("inf")
        prev = c[i - 1] if i > 0 else float("inf")
        cur = c[i]
        return (prev - cur) if np.isfinite(prev) else float("inf")
    for _ in range(K):
        if ia >= K:  ib += 1; continue
        if ib >= K:  ia += 1; continue
        if gain(ca, ia) >= gain(cb, ib): ia += 1
        else: ib += 1
    ea = ca[ia - 1] if ia > 0 else float("inf")
    eb = cb[ib - 1] if ib > 0 else float("inf")
    return min(ea, eb)


def cota_oraculo():
    out = {}
    for pdir, (A, B, levels) in PAIRS.items():
        for lv in levels:
            ca_all, cb_all = load_curves(A, lv), load_curves(B, lv)
            cells = load_cells(f"{pdir}_{lv}")
            if not ca_all or not cb_all or not cells:
                out[f"{pdir}_{lv}"] = {"status": "sin_curvas (diferido/en curso)"}
                continue
            rows_g, rows_s, bitm = [], [], []
            for name, c in cells.items():
                if name not in ca_all or name not in cb_all:
                    continue
                CA, CB = ca_all[name], cb_all[name]
                bitm.append((CA.get("bitmatch_hist"), CB.get("bitmatch_hist")))
                g = [_greedy_clairvoyant(CA["curves"][r], CB["curves"][r]) for r in range(c["runs"])]
                s = [_static_opt(CA["curves"][r], CB["curves"][r]) for r in range(c["runs"])]
                rows_g.append((g, c["errors"]["C1_div"]))
                rows_s.append((s, c["errors"]["C1_div"]))
            tg, ts = contrast_table(rows_g), contrast_table(rows_s)
            tg["pass"] = bool(tg["wins"] >= TH["wins_min"] and tg["median_r"] >= TH["median_r_min"])
            ts["pass"] = bool(ts["wins"] >= TH["wins_min"] and ts["median_r"] >= TH["median_r_min"])
            out[f"{pdir}_{lv}"] = {"2b_conmutacion_clarividente": tg,
                                   "2a_asignacion_estatica_optima": ts,
                                   "n_funcs_con_curvas": len(rows_g),
                                   "bitmatch_all": bool(all(x in (True, None) and y in (True, None) for x, y in bitm))}
    return out


# ---- (3) cribado 70 x 7 ---------------------------------------------------------
def cota_cribado():
    out = {}
    for lv in [5000, 50000]:
        finals = {}
        for s in SOLVERS7:
            cur = load_curves(s, lv)
            if cur:
                finals[s] = {n: v["finals"] for n, v in cur.items()}
        if len(finals) < 7:
            # fallback: 5 solvers desde celdas (SSA/WOA en curso)
            for pdir, (A, B, _) in PAIRS.items():
                for n, c in load_cells(f"{pdir}_{lv}").items():
                    finals.setdefault(A, {})[n] = c["errors"][f"C0_{A}"]
                    finals.setdefault(B, {})[n] = c["errors"][f"C0_{B}"]
        names = sorted(set.intersection(*[set(v) for v in finals.values()])) if finals else []
        winners = []
        for n in names:
            med = {s: float(np.median(finals[s][n])) for s in finals}
            winners.append(min(med, key=med.get))
        cnt = Counter(winners)
        modal, fmodal = (cnt.most_common(1)[0] if cnt else (None, 0))
        change = 1.0 - fmodal / len(names) if names else 0.0
        pair_split = {}
        for pdir, (A, B, _) in PAIRS.items():
            if A in finals and B in finals:
                wa = sum(1 for n in names if np.median(finals[A][n]) < np.median(finals[B][n]))
                pair_split[pdir] = {A: wa, B: len(names) - wa}
        out[str(lv)] = {"solvers": sorted(finals), "n_funcs": len(names),
                        "winner_counts": dict(cnt), "modal": modal,
                        "winner_change": round(change, 3),
                        "pass": bool(change >= TH["winner_change_min"]),
                        "pair_split": pair_split}
    return out


# ---- (4) estabilidad del efecto ------------------------------------------------
def cota_estabilidad():
    if not os.path.exists(E2LOG):
        return {"status": "sin_logs (en curso)"}
    d = json.load(open(E2LOG))
    res = {}
    for arm in d["config"]["arms"]:
        agg = defaultdict(list)          # triple -> lista de signos por (func, seed)
        for f, arms in d["per_func"].items():
            for triple, v in arms.get(arm, {}).items():
                for m in v["per_seed_mean_effect"]:
                    if m is not None:
                        agg[triple].append(np.sign(m))
        rows = {}
        for triple, signs in agg.items():
            signs = np.asarray(signs)
            maj = 1.0 if (signs > 0).sum() >= (signs < 0).sum() else -1.0
            stab = float((signs == maj).mean()) if len(signs) else 0.0
            rows[triple] = {"n_seed_obs": int(len(signs)), "majority_sign": "daño" if maj > 0 else "beneficio",
                            "stability": round(stab, 3)}
        elig = [r for r in rows.values() if r["n_seed_obs"] >= TH["stability_min_seeds"]]
        ok = sum(1 for r in elig if r["stability"] >= TH["stability_min"])
        res[arm] = {"triples": rows, "n_eligible": len(elig), "n_stable": ok,
                    "pass": bool(elig and ok >= (len(elig) + 1) // 2)}
    return res


def main():
    os.makedirs(F1, exist_ok=True)
    c1, c2, c3, c4 = cota_vbs(), cota_oraculo(), cota_cribado(), cota_estabilidad()
    any1 = any(v.get("pass") for v in c1.values())
    any2 = any(isinstance(v, dict) and v.get("2b_conmutacion_clarividente", {}).get("pass")
               for v in c2.values())
    decision = ("CONTINUAR a Fase 2 (alguna cota de asignacion supera el umbral)"
                if (any1 or any2) else
                "CAMINO ALTERNO (ninguna cota de asignacion supera el umbral)")
    out = {"thresholds": TH, "cota1_vbs": c1, "cota2_oraculo": c2,
           "cota3_cribado": c3, "cota4_estabilidad": c4,
           "corte1": {"cota1_supera": any1, "cota2_supera": any2, "decision": decision},
           "provenance": provenance()}
    with open(os.path.join(F1, "cotas_fase1.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    # markdown
    L = ["# Cotas de Fase 1 (pre-registro v0.2)\n",
         f"Umbrales: {TH}\n", "## (1) Virtual-best por funcion vs C1_div\n",
         "| celda | mejor/peor | mediana r | eleccion VBS | supera |", "|---|---|---|---|---|"]
    for k, v in c1.items():
        L.append(f"| {k} | {v['wins']}/{v['losses']} | {v['median_r']:.2f} | {v['vbs_choice']} | {'SI' if v['pass'] else 'no'} |")
    L += ["\n## (2) Oraculo de conmutacion por Δ vs C1_div\n",
          "| celda | 2b clarividente mejor/peor (r) | 2a estatica optima mejor/peor (r) | funcs | bitmatch | supera(2b) |", "|---|---|---|---|---|---|"]
    for k, v in c2.items():
        if "status" in v:
            L.append(f"| {k} | {v['status']} | | | | |"); continue
        g, s = v["2b_conmutacion_clarividente"], v["2a_asignacion_estatica_optima"]
        L.append(f"| {k} | {g['wins']}/{g['losses']} ({g['median_r']:.2f}) | {s['wins']}/{s['losses']} ({s['median_r']:.2f}) | {v['n_funcs_con_curvas']} | {v['bitmatch_all']} | {'SI' if g['pass'] else 'no'} |")
    L += ["\n## (3) Cribado de complementariedad\n",
          "| nivel | solvers | ganadores | modal | cambio de ganador | supera | split por par |", "|---|---|---|---|---|---|---|"]
    for k, v in c3.items():
        L.append(f"| {k} | {len(v['solvers'])} | {v['winner_counts']} | {v['modal']} | {v['winner_change']:.2f} | {'SI' if v['pass'] else 'no'} | {v['pair_split']} |")
    L += ["\n## (4) Estabilidad del efecto por triple\n"]
    if "status" in c4:
        L.append(c4["status"])
    else:
        for arm, v in c4.items():
            L.append(f"\n**{arm}**: elegibles={v['n_eligible']}, estables={v['n_stable']}, supera={'SI' if v['pass'] else 'no'}\n")
            L += ["| triple | semillas | signo mayoritario | estabilidad |", "|---|---|---|---|"]
            for t, r in sorted(v["triples"].items()):
                L.append(f"| {t} | {r['n_seed_obs']} | {r['majority_sign']} | {r['stability']:.2f} |")
    L += ["\n## Corte 1\n", f"cota1 supera: {any1}; cota2 supera: {any2}", f"\n**Decision: {decision}**"]
    with open(os.path.join(F1, "cotas_fase1.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
