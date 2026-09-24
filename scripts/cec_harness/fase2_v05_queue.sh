#!/bin/zsh
# v0.5: afinado benigno -> piloto -> agregado -> secundarios (resumible por celda)
set -u
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python; LOG=results/cooperative/fase2_v05/queue.log
export N_JOBS="${N_JOBS:-12}"
step(){ echo "[$(date '+%F %T')] >>> $*" >> "$LOG"; "$@" >> "$LOG" 2>&1; echo "[$(date '+%F %T')] <<< rc=$? $*" >> "$LOG"; }
[ -f results/cooperative/fase2_v05/benign_regimes.json ] || step $PY scripts/cec_harness/fase2_tuning_benigno.py
step $PY scripts/cec_harness/run_fase2_piloto.py run
step $PY scripts/cec_harness/run_fase2_piloto.py aggregate
step $PY scripts/cec_harness/fase2_secundarios.py
echo "[$(date '+%F %T')] COLA TERMINADA" >> "$LOG"
