# Fase positiva: guía para revisar el pre-registro y su ejecución

Cooperación entre metaheurísticas heterogéneas con presupuesto total compartido
y un gate de seguridad contra la transferencia negativa. Esta guía reúne, para la
rama `main` de este repositorio público, el estado del estudio, el entorno, las pruebas y
el origen de cada tabla del artículo (borrador v21, 21-Oct-2026). Actualizada el 22 de octubre de 2026.

## 1. Estado a octubre de 2026

| Etapa | Resultado | Registro |
|---|---|---|
| Fase 0 | pre-registro v0.1 y enmienda v0.2 congelados (umbrales y definiciones de las cotas) | D0 |
| Fase 1: cotas | Corte 1: continuar a la Fase 2 | D27, D28 |
| Fase 2: piloto de los candidatos A, B y C | Corte 2: ningún candidato cumple; camino alterno | D20, D22, D23 |
| Fase 3: confirmatorio | no se ejecuta sobre el benchmark oficial | D22 |
| Camino alterno a 10D (gate como componente de seguridad) | G1 no se cumple: GWO+GA cumple en ambos presupuestos, PSO+ACO solo a 5·10⁴ y DE+GA en ninguno | D24, D25 |
| Camino alterno a 50D (exploratorio) | ningún par cumple G1 en ambos presupuestos; GWO+GA cumple solo a 5·10³ | D26; `camino_alterno_v06_dim50/analisis.json` |
| Registro del 18-Oct-2026 | D29 (propuesta, pendiente de visto bueno), D30, D31 y D32 | `deviations-log.md` |
| Registro del 20-Oct-2026 | D34–D37: recorte de la memoria inerte, corrección de fecha, análisis descriptivos añadidos (S8–S10, figuras) y unidad de análisis | `deviations-log.md` |
| Publicación (19-Oct-2026) | código, datos y registro del estudio publicados en este repositorio | D33 |
| Extensión del 21-Oct-2026 (ejecutor común C1_shared, replay de identidad/permutado, referencia L-SHADE) | C3p sin ventaja consistente sobre C1_shared; pierde frente a L-SHADE en 42–69 de 71; análisis adicional diseñado tras conocer los resultados, ejecutado sin visto bueno del director y pendiente de ratificación | D38, D39; `attribution_v20_20261021/`, `attribution_lshade_20261021/` |
| Revisión del repositorio (21-Oct-2026) | material heredado sin validez no publicado, avisos de histórico, corrección de docstrings y configuración; SSA y WOA ignoran las cotas del problema (cota 3 de la Fase 1: mismo veredicto con 5 solvers) | D40 |

Cronología del 21-Sep-2026: las enmiendas v0.2–v0.4 y los Cortes 1 y 2 se
decidieron ese día sobre corridas de julio y agosto re-instrumentadas (D1–D3);
todo quedó invalidado el 24-Sep por el benchmark (D16) y se re-ejecutó entre el
24 y el 26-Sep (D20–D28). El registro conserva ambas decisiones.

## 2. Validez de los datos

Los resultados CEC anteriores al tag `preregistro-fase-positiva-v0.5`
(24-Sep-2026) se obtuvieron con una implementación del benchmark que no coincide
con el código C oficial; quedan invalidados como resultados CEC y se conservan
solo como registro (D16). La Fase 1, el piloto y el camino alterno se
re-ejecutaron sobre el benchmark oficial (`CECProblem` con minionpy 1.9.1; 142 de
142 casos coinciden con el código C oficial en `tests/test_cec_official.py`).
Qué directorio es válido y cuál no:
[`results/cooperative/LEEME_VALIDEZ.md`](results/cooperative/LEEME_VALIDEZ.md).

## 3. Pre-registro, enmiendas y registro de desviaciones

Todo en [`docs/preregistro_fase_positiva/`](docs/preregistro_fase_positiva/):

| Documento | Etiqueta | Registro |
|---|---|---|
| [`PREREGISTRO_v0.1_rodrigo.md`](docs/preregistro_fase_positiva/PREREGISTRO_v0.1_rodrigo.md) (y `.docx`) | versionado con v0.2 | D0 |
| [`ENMIENDA_v0.2.md`](docs/preregistro_fase_positiva/ENMIENDA_v0.2.md) | `preregistro-fase-positiva-v0.2` | D0 |
| [`ENMIENDA_v0.3.md`](docs/preregistro_fase_positiva/ENMIENDA_v0.3.md) | `preregistro-fase-positiva-v0.3` | D8 |
| [`ENMIENDA_v0.4.md`](docs/preregistro_fase_positiva/ENMIENDA_v0.4.md) | `preregistro-fase-positiva-v0.4` | D11; anulada por D20/D22 (D30) |
| [`ENMIENDA_v0.5.md`](docs/preregistro_fase_positiva/ENMIENDA_v0.5.md) | `preregistro-fase-positiva-v0.5` | D16–D21 |
| [`ENMIENDA_v0.6.md`](docs/preregistro_fase_positiva/ENMIENDA_v0.6.md) | `preregistro-fase-positiva-v0.6` | D23, D24 |
| [`deviations-log.md`](docs/preregistro_fase_positiva/deviations-log.md) | — | D0–D40 |
| [`extension_21oct2026/`](docs/preregistro_fase_positiva/extension_21oct2026/) | protocolo, congelamientos, equivalencia de código y resultados de la extensión del 21-Oct; etiqueta `extension-21oct2026` | D38, D39 |
| [`TABLA_THETA_K.md`](docs/preregistro_fase_positiva/TABLA_THETA_K.md) | parámetros base θ_k por solver; versionado con v0.2 | — |

Cada etiqueta `preregistro-fase-positiva-v0.2`…`v0.6` marca el estado del
repositorio en que se congeló la enmienda correspondiente: sus árboles de `results/`
son los de ese estado y sus documentos conservan íntegros sus cifras, decisiones y
fechas (D33). Las entradas D25–D40 son posteriores
a la última etiqueta del pre-registro (v0.6); la etiqueta `extension-21oct2026`
marca el estado que contiene los datos y el congelamiento de la extensión del
21-Oct (D38). El hash de cada etiqueta se rellenó en su fila del registro en el
estado siguiente (D0, D11, D16, D24).

Los hashes de commit citados en el registro de desviaciones, en los documentos
congelados, en `results/cooperative/LEEME_VALIDEZ.md`, en los bloques `provenance`
de `results/` y en la sección 4 de esta guía son los del repositorio de trabajo en que se ejecutó
el estudio, y se conservan tal como fueron escritos (D33). En este repositorio,
el estado correspondiente a cada uno es el de la etiqueta que lo contiene.
Las fechas de commits y etiquetas son metadatos de git fijados por el autor:
prueban la consistencia interna (orden, contenido por etiqueta, hashes citados)
pero no son una prueba independiente de la fecha de congelamiento.

Vocabulario de los documentos congelados y de los comentarios del código
anteriores a la etiqueta v0.5 (24-Sep-2026):

- «auditoría» (integral del 23-Sep, de solvers, estadística) y «revisión interna»: revisiones
  del autor sobre su propio código y análisis; no son revisiones del director ni de pares.
- «Fase 3» en `cooperative/` y en los scripts de julio–agosto nombra la línea de trabajo
  iniciada en julio de 2026, no la Fase 3 confirmatoria del pre-registro (que no se ejecutó).
  «F1/F2» en los scripts de julio son etapas del estudio de imitación.
- «campaña v11», «borrador v11/v12»: la campaña `results/cooperative/scale*/` (jul–ago 2026)
  y los borradores que la reportaban, invalidados por D16.
- «F22 anómala» en scripts de julio–agosto: artefacto de la biblioteca anterior (D12 → D20);
  F22 es normal con el benchmark oficial.
- Los bloques `provenance` de `results/` conservan el campo `hostname` por estar congelados.
- Lo que sostiene cada decisión está en la enmienda o entrada correspondiente del registro.
  `ENMIENDA_v0.4.md` §A reporta un Corte 2 positivo cuyas cifras son del benchmark
  invalidado (D16); quedó anulada (D20, D22, D30).
- `TABLA_THETA_K.md` se versionó con v0.2 y se actualizó en v0.4 (D14) y v0.5 (D18); el
  hash de cada etiqueta se rellenó en el estado siguiente (D0, D11, D16, D24).
- `extension_21oct2026/PROTOCOLO_CIERRE.md` se redactó antes del congelamiento: las
  secciones «Preguntas y matriz fija» y «Controles de validez» son el diseño fijado; la
  sección «Otros límites y cierre documental» acota el alcance del método y no forma parte
  del diseño experimental. `RESULTADOS_ADICIONALES.md` es la tabla derivada de
  `RESULTADOS_ADICIONALES.json` (mismas cifras; el analizador escribe solo el JSON); la interpretación está en el borrador v21 §5.5 y en D38.
- Versiones del borrador del artículo citadas aquí y en los documentos: v11 (jul–ago 2026,
  benchmark anterior, invalidado), v13 (18-Oct; da nombre a `tablas_paper_v13.py` y a su
  numeración), v14 (20-Oct; `figuras_paper_v14.py`), v20 (21-Oct, intermedia; da nombre a
  `attribution_v20_20261021/` y es el «análisis primario» que cita `PROTOCOLO_CIERRE.md`) y
  v21 (21-Oct, vigente). Ninguna está en el repositorio; los scripts conservan el nombre de
  la versión en que se crearon porque su SHA-256 está congelado (D39).

## 4. Entorno

Python 3.12.13 (macOS arm64). El lock
[`requirements-fase-positiva.lock`](requirements-fase-positiva.lock) es el
`pip freeze` del entorno que produjo los datos válidos.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-fase-positiva.lock
```

- El benchmark oficial depende de minionpy 1.9.1. opfunu 1.0.1 queda instalado
  solo para `CECProblem(..., backend="opfunu_legacy")` (D16).
- `requirements.lock`, `requirements.txt` y `REPRODUCIBILITY.md` corresponden a
  estudios anteriores.
- Llevan un bloque `provenance` (commit, `git_dirty`, fecha UTC, Python,
  plataforma, host y versiones de numpy, scipy, minionpy, opfunu y otros
  paquetes; el campo `hostname` identifica la máquina de cómputo y se conserva
  porque los archivos están congelados) los JSON de resumen de `results/cooperative/`: `run_meta_*.json`,
  `benign_regimes.json` y `analisis.json` de `camino_alterno_v06/` y
  `camino_alterno_v06_dim50/`; `cotas_fase1.json` y `e2_effect_logs.json` de
  `fase1_v05/`; `benign_regimes.json` y `piloto_summary.json` de `fase2_v05/`
  (también `piloto_pre_D23/piloto_summary.json`). No lo llevan las celdas por
  función (`camino_alterno_v06*/<par>_<nivel>/`, `fase2_v05/piloto*/<par>_<nivel>/`,
  `fase1_v05/c0_half/` y las curvas `fase1_v05/c0_curves/`) ni
  `fase2_v05/piloto_secundarios.json` (tampoco el de `piloto_pre_D23/`), que
  `fase2_secundarios.py` escribe sin ese bloque.
- Todos esos bloques se escribieron entre el 24 y el 26 de septiembre de 2026 y
  registran `git_dirty=true`, lo que no indica por sí solo código modificado:
  hasta el 18-Oct-2026 (406fc3a), `utils/provenance.py` usaba
  `git status --porcelain`, que también cuenta los archivos sin versionar, y en
  el clon de trabajo había al menos un archivo de lock local no versionado. Desde 406fc3a solo cuenta archivos versionados. Lo registrado es
  consistente con que el código sea el del commit indicado: entre el tag v0.6
  (2fdb035) y 34a4806, el commit que registran `run_meta_*.json` y
  `benign_regimes.json` de `camino_alterno_v06/`, no hay cambios fuera de
  `results/` y `docs/`, y las 426 celdas a 10D no llevan el campo `dimset` que
  introdujo 337fc79 (las 426 a 50D sí lo llevan).
- `camino_alterno_v06/analisis.json` registra 337fc79 y no f60a1f6: se generó con
  el código del ómnibus (Friedman, Iman-Davenport y Shaffer) todavía sin
  confirmar, y ese código se confirmó a continuación en f60a1f6 (24-Sep-2026,
  13:11), junto con `analisis.json` y `analisis.md` (D32).
  `camino_alterno_v06_dim50/analisis.json` registra f60a1f6. Verificado el
  18-Oct-2026 sobre un `git archive` de HEAD: `camino_alterno_analisis.py`, sin
  cambios desde f60a1f6, reproduce a 10D y a 50D `analisis.md` byte a byte y
  `analisis.json` salvo el bloque `provenance`.

## 5. Pruebas

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider -o addopts="" \
    tests/test_cec_official.py tests/test_cooperative_invariants.py
```

192 pruebas (18-Oct-2026: 192 pasan): el benchmark frente a la referencia del
código C oficial y los invariantes del runner cooperativo (presupuesto exacto,
CRN, incumbente, rollback, memoria). `-o addopts=""` desactiva las opciones de
cobertura de `tox.ini`, que requieren pytest-cov (no está en el lock).

La suite completa (`.venv/bin/python -m pytest -q -p no:cacheprovider -o addopts=""`)
dio el 21-Oct-2026: 345 pasan, 11 fallan y 29 módulos se omiten. Los omitidos son
tests heredados de VRP e IL que requieren pandas o torch. Las 11 fallas también
son de tests heredados (ejemplos de documentación, importaciones, registro de
algoritmos, parámetros heredados de HO), ya existían antes de esta guía y no
afectan a los dos archivos de la fase positiva.

## 6. Origen de cada tabla

El borrador vigente es el v21 (21-Oct-2026). Sus tablas y su suplemento salen de
aquí así:

| Borrador v21 | Marcador o script | Datos |
|---|---|---|
| Tabla 2 | `G1_10` de `tablas_paper_v13.py` | `camino_alterno_v06/` |
| Tabla 3 | columnas Par, Presupuesto, Stop-loss, Memoria y Costo de `COMP_10` | `camino_alterno_v06/` |
| Tabla 4 | filas C3p/C1_shared, replay/permutado y C3p/L-SHADE de `analyze_attribution_controls.py` | `attribution_v20_20261021/`, `attribution_lshade_20261021/` |
| S1–S10 | `tablas_paper_v13.py` (misma numeración) | ídem Tablas 3–15 |
| S25 (sensibilidad exacta, 6816 pruebas, 56 cambios) | `sensibilidad_exacta_completa.py` | `camino_alterno_v06/` |
| S32 | `analyze_attribution_controls.py` (36 contrastes) | extensión del 21-Oct |
| S11–S24, S26–S31 | texto y tablas trasladados del suplemento de la versión anterior sobre los mismos datos (piloto, cotas, mecanismo, 50D); sus cifras son las de las Tablas 3–15 y S1–S10 | — |

Método estadístico: las tablas primarias (`tablas_paper_v13.py`,
`camino_alterno_analisis.py`) usan `scipy.stats.wilcoxon(zero_method="wilcox")`
con `method="auto"`, que con 51 corridas es la aproximación asintótica
(exacta solo si quedan ≤ 50 pares no nulos sin empates), con SciPy 1.16.3 del
lock. La extensión (`analyze_attribution_controls.py`) y S25 usan un Wilcoxon
exacto condicional con empates y ceros excluidos, implementado en el propio
script. Los veredictos G1 coinciden con ambos métodos; los conteos pueden
diferir (S25).

La numeración que sigue (Tablas 3–15, S0–S10) es la del generador, heredada del
borrador v13.

Pasos para regenerar los datos, en un clon aparte (los runners son resumibles
por celda y no recalculan las celdas que ya existen):

```bash
# Fase 1 (D27, D28). Orden obligatorio: curves -> e2 -> cotas (D31)
N_JOBS=12 LEVELS=5000,50000 .venv/bin/python scripts/cec_harness/fase1_v05.py curves
N_JOBS=12 SOLVERS=GWO,GA LEVELS=500000 .venv/bin/python scripts/cec_harness/fase1_v05.py curves
N_JOBS=12 .venv/bin/python scripts/cec_harness/fase1_v05.py e2
.venv/bin/python scripts/cec_harness/fase1_v05.py cotas

# Piloto v0.5 (D20, D22, D23)
.venv/bin/python scripts/cec_harness/fase2_tuning_benigno.py
.venv/bin/python scripts/cec_harness/run_fase2_piloto.py run
.venv/bin/python scripts/cec_harness/run_fase2_piloto.py aggregate
.venv/bin/python scripts/cec_harness/fase2_secundarios.py

# Camino alterno a 10D (D24, D25)
.venv/bin/python scripts/cec_harness/run_camino_alterno.py tune
.venv/bin/python scripts/cec_harness/run_camino_alterno.py run
.venv/bin/python scripts/cec_harness/camino_alterno_analisis.py

# Camino alterno a 50D, exploratorio (D26)
DIMSET=50 .venv/bin/python scripts/cec_harness/run_camino_alterno.py tune
DIMSET=50 .venv/bin/python scripts/cec_harness/run_camino_alterno.py run
CA_OUT=results/cooperative/camino_alterno_v06_dim50 .venv/bin/python scripts/cec_harness/camino_alterno_analisis.py

# Extensión del 21-Oct-2026 (D38): controles de ejecutor y exposición, y referencia L-SHADE.
# Requiere results/cooperative/camino_alterno_v06/ (puente bit a bit con el C3p archivado).
.venv/bin/python scripts/cec_harness/run_attribution_controls.py run \
    --out /ruta/de/salida/attribution_controls --jobs 12 --kind all \
    --freeze docs/preregistro_fase_positiva/extension_21oct2026/CONGELAMIENTO_DISTRIBUCION.json          # 426 celdas, resumible
.venv/bin/python scripts/cec_harness/run_attribution_lshade.py run \
    --out /ruta/de/salida/attribution_lshade \
    --freeze docs/preregistro_fase_positiva/extension_21oct2026/CONGELAMIENTO_LSHADE_DISTRIBUCION.json   # 142 celdas
.venv/bin/python scripts/cec_harness/analyze_attribution_controls.py \
    --controls results/cooperative/attribution_v20_20261021 \
    --lshade results/cooperative/attribution_lshade_20261021 \
    --out /ruta/de/salida/attribution_controls.json                     # 36 contrastes (Tabla 4 del borrador v21)

# Sensibilidad exacta completa (S25 del borrador v21)
.venv/bin/python scripts/cec_harness/sensibilidad_exacta_completa.py --salida /ruta/de/salida \
    --esperado docs/preregistro_fase_positiva/extension_21oct2026/SENSIBILIDAD_EXACTA_ESPERADA.json
```

Los runners de la extensión exigen `--freeze` con un congelamiento cuyos SHA-256
coincidan con el código: en este repositorio son `CONGELAMIENTO_DISTRIBUCION.json`
(controles) y `CONGELAMIENTO_LSHADE_DISTRIBUCION.json` (L-SHADE), ambos en
`docs/preregistro_fase_positiva/extension_21oct2026/`, y `--kind all` para las cuatro
condiciones por celda. `CONGELAMIENTO.json` y `CONGELAMIENTO_LSHADE.json` son los
congelamientos originales, hechos sobre el árbol del repositorio de trabajo: 26 de sus
archivos difieren de los publicados solo en comentarios y docstrings;
`EQUIVALENCIA_CODIGO.json` registra ambos SHA-256 y la igualdad del AST ejecutable sin
docstrings (D39). Cada celda registra en `identity` el SHA-256 del congelamiento usado y
las celdas versionadas llevan el de los originales; por eso la réplica se escribe en un
directorio nuevo y se compara con las versionadas por `errors` y `changed_windows`
(L-SHADE: `errors` y `fes_used`). El analizador congelado
(`analyze_attribution_controls.congelado.py`, SHA-256 en `ANALISIS_FIJADO.json`)
difiere del publicado solo en la conversión de enteros NumPy al escribir JSON
(`CORRECCION_SERIALIZACION.json`).

Cada celda de la extensión guarda los errores finales de C1_shared, C3p, replay de
identidad y replay permutado (51 semillas), el conteo de ventanas modificadas y el
SHA-256 de su traza (`*.traces.json.gz`; al regenerar, el contenido descomprimido de la
traza coincide, pero el SHA-256 del `.gz`, `identity` y `seconds` cambian). El runner comprueba que C3p instrumentado
reproduce bit a bit el error archivado en `camino_alterno_v06/` y que el replay de
identidad reproduce C3p; si no, se detiene. L-SHADE registra las FES consumidas. La
salida de `analyze_attribution_controls.py` debe coincidir con
`docs/preregistro_fase_positiva/extension_21oct2026/RESULTADOS_ADICIONALES.json`.

Las colas `scripts/cec_harness/{fase1_v05,fase2_v05,camino_alterno,camino_alterno_dim50}_queue.sh`
(zsh) encadenan esos pasos. En `fase1_v05_queue.sh`, el `cotas` intermedio, previo
a las curvas a 5·10⁵, termina con error porque aún faltan celdas; el último
`cotas` hace el cálculo.

Las curvas C0 de la Fase 1 (D31: 1136 JSON, 196 498 137 bytes, unos 196 MB)
no se versionan. Se descargan como archivo adjunto del Release
[`datos-c0-fase1-v05`](https://github.com/kaosb/BioAlgoCompare/releases/tag/datos-c0-fase1-v05)
de este repositorio: `c0_curves.tgz`, de 14 232 318 bytes (unos 14 MB) y SHA-256
`35fa0721b6b721876c06ef8bcbf39dbf48c5894f30a5af6473f221675f139ec4`, que contiene
`results/cooperative/fase1_v05/c0_curves/`. Desde la raíz del clon:

```bash
curl -LO https://github.com/kaosb/BioAlgoCompare/releases/download/datos-c0-fase1-v05/c0_curves.tgz
shasum -a 256 c0_curves.tgz   # debe dar el SHA-256 indicado arriba
tar -xzf c0_curves.tgz        # crea results/cooperative/fase1_v05/c0_curves/
.venv/bin/python scripts/cec_harness/fase1_v05.py cotas
```

Con las curvas, `fase1_v05.py cotas` reescribe `cotas_fase1.md`, idéntico byte
a byte al versionado, y `cotas_fase1.json`, igual salvo el bloque `provenance`
(verificado el 19-Oct-2026 sobre un clon con este archivo extraído). Sin ellas, termina con error y no escribe nada; la Tabla 3
se lee de `cotas_fase1.json`, que sí está versionado.

Con los datos ya generados (los versionados bastan), todas las tablas se
componen con un solo script, que solo calcula: no contiene ni modifica el texto
del paper.

```bash
.venv/bin/python scripts/cec_harness/tablas_paper_v13.py --salida /ruta/de/salida
```

Escribe en `--salida`: `tablas_v13.json` (cifras de todas las tablas),
`tablas_v13_preview.md` (las tablas renderizadas, una sección por marcador),
`tablas_v13_supl.json` y `tablas_v13_supl.md` (suplementario: S0 contenido y
archivos; S1–S7: post-hoc de Shaffer y ómnibus sin controles a 10D y 50D,
ómnibus a 50D, mecanismo del gate a 50D y ómnibus por banco; S8–S10, añadidos el
20-Oct-2026 (D36): sensibilidad de los contrastes pareados, robustez de G1 por
banco y sin funciones repetidas, y ómnibus de los seis brazos reales con Shaffer
por banco) y `suplementario_v13_estadisticos.csv` (media, mediana y desviación
por celda y brazo). Lee los datos de `results/cooperative/`
(otra ruta con `--resultados`) y verifica los enunciados de H1–H5 contra la
sección 2 de `PREREGISTRO_v0.1_rodrigo.md`. Los veredictos de la Tabla 6 llevan
comprobaciones sobre los datos, y las cifras del camino alterno (SBS, contrastes
de G1 y G2, contextos C1_div vs SBS y C3p vs ABL, χ², F_F y rangos medios) se
contrastan con `analisis.json`; si algo no coincide, el script se detiene antes
de escribir. Verificado el 18-Oct-2026 (con S7): sobre un `git archive` de los
datos versionados, las cinco salidas son idénticas byte a byte a las que
acompañan al borrador v13, salvo la ruta del pre-registro registrada en
`tablas_v13.json` y el texto fijo de S0. El 20-Oct-2026 el script cambió solo la presentación de las
tablas del artículo (negritas por umbral en las tablas de contrastes, «σ» en vez
de «DE» para la desviación de los rangos medios, redacción de los veredictos de
la Tabla 6) y añadió S0 y S8–S10; ninguna cifra de las Tablas 3–15 ni de S1–S7
cambió (verificado por diff).

Las figuras del artículo las compone `scripts/cec_harness/figuras_paper_v14.py`
a partir de `tablas_v13.json` (no de los crudos):
`.venv/bin/python scripts/cec_harness/figuras_paper_v14.py --tablas DIR`
escribe `DIR/figs/fig2_rangos_10D.{pdf,png}` (rangos medios de la Tabla 11) y
`DIR/figs/fig1_g1_10D.{pdf,png}` (contrastes de la Tabla 7).

S7 (ómnibus por banco) responde a la unidad de análisis del pre-registro (§8:
banco × dimensión × presupuesto): Friedman con corrección de Iman-Davenport y
rangos medios de los 8 brazos del ómnibus, por banco (CEC 2014 con 30 funciones,
CEC 2017 con 29 y CEC 2022 con 12), par, presupuesto y dimensión (36
configuraciones), sobre la misma matriz de medianas de 51 corridas que
`camino_alterno_analisis.py` (errores < 1e-8 = 0, rangos promedio en los
empates), leída de las celdas crudas y no del CSV redondeado. Sin post-hoc de
Shaffer por banco; los p no se corrigen por multiplicidad entre las 36 (el
resumen da además el conteo con Holm), y con N = 12 el ómnibus de CEC 2022 tiene
poca potencia. Lo componen `omnibus_por_banco`, `supl_por_banco` y
`resumen_por_banco`; el resumen para la prosa (configuraciones significativas y
coincidencia del brazo de menor rango con el agregado) queda en
`tablas_v13.json`, clave `omnibus_por_banco_S7`.

Numeración actual del borrador v13 (la tabla de mecanismo del gate, `MECH_10`,
es la Tabla 9). La última columna es la función de `tablas_paper_v13.py` que
compone cada tabla.

| Tabla | Marcador | Datos (`results/cooperative/`) | Datos generados por (`scripts/cec_harness/`) | Compuesta por (`tablas_paper_v13.py`) |
|---|---|---|---|---|
| 3. Cotas de la Fase 1 (10D) | `FASE1` | `fase1_v05/cotas_fase1.json`, `fase1_v05/e2_effect_logs.json` | `fase1_v05.py` (curves, e2, cotas) | `t_fase1` |
| 4. Contraste primario del piloto (10D) | `PILOTO` | `fase2_v05/piloto/` | `fase2_tuning_benigno.py`, `run_fase2_piloto.py` | `t_piloto` |
| 5. Contrastes secundarios del piloto (10D) | `PILOTO_SEC` | `fase2_v05/piloto/` | ídem | `t_piloto` |
| 6. Hipótesis pre-registradas y veredicto | `HIPOTESIS` | `fase1_v05/cotas_fase1.json`, `fase2_v05/piloto/` | los de las Tablas 3 y 4 | `t_hipotesis` |
| 7. Detección y criterio G1 (10D) | `G1_10` | `camino_alterno_v06/` | `run_camino_alterno.py` (tune, run), `camino_alterno_analisis.py` | `t_alterno` |
| 8. Ablación de componentes y costo del gate (10D) | `COMP_10` | `camino_alterno_v06/` | ídem | `t_alterno` |
| 9. Mecanismo del gate (10D) | `MECH_10` | `camino_alterno_v06/` (`mech_stats` de cada celda) | `run_camino_alterno.py` (run) | `mech_table` |
| 10. Transferencia paramétrica frente al portafolio (10D) | `CANAL_10` | `camino_alterno_v06/` | `run_camino_alterno.py`, `camino_alterno_analisis.py` | `t_alterno` |
| 11. Friedman e Iman-Davenport (10D) | `FRIED_10` | `camino_alterno_v06/` (Shaffer, en el suplementario, se lee de `analisis.json`, D32) | ídem | `t_alterno`, `supl_shaffer` |
| 12. Detección y daño residual por clase de función (10D) | `TAX_10` | `camino_alterno_v06/` | ídem | `t_taxonomia` |
| 13. Detección y criterio G1 a 50D | `G1_50` | `camino_alterno_v06_dim50/` | ídem, con `DIMSET=50` y `CA_OUT` | `t_alterno` |
| 14. Componentes y costo a 50D | `COMP_50` | `camino_alterno_v06_dim50/` | ídem | `t_alterno` |
| 15. Canal real a 50D | `CANAL_50` | `camino_alterno_v06_dim50/` | ídem | `t_alterno` |
| S0. Contenido y archivos | — | — | — | `calcular_supl` (texto fijo `S0_TEXTO`) |
| S1–S7 (suplementario) | — | `camino_alterno_v06{,_dim50}/` (`analisis.json` para S1 y S4) | ídem | `supl_shaffer`, `supl_sin_controles`, `omnibus_por_banco`, `seccion_por_banco` |
| S8. Sensibilidad de los contrastes a 10D (D36) | — | `camino_alterno_v06/` | ídem | `supl_sensibilidad`, `contrast_sens` |
| S9. Robustez de G1 por banco y sin repetidas (D36) | — | `camino_alterno_v06/` | ídem | `supl_robustez` (lista `DUPLICADAS`) |
| S10. Seis brazos reales, Friedman y Shaffer por banco (D36) | — | `camino_alterno_v06/` | ídem | `supl_seis_brazos`, `shaffer`, `tabla_friedman` |
| Figura 1. Contrastes de G1 (Tabla 7), 10D | — | `tablas_v13.json` (`alterno_10.*.det`, `.noninf`) | `tablas_paper_v13.py` | `figuras_paper_v14.py`: `fig_g1` |
| Figura 2. Rangos medios (Tabla 11), 10D | — | `tablas_v13.json` (`alterno_10.*.friedman`) | `tablas_paper_v13.py` | `figuras_paper_v14.py`: `fig_rangos` |
| Extensión del 21-Oct (D38): 36 contrastes de ejecutor, exposición y L-SHADE | — | `attribution_v20_20261021/`, `attribution_lshade_20261021/` | `run_attribution_controls.py`, `run_attribution_lshade.py` | `analyze_attribution_controls.py` |

Correspondencia con el borrador v21 (21-Oct-2026, 13 páginas): su Tabla 2 es `G1_10`;
su Tabla 3, las columnas Par, Presupuesto, Stop-loss, Memoria y Costo de `COMP_10`;
su Tabla 4, las filas C3p/C1_shared, replay/permutado y C3p/L-SHADE de la salida de
`analyze_attribution_controls.py`.

## 7. Código

- `cooperative/`: runner, gate, memoria y candidatos; ver
  [`cooperative/README.md`](cooperative/README.md).
- `problems/continuous/cec_problem.py`: benchmark oficial (`CECProblem`).
- `scripts/cec_harness/`: runners y análisis de la sección 6; la clasificación de los
  46 scripts (vigentes, previstos no ejecutados, históricos invalidados) está en
  [`scripts/cec_harness/README.md`](scripts/cec_harness/README.md). Las funciones
  estadísticas primarias son `paired`/`holm` de `tablas_paper_v13.py` (iguales a las de
  `camino_alterno_analisis.py`); las copias en scripts históricos no alimentan el v21.
- Solvers del estudio: `algorithms/{de,ga,pso,gwo,aco}.py`; `algorithms/__init__.py` es el
  catálogo histórico de la plataforma VRP (no registra DE ni ACO_R). `algorithms/ssa.py` y
  `algorithms/woa.py`, usados solo en la cota 3 de la Fase 1, ignoran las cotas del problema
  y buscan en [0,1]^D (D40); con los cinco solvers restantes el índice de cambio de ganador es
  0.704 a 5·10³ y 0.310 a 5·10⁴ (frente a 0.732 y 0.352 con siete; recálculo descriptivo sin
  script versionado), mismo veredicto.
  L-SHADE (`minion_adapter.py`) corre con los parámetros de Tanabe y Fukunaga pasados
  explícitamente (D14), no con los valores por defecto de minionpy; mealpy y minionpy son
  implementaciones de terceros no verificadas contra el código de sus autores.
- Material heredado cuyo código ejecutable está congelado por SHA-256 (D39):
  `algorithms/de_il.py` llama «hallazgo central» al resultado «nivel, no schedule», invalidado
  por D16; `algorithms/ho_gated.py` cita cifras del estudio HO+IL (hipótesis refutada);
  `problems/qc_dvrp.py` y `problems/vrp.py` citan el artículo de QC-DVRP (CISTI 2026)
  y describen la versión de HO anterior a la reescritura fiel.
  Los modelos `models/ho_il_model*.json` y las demostraciones `data/demos/` pertenecen a esa
  fase; `scripts/run_dvrp_experiments.py` degrada HO+IL a HO si el modelo `.pkl` no existe.
- `tests/`: los 11 tests heredados que fallan (sección 5) describen una versión anterior de
  HO y de la CLI; no cubren la fase positiva.
