#!/bin/zsh
# D27: Fase 1 sobre benchmark oficial. Resumible por celda.
set -u
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python; OUT=results/cooperative/fase1_v05; mkdir -p $OUT; LOG=$OUT/queue.log
export N_JOBS="${N_JOBS:-14}"
step(){ echo "[$(date '+%F %T')] >>> $*" >> "$LOG"; env "$@" >> "$LOG" 2>&1; echo "[$(date '+%F %T')] <<< rc=$? $*" >> "$LOG"; }
step LEVELS=5000,50000 $PY scripts/cec_harness/fase1_v05.py curves
step $PY scripts/cec_harness/fase1_v05.py e2
step $PY scripts/cec_harness/fase1_v05.py cotas
step SOLVERS=GWO,GA LEVELS=500000 $PY scripts/cec_harness/fase1_v05.py curves
step $PY scripts/cec_harness/fase1_v05.py cotas
echo "[$(date '+%F %T')] COLA TERMINADA" >> "$LOG"
