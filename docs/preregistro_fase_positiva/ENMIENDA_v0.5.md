# Enmienda v0.5 — corrección integral de benchmark e instrumentación

*24 de septiembre de 2026 · Complementa v0.1–v0.4. Origen: auditoría integral del
23-Sep-2026, que
invalidó el benchmark y detectó defectos de instrumentación en el runner
cooperativo. Se congela con tag `preregistro-fase-positiva-v0.5` ANTES de
re-ejecutar nada. Toda desviación posterior va al `deviations-log.md`.*

## A. Qué invalida la auditoría

1. **Benchmark.** `opfunu 1.0.1` coincide con el código C oficial de Suganthan en
   32 de 142 casos (función × dimensión); 36 casos son inválidos (NaN o valores
   bajo el óptimo) y el wrapper los convertía en error 0. **Todos los resultados
   CEC previos (fase IL, campaña v11/v12, Fase 1, piloto Fase 2, Fase 3 v0.4)
   quedan invalidados como resultados CEC.** No se usan para ninguna decisión de
   esta fase; se conservan (`results/cooperative/{fase1,fase2,fase3}`) solo como
   registro, reproducibles con `CECProblem(..., backend="opfunu_legacy")`.
2. **Instrumentación cooperativa** (afecta C1_island, B, A, C, BENg/BENn):
   reparto del presupuesto por iteraciones (PSO+ACO 94/6), schedules que exceden
   su horizonte, migrante perdido en GWO y PSO, mejor reportado ≠ mínimo
   evaluado, poblaciones iniciales idénticas en ambos solvers del par.
3. **Solvers:** GA perdía 5.9–6.6 % de su presupuesto; GWO no era fiel al
   GWO.m (líderes no elitistas).
4. **Análisis:** VBS como mínimo por corrida (oráculo con 2B); Wilcoxon sin el
   umbral CEC de 10⁻⁸; rangos sin promediar empates.

Consecuencia sobre el diseño: la elección de C1_island como mecanismo
confirmatorio (v0.4, D11) se tomó con datos inválidos. **El Corte 2 se re-decide
con el piloto re-ejecutado** (misma regla v0.1 §5 y mismos contrastes
secundarios) antes de lanzar Fase 3.

## B. Correcciones (código congelado en el tag)

| Componente | Corrección | Verificación |
|---|---|---|
| `CECProblem` | backend oficial `minionpy` (C++ del C oficial), numeración oficial (CEC2017 1–30, F2 retirada rechazada), dims soportadas; `evaluate` lanza `InvalidEvaluation` si error < −10⁻⁸ o no finito (sin recorte silencioso) | `tests/test_cec_official.py`: 142/142 casos vs C oficial compilado, rel < 10⁻⁸ |
| Horizonte de schedule | `schedule_horizon(algo, B)`: T = ⌈(B − init_evals)/evals_per_iteration⌉; GA declara pop − elitismo; ACO_R declara archivo k de inicialización | FES exactas en los 5 solvers a B y B/2 |
| GWO | líderes α/β/δ elitistas, reglas exactas de GWO.m (verificado en dos copias independientes); a = 2 − l·2/T con l desde 0 | test de elitismo (α = mínimo evaluado, monótono) |
| Orquestador | presupuesto por solver (`_SolverBudget`); paso al solver con menos evaluaciones propias; T por solver con B/N real; `solver_seed(seed, i)` (semillas independientes; C0/C1_div usan el mismo mapeo → CRN intacto); élite de la fuente = gbest en PSO; migrante absorbido (`absorb_injected`: líderes GWO, pbest/gbest PSO); mejor = mínimo evaluado | `tests/test_cooperative_invariants.py` (35 tests); prueba de mutación: reintroducir cada defecto hace fallar sus tests |
| Brazo B | mismas correcciones; el rollback repone el individuo desplazado pero no deshace líderes/pbest/gbest que absorbieron al migrante (declarado) | smoke Fase 2 |
| Análisis | VBS = mejor solver por función (mediana); Wilcoxon con errores < 10⁻⁸ = 0; rangos promedio en rank-biserial y SBS | e2e en directorio temporal |

## C. Cambio de diseño: control de atribución

Se añade el brazo **C1_shared**: el mismo runner cooperativo que C1_island
(presupuesto compartido, reparto por evaluaciones, mismas semillas) **sin
migración**. Motivo: la auditoría mostró que el runner compartido sin migrar ya
difería de C1_div, de modo que C1_island vs C1_div no aislaba la migración.

- En el piloto: C1_shared entra como brazo y los contrastes secundarios incluyen
  C1_island vs C1_shared y C1_shared vs C1_div.
- En Fase 3: **co-primario** C1_island vs C1_shared. El criterio de éxito por
  presupuesto pasa a exigir C1_island mejor>peor vs C1_div **y** vs C1_shared
  (Holm sobre funciones). Si solo se cumple el primero, la ganancia se reporta
  como efecto del reparto compartido, no de la migración.

## D. Re-ejecución y orden (sin cambios de parámetros de mecanismo)

1. Afinado benigno (`fase2_tuning_benigno.py`, seed0 = 12500) → piloto
   (`run_fase2_piloto.py`, 12 funciones CEC2014-10D oficiales, 51 CRN seed0 =
   12000, {5·10³, 5·10⁴}, 3 pares, 11 brazos) → `aggregate` + `fase2_secundarios.py`
   → **Corte 2 re-decidido** con la regla de v0.1 §5 y la lectura de atribución
   de D10 (si el candidato que cumple no supera a su baseline estructural, va el
   baseline). Salida `results/cooperative/fase2_v05/`.
2. Si el Corte 2 re-decidido confirma el mecanismo de v0.4 (C1_island), la Fase 3
   corre con v0.4 + esta enmienda: 71 problemas oficiales (CEC2014 F1–F30 —
   F22 vuelve: su exclusión se debía a opfunu —, CEC2017 F1, F3–F30, CEC2022
   F1–F12), brazos C0_A, C0_B, C1_div, C1_shared, C1_island, B, L-SHADE; 51 CRN
   seed0 = 11000; salida `results/cooperative/fase3_v05/`. Si el Corte 2 cambia,
   se escribe v0.6 antes de lanzar Fase 3.
3. Los parámetros de A, B, C, del control benigno y de C1_island (Δ = 500,
   élite → peor, población 30, θ_k) no cambian.

Costo medido (smoke v0.5, un núcleo): ~0.6–0.8 s por corrida a 5·10⁴;
horas-núcleo 10D: 5·10³ 1.1 / 5·10⁴ 11 / 5·10⁵ 111 / 5·10⁶×12 190; 50D: 1.4 /
14 / 144.

## E. Lo que se reporta sobre lo invalidado

El paper declara que el borrador v11 y todas las
cifras CEC previas se obtuvieron con una implementación del benchmark que no
coincide con la oficial, cómo se detectó (auditoría + contraste con el C
oficial) y que se re-ejecuta todo lo que sostiene un claim. Ninguna cifra previa
se reutiliza.
