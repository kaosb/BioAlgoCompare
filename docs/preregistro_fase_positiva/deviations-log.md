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
| D0 | 2026-09-21 | 0 | enmienda | Enmienda v0.2: fija umbrales (adoptados de v0.1 sin cambio) y definiciones operacionales de las 4 cotas de Fase 1 antes de ejecutar el análisis; fija funciones del piloto; difiere parámetros de candidatos A/B/C a v0.3. Tag `preregistro-fase-positiva-v0.2`, hash: `2a63c3919b02` | v0.1 dejó umbrales y definiciones como propuesta | ninguno sobre resultados: se fija antes de calcular | ENMIENDA_v0.2.md |
| D1 | 2026-09-21 | 1 | re-instrumentacion | C0 de DE, PSO, GWO, GA, ACO_R re-ejecutado con registro de curvas en grilla Δ=500 (70 funcs × 51 × {5e3, 5e4}, seed0=5000). Error final verificado bit-idéntico al histórico por `fase1_c0_curves.py` | las celdas históricas guardan solo errores finales; la cota (2) requiere curvas | ninguno sobre las tablas del borrador (mismos finales) | setup experimental / suplementario |
| D2 | 2026-09-21 | 1 | corrida-nueva | SSA y WOA ejecutados aislados sobre las 70 funciones × 51 × {5e3, 5e4} | solo existían sobre las 6 funciones del cribado; la cota (3) exige 70 × 7 | añade baselines aislados; no altera tratamientos | setup experimental |
| D3 | 2026-09-21 | 1 | re-instrumentacion | E2 (DE+GA @ 5e3, 6 funcs) re-ejecutado en C2p y C3p con `log_transfers=True` y 51 corridas (antes 31) | E2 no persistió efectos por transferencia; regla de Fase 0 exige 51 corridas | la cota (4) usa 51 semillas (más poder); los conteos de E2 en el borrador siguen siendo los de 31 hasta que se re-tabulen | ENMIENDA_v0.2.md §C |
| D4 | 2026-09-21 | 1 | recorte | Cota (2) a 5·10⁵ diferida (curvas C0 de GWO y GA a ese nivel); cota (1) a 5·10⁵ sí se calcula | costo de cómputo | el Corte 1 se decide con 5e3 y 5e4 en (2); 5e5 solo en (1) | ENMIENDA_v0.2.md §C, limitaciones |
| D5 | 2026-09-21 | 1 | enmienda | **Corte 1 decidido: CONTINUAR a Fase 2.** Cota (1) VBS supera el umbral en 5/7 celdas (GWO+GA 5e4 39/3 r=0.83, 5e5 46/3 r=1.00; DE+GA 5e3 63/1 r=0.98, 5e4 49/0 r=0.95; PSO+ACO 5e3 27/1 r=0.44). Cota (2b) conmutación clarividente supera solo en DE+GA 5e4 (40/8, r=0.86) y es PEOR que C1_div en GWO+GA 5e4 (0/57, r=−0.95) y PSO+ACO; cota (2a) reparto estático óptimo supera en 5/6 celdas con curvas. Cota (3) cambio de ganador 0.69 a 5e3 (supera) y 0.37 a 5e4 (no supera; DE gana 44/70). Cota (4) 4/4 triples estables (≥0.90) en C2p y C3p; DE→GA:DIVERSIFY = daño consistente. Tabla completa: `results/cooperative/fase1/cotas_fase1.md` | regla de decisión de v0.1 §4 / v0.2 §A | habilita Fase 2; informa v0.3: la señal de "mejora" es una guía de asignación pobre (converge rápido y estanca), el valor está en el NIVEL de reparto por función | ENMIENDA_v0.3 (por escribir), paper |
| D6 | 2026-09-21 | 1 | enmienda | Añadida cota (2c) *exploratoria, etiquetada como tal* (v0.1 §8): conmutación clarividente por mejora RELATIVA, la señal que H1 nombra. No cambia el Corte 1 (DE+GA 5e3 sube a 36/1; GWO+GA 5e4 sigue 0/57). No sustituye a (2b), que era la definición pre-registrada | H1 habla de mejora relativa; (2b) usó mejora absoluta | ninguno sobre la decisión; insumo de diseño del candidato A | fase1_cotas.py, ENMIENDA_v0.3 |
| D7 | 2026-09-21 | 1 | recorte | Las curvas C0 re-instrumentadas (980 celdas, 50 MB) no se versionan; se regeneran bit a bit con `fase1_c0_curves.py` (mismas semillas). Se versionan `cotas_fase1.{json,md}` y `e2_effect_logs.json` | tamaño del repositorio | ninguno: reproducible por script | suplementario |
