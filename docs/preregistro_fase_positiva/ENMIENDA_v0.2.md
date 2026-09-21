# Enmienda v0.2 al pre-registro "cooperación entre metaheurísticas heterogéneas, fase positiva"

*21 de septiembre de 2026 · Complementa el pre-registro v0.1 (R. Olivares,
`PREREGISTRO_v0.1_rodrigo.md`), que se conserva íntegro. Esta enmienda fija lo
que v0.1 dejó como "propuesta" —umbrales y definiciones operacionales de la Fase
1— ANTES de ejecutar cualquier análisis, declara qué datos de Fase 1 requieren
re-instrumentación, y documenta los cambios de Fase 0 ya implementados en el
código. Se congela con tag y hash (Sección F). Todo cambio posterior va al
`deviations-log.md`.*

## A. Umbrales de la Fase 1, fijados

Se adoptan sin modificación los umbrales propuestos en v0.1, Sección 4:

| Cota | Umbral fijado |
|---|---|
| (1) Virtual-best por función vs C1_div | mejor en ≥ 20/70 funciones con Holm (α = 0.05) **y** mediana del rank-biserial pareado ≥ 0.3 |
| (2) Oráculo de conmutación por Δ vs C1_div | igual que (1) |
| (3) Cribado de complementariedad 70 × 7 | cambio de ganador en ≥ 40 % de las funciones |
| (4) Estabilidad del efecto por régimen | signo del efecto por triple estable en ≥ 70 % de las semillas |

**Regla de decisión del Corte 1** (v0.1, §4): si ni (1) ni (2) superan su
umbral en ningún par ni presupuesto, se abandona la Fase 2 y se sigue el camino
alterno pre-registrado (gate como componente de seguridad + protocolo de
atribución, con los datos existentes). Las cotas (3) y (4) informan la
priorización de candidatos (A/B/C) pero no bloquean el Corte 1 por sí solas.

## B. Definiciones operacionales (nuevas en v0.2)

Comunes: 51 corridas pareadas por semillas comunes (seed0 = 5000, la misma de la
campaña v11), población 30, error $f(\hat x) - f(x^*)$, Wilcoxon de rangos con
signo por función (empates descartados) y corrección de Holm sobre la familia de
las 70 funciones de cada contraste; "mejor" = significativo con rank-biserial
$r > 0$; "peor" = significativo con $r < 0$. Los scripts leen los crudos y
regeneran cada tabla (`scripts/cec_harness/fase1_cotas.py`).

**(1) Virtual-best por función (VBS_f).** Para cada par $(A, B)$, presupuesto
$B_{fes}$ y función $f$: $\text{VBS}_f$ = el solver del par con menor mediana de
error C0 (presupuesto completo) en $f$. Contraste: las 51 corridas C0 de
$\text{VBS}_f$ frente a las 51 de C1_div (mismas semillas). Es una cota **a
posteriori** (elección por función con los mismos datos) de la ganancia máxima
de una asignación estática; por construcción es optimista. Datos: celdas
históricas (`results/cooperative/scale/`), niveles 5·10³ y 5·10⁴ en los tres
pares, y 5·10⁵ en GWO+GA. No requiere corridas nuevas.

**(2) Oráculo de conmutación por Δ.** Sea $c_A[k]$ el mejor error del solver
$A$ ejecutado **aislado con presupuesto completo** $B_{fes}$ tras $k\Delta$
evaluaciones ($\Delta = 500$; mismas semillas), e idem $c_B$. Una asignación
$(x_A, x_B)$ con $x_A + x_B = B_{fes}$ obtiene error
$\min(c_A[x_A/\Delta],\, c_B[x_B/\Delta])$. Se reportan dos cotas por corrida:

- (2a) *asignación estática óptima*: $\max_{x_A \in \{\Delta, \dots, B_{fes}-\Delta\}}$ del error anterior (mejor reparto fijo, elegido a posteriori);
- (2b) *conmutación clarividente por ventana* (la definición de v0.1 "el solver que más mejora"): partiendo de $(0,0)$, en cada punto de control se asigna la siguiente ventana $\Delta$ al solver cuya curva más decrece en su próxima ventana desde su posición actual; el error final es el mínimo de ambas curvas en las posiciones alcanzadas.

Contraste primario: (2b) vs C1_div; secundario: (2a) vs C1_div. Ambas son cotas
superiores de un controlador reactivo (usan información futura) y usan las
curvas de corridas con el *schedule* de presupuesto completo, lo que se declara
como aproximación. **Requiere re-instrumentación** (Sección C): las celdas
históricas no guardan curvas.

**(3) Cribado de complementariedad 70 × 7.** Con los errores finales C0 de los 7
solvers (DE, PSO, GWO, GA, ACO_R, SSA, WOA) a un mismo presupuesto, el
*ganador* de cada función es el solver de menor mediana; el *ganador modal* es el
más frecuente. Cambio de ganador = $1 - (\text{frecuencia del modal} / 70)$.
Se reporta además, por par de la campaña, la fracción de funciones que gana cada
lado (complementariedad del par). **Requiere re-instrumentación** para SSA y
WOA (nunca corrieron sobre las 70 funciones).

**(4) Estabilidad del efecto por régimen.** En DE+GA @ 5·10³ sobre las 6
funciones taxonómicas, brazos C2p y C3p (intención de fuente), 51 semillas
(regla de Fase 0), se registra cada transferencia aplicada con su efecto
$\tilde f^{now} - \tilde f^{commit}$ (>0 = daño). Por triple (fuente, destino,
intención) y semilla se toma el signo de la media del efecto; la *estabilidad*
del triple es la fracción de semillas (con ≥ 1 observación) cuyo signo coincide
con el mayoritario. Umbral: ≥ 70 % en al menos la mitad de los triples con
≥ 30 semillas observadas. **Requiere re-instrumentación**: E2 no persistió los
efectos por transferencia.

## C. Datos: existentes vs re-instrumentados (declarado)

| Cota | Datos existentes | Re-instrumentación | Naturaleza |
|---|---|---|---|
| (1) | Celdas históricas, 3 pares, 5e3/5e4 (+5e5 GWO+GA) | ninguna | — |
| (2) | — | `fase1_c0_curves.py`: C0 de los 5 solvers, 70 funcs × 51 corridas × {5e3, 5e4}, mismas semillas, curva en grilla Δ=500; **el error final se verifica bit-idéntico al histórico** | misma corrida, más registro |
| (3) | C0 de 5 solvers (celdas) | SSA y WOA sobre 70 funcs × 51 × {5e3, 5e4} | corridas nuevas de baseline aislado |
| (4) | E2 (31 corridas, sin logs) | `fase1_e2_effect_logs.py`: C2p y C3p, DE+GA @ 5e3, 6 funcs, 51 corridas, con log de efectos | misma condición, más corridas y registro |

Diferido y declarado: la cota (2) a 5·10⁵ (curvas C0 de GWO y GA a ese nivel)
por costo; la cota (1) a 5·10⁵ sí se calcula desde las celdas.

## D. Cambios de Fase 0 implementados antes de correr

- **Δ fijo**: el runner de escala acepta `TE_FIXED` (Δ en evaluaciones, igual en
  todos los niveles); las corridas de Fase 1 usan Δ = 500 y así se fijará en la
  Fase 2. La regla histórica Δ = max(500, B/10) queda documentada en el borrador.
- **Memoria de efectos activa** (métrica de mediana poblacional) en el código
  vigente; la campaña con memoria inerte queda como verificación bit-idéntica en
  el suplementario del borrador v12.
- **51 corridas** en toda celda que llegue a una tabla, incluidos los estudios
  de Fase 1 (E2 pasa de 31 a 51).
- **Vocabulario acotado** a las regiones de convergencia: `PRESETS_V2` en
  `cooperative/functional_intent.py` (F ≤ 1, w < 1, ξ < 1, a ≤ 2). Consecuencia
  declarada: bajo el binding multiplicativo y a ≤ 2, GWO no dispone de acción
  DIVERSIFY distinta del neutral; se propone para v0.3 un binding por
  desplazamiento del *schedule* de a. ADVERSARIAL queda fuera de las cotas por
  diseño (control de sanidad).
- **Tabla θ_k** con procedencia y tamaño de población: `TABLA_THETA_K.md`.

## E. Piloto (Fase 2): lo fijado ahora y lo pendiente

- Funciones del piloto, fijadas: CEC 2014 10D F2, F3 (unimodales); F5, F8, F11,
  F14 (multimodales); F17, F18, F20 (híbridas); F24, F26, F29 (composición) —
  disjuntas de las 6 taxonómicas del cribado y de E1–E4.
- Diseño fijado: 51 corridas CRN, presupuestos 5·10³ y 5·10⁴, tres pares, Δ = 500,
  control positivo de transferencia benigna (inyección del mejor régimen
  estático por función de E1) para medir falsos positivos del gate.
- **Pendiente para la enmienda v0.3** (antes de la primera corrida de la Fase
  2, condición bloqueante): parámetros de los candidatos A (bandit de
  asignación), B (transferencia estructural con admisión) y C (UCB por efecto
  observado sobre `PRESETS_V2`), y el binding alternativo de GWO.

## F. Congelamiento

Este documento, el pre-registro v0.1, la tabla θ_k, el `deviations-log.md` y el
código de Fase 0/1 se congelan con el tag `preregistro-fase-positiva-v0.2` en
el repositorio del framework; el hash del commit etiquetado se registra en la
primera entrada del `deviations-log.md`. Ningún umbral ni definición de esta
enmienda se edita tras el tag.
