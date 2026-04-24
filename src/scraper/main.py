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
DATA_DIR = Path("docs/data")


def run_scraper(data_dir: Path | None = None) -> dict:
    """
    Ejecuta el scraper y devuelve datos estructurados.
    
    Returns:
        {
            "success": bool,
            "month": str (YYYYMM) o None,
            "total_links_found": int,
            "new_links_count": int,
            "new_links": list[dict],
            "links_file": Path,
            "error": str o None,
        }
    """
    if data_dir is None:
        data_dir = DATA_DIR
    
    try:
        html = fetch_page(BASE_URL)
        links = extract_pdf_links(html)

        if not links:
            return {
                "success": False,
                "month": None,
                "total_links_found": 0,
                "new_links_count": 0,
                "new_links": [],
                "links_file": None,
                "error": "No se detectaron enlaces de PDFs",
            }

        month = detect_month(links)
        month_dir = data_dir / month
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

        new_links = [l for l in links if l.get("is_new")]

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
            "success": True,
            "month": month,
            "total_links_found": len(links),
            "new_links_count": len(new_links),
            "new_links": new_links,
            "links_file": links_path,
            "error": None,
        }
    
    except Exception as e:
        logger.error(f"❌ Error en scraper: {e}")
        return {
            "success": False,
            "month": None,
            "total_links_found": 0,
            "new_links_count": 0,
            "new_links": [],
            "links_file": None,
            "error": str(e),
        }


if __name__ == "__main__":
    setup_logging()

    result = run_scraper()
    logger.info(f"Scraper completado: {result['new_links_count']} enlaces nuevos")
