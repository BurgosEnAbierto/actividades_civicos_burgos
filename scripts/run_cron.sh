#!/bin/bash
# Script para ejecutar scraper + orchestrator desde crontab
# Ubicación: /scripts/run_cron.sh
# Uso en crontab (ejemplo: ejecutar a las 2 AM):
#   0 2 * * * /path/to/scripts/run_cron.sh >> /dev/null 2>&1

set -e

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Calcular workspace root (padre de /scripts)
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"

# Cambiar al workspace root
cd "$WORKSPACE_ROOT"

# Activar venv si existe (descomenta si es necesario)
# if [ -d "venv" ]; then
#     source venv/bin/activate
# fi

# Ejecutar el wrapper Python (busca .env en WORKSPACE_ROOT)
python3 -m src.task_wrapper --config .env

exit $?
