# Cotas de Fase 1 (pre-registro v0.2)

Umbrales: {'wins_min': 20, 'n_funcs': 70, 'median_r_min': 0.3, 'winner_change_min': 0.4, 'stability_min': 0.7, 'stability_min_seeds': 30, 'alpha': 0.05}

## (1) Virtual-best por funcion vs C1_div

| celda | mejor/peor | mediana r | eleccion VBS | supera |
|---|---|---|---|---|
| GWOGA_5000 | 15/0 | 0.33 | {'GA': 42, 'GWO': 28} | no |
| GWOGA_50000 | 39/3 | 0.83 | {'GA': 57, 'GWO': 13} | SI |
| GWOGA_500000 | 46/3 | 1.00 | {'GA': 58, 'GWO': 11} | SI |
| DEGA_5000 | 63/1 | 0.98 | {'DE': 34, 'GA': 36} | SI |
| DEGA_50000 | 49/0 | 0.95 | {'DE': 58, 'GA': 12} | SI |
| PSOACO_5000 | 27/1 | 0.44 | {'ACO': 44, 'PSO': 26} | SI |
| PSOACO_50000 | 8/7 | -0.12 | {'ACO': 26, 'PSO': 44} | no |

## (2) Oraculo de conmutacion por Δ vs C1_div

| celda | 2b clarividente abs. mejor/peor (r) | 2a estatica optima mejor/peor (r) | 2c EXPLORATORIO rel. mejor/peor (r) | funcs | bitmatch | supera(2b) | supera(2a) |
|---|---|---|---|---|---|---|---|
| GWOGA_5000 | 5/15 (0.00) | 31/1 (0.52) | 7/14 (0.00) | 70 | True | no | SI |
| GWOGA_50000 | 0/57 (-0.95) | 43/0 (0.86) | 0/57 (-0.95) | 70 | True | no | SI |
| GWOGA_500000 | sin_curvas (diferido/en curso) | | | | | | |
| DEGA_5000 | 16/0 (0.44) | 65/0 (1.00) | 36/1 (0.60) | 70 | True | no | SI |
| DEGA_50000 | 40/8 (0.86) | 55/0 (1.00) | 40/8 (0.86) | 70 | True | SI | SI |
| PSOACO_5000 | 1/13 (-0.22) | 61/0 (0.77) | 3/8 (-0.06) | 70 | True | no | SI |
| PSOACO_50000 | 1/7 (-0.05) | 17/0 (0.47) | 1/7 (-0.05) | 70 | True | no | no |

## (3) Cribado de complementariedad

| nivel | solvers | ganadores | modal | cambio de ganador | supera | split por par |
|---|---|---|---|---|---|---|
| 5000 | 7 | {'ACO': 22, 'DE': 19, 'GWO': 3, 'PSO': 9, 'GA': 11, 'SSA': 5, 'WOA': 1} | ACO | 0.69 | SI | {'GWOGA': {'GWO': 23, 'GA': 47}, 'DEGA': {'DE': 29, 'GA': 41}, 'PSOACO': {'PSO': 21, 'ACO': 49}} |
| 50000 | 7 | {'DE': 44, 'PSO': 7, 'GWO': 1, 'SSA': 4, 'GA': 9, 'ACO': 5} | DE | 0.37 | no | {'GWOGA': {'GWO': 8, 'GA': 62}, 'DEGA': {'DE': 50, 'GA': 20}, 'PSOACO': {'PSO': 37, 'ACO': 33}} |

## (4) Estabilidad del efecto por triple


**C2p**: elegibles=4, estables=4, supera=SI

| triple | obs (función×semilla) | signo mayoritario | estabilidad |
|---|---|---|---|
| DE->GA:DIVERSIFY | 301 | daño | 0.90 |
| DE->GA:INTENSIFY | 46 | beneficio | 1.00 |
| GA->DE:DIVERSIFY | 305 | beneficio | 1.00 |
| GA->DE:INTENSIFY | 80 | beneficio | 1.00 |

**C3p**: elegibles=4, estables=4, supera=SI

| triple | obs (función×semilla) | signo mayoritario | estabilidad |
|---|---|---|---|
| DE->GA:DIVERSIFY | 96 | daño | 1.00 |
| DE->GA:INTENSIFY | 67 | beneficio | 1.00 |
| GA->DE:DIVERSIFY | 246 | beneficio | 1.00 |
| GA->DE:INTENSIFY | 175 | beneficio | 1.00 |

## Corte 1

cota1 supera: True; cota2 supera: True

**Decision: CONTINUAR a Fase 2 (alguna cota de asignacion supera el umbral)**
