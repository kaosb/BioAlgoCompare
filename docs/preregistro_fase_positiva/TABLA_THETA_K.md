# Tabla θ_k — parámetros base por solver (Fase 0, entregable 3)

*Pre-registro fase positiva, enmienda v0.2 (21 Sep 2026). Valores leídos del
código de `algorithms/` (fuente de verdad), con la procedencia bibliográfica que
cada implementación declara. Tamaño de población común: 30 (fijado por el
protocolo de la campaña v11 para no confundir cooperación con tamaño
poblacional). Todos los solvers corren bajo `run_with_fes`, que fija
`max_iterations = ceil((MaxFES − evaluaciones_de_inicialización) / evaluaciones_por_iteración)` (v0.5) para que los
schedules por iteración cubran exactamente el presupuesto.*

| Solver | Parámetros base θ_k (código) | Schedules | Población | Procedencia declarada en el código | Archivo |
|---|---|---|---|---|---|
| DE (rand/1/bin) | F = 0.8, CR = 0.9 | ninguno | 30 | Storn & Price (1997) | `algorithms/de.py:87` |
| PSO | w: 0.9 → 0.4 lineal; c1 = c2 = 2.0; v_max = 0.2·(ub−lb) | inercia lineal decreciente | 30 | Kennedy & Eberhart (1995); Shi & Eberhart (1998) | `algorithms/pso.py:51-60` |
| GWO | a: 2 → 0 lineal; líderes α/β/δ elitistas (reglas de GWO.m, v0.5) | a lineal | 30 | Mirjalili, Mirjalili & Lewis (2014); código GWO.m | `algorithms/gwo.py` |
| GA (random keys: cruce uniforme discreto, reinicio uniforme por gen) | p_cx = 0.8, p_mut = 0.1 (por gen), torneo k = 3, elitismo 2 (28 evaluaciones por generación, v0.5) | ninguno | 30 (default del código 50, sobrescrito) | Holland (1975); Goldberg (1989); Bean (1994) para random keys | `algorithms/ga.py:136-142` |
| ACO_R | m = 2 hormigas/iter, q = 1e-4, ξ = 0.85, k = max(50, pop) | ninguno | 30 (archivo k = 50) | Socha & Dorigo (2008), Tabla 2 | `algorithms/aco.py:100-129` |
| SSA | c1 = 2·exp(−(4t/T)²); N/2 líderes | c1 exponencial | 30 | Mirjalili et al. (2017) (Faris & Mirjalili, código MATLAB) | `algorithms/ssa.py:129-143` |
| WOA | a: 2 → 0; b (espiral) con a2 = 0.5; p = 0.5 | a lineal (con ajuste por estancamiento en el código) | 30 | Mirjalili & Lewis (2016) | `algorithms/woa.py:143,164` |
| L-SHADE (referencia externa, Fase 3) | N_init = 18·D, H = 6, r_arc = 2.6, N_min = 4, current-to-pbest/1/bin con archivo, reducción lineal; sin parada por tolerancia | reducción lineal de población en FES | 18·D → 4 | Tanabe & Fukunaga (2014); implementación C++ `minionpy 1.9.1`, opciones explícitas (v0.4 §D, D14) | `algorithms/minion_adapter.py`, `run_fase3_confirmatorio.py:lshade_options` |

## Manejo de límites del dominio (v0.1 §6, declarado en v0.4)

No es común entre solvers: cada implementación sigue su referencia. DE:
reinicialización uniforme de la componente fuera de rango (`de.py:172`); PSO:
recorte de posición y de velocidad (`pso.py:118-124`); GWO: recorte
(`gwo.py:208`); ACO_R: recorte (`aco.py:216`); GA: operadores acotados al rango;
L-SHADE (minionpy): reinicialización uniforme (`bound_strategy="random"`).

## Notas de fidelidad y alcance

- Los cinco solvers de la campaña v11 (DE, PSO, GWO, GA, ACO_R) fueron
  verificados como fieles al código/paper de referencia en la fase IL y su
  reproducibilidad es bit a bit entre
  máquinas (verificado 16-Ago-2026 y 21-Sep-2026 por `fase1_c0_curves.py`).
- SSA y WOA se usaron solo en el cribado de complementariedad de 6 funciones;
  Fase 1 los extiende a las 70 funciones (fila 3 del pre-registro).
- El `hook` de control multiplicativo escala exactamente los parámetros de la
  columna θ_k: DE (F, CR), PSO (w, c1, c2), GWO (a), GA (p_cx, p_mut), ACO_R
  (ξ, q). Con factores = 1.0 cada solver se reduce al algoritmo base.
- Regiones de convergencia usadas para acotar el vocabulario (enmienda v0.2):
  F ≤ 1 (Storn & Price 1997), w < 1 (condición clásica de convergencia de PSO),
  ξ < 1 (contracción del kernel en ACO_R, Socha & Dorigo 2008), a ≤ 2 (rango
  nominal del schedule de GWO).
