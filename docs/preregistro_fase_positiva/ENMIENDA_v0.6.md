# Enmienda v0.6 — camino alterno: el gate como componente de seguridad

*24 de septiembre de 2026 · Complementa v0.1–v0.5. Origen: Corte 2 re-decidido
sobre el benchmark oficial = camino alterno (D22). El camino alterno de v0.1 §2
("gate como componente de seguridad + protocolo de atribución, con los datos
existentes") no puede usar los datos existentes (inválidos, D16): se re-ejecuta
la campaña que lo sostiene. Se congela con tag `preregistro-fase-positiva-v0.6`
antes de correr.*

## A. Corrección previa (D23)

El incumbente que usa el stop-loss (y el resultado por solver) se leía de
`best_solution`, que en PSO es la mejor partícula ACTUAL (no monótona) → rollbacks
espurios con destino PSO. Pasa a la élite real (gbest en PSO; los demás solvers
ya eran monótonos). Afecta a los brazos B, C, BEN y C3p_v2 del piloto en
PSO+ACO: esas 24 celdas se re-ejecutan y se re-agrega el Corte 2 (sin cambio de
parámetros). Test: incumbente de PSO monótono = gbest.

## B. Hallazgo previo a correr, declarado (D24)

Medición en 5 funciones × 8 semillas: el preset ADVERSARIAL sin gate empeora
frente a no transferir en 60–98 % de las corridas, pero **no en todas las
funciones** (p. ej. ayuda en DE+GA F9/F10 a 5·10⁴). El borrador lo trataba como
"dañino por construcción"; aquí se mide función a función: la detección se evalúa
sobre el conjunto de funciones donde el control es efectivamente dañino.
Además, CTRLn con y sin stop-loss dieron resultados idénticos (stop-loss sin
admisión inoperante, coherente con E4 del borrador).

## C. Diseño (congelado)

- Problemas: 71 oficiales (v0.5). 10D. Presupuestos 5·10³ y 5·10⁴. Pares
  GWO+GA, DE+GA, PSO+ACO. 51 corridas CRN, seed0 = 13000; afinado benigno
  seed0 = 13500 (11 semillas, corrida aislada a B/2, grillas de v0.3 §C).
- Δ = 500 FES; vocabulario PRESETS_V2; memoria por mediana (triple min_obs 2,
  recencia 20); gate: fuente mejorando y destino estancado (w = 5, τ = 10⁻¹²).
- Brazos por celda (15): C0_A, C0_B, C1_div; C2p, C3p, ABL; CTRLn, CTRLn_noSL,
  CTRLg, CTRLg_noSL, CTRLg_nomem; MODn, MODg; BENn, BENg.
- Runner `scripts/cec_harness/run_camino_alterno.py`; análisis
  `camino_alterno_analisis.py`; salida `results/cooperative/camino_alterno_v06/`.
- 50D y 5·10⁵ quedan fuera de esta entrega (recorte declarado); se añaden solo
  si G1 se cumple.

## D. Contrastes y criterios (Holm sobre las 71 funciones, Wilcoxon con errores < 10⁻⁸ = 0)

| Claim | Contraste | Criterio / lectura |
|---|---|---|
| **G1 protección** (primario) | CTRLg vs CTRLn; CTRLg vs C1_div | éxito por presupuesto: mejor>peor vs CTRLn con mediana r ≥ 0.3 **y** no inferior a C1_div (peor ≤ 7/71). **Gate validado** si se cumple en ambos presupuestos en ≥ 2 de 3 pares |
| G1b detección | entre funciones con CTRLn_noSL peor que C1_div (Holm), fracción con CTRLg mejor que CTRLn | descriptivo (tasa por celda) |
| G2 canal real | C3p vs C2p; C3p vs C1_div | descriptivo; no inferioridad con el mismo umbral |
| G3 componentes | CTRLg vs CTRLg_noSL (stop-loss); CTRLg vs CTRLg_nomem (memoria); CTRLn vs CTRLn_noSL | descriptivo; atribución del mecanismo de protección |
| G4 costo | BENg vs BENn (falsos positivos); MODg vs MODn (daño sutil) | descriptivo; el costo se reporta siempre |
| contexto | C2p vs C1_div; C3p vs ABL; C1_div vs SBS | descriptivo |

Si G1 no se cumple, se reporta igual: el paper queda en protocolo + diagnóstico +
lección del benchmark, y el gate se describe con su evidencia real.
