import logging
from pathlib import Path

def setup_logging(level=logging.INFO, log_file=None):
    """
    Configura logging con:
    - Consola: INFO level (logger.info, logger.warning, logger.error)
    - Archivo: WARNING level y superiores
    
    Args:
        level: Nivel de logging para consola (default: INFO)
        log_file: Ruta del archivo de log (opcional)
    """
    # Logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capturar todo
    
    # Handler para consola (INFO+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "[%(levelname).1s] %(name)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para archivo (WARNING+) si se proporciona
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.WARNING)
        file_formatter = logging.Formatter(
            "[%(levelname)s] %(asctime)s - %(name)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
