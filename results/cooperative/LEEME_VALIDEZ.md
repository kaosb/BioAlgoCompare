# Validez de los resultados de `results/`

21 de octubre de 2026. Los directorios sin sufijo (`fase1/`, `fase2/`, `fase3/`) y
`scale*/` son inválidos; los válidos llevan `_v05`, `_v06` o la fecha `20261021`.
Nada se movió ni se borró: el registro de desviaciones
(`docs/preregistro_fase_positiva/deviations-log.md`) cita estas rutas. Cada
directorio inválido o superado lleva además un `INVALIDO_LEEME.md`.

Todo resultado CEC generado antes del tag `preregistro-fase-positiva-v0.5`
(commit d15482c, 24-Sep-2026) usa una implementación del benchmark que no
coincide con el código C oficial y queda invalidado como resultado CEC (D16).
Solo los directorios de la primera tabla constituyen la evidencia vigente.
Los hashes de las columnas «Commits» son los del repositorio de trabajo en que se
ejecutó el estudio (D33); el estado correspondiente es el de la etiqueta que los
contiene.

## Válidos (benchmark oficial, desde v0.5)

| Ruta | Contenido | Registro | Commits de los datos |
|---|---|---|---|
| `fase1_v05/` | Fase 1 re-ejecutada: cotas y Corte 1 | D27, D28; curvas C0 no versionadas (D31) | dc08539, eea396d |
| `fase2_v05/` (salvo `piloto_pre_D23/`) | piloto v0.5 y Corte 2 | D20, D22, D23 | ec03e67, 34a4806 |
| `camino_alterno_v06/` | camino alterno a 10D (gate como componente de seguridad) | D24, D25, D32 | 13cfc27; análisis f60a1f6 |
| `camino_alterno_v06_dim50/` | camino alterno a 50D, exploratorio | D26 | dc08539 |
| `attribution_v20_20261021/`, `attribution_lshade_20261021/` | extensión del 21-Oct: ejecutor común, replay de identidad/permutado y L-SHADE (Tabla 4 del v21); análisis adicional, no confirmatorio, ejecutado sin visto bueno del director | D38, D39 | etiqueta `extension-21oct2026` |

## Inválidos o superados (se conservan solo como registro)

| Ruta | Qué es | Motivo | Commits |
|---|---|---|---|
| `fase1/` | Fase 1 de v0.2 (21-Sep) | benchmark no oficial (D16) y C1_div tomado de la campaña inválida (D27); reemplazada por `fase1_v05/` | eddf439 |
| `fase2/` | piloto de la Fase 2 de v0.3 (21-Sep) | D16 y runner corregido después (D17); reemplazado por `fase2_v05/` | 0d377e7 |
| `fase3/` | Fase 3 v0.4: confirmatorio lanzado el 21-Sep con el Corte 2 de entonces (D10/D11); bloques 1–2 completados | anulado por D16/D20; runner corregido después (D17) | 03a1be3, 55d744a, 3e0d200 |
| `fase3_v05/` | solo `costo_estimado.json` | la Fase 3 v0.5 no se ejecutó (Corte 2 = camino alterno, D22) | d15482c |
| `fase2_v05/piloto_pre_D23/` | 24 celdas PSO+ACO del piloto v0.5 y sus agregados, anteriores a la corrección del incumbente | superado por D23 (re-ejecutado en `fase2_v05/piloto/`) | ec03e67, 2fdb035 |
| `scale/`, `scale_dt500/`, `scale_v2_memfix/` | estudio a escala previo al pre-registro (campaña v11/v12, jul–ago 2026) | D16; la campaña se re-ejecutó como camino alterno (D22, D24) | 76bc64f, f3b0483 |
| JSON sueltos de esta carpeta: `pilot_C0C2C3*.json`, `ladder_C1.json`, `complementarity_screen.json`, `parametric_ladder*.json`, `e1_action_space.json`, `e5_discriminant.json`, `stoploss_ablation*.json` | estudios previos al pre-registro (jul–ago 2026) | D16 | c62b5e7 a e933e84 |
| `../cec_protocol/`, `../constructo/`, `../expert_il/` | estudio de aprendizaje por imitación (jul 2026) | D16 (la fase IL queda invalidada como resultado CEC) | 74ef1c4 |

Guía de reproducción de la fase positiva: `README_FASE_POSITIVA.md` en la raíz
del repositorio.
