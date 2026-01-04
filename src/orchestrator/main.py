import json
import logging
from pathlib import Path

from src.parser.registry import get_parser
from src.downloader.download_pdf import download_pdf

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")


def run_orchestrator(month: str):
    month_dir = DATA_DIR / month
    links_file = month_dir / "links.json"

    if not links_file.exists():
        logger.warning("No existe links.json para el mes %s", month)
        return

    links = json.loads(links_file.read_text(encoding="utf-8"))
    new_links = [l for l in links if l.get("is_new")]

    if not new_links:
        logger.info("No hay PDFs nuevos que procesar")
        return

    all_activities = []

    for link in new_links:
        civico_id = link["civico_id"]
        url = link["url"]

        logger.info("Procesando %s → %s", civico_id, url)

        pdf_dir = month_dir / "pdfs" / civico_id
        pdf_path = download_pdf(url, pdf_dir)

        parser = get_parser(civico_id)

        raw = parser["extract_raw"](pdf_path)

        raw_path = month_dir / f"actividades_raw_{civico_id}.json"
        raw_path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        activities = parser["parse_raw"](raw, month=month)

        for a in activities:
            a["civico_id"] = civico_id

        all_activities.extend(activities)

    output_file = month_dir / "actividades.json"
    output_file.write_text(
        json.dumps(all_activities, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    logger.info("Actividades guardadas en %s", output_file)
