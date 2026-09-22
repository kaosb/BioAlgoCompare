# Enmienda v0.4 — Corte 2 y diseño congelado de la Fase 3 (confirmatorio)

*21 de septiembre de 2026 · Complementa v0.1 (R. Olivares), v0.2 (Fase 0/1) y
v0.3 (Fase 2). Se congela con tag `preregistro-fase-positiva-v0.4` ANTES de la
primera corrida del confirmatorio. Toda desviación posterior va al
`deviations-log.md`.*

## A. Resolución del Corte 2 (D10)

El Corte 2 formal de v0.1 §5 se cumple: **B** (élite bajo admisión) supera a
C1_div con el criterio pre-registrado en 2 de 3 pares (GWO+GA: 3/0 r=0.51 y
6/0 r=0.54; DE+GA: 7/0 r=0.72 y 7/1 r=0.51). A cumple solo en DE+GA; C en
ninguno. Por la regla literal, la Fase 3 correría "una única configuración de
B".

Los contrastes secundarios que el propio pre-registro ordena (v0.1 §8: "vs
C1_island") cambian la atribución: **B no supera a C1_island en ninguna de las
6 celdas** (0 victorias; significativamente peor en 4: GWO+GA 0/2 y 0/1, DE+GA
0/3 y 0/5) y C1_island vs C1_div ≈ B vs C1_div. La ganancia que B exhibe es la
de la **migración fija de una élite** (modelo de islas), no la de la admisión ni
del rollback, que solo la recortan (B admite 7–11 de 18 propuestas a 5·10³ y
25–94 de 198 a 5·10⁴, con 2–44 rollbacks por corrida). Además, el control
benigno mide falsos positivos del gate: BENg vs BENn = 2/7 (r=−0.56) en
DE+GA@5·10³.

Llevar B al confirmatorio como "el mecanismo" repetiría el error de atribución
que el borrador v11 diagnosticó (atribuir a la transferencia lo que hace otro
componente). Esta enmienda declara la desviación y su motivo (D11):

- **Mecanismo confirmatorio: C1_island** — migración estructural fija de una
  élite entre dos solvers heterogéneos, sin admisión, sin rollback, sin memoria.
- **Variante con admisión: B** (exactamente como quedó congelado en v0.3),
  para medir a escala si la admisión/rollback *cuesta* o *protege*.
- **H2 se reformula con el signo que dan los datos:** "la migración de élite
  entre solvers complementarios supera al portafolio (C1_div) y al mejor solver
  aislado (SBS); la admisión por estado no añade ganancia sobre la migración
  fija". La segunda mitad es la hipótesis original de H2 negada; se prueba
  igual (B vs C1_island).
- A y C quedan **abandonados** con sus tablas completas en el suplementario
  (v0.1 §5). BENg/BENn se reporta como resultado del piloto (12 funciones,
  5·10³/5·10⁴, 51 CRN) y no se extiende a la Fase 3 (recorte declarado: el
  régimen benigno exige afinado por función y nivel).

## B. Mecanismo bajo prueba (definición operacional, congelada)

`CooperativeRunner(transfer_mode="structural", gate_enabled=False)`,
`cooperative/orchestrator.py`. Dos poblaciones de 30 (una por solver) sobre un
contador de FES compartido. Cada Δ = 500 evaluaciones (fijo en todos los
niveles), en cada dirección ordenada (fuente → destino), la mejor solución de la
fuente reemplaza al peor individuo del destino y se re-evalúa (1 FES; velocidad
a cero si el destino es PSO). Sin condición de admisión, sin rollback, sin
memoria. En términos de modelos de islas: 2 islas heterogéneas, topología
completa (≡ anillo con 2 islas), tamaño de migración 1, política élite → peor,
intervalo 500 FES, migración síncrona. Es la configuración exacta del brazo
C1_island del piloto; no se ajusta nada por función, presupuesto ni dimensión.

Variante B: `StructuralGatedRunner` de v0.3 §B sin cambios.

## C. Matriz del confirmatorio

| Conjunto | Problemas | Dimensión | MaxFES | Corridas |
|---|---|---|---|---|
| CEC_70_10 | CEC2014 (29, sin F22), CEC2017 (29, sin F2), CEC2022 (12) | 10D | 5·10³, 5·10⁴, 5·10⁵; **5·10⁶ solo en las 12 funciones del piloto** | 51 |
| CEC_70_50 | los mismos | 50D en 2014/2017; 20D en 2022 | 5·10³, 5·10⁴; 5·10⁵ si el cómputo lo permite (ver §F); 5·10⁶ aplazado | 51 |

Decisiones sobre el banco (v0.1 §6, D12), iguales para todos los tratamientos:

- **F2 de CEC2017: excluida.** Retirada por los organizadores del banco
  (comportamiento inestable); admisible con declaración (v0.1 §10).
- **F22 de CEC2014: excluida con razón verificable.** En la implementación de
  `opfunu 1.0.1` el error en puntos uniformes del dominio es del orden de
  10¹⁵–10¹⁸ y DE alcanza error exactamente 0 en 10/10 semillas con 5·10³
  evaluaciones (`fase3` verificación 21-Sep), incompatible con una función
  híbrida de CEC2014; se trata como defecto de la implementación, no del banco.
- **F12 de CEC2022: vuelve al banco.** Verificada: error 0 en x* y valores del
  orden de 10²–10⁴ en puntos uniformes a 10D y 20D.

Semillas: CRN con seed0 = 10000 (disjunto de 5000 campaña, 8000 E2, 9000
piloto, 9500 afinado). Cada presupuesto parte de cero con las mismas 51
semillas para todos los brazos de la celda. El contador de FES incluye la
población inicial y la re-evaluación de cada migrante.

Pares: los tres pre-registrados (GWO+GA, DE+GA, PSO+ACO). El piloto anticipa
que PSO+ACO a 5·10⁴ no gana; se corre igual y se reporta (v0.1 §9: "reportar
dónde gana y dónde no").

## D. Brazos y baselines por celda

| Brazo | Definición | Rol |
|---|---|---|
| C0_A, C0_B | cada solver aislado, presupuesto completo, θ_k | SBS y VBS |
| SBS | el C0 con menor rango medio (mediana por función) en la configuración (par × dimset × nivel); definido a posteriori por configuración, declarado | piso clásico |
| VBS | mínimo por función de C0_A, C0_B | cota superior de selección (exploratorio) |
| C1_div | cada solver con B/2, mejor de los dos | **contraste primario** |
| **C1_island** | §B | tratamiento |
| B | v0.3 §B | variante con admisión |
| L-SHADE | aislado, presupuesto completo, celda por (dimset, nivel, función), independiente del par | referencia externa (H5) |

L-SHADE: `minionpy 1.9.1` (núcleo C++), parámetros de Tanabe & Fukunaga
(2014): N_init = 18·D, H = 6, r_arc = 2.6, N_min = 4, reducción lineal,
current-to-pbest/1/bin con archivo; sin parada por tolerancia. El adaptador
impone un tope duro en MaxFES (verificado: `fes_used` ≤ MaxFES en toda
configuración; a 10D/5·10⁴ la reducción lineal del propio algoritmo lo detiene
en 49 801). Manejo de límites: reinicialización uniforme en el rango
(`bound_strategy="random"`), la misma convención que DE en este framework; la
regla del punto medio del paper no está disponible en minionpy (D14). No se
pudo localizar código público del portafolio cooperativo de Żychowski et al.
(2025); se aplica el reemplazo pre-registrado por el modelo de islas (D13).
C3p (referencia de lo que no funciona) se reporta desde la campaña v11 a 70
funciones y no se re-corre.

Manejo de límites de los solvers propios: cada uno sigue la convención de su
publicación de referencia (documentado en `TABLA_THETA_K.md`); no es común
entre solvers y se declara así.

## E. Análisis (v0.1 §8, sin cambios) y criterios (§9)

Por configuración (dimset × nivel × par), nunca agregando entre presupuestos:

- **Primario:** C1_island vs C1_div — Wilcoxon de rangos con signo por función
  sobre 51 pares CRN (empates descartados), Holm sobre la familia de funciones,
  rank-biserial pareado; tabla better/equal/worse.
- **Secundarios (mismo formato):** C1_island vs SBS; vs VBS (cota); vs L-SHADE;
  **B vs C1_island** (costo/protección de la admisión a escala); C1_div vs SBS
  (efecto portafolio, contexto); C1_div vs L-SHADE; SBS vs L-SHADE.
- **Omnibus:** Friedman con Iman-Davenport (χ², F_F, gl, p) y post-hoc de
  Shaffer sobre {C0_A, C0_B, C1_div, C1_island, B, L-SHADE}, con la mediana de
  51 corridas por función (empate a 10⁻⁸).
- **Exploratorio, etiquetado:** contraste primario por clase taxonómica
  (unimodal / multimodal / híbrida / composición).
- **Suplementario:** media, mediana, desviación estándar y actividad del
  mecanismo (migraciones, admisiones, rollbacks) por celda; horas de pared.

Criterios de éxito (v0.1 §9, por par):

- **10D:** C1_island mejor que peor vs C1_div con Holm en ≥ 3 de 4 presupuestos.
  Abandono: peor que mejor en ≥ 2 presupuestos → reportar igual y acotar el
  claim al régimen donde gana.
- **50D:** mismo criterio sobre los presupuestos ejecutados (con 2, se exige
  ambos; se declara la dependencia de dimensión si falla).
- **H5:** C1_island no inferior a L-SHADE (better ≥ worse con Holm) en ≥ 2
  presupuestos; si se rechaza, el claim se acota al portafolio de los mismos
  solvers.
- **Admisión (H2 original):** B mejor que C1_island en más funciones de las que
  pierde en ≥ 3 de 4 presupuestos; si no, se concluye que la admisión no añade
  ganancia sobre la migración fija (y se cuantifica su costo).

Scripts congelados: `scripts/cec_harness/run_fase3_confirmatorio.py` (corridas,
celdas atómicas y resumibles con tiempo de pared), `fase3_analisis.py`
(todas las tablas desde los crudos), `fase3_smoke.py` (verificación y costo).

## F. Costo estimado y recortes declarados antes de lanzar (v0.1 §6)

Medido por `fase3_smoke.py` (CEC2014 F4, 3 semillas, un núcleo, Apple M5 Max,
18 núcleos, 48 GB): por corrida a 5·10⁴, 0.79–0.86 s (10D) y 0.88–1.06 s (50D)
en los brazos propios; L-SHADE 0.35–0.38 s. Extrapolación lineal en FES a la
matriz completa (5 brazos × 3 pares + L-SHADE, 51 corridas, 70 problemas):

| Bloque | Horas-núcleo (estimadas) | Orden en la cola |
|---|---|---|
| 10D 5·10³ | 1.3 | 1 |
| 10D 5·10⁴ | 12.6 | 1 |
| 50D 5·10³ | 1.4 | 2 |
| 50D 5·10⁴ | 14.5 | 2 |
| 10D 5·10⁵ | 126 | 3 |
| 10D 5·10⁶ (12 funciones) | 216 | 4 |
| 50D 5·10⁵ | 145 | 5 (condicional) |

Las horas de pared dependen del rendimiento paralelo real (el piloto mostró una
aceleración agregada muy por debajo del número de procesos); se registran por
celda y por bloque en los crudos. Recortes declarados: (i) 5·10⁶ restringido a
las 12 funciones del piloto (admisible, v0.1 §10); (ii) 50D a 5·10⁵ se ejecuta
solo si el bloque 4 termina en plazo razonable, si no se aplaza a una segunda
entrega declarada en limitaciones; (iii) 50D a 5·10⁶ aplazado. Nada baja de 51
corridas; ningún presupuesto se evalúa solo.

## G. Congelamiento

Tag `preregistro-fase-positiva-v0.4` sobre el commit que contiene esta
enmienda, el runner, el análisis, el smoke y la corrección del adaptador de
minionpy; hash registrado en `deviations-log.md` (D11). Después del tag no se
modifica ningún parámetro de las Secciones B–E.
