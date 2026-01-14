import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    )
}


def download_pdf(url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = url.split("/")[-2] or "document.pdf"
    path = output_dir / filename

    logger.info("Descargando PDF: %s", filename)

    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()

    path.write_bytes(r.content)

    logger.debug("PDF guardado en %s (%d bytes)", path, path.stat().st_size)
    return path
