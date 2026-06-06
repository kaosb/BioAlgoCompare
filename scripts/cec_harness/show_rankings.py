"""Pretty-print the rankings from a protocol_summary.json.

Usage: python scripts/cec_harness/show_rankings.py [path]
Default path: results/cec_protocol/protocol_summary.json
"""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    _REPO, "results", "cec_protocol", "protocol_summary.json")

with open(path) as fh:
    s = json.load(fh)

cfg = s["config"]
print("=" * 74)
print("CEC PROTOCOL RANKINGS  (avg rank, lower = better)")
print(f"problems={cfg['problems']} algos={len(cfg['algos'])} reps={cfg['n_reps']} "
      f"pop={cfg['pop_size']} levels={cfg['maxfes_levels']}")
print(f"ref(Wilcoxon)={cfg['reference']} | {cfg['note_71']}")
print("=" * 74)


def _line(avg_ranks, fr=None):
    ordered = sorted(avg_ranks.items(), key=lambda kv: kv[1])
    medal = ["1.", "2.", "3."]
    parts = []
    for i, (a, r) in enumerate(ordered):
        tag = medal[i] if i < 3 else "  "
        parts.append(f"{tag}{a}={r:.2f}")
    p = ""
    if fr and fr.get("friedman", {}).get("p_value") is not None:
        p = f"   [Friedman p={fr['friedman']['p_value']:.2e}, "
        p += f"rank-std={fr.get('rank_std', float('nan')):.2f}]"
    return "   ".join(parts) + p


print("\n### AGREGADOS (CEC_71 — los rankings titulares del protocolo) ###")
for key, rk in s["rankings"]["aggregate"].items():
    fr = s["friedman_shaffer"]["aggregate"].get(key)
    print(f"\n {key}  (n={rk['n_problems']} problemas)")
    print("   " + _line(rk["avg_ranks"], fr))

print("\n\n### POR BENCHMARK INDIVIDUAL ###")
for key, rk in s["rankings"]["per_benchmark"].items():
    fr = s["friedman_shaffer"]["per_benchmark"].get(key)
    print(f"\n {key}  (n={rk['n_problems']})")
    print("   " + _line(rk["avg_ranks"], fr))

print("\n\n### WILCOXON better/equal/worse  (" + cfg["reference"] +
      " vs cada competidor, agregados) ###")
for key, tbl in s["wilcoxon_bew"]["aggregate"].items():
    print(f"\n {key}:")
    for comp, r in sorted(tbl.items(), key=lambda kv: -kv[1]["better"]):
        print(f"   {cfg['reference']} vs {comp:8s} "
              f"B={r['better']:>2} E={r['equal']:>2} W={r['worse']:>2}")

# Shaffer: how many competitors each algorithm significantly differs from.
print("\n\n### SHAFFER post-hoc — % de pares significativos (agregados) ###")
for key, fr in s["friedman_shaffer"]["aggregate"].items():
    pairs = fr["shaffer"]["pairs"]
    sig = sum(1 for p in pairs if p["significant"])
    print(f" {key}: {sig}/{len(pairs)} pares significativos (p<0.05)")
print("=" * 74)
