import json
import logging
from pathlib import Path
from typing import Callable

from src.parser.registry import get_parser
from src.downloader.download_pdf import download_pdf
from src.validators.validate_activities import validate_activities

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "actividades.schema.v1.json"

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")

def run_orchestrator(
    month: str,
    *,
    base_data_path: Path | None = None,
    download_fn=None,
    parsers: dict | None = None,
):
    """
    Orquesta la descarga, parseo y validación de actividades para un mes.
    """

    if base_data_path is None:
        base_data_path = Path("data")

    if download_fn is None:
        from src.downloader.download_pdf import download_pdf
        download_fn = download_pdf

    if parsers is None:
        # fallback a producción
        def _get_parser(cid):
            return get_parser(cid)
    else:
        def _get_parser(cid):
            return parsers[cid]

    month_dir = base_data_path / month
    links_file = month_dir / "links.json"

    if not links_file.exists():
        logger.warning("No existe links.json para el mes %s", month)
        return None

    links = json.loads(links_file.read_text(encoding="utf-8"))

    new_links = []

    for civico_id, civico_links in links.items():
        for link in civico_links:
            if link.get("is_new"):
                new_links.append(
                    {
                        "civico_id": civico_id,
                        **link,
                    }
                )
                
    if not new_links:
        logger.info("No hay PDFs nuevos que procesar")
        return

    all_activities: dict[str, list[dict]] = {}

    with SCHEMA_PATH.open(encoding="utf-8") as f:
        ACTIVITIES_SCHEMA = json.load(f)

    for link in new_links:
        civico_id = link["civico_id"]
        url = link["url"]

        logger.info("Procesando %s → %s", civico_id, url)

        pdf_dir = (
            month_dir
            / "pdfs"
            / civico_id
        )

        pdf_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = download_fn(url, pdf_dir)

        parser = _get_parser(civico_id)
        
        raw = parser["extract_raw"](pdf_path)

        raw_path = month_dir / f"actividades_raw_{civico_id}.json"
        raw_path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        activities = parser["parse_raw"](raw, month=month)

        all_activities.setdefault(civico_id, []).extend(activities)

    validate_activities(all_activities, ACTIVITIES_SCHEMA)

    output_file = month_dir / "actividades.json"
    output_file.write_text(
        json.dumps(all_activities, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    logger.info("Actividades guardadas en %s", output_file)

    return all_activities
