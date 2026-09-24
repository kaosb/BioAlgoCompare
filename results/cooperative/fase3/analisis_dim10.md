# Fase 3 — dim10 (n funcs, better/equal/worse, mediana r)

| celda | SBS | C1_island vs C1_div | vs SBS | vs VBS | vs L-SHADE | B vs C1_island | C1_div vs SBS | rangos Friedman (p_FF) |
|---|---|---|---|---|---|---|---|---|
| GWO+GA_5000 (n=70) | GA | 24/46/0 (0.361) | 20/46/4 (0.23) | 2/64/4 (-0.151) | 11/16/43 (-0.9) | 0/64/6 (-0.162) | 11/42/17 (-0.061) | GWO 4.864, GA 3.879, C1_div 4.307, C1_island 2.521, B 3.164, LSHADE 2.264 (p=3.2e-28) |
| GWO+GA_50000 (n=70) | GA | 28/42/0 (0.445) | 15/48/7 (0.011) | 11/52/7 (0.0) | 6/11/53 (-1.0) | 0/59/11 (-0.204) | 7/23/40 (-0.835) | GWO 5.629, GA 3.157, C1_div 4.236, C1_island 2.836, B 3.507, LSHADE 1.636 (p=2.5e-64) |
| DE+GA_5000 (n=70) | GA | 43/27/0 (0.694) | 19/25/26 (-0.12) | 0/17/53 (-0.756) | 6/15/49 (-0.922) | 0/52/18 (-0.345) | 8/19/43 (-0.787) | DE 3.493, GA 3.279, C1_div 5.057, C1_island 3.179, B 4.129, LSHADE 1.864 (p=5.4e-31) |
| DE+GA_50000 (n=70) | DE | 32/35/3 (0.469) | 10/34/26 (-0.277) | 2/38/30 (-0.513) | 5/23/42 (-0.8) | 0/53/17 (-0.211) | 9/23/38 (-0.938) | DE 3.05, GA 5.05, C1_div 4.243, C1_island 3.064, B 3.429, LSHADE 2.164 (p=3.7e-32) |
| PSO+ACO_5000 (n=70) | ACO | 11/46/13 (-0.011) | 12/46/12 (0.009) | 0/45/25 (-0.445) | 8/34/28 (-0.294) | 0/70/0 (-0.03) | 11/40/19 (-0.093) | PSO 4.593, ACO 3.407, C1_div 3.407, C1_island 3.236, B 3.493, LSHADE 2.864 (p=3.5e-07) |
| PSO+ACO_50000 (n=70) | PSO | 4/51/15 (-0.187) | 11/59/0 (0.177) | 1/52/17 (-0.349) | 0/13/57 (-0.995) | 0/69/1 (0.0) | 25/42/3 (0.317) | PSO 4.357, ACO 4.543, C1_div 3.164, C1_island 3.671, B 3.729, LSHADE 1.536 (p=7.9e-38) |

## Decisión (v0.1 §9)

- GWO+GA: {'presupuestos_evaluados': 2, 'mejor_que_peor_vs_C1_div': 2, 'criterio_10D_3_de_4': None, 'criterio_parcial_todos': True, 'H5_no_inferior_LSHADE_n_presupuestos': 0}
- DE+GA: {'presupuestos_evaluados': 2, 'mejor_que_peor_vs_C1_div': 2, 'criterio_10D_3_de_4': None, 'criterio_parcial_todos': True, 'H5_no_inferior_LSHADE_n_presupuestos': 0}
- PSO+ACO: {'presupuestos_evaluados': 2, 'mejor_que_peor_vs_C1_div': 0, 'criterio_10D_3_de_4': None, 'criterio_parcial_todos': False, 'H5_no_inferior_LSHADE_n_presupuestos': 0}
