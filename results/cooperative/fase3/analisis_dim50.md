# Fase 3 — dim50 (n funcs, better/equal/worse, mediana r)

| celda | SBS | C1_island vs C1_div | vs SBS | vs VBS | vs L-SHADE | B vs C1_island | C1_div vs SBS | rangos Friedman (p_FF) |
|---|---|---|---|---|---|---|---|---|
| GWO+GA_5000 (n=70) | GWO | 8/62/0 (0.255) | 8/54/8 (-0.122) | 0/59/11 (-0.241) | 60/4/6 (0.995) | 0/67/3 (-0.104) | 5/52/13 (-0.19) | GWO 2.386, GA 4.9, C1_div 3.571, C1_island 2.343, B 2.686, LSHADE 5.114 (p=6.3e-43) |
| GWO+GA_50000 (n=70) | GA | 50/20/0 (0.738) | 32/28/10 (0.354) | 28/29/13 (0.196) | 4/5/61 (-1.0) | 0/51/19 (-0.294) | 6/23/41 (-0.83) | GWO 5.771, GA 3.479, C1_div 4.457, C1_island 2.6, B 3.371, LSHADE 1.321 (p=6.4e-84) |
| DE+GA_5000 (n=70) | GA | 6/64/0 (0.23) | 0/8/62 (-0.822) | 0/6/64 (-0.827) | 23/10/37 (-0.566) | 0/69/1 (-0.09) | 0/3/67 (-1.0) | DE 5.914, GA 1.571, C1_div 4.271, C1_island 3.093, B 3.321, LSHADE 2.829 (p=8.8e-71) |
| DE+GA_50000 (n=70) | DE | 64/5/1 (1.0) | 41/18/11 (0.712) | 35/25/10 (0.511) | 6/12/52 (-1.0) | 0/23/47 (-0.881) | 18/5/47 (-1.0) | DE 3.764, GA 5.107, C1_div 5.071, C1_island 2.214, B 3.421, LSHADE 1.421 (p=1e-76) |
| PSO+ACO_5000 (n=70) | ACO | 22/32/16 (-0.017) | 18/19/33 (-0.348) | 3/26/41 (-0.648) | 61/4/5 (0.923) | 1/69/0 (-0.028) | 8/20/42 (-0.655) | PSO 4.186, ACO 2.329, C1_div 3.343, C1_island 2.707, B 2.907, LSHADE 5.529 (p=3.8e-36) |
| PSO+ACO_50000 (n=70) | ACO | 8/19/43 (-0.656) | 15/17/38 (-0.682) | 2/24/44 (-0.815) | 2/6/62 (-1.0) | 1/68/1 (0.026) | 13/25/32 (-0.451) | PSO 5.05, ACO 3.264, C1_div 3.179, C1_island 4.193, B 3.879, LSHADE 1.436 (p=6.1e-43) |

## Decisión (v0.1 §9)

- GWO+GA: {'presupuestos_evaluados': 2, 'mejor_que_peor_vs_C1_div': 2, 'criterio_10D_3_de_4': None, 'criterio_parcial_todos': True, 'H5_no_inferior_LSHADE_n_presupuestos': 1}
- DE+GA: {'presupuestos_evaluados': 2, 'mejor_que_peor_vs_C1_div': 2, 'criterio_10D_3_de_4': None, 'criterio_parcial_todos': True, 'H5_no_inferior_LSHADE_n_presupuestos': 0}
- PSO+ACO: {'presupuestos_evaluados': 2, 'mejor_que_peor_vs_C1_div': 1, 'criterio_10D_3_de_4': None, 'criterio_parcial_todos': False, 'H5_no_inferior_LSHADE_n_presupuestos': 1}
