#!/bin/zsh
# v0.6: re-piloto PSO+ACO (D23) -> afinado benigno 71 funcs -> campaña -> análisis
set -u
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python; OUT=results/cooperative/camino_alterno_v06; LOG=$OUT/queue.log
mkdir -p $OUT; export N_JOBS="${N_JOBS:-12}"
step(){ echo "[$(date '+%F %T')] >>> $*" >> "$LOG"; "$@" >> "$LOG" 2>&1; echo "[$(date '+%F %T')] <<< rc=$? $*" >> "$LOG"; }
step $PY scripts/cec_harness/run_fase2_piloto.py run
step $PY scripts/cec_harness/run_fase2_piloto.py aggregate
step $PY scripts/cec_harness/fase2_secundarios.py
step $PY scripts/cec_harness/run_camino_alterno.py tune
step $PY scripts/cec_harness/run_camino_alterno.py run
step $PY scripts/cec_harness/camino_alterno_analisis.py
echo "[$(date '+%F %T')] COLA TERMINADA" >> "$LOG"
