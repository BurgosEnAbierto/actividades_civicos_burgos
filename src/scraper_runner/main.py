"""
Scraper Runner - Ejecuta SOLO scraper y notifica si hay enlaces nuevos

Flujo:
  1. Ejecuta scraper
  2. Si hay enlaces nuevos (new_links_count > 0) -> envía notificación
  3. Si no hay enlaces nuevos -> no hace nada (ejecución silenciosa)

Uso:
  python -m src.scraper_runner --config .env
  python -m src.scraper_runner --help
"""
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from src.scraper.main import run_scraper
from src.utils.logging_config import setup_logging
from src.utils.notifier import notify

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> dict:
    """Carga configuración desde archivo .env"""
    if config_path:
        config_path = Path(config_path)
    else:
        config_path = Path.cwd() / ".env"
    
    if config_path.exists():
        load_dotenv(config_path)
        logger.info(f"✓ Configuración cargada desde {config_path}")
    else:
        logger.warning(f"⚠ Archivo .env no encontrado: {config_path}")
    
    config = {
        "workspace": Path(os.getenv("WORKSPACE", Path.cwd())).resolve(),
        "data_dir": Path(os.getenv("DATA_DIR", "docs/data")).resolve(),
        "log_dir": Path(os.getenv("LOG_DIR", "logs")).resolve(),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "discord_webhook": os.getenv("DISCORD_WEBHOOK_URL", "").strip() or None,
        "smtp": {
            "host": os.getenv("SMTP_HOST", "").strip() or None,
            "port": int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None,
            "user": os.getenv("SMTP_USER", "").strip() or None,
            "password": os.getenv("SMTP_PASSWORD", "").strip() or None,
            "from": os.getenv("SMTP_FROM", "").strip() or None,
            "to": os.getenv("SMTP_TO", "").strip() or None,
        }
    }
    
    config["log_dir"].mkdir(parents=True, exist_ok=True)
    
    return config


def run_scraper_only(config: dict) -> dict:
    """
    Ejecuta scraper y devuelve resultados
    
    Args:
        config: Configuración cargada
    
    Returns:
        Diccionario con resultados del scraper
    """
    logger.info("=" * 60)
    logger.info("🚀 Iniciando Scraper Runner (SOLO SCRAPER)")
    logger.info("=" * 60)
    
    result = {
        "success": False,
        "scraper": None,
        "errors": [],
    }
    
    # --- SCRAPER ---
    logger.info("\n📥 Ejecutando SCRAPER...")
    
    try:
        scraper_result = run_scraper(data_dir=config["data_dir"])
        result["scraper"] = scraper_result
        
        if scraper_result["success"]:
            logger.info(f"✓ Scraper completado")
            logger.info(
                f"  Mes: {scraper_result['month']}, "
                f"Enlaces: {scraper_result['total_links_found']}, "
                f"Nuevos: {scraper_result['new_links_count']}"
            )
        else:
            logger.error(f"✗ Error en scraper: {scraper_result['error']}")
            result["errors"].append(f"Scraper: {scraper_result['error']}")
            return result
    
    except Exception as e:
        logger.error(f"✗ Excepción en scraper: {e}")
        result["errors"].append(f"Scraper (excepción): {e}")
        return result
    
    # --- RESULTADO FINAL ---
    result["success"] = len(result["errors"]) == 0
    
    logger.info("\n" + "=" * 60)
    if result["success"]:
        logger.info("✅ Scraper Runner completado exitosamente")
    else:
        logger.error(f"❌ Scraper Runner con errores ({len(result['errors'])})")
        for err in result["errors"]:
            logger.error(f"  • {err}")
    logger.info("=" * 60)
    
    return result


def notify_if_new_links(result: dict, config: dict) -> None:
    """
    Envía notificaciones SOLO si hay enlaces nuevos
    
    Args:
        result: Resultado del scraper
        config: Configuración con datos de notificación
    """
    scraper = result.get("scraper") or {}
    
    # Extraer mes del scraper
    month = scraper.get("month")
    new_links_count = scraper.get("new_links_count", 0)
    
    # SOLO notificar si hay enlaces nuevos
    if new_links_count == 0:
        logger.info("ℹ No hay enlaces nuevos - sin notificación")
        return
    
    logger.info(f"📢 Hay {new_links_count} enlaces nuevos - enviando notificación")
    
    if result["success"]:
        title = "🔗 Actividades Cívicos Burgos - Enlaces nuevos detectados"
        status = "success"
    else:
        title = f"⚠️ Actividades Cívicos Burgos - Scraper con problemas"
        status = "warning"
    
    # Preparar config SMTP si todos los campos están presentes
    smtp_config = None
    if all(config["smtp"].values()):
        smtp_config = {
            "smtp_host": config["smtp"]["host"],
            "smtp_port": config["smtp"]["port"],
            "smtp_user": config["smtp"]["user"],
            "smtp_password": config["smtp"]["password"],
            "smtp_from": config["smtp"]["from"],
            "smtp_to": config["smtp"]["to"],
        }
    
    notify(
        title=title,
        month=month,
        status=status,
        scraped_count=scraper.get("total_links_found", 0),
        scraped_new=new_links_count,
        orchestrator_civicos=0,
        orchestrator_activities=0,
        orchestrator_errors=0,
        warnings=[],
        errors=result.get("errors", []),
        log_file=None,
        discord_webhook=config["discord_webhook"],
        smtp_config=smtp_config,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Scraper Runner - Ejecuta SOLO scraper y notifica si hay enlaces nuevos"
    )
    parser.add_argument(
        "--config",
        help="Ruta al archivo .env (búsqueda: CWD/.env)",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Desactiva notificaciones (no notifica incluso si hay enlaces nuevos)",
    )
    
    args = parser.parse_args()
    
    # === INICIALIZACIÓN ===
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Error en configuración: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Setup logging
    log_dir = config["log_dir"]
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(level=getattr(logging, config["log_level"]))
    
    # === EJECUCIÓN ===
    result = run_scraper_only(config)
    
    # === NOTIFICACIÓN (SOLO SI HAY ENLACES NUEVOS) ===
    if not args.no_notify:
        notify_if_new_links(result, config)
    
    # === SALIDA ===
    exit_code = 0 if result["success"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
