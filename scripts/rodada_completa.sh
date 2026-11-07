#!/bin/sh
# Track 2: refaz as simulações do pacote fiel a partir do painel anonimizado (horas de CPU).
set -e
cd "$(dirname "$0")/../code"
PY="${PYTHON:-python3}"
for m in verificacoes_port diagnostico_ado diagnostico_ado_mascara_real diagnostico_ado_escala diagnostico_ado_juizes; do
  echo "== $m $(date -u +%FT%TZ)"
  "$PY" "$m.py" > "../output/rerun/$m.log" 2>&1
done
echo "== fim $(date -u +%FT%TZ)"
