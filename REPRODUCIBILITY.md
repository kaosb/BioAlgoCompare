# Reproducibilidad — estudio IL × CEC (Paper 2 / tesis MIA)

Receta end-to-end para reproducir los números del estudio "¿mejora el Imitation
Learning la optimización?" (DE + control de parámetros por Behavioral Cloning,
benchmarks CEC 2014/2017/2022). Cierra los hallazgos de reproducibilidad de la
meta-auditoría del 8 Jul 2026 (C2/C3).

## 1. Entorno

Versiones **exactas** verificadas en `requirements.lock` (el binario de
`minionpy` encapsula los competidores CEC C++; `scikit-learn` fija el
RandomForest del clon BC — versiones distintas pueden cambiar los números):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock          # versiones fijas (reproducible)
# o requirements.txt para rangos flexibles (NO garantiza números idénticos)
```

Referencia: Python 3.12.5, macOS arm64. Cada JSON de resultado lleva un bloque
`provenance` (git commit, timestamp, versiones, host) — un número siempre
rastrea a su código + entorno.

## 2. Qué se versiona y qué se regenera

| Artefacto | En git | Cómo obtenerlo |
|---|---|---|
| Summaries JSON (protocol, expert_il, constructo) | **Sí** (con provenance) | ya presentes |
| Celdas raw (`results/**/raw/`) | No (voluminoso) | regenerar con los runners |
| Modelos BC (`models/*.pkl`, hasta 458 MB) | No | regenerar (§3), deterministas |

Los `.pkl` no entran al repo por tamaño; son **deterministas** (seeds fijas), así
que regenerarlos reproduce el mismo modelo bit a bit dentro de una misma versión
del stack.

## 3. Pipeline (en orden)

### 3a. Constructo K — el hallazgo central ("nivel, no schedule")
```bash
python scripts/cec_harness/run_constructo.py
# -> results/constructo/constructo_K.json + tabla del veredicto
# robustez: CMA_SCALE_K=1 python .../run_constructo.py   (CMA ~ 2K)
```

### 3b. Estudio expert-IL (experto JADE clonado por BC, 41 funcs OOD)
```bash
python scripts/cec_harness/run_expert_il.py all     # demos->grid->train->eval->report
# etapas individuales: demos | grid | train | eval | report
# -> models/de_il_jade_cec2014_10d.pkl
# -> results/expert_il/expert_il_report.json  (veredicto pre-registrado)
```
Config congelada (ver `tesis-mia/.../PREREGISTRO_IL_EXPERTO.md`): train=CEC2014,
test=CEC2017+CEC2022, 10D, pop=30, budgets {5e3, 5e4}, 51 semillas pareadas.

### 3c. Protocolo CEC (contexto de campo, 18 algoritmos)
```bash
MAXFES_LEVELS=5000 python scripts/cec_harness/run_protocol.py
# resumible: celdas ya computadas se saltan
# -> results/cec_protocol/protocol_summary.json  (rankings, Friedman+Shaffer, Wilcoxon)
```
Niveles por defecto {5e3, 5e4, 5e5}; 5e6 fuera de alcance por cómputo (declarado).
DE-IL usa la política **legítima** (BC-de-JADE) vía `AbsoluteToFactor`; la política
del oráculo miope quedó archivada en `results/cec_protocol/_REFUTED_myopic_deil/`.

## 4. Garantías de reproducibilidad

- **RNG** por instancia (`np.random.default_rng(seed)`), sin estado global.
- **Diseño pareado (CRN):** `seed_base = max_fes`, independiente del algoritmo →
  misma réplica = mismo seed en todos los algoritmos → Wilcoxon pareado legítimo.
- **FES:** contador duro (`FESLimitProblem`), corte exacto en `max_fes`.
- **IL determinista:** RandomForest `random_state` + `n_jobs=1`; oráculo CMA
  `seed=0`; split train/test congelado.

> Nota: la sección "Flujo de Reproducibilidad" del `README.md` describe el
> experimento VRP masivo **antiguo** (legacy), no este pipeline CEC/IL.
