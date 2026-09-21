# deviations-log — pre-registro fase positiva

*Regla de uso (v0.1, §1): nada se edita in situ tras el congelamiento; todo
cambio se anota aquí con fecha, descripción, motivo e impacto, y se declara en
el paper. Un recorte declarado es una restricción de recursos; el mismo recorte
sin declarar es un defecto de integridad.*

Tipos: `enmienda` (cambio al pre-registro), `re-instrumentacion` (misma corrida
con más registro), `corrida-nueva` (condición no existente antes), `recorte`
(restricción declarada de recursos), `reemplazo` (competidor/implementación).

| # | Fecha | Fase | Tipo | Descripción | Motivo | Impacto | Se declara en |
|---|---|---|---|---|---|---|---|
| D0 | 2026-09-21 | 0 | enmienda | Enmienda v0.2: fija umbrales (adoptados de v0.1 sin cambio) y definiciones operacionales de las 4 cotas de Fase 1 antes de ejecutar el análisis; fija funciones del piloto; difiere parámetros de candidatos A/B/C a v0.3. Tag `preregistro-fase-positiva-v0.2`, hash: `[se completa tras el tag]` | v0.1 dejó umbrales y definiciones como propuesta | ninguno sobre resultados: se fija antes de calcular | ENMIENDA_v0.2.md |
| D1 | 2026-09-21 | 1 | re-instrumentacion | C0 de DE, PSO, GWO, GA, ACO_R re-ejecutado con registro de curvas en grilla Δ=500 (70 funcs × 51 × {5e3, 5e4}, seed0=5000). Error final verificado bit-idéntico al histórico por `fase1_c0_curves.py` | las celdas históricas guardan solo errores finales; la cota (2) requiere curvas | ninguno sobre las tablas del borrador (mismos finales) | setup experimental / suplementario |
| D2 | 2026-09-21 | 1 | corrida-nueva | SSA y WOA ejecutados aislados sobre las 70 funciones × 51 × {5e3, 5e4} | solo existían sobre las 6 funciones del cribado; la cota (3) exige 70 × 7 | añade baselines aislados; no altera tratamientos | setup experimental |
| D3 | 2026-09-21 | 1 | re-instrumentacion | E2 (DE+GA @ 5e3, 6 funcs) re-ejecutado en C2p y C3p con `log_transfers=True` y 51 corridas (antes 31) | E2 no persistió efectos por transferencia; regla de Fase 0 exige 51 corridas | la cota (4) usa 51 semillas (más poder); los conteos de E2 en el borrador siguen siendo los de 31 hasta que se re-tabulen | ENMIENDA_v0.2.md §C |
| D4 | 2026-09-21 | 1 | recorte | Cota (2) a 5·10⁵ diferida (curvas C0 de GWO y GA a ese nivel); cota (1) a 5·10⁵ sí se calcula | costo de cómputo | el Corte 1 se decide con 5e3 y 5e4 en (2); 5e5 solo en (1) | ENMIENDA_v0.2.md §C, limitaciones |
