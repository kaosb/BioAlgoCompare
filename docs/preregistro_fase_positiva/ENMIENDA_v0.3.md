# Enmienda v0.3 — diseño y parámetros congelados de los candidatos de la Fase 2

*21 de septiembre de 2026 · Complementa v0.1 (R. Olivares) y v0.2 (Fase 0/1).
Condición bloqueante de v0.1 §5: "Parámetros de cada candidato fijados antes de
correr y sin ajuste posterior". Esta enmienda los fija. Se congela con tag
`preregistro-fase-positiva-v0.3` antes de la primera corrida del piloto. Toda
desviación posterior va al `deviations-log.md`.*

## A. Lo que Fase 1 cambió del diseño de v0.1

Los umbrales, funciones del piloto y criterios de éxito/abandono de v0.1 §5 se
mantienen. Las cotas de Fase 1 (D5) obligan a dos ajustes de diseño, ambos
declarados aquí antes de correr:

1. **Candidato A no usa la mejora como señal.** v0.1 lo describía como "bandit
   que mueve la fracción de presupuesto hacia el solver en mejora". La cota (2b)
   mostró que conmutar por mejora es una política mala incluso con clarividencia
   (GWO+GA @ 5·10⁴: 0/57, r = −0.95): el solver que mejora rápido temprano suele
   estancarse y no es el que gana. La cota (1)/(2a) mostró que el techo está en el
   *nivel* de reparto por función. A se redefine como asignación por **nivel**
   (incumbente actual) con piso de exploración y stop-loss al reparto igual.
2. **Candidato C se apoya en la señal estable de la cota (4).** El signo del
   efecto por triple es estable en ≥ 90 % de las observaciones, con
   DE→GA:DIVERSIFY consistentemente dañino; un bandit por efecto observado tiene
   señal que aprender.

## B. Candidatos: definición operacional y parámetros congelados

Comunes a los tres: Δ = 500 evaluaciones (fijo en todos los niveles), contador
de FES compartido con aserción de presupuesto exacto, semillas CRN (mismas
semillas que C1_div y los demás brazos de la celda), stop-loss por incumbente
(§4.3 del borrador), población 30, `PRESETS_V2` como vocabulario (F ≤ 1, w < 1,
ξ < 1, a ≤ 2). Implementación: `cooperative/candidates.py`.

**A — `BudgetAllocRunner` (asignación por nivel).** Ventanas de Δ FES. En cada
punto de control (0 FES) se leen los incumbentes cacheados $e_A, e_B$; el solver
con menor error recibe la fracción $s_{hi}$ de la ventana siguiente y el otro
$s_{lo}$ (piso de exploración: ningún solver se apaga, para que un rezagado
pueda alcanzar). Stop-loss: si el mejor global no mejoró durante una ventana con
reparto desigual, la ventana siguiente vuelve a 0.5/0.5. Parámetros congelados:
$s_{hi} = 0.8$, $s_{lo} = 0.2$, Δ = 500. Las fracciones se materializan en
iteraciones enteras por solver según sus evaluaciones por iteración (población
30 para DE/PSO/GWO/GA; m = 2 hormigas por iteración en ACO_R), igual que
`run_with_fes`; declarado como aproximación a Δ por granularidad de iteración
(el smoke test verifica que el reparto observado de FES aproxima
$s_{hi}/s_{lo}$). Schedules por iteración (PSO, GWO) fijados al presupuesto
completo $B$ para ambos solvers (un solver con menos presupuesto termina antes
en su schedule — más exploratorio —; ninguno lo excede), declarado como
asimetría respecto de C1_div (schedules a $B/2$). A no transfiere nada.

**B — `StructuralGatedRunner` (élite bajo admisión).** En cada punto de control,
para cada par ordenado (fuente, destino) sin commit pendiente: se admite la
reinyección de la mejor solución de la fuente en lugar del peor individuo del
destino si (1) su fitness es menor que la mediana cacheada del destino, (2) el
destino está estancado (ventana w = 5 iteraciones, τ = 10⁻¹²) y (3) el par no
está vetado por la memoria (media del efecto > 0 con ≥ 3 observaciones,
recencia 20). Costo: 1 FES por inyección admitida (re-evaluación). Commit
provisional; en el punto de control siguiente, si el incumbente del destino no
mejoró, rollback = reinserción del individuo desplazado (posición y fitness
cacheado, 0 FES) en lugar del peor actual. Efecto para la memoria = mediana
poblacional ahora − mediana en el commit. Sin parámetros libres adicionales.

**C — `UCBRegimeRunner` (régimen por efecto observado).** Cada solver elige en
cada punto de control su régimen de la ventana siguiente con UCB1 sobre los
brazos {INTENSIFY, DIVERSIFY, NEUTRAL} de `PRESETS_V2`, condicionado a su estado
{estancado, mejorando} (misma regla de estancamiento del gate). Recompensa
binaria: 1 si el efecto medido sobre la mediana poblacional fue una mejora
(effect < 0), 0 en caso contrario. Brazos no probados se prueban primero; empate
por orden fijo. Stop-loss por incumbente sobre INTENSIFY/DIVERSIFY (NEUTRAL no
se revierte). Parámetro congelado: $c = \sqrt{2}$. C no usa la intención de la
fuente: el crédito proviene del efecto medido en el propio destino (es, por
construcción, selección adaptativa de régimen por solver; se declara y se
compara igual contra C1_div). Consecuencia de la cota a ≤ 2: para GWO, DIVERSIFY
coincide con NEUTRAL (declarado en v0.2); el binding alternativo por
desplazamiento del schedule queda fuera del piloto y se anota como trabajo
futuro si C falla solo en GWO.

**Control positivo de transferencia benigna — `BenignControlRunner`.** Régimen
BENIGN por (función, solver) = el mejor régimen estático afinado en 11 semillas
separadas (Sección C) sobre las 12 funciones del piloto; se propone en cada
punto de control como intención fija. Dos brazos: BENg (con gate: admisión +
stop-loss + veto) y BENn (sin gate; stop-loss opera igual en ambos, §4.3). El
contraste BENg vs BENn mide cuánta transferencia útil bloquea o revierte el
gate (tasa de falsos positivos), respondiendo la pregunta abierta del borrador
§7.

## C. Afinado del régimen benigno (E1 generalizado, `fase2_tuning_benigno.py`)

Por solver y función, corrida **aislada** con presupuesto $B/2$ y factores
multiplicativos constantes, grilla dentro de las regiones de convergencia; 11
semillas de tuning (seed0 = 9500, disjuntas de las del piloto); se elige por
mediana de error. Grillas congeladas (factores sobre θ_k):

| Solver | Grilla de factores | Configs |
|---|---|---|
| DE ($F$, $CR$) | $F \in \{0.75, 1.00, 1.20\}$ × $CR \in \{0.67, 1.00\}$ | 6 |
| PSO ($w$, $c_1$, $c_2$) | $w \in \{0.8, 1.0, 1.1\}$ × $(c_1,c_2) \in \{(1,1), (0.8,1.3), (1.3,0.7)\}$ | 9 |
| GWO ($a$) | $a \in \{0.5, 0.7, 1.0\}$ | 3 |
| GA ($p_{cx}$, $p_{mut}$) | $p_{cx} \in \{0.9, 1.0, 1.1\}$ × $p_{mut} \in \{0.4, 1.0, 1.5\}$ | 9 |
| ACO_R ($\xi$, $q$) | $\xi \in \{0.7, 1.0, 1.15\}$ × $q \in \{0.5, 1.0, 1.8\}$ | 9 |

Se declara la maldición del ganador de E1: con 11 semillas la selección es
ruidosa; el régimen BENIGN es "benigno en expectativa", no garantizado, y por
eso el contraste que importa es BENg vs BENn (mismo régimen, con y sin gate).

## D. Diseño del piloto (fijado; `run_fase2_piloto.py`)

- Funciones: CEC 2014 10D F2, F3, F5, F8, F11, F14, F17, F18, F20, F24, F26, F29
  (v0.1 §5; disjuntas de las 6 taxonómicas).
- 51 corridas CRN por celda, seed0 = 9000 (fresco; disjunto de la campaña, de
  E1–E4 y del tuning); presupuestos 5·10³ y 5·10⁴; pares GWO+GA, DE+GA, PSO+ACO.
- Brazos por celda: SBS_A, SBS_B (C0 a presupuesto completo, para el contraste
  secundario vs SBS), C1_div (contraste primario), C1_island (migración fija de
  una élite cada Δ = estructural sin gate ni rollback), C3p_v2 (referencia de lo
  que no funciona, con `PRESETS_V2`), **A**, **B**, **C**, BENg, BENn.
- Contraste primario por candidato: candidato vs C1_div, Wilcoxon de rangos con
  signo por función + Holm sobre las 12 funciones, rank-biserial pareado.
- Criterio de éxito por candidato (v0.1 §5, sin cambio): más funciones mejor que
  peor en ambos presupuestos; mediana del rank-biserial ≥ 0.3; peor en ≤ 2 de
  12; cumplido en ≥ 2 de los 3 pares. Abandono: incumplir en ambos presupuestos
  y en los tres pares; el candidato abandonado se reporta completo en el
  suplementario.
- Corte 2: si ningún candidato cumple → camino alterno; si alguno cumple → Fase 3
  con una única configuración del ganador.

## E. Verificación previa a correr

`scripts/cec_harness/fase2_smoke.py`: cada brazo corre en 1 función × 3
semillas a 5·10³ con aserción de presupuesto exacto, sin excepciones, y con
estadísticas de mecanismo no triviales (A: ventanas y reparto; B: admisiones y
rollbacks; C: conteo de brazos). El piloto no se lanza si el smoke falla.

## F. Congelamiento

Tag `preregistro-fase-positiva-v0.3` sobre el commit que contiene esta enmienda,
`cooperative/candidates.py`, el tuning y el runner del piloto; hash registrado
en `deviations-log.md` (D8). Después del tag no se modifica ningún parámetro de
las Secciones B–D.
