#!/bin/zsh
# D26: camino alterno a 50D (exploratorio). Resumible por celda.
set -u
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python; export DIMSET=50; export CA_OUT=results/cooperative/camino_alterno_v06_dim50
mkdir -p $CA_OUT; LOG=$CA_OUT/queue.log; export N_JOBS="${N_JOBS:-12}"
step(){ echo "[$(date '+%F %T')] >>> $*" >> "$LOG"; "$@" >> "$LOG" 2>&1; echo "[$(date '+%F %T')] <<< rc=$? $*" >> "$LOG"; }
step $PY scripts/cec_harness/run_camino_alterno.py tune
step $PY scripts/cec_harness/run_camino_alterno.py run
step $PY scripts/cec_harness/camino_alterno_analisis.py
echo "[$(date '+%F %T')] COLA TERMINADA" >> "$LOG"
