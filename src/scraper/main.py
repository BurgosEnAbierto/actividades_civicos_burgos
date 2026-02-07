from pathlib import Path
from datetime import datetime, timezone
import json
import logging

from src.scraper.fetch_page import fetch_page
from src.scraper.parse_links import extract_pdf_links
from src.utils.detect_month import detect_month
from src.scraper.compare_links import mark_new_links
from src.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

BASE_URL = "https://www.aytoburgos.es/es/servicios-y-programas/-/asset_publisher/rCUegBWr9yud/content/agendacivicos"
DATA_DIR = Path("data")


def run_scraper() -> dict:
    html = fetch_page(BASE_URL)
    links = extract_pdf_links(html)

    if not links:
        raise RuntimeError("No se detectaron enlaces de PDFs")

    month = detect_month(links)
    month_dir = DATA_DIR / month
    month_dir.mkdir(parents=True, exist_ok=True)

    links_path = month_dir / "links.json"

    now = datetime.now(timezone.utc).isoformat()

    if links_path.exists():
        old_payload = json.loads(links_path.read_text(encoding="utf-8"))
        old_links = old_payload.get("links", [])
        links = mark_new_links(old_links, links)
    else:
        # primera vez: todos nuevos
        for link in links:
            link["is_new"] = True

    payload = {
        "meta": {
            "month": month,
            "scraped_at": now,
            "source": BASE_URL,
        },
        "links": links,
    }

    links_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "month": month,
        "links_path": str(links_path),
        "new_links": [
            l for l in links if l.get("is_new")
        ],
    }


if __name__ == "__main__":
    setup_logging()

    result = run_scraper()
    logger.info("Resultado: %s", result)
