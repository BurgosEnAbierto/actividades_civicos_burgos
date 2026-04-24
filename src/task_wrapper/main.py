"""
Task wrapper para ejecutar scraper + orchestrator

Flujo:
  1. Ejecuta scraper -> obtiene mes y si hay enlaces nuevos
  2. Si hay enlaces nuevos -> ejecuta orchestrator para ese mes
  3. Devuelve resultados estructurados
  4. Si está configurado, notifica resultados

Uso:
  python -m src.task_wrapper --config .env
  python -m src.task_wrapper --help
"""
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from src.scraper.main import run_scraper
from src.orchestrator.main import run_orchestrator
from src.utils.logging_config import setup_logging
from src.utils.notifier import notify, notify_task_started

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


def run_wrapper(config: dict, run_orchestrator_if_no_new: bool = False) -> dict:
    """
    Ejecuta scraper + orchestrator y devuelve resultados consolidados
    
    Args:
        config: Configuración cargada
        run_orchestrator_if_no_new: Si True, ejecuta orchestrator incluso sin enlaces nuevos
    
    Returns:
        Diccionario con resultados consolidados
    """
    logger.info("=" * 60)
    logger.info("🚀 Iniciando task wrapper")
    logger.info("=" * 60)
    
    # Notificar inicio si Discord está habilitado
    if config.get("discord_webhook"):
        notify_task_started(discord_webhook=config["discord_webhook"])
    
    result = {
        "success": False,
        "scraper": None,
        "orchestrator": None,
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
            # Devolver resultado parcial
            return result
    
    except Exception as e:
        logger.error(f"✗ Excepción en scraper: {e}")
        result["errors"].append(f"Scraper (excepción): {e}")
        return result
    
    # --- ORCHESTRATOR (si hay enlaces nuevos) ---
    if scraper_result["new_links_count"] > 0 or run_orchestrator_if_no_new:
        logger.info(f"\n⚙️  Ejecutando ORCHESTRATOR para {scraper_result['month']}...")
        
        try:
            orchestra_result = run_orchestrator(
                month=scraper_result["month"],
                base_data_path=config["data_dir"],
            )
            result["orchestrator"] = orchestra_result
            
            if orchestra_result["success"]:
                logger.info(f"✓ Orchestrator completado")
                logger.info(
                    f"  Civicos: {orchestra_result['civicos_processed']}, "
                    f"Actividades: {orchestra_result['total_activities']}, "
                    f"Errores: {orchestra_result['civicos_with_errors']}"
                )
            else:
                logger.warning(f"⚠ Orchestrator con problemas")
                if orchestra_result.get("errors"):
                    result["errors"].extend([e for e in orchestra_result["errors"]])
        
        except Exception as e:
            logger.error(f"✗ Excepción en orchestrator: {e}")
            result["errors"].append(f"Orchestrator (excepción): {e}")
    
    else:
        logger.info("ℹ No hay enlaces nuevos, omitiendo orchestrator")
    
    # --- RESULTADO FINAL ---
    result["success"] = len(result["errors"]) == 0
    scraper_ok = result["scraper"] and result["scraper"]["success"]
    orchestrator_ok = (
        result["orchestrator"] is None or result["orchestrator"]["success"]
    )
    result["success"] = scraper_ok and orchestrator_ok
    
    logger.info("\n" + "=" * 60)
    if result["success"]:
        logger.info("✅ Task wrapper completado exitosamente")
    else:
        logger.error(f"❌ Task wrapper con errores ({len(result['errors'])})")
        for err in result["errors"]:
            logger.error(f"  • {err}")
    logger.info("=" * 60)
    
    return result


def notify_results(
    result: dict,
    config: dict,
    log_file: Optional[Path] = None,
) -> None:
    """Envía notificaciones de los resultados"""
    
    scraper = result.get("scraper") or {}
    orchestrator = result.get("orchestrator") or {}
    
    # Extraer mes (puede venir de scraper u orchestrator)
    month = scraper.get("month") or orchestrator.get("month")
    
    if result["success"]:
        title = "✅ Actividades Cívicos Burgos - Ejecución exitosa"
        status = "success"
    else:
        title = f"❌ Actividades Cívicos Burgos - Ejecución fallida ({len(result.get('errors', []))} errores)"
        status = "error"
    
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
        scraped_new=scraper.get("new_links_count", 0),
        orchestrator_civicos=orchestrator.get("civicos_processed", 0),
        orchestrator_activities=orchestrator.get("total_activities", 0),
        orchestrator_errors=orchestrator.get("civicos_with_errors", 0),
        warnings=[],
        errors=result.get("errors", []),
        log_file=str(log_file) if log_file else None,
        discord_webhook=config["discord_webhook"],
        smtp_config=smtp_config,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Task wrapper para ejecutar scraper + orchestrator"
    )
    parser.add_argument(
        "--config",
        help="Ruta al archivo .env (búsqueda: CWD/.env)",
    )
    parser.add_argument(
        "--force-orchestrator",
        action="store_true",
        help="Ejecuta orchestrator incluso aunque no haya enlaces nuevos",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Desactiva notificaciones (Discord/Email)",
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
    result = run_wrapper(config, run_orchestrator_if_no_new=args.force_orchestrator)
    
    # === NOTIFICACIÓN ===
    if not args.no_notify:
        notify_results(result, config)
    
    # === SALIDA ===
    exit_code = 0 if result["success"] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
