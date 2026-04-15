#!/bin/bash
# Script para ejecutar scraper + orchestrator desde crontab (PIPELINE COMPLETO)
# Ubicación: /scripts/run_full_pipeline.sh
# Uso en crontab (ejemplo: ejecutar a las 2 AM):
#   0 2 * * * /path/to/scripts/run_full_pipeline.sh >> /dev/null 2>&1

set -e

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Calcular workspace root (padre de /scripts)
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"

# Cambiar al workspace root
cd "$WORKSPACE_ROOT"

# Activar venv (.venv es el directorio estándar)
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️  Advertencia: .venv no encontrado en $WORKSPACE_ROOT" >&2
fi

# Ejecutar el wrapper Python (busca .env en WORKSPACE_ROOT)
python3 -m src.task_wrapper --config .env

exit $?
