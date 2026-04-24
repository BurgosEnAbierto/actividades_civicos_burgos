#!/bin/bash
# Script para ejecutar SOLO scraper y notificar si hay enlaces nuevos
# Ubicación: /scripts/run_scraper_only.sh
# Uso en crontab (ejemplo: ejecutar diariamente a las 6 AM):
#   0 6 * * * /path/to/scripts/run_scraper_only.sh >> /dev/null 2>&1

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

# Ejecutar scraper runner (notifica SOLO si hay enlaces nuevos)
python3 -m src.scraper_runner --config .env

exit $?
