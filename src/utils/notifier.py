"""
Módulo para notificaciones via Discord y/o Email
"""
import logging
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Optional

logger = logging.getLogger(__name__)


def send_discord_notification(
    webhook_url: str,
    title: str,
    message: str,
    color: int = 0x0099FF,  # Azul
    status: str = "info"
) -> bool:
    """
    Envía notificación a Discord
    
    Args:
        webhook_url: URL del webhook de Discord
        title: Título del embed
        message: Mensaje (puede ser multilinea)
        color: Color del embed en hexadecimal
        status: 'success' (verde), 'error' (rojo), 'warning' (naranja), 'info' (azul)
    
    Returns:
        True si se envió correctamente
    """
    if not webhook_url:
        return False
    
    colors = {
        "success": 0x00AA00,  # Verde
        "error": 0xCC0000,    # Rojo
        "warning": 0xFFAA00,  # Naranja
        "info": 0x0099FF,     # Azul
    }
    
    color = colors.get(status, color)
    
    try:
        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color,
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"✓ Notificación Discord enviada")
        return True
    except Exception as e:
        logger.error(f"✗ Error enviando notificación Discord: {e}")
        return False


def send_email_notification(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_from: str,
    smtp_to: str,
    subject: str,
    message: str,
    html: bool = False,
) -> bool:
    """
    Envía notificación por email
    
    Args:
        smtp_host: Host del servidor SMTP (ej: smtp.gmail.com)
        smtp_port: Puerto (ej: 587)
        smtp_user: Usuario SMTP
        smtp_password: Contraseña SMTP
        smtp_from: Email origen
        smtp_to: Email destino (puede ser comma-separated)
        subject: Asunto
        message: Cuerpo del mensaje
        html: Si es True, interpreta como HTML
    
    Returns:
        True si se envió correctamente
    """
    if not all([smtp_host, smtp_user, smtp_password, smtp_from, smtp_to]):
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = smtp_from
        msg["To"] = smtp_to
        msg["Subject"] = subject
        
        # Agregar cuerpo
        if html:
            msg.attach(MIMEText(message, "html", _charset="utf-8"))
        else:
            msg.attach(MIMEText(message, "plain", _charset="utf-8"))
        
        # Conectar y enviar
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, smtp_to.split(","), msg.as_string())
        
        logger.info(f"✓ Email enviado a {smtp_to}")
        return True
    except Exception as e:
        logger.error(f"✗ Error enviando email: {e}")
        return False

def notify_task_started(
    discord_webhook: Optional[str] = None,
) -> bool:
    """
    Envía notificación de inicio de tarea a Discord (si está habilitado)
    
    Args:
        discord_webhook: URL del webhook de Discord
    
    Returns:
        True si se envió correctamente (o está deshabilitado)
    """
    if not discord_webhook:
        return False
    
    return send_discord_notification(
        webhook_url=discord_webhook,
        title="🚀 Actividades Cívicos Burgos - Iniciando tarea",
        message="Iniciando scraper + Orchestrator...",
        status="info"
    )

def notify(
    title: str,
    month: Optional[str] = None,
    status: str = "info",
    scraped_count: int = 0,
    scraped_new: int = 0,
    orchestrator_civicos: int = 0,
    orchestrator_activities: int = 0,
    orchestrator_errors: int = 0,
    warnings: Optional[list[str]] = None,
    errors: Optional[list[str]] = None,
    log_file: Optional[Path] = None,
    discord_webhook: Optional[str] = None,
    smtp_config: Optional[dict] = None,
) -> None:
    """
    Envía notificaciones consolidadas a Discord y/o Email
    
    Args:
        title: Título principal (ej: "✅ Burgos en Abierto - Ejecución exitosa")
        month: Mes en formato YYYYMM (ej: "202604") - opcional
        status: 'success', 'error', 'warning', 'info'
        scraped_count: Total de enlaces detectados
        scraped_new: Enlaces nuevos detectados
        orchestrator_civicos: Civicos procesados
        orchestrator_activities: Actividades extraidas
        orchestrator_errors: Errores en orchestrator
        warnings: Lista de advertencias
        errors: Lista de errores
        log_file: Ruta del archivo de log
        discord_webhook: URL webhook Discord
        smtp_config: Dict con credenciales SMTP
    """
    warnings = warnings or []
    errors = errors or []
    
    # Construir mensaje de texto plano
    month_str = f" para {month}" if month else ""
    text_message = f"""
**Ejecución completada{month_str}**

📊 **Resultados Scraper:**
  • Enlaces detectados: {scraped_count}
  • Enlaces nuevos: {scraped_new}

📈 **Resultados Orchestrator:**
  • Civicos procesados: {orchestrator_civicos}
  • Actividades extraidas: {orchestrator_activities}
  • Errores detectados: {orchestrator_errors}
"""
    
    if warnings:
        text_message += f"\n⚠️  **Advertencias ({len(warnings)}):**\n"
        for w in warnings[:5]:  # Primeras 5
            text_message += f"  • {w}\n"
        if len(warnings) > 5:
            text_message += f"  • ... y {len(warnings) - 5} más\n"
    
    if errors:
        text_message += f"\n❌ **Errores ({len(errors)}):**\n"
        for e in errors[:5]:  # Primeras 5
            text_message += f"  • {e}\n"
        if len(errors) > 5:
            text_message += f"  • ... y {len(errors) - 5} más\n"
    
    if log_file and Path(log_file).exists():
        text_message += f"\n📄 Log: {log_file}\n"
    
    # Notificación Discord
    if discord_webhook:
        send_discord_notification(
            webhook_url=discord_webhook,
            title=title,
            message=text_message.strip(),
            status=status
        )
    
    # Notificación Email
    if smtp_config and all(smtp_config.values()):
        send_email_notification(
            subject=title,
            message=text_message.strip(),
            **smtp_config
        )
