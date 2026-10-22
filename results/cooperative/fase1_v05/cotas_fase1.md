# Fase 1 re-ejecutada (benchmark oficial, v0.5) — cotas

Umbrales (v0.2 §A): {'wins_min': 20, 'median_r_min': 0.3, 'winner_change_min': 0.4, 'stability_min': 0.7, 'stability_min_seeds': 30, 'alpha': 0.05}

| celda | (1) VBS | (2a) estático óptimo | (2b) conmutación | (2c) exploratorio |
|---|---|---|---|---|
| GWOGA_5000 | 14/1 (r=0.175) | 34/2 (r=0.425) ✓ | 2/16 (r=-0.199) | 3/15 (r=-0.165) |
| GWOGA_50000 | 16/3 (r=0.054) | 40/0 (r=0.56) ✓ | 0/42 (r=-0.594) | 0/42 (r=-0.594) |
| GWOGA_500000 | 22/1 (r=0.196) | 39/0 (r=0.573) ✓ | 0/50 (r=-0.772) | 0/50 (r=-0.772) |
| DEGA_5000 | 67/0 (r=1.0) ✓ | 71/0 (r=1.0) ✓ | 20/1 (r=0.445) ✓ | 32/1 (r=0.615) ✓ |
| DEGA_50000 | 66/0 (r=1.0) ✓ | 71/0 (r=1.0) ✓ | 54/7 (r=0.923) ✓ | 54/7 (r=0.923) ✓ |
| PSOACO_5000 | 24/1 (r=0.367) ✓ | 64/0 (r=0.74) ✓ | 0/11 (r=-0.222) | 1/6 (r=-0.178) |
| PSOACO_50000 | 3/8 (r=-0.063) | 14/0 (r=0.345) | 2/8 (r=0.0) | 2/8 (r=0.0) |

## (3) cribado 71 × 7

- 5000: {'n_funcs': 71, 'winner_counts': {'ACO': 15, 'GA': 13, 'PSO': 12, 'DE': 19, 'SSA': 5, 'GWO': 6, 'WOA': 1}, 'modal': 'DE', 'winner_change': 0.732, 'pass': True}
- 50000: {'n_funcs': 71, 'winner_counts': {'DE': 46, 'GA': 7, 'PSO': 12, 'GWO': 2, 'SSA': 3, 'ACO': 1}, 'modal': 'DE', 'winner_change': 0.352, 'pass': False}

## (4) estabilidad por triple

- C2p: 3/4 estables {'GA->DE:INTENSIFY': ('beneficio', 1.0, 57), 'DE->GA:INTENSIFY': ('beneficio', 1.0, 41), 'DE->GA:DIVERSIFY': ('daño', 0.535, 301), 'GA->DE:DIVERSIFY': ('beneficio', 1.0, 306)}
- C3p: 4/4 estables {'DE->GA:DIVERSIFY': ('daño', 0.878, 131), 'DE->GA:INTENSIFY': ('beneficio', 1.0, 56), 'GA->DE:INTENSIFY': ('beneficio', 1.0, 116), 'GA->DE:DIVERSIFY': ('beneficio', 1.0, 274)}

**Corte 1: CONTINUAR a Fase 2** ({'cota1_supera': True, 'cota2b_supera': True, 'decision': 'CONTINUAR a Fase 2'})
