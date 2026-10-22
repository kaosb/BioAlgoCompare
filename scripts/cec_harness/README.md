# scripts/cec_harness

Clasificación de los scripts (21-Oct-2026, D40). La guía de uso es
[`README_FASE_POSITIVA.md`](../../README_FASE_POSITIVA.md) §6.

**Vigentes (producen o reproducen los resultados del estudio vigente):** `run_camino_alterno.py`,
`camino_alterno_analisis.py`, `tablas_paper_v13.py`, `figuras_paper_v14.py`,
`fase1_v05.py`, `fase2_tuning_benigno.py`, `run_fase2_piloto.py`, `fase2_secundarios.py`,
`fase2_smoke.py` (auxiliar), `run_attribution_controls.py`, `run_attribution_lshade.py`,
`analyze_attribution_controls.py`, `sensibilidad_exacta_completa.py`, `stats.py`
(`friedman_test` y `shaffer_posthoc`), y las colas `fase1_v05_queue.sh`,
`fase2_v05_queue.sh`, `camino_alterno_queue.sh`, `camino_alterno_dim50_queue.sh`.

**Vigente por dependencia, superado en lo demás:** `fase1_cotas.py` (`fase1_v05.py`
importa sus tres oráculos; el resto lee `results/cooperative/scale/` y `fase1/`, inválidos).

**Previstos y no ejecutados (Fase 3 v0.5; el Corte 2 llevó al camino alterno, D22):**
`run_fase3_confirmatorio.py`, `fase3_analisis.py`, `fase3_smoke.py`, `fase3_queue.sh`.
La referencia L-SHADE vigente es la de `run_attribution_lshade.py` (D38).

**Históricos, invalidados como resultado CEC (D16), línea de transferencia de julio–agosto
de 2026 sobre la biblioteca anterior:** `run_cooperative_pilot.py`, `run_cooperative_ladder.py`,
`run_complementarity_screen.py`, `run_parametric_ladder.py`, `run_cooperative_scale.py`,
`run_e1_action_space.py`, `run_e5_discriminant.py`, `run_stoploss_ablation.py`,
`run_stoploss_ablation_g.py` (sus claves `median_CTRLn` corresponden a CTRLg),
`fase1_c0_curves.py`, `fase1_e2_effect_logs.py`. Sus docstrings describen campañas y
cifras que no son evidencia vigente.

**Históricos, estudio de imitación (junio–julio de 2026), invalidados (D16):**
`run_protocol.py`, `run_cell.py`, `build_rankings.py`, `show_rankings.py`,
`make_figures.py`, `run_poc.py`, `run_oracle_screen.py`, `run_il_pipeline.py`,
`run_expert_il.py`, `report_il_v2.py`, `make_il_figures.py`, `run_constructo.py` y
`stats.wilcoxon_bew`. Ninguno define un «algoritmo propuesto» del estudio vigente.
