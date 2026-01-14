import logging
from pathlib import Path

def get_warning_logger(month: str | int):
    month_str = str(month).zfill(2) if isinstance(month, int) else month

    logger = logging.getLogger(f"warnings.{month_str}")
    logger.setLevel(logging.WARNING)
    logger.propagate = False

    log_path = Path("data") / month_str / "warnings.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s [W] %(name)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger

