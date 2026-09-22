#!/bin/zsh
# Cola de la Fase 3 (enmienda v0.4 §F). Bloques en orden de costo; cada bloque
# es resumible por celda, así que la cola se puede matar y relanzar sin perder
# nada. Log: results/cooperative/fase3/queue.log
set -u
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python
LOG=results/cooperative/fase3/queue.log
mkdir -p results/cooperative/fase3
export N_JOBS="${N_JOBS:-12}"
run_block() {
  echo "[$(date '+%F %T')] >>> bloque DIMSET=$1 LEVELS=$2" >> "$LOG"
  DIMSET="$1" LEVELS="$2" "$PY" scripts/cec_harness/run_fase3_confirmatorio.py run >> "$LOG" 2>&1
  echo "[$(date '+%F %T')] <<< bloque DIMSET=$1 LEVELS=$2 rc=$?" >> "$LOG"
}
run_block 10 5000,50000     # bloque 1
run_block 50 5000,50000     # bloque 2
run_block 10 500000         # bloque 3
run_block 10 5000000        # bloque 4 (12 funciones del piloto)
run_block 50 500000         # bloque 5 (condicional, v0.4 §F)
echo "[$(date '+%F %T')] COLA TERMINADA" >> "$LOG"
