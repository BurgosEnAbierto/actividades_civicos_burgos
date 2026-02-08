import json
import logging
from pathlib import Path
from typing import Callable
import argparse

from src.parser.registry import get_parser
from src.downloader.download_pdf import download_pdf
from src.validators.validate_activities import validate_activities
from src.utils.logging_config import setup_logging

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
    
    Flujo:
    1. Lee links.json
    2. Para cada link con is_new=true:
       - Descarga PDF
       - Extrae raw
       - Parsea actividades
       - Agrega a actividades.json
       - Marca is_new=false
    3. Valida schema
    4. Guarda actividades.json actualizado
    5. Guarda links.json actualizado
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
    actividades_file = month_dir / "actividades.json"
    pdfs_dir = month_dir / "pdfs"

    if not links_file.exists():
        logger.warning("No existe links.json para el mes %s", month)
        return None

    # Cargar links.json
    links_data = json.loads(links_file.read_text(encoding="utf-8"))
    links = links_data["links"]

    # Cargar actividades.json existentes (para agregar nuevas)
    if actividades_file.exists():
        all_activities = json.loads(actividades_file.read_text(encoding="utf-8"))
        logger.info("Cargadas %d cívicos de actividades.json existente", len(all_activities))
    else:
        all_activities = {}
        logger.info("Creando actividades.json nuevo para %s", month)

    # Cargar schema
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        ACTIVITIES_SCHEMA = json.load(f)

    # Filtrar links nuevos
    new_links = [link for link in links if link.get("is_new")]
    
    if not new_links:
        logger.info("No hay PDFs nuevos que procesar")
        return all_activities

    logger.info("Procesando %d cívicos nuevos", len(new_links))

    # Procesar cada link nuevo - guardar e actualizar tras CADA cívico
    errors = []
    for link in new_links:
        civico_id = link["civico_id"]
        url = link["url"]

        try:
            logger.info("Procesando %s → %s", civico_id, url)

            # Crear directorio de PDFs
            pdfs_dir.mkdir(parents=True, exist_ok=True)

            # Descargar PDF
            try:
                pdf_path = download_fn(url, pdfs_dir)
            except Exception as e:
                logger.error(f"  ✗ Error descargando PDF: {e}")
                errors.append((civico_id, f"Descarga: {e}"))
                continue

            # Obtener parser para este cívico
            try:
                parser = _get_parser(civico_id)
            except Exception as e:
                logger.error(f"  ✗ Error obteniendo parser: {e}")
                errors.append((civico_id, f"Parser: {e}"))
                continue
            
            # Extraer raw
            try:
                raw = parser["extract_raw"](pdf_path)
                if not raw:
                    logger.warning(f"  ⚠ extract_raw devolvió lista vacía para {civico_id}")
                    errors.append((civico_id, "extract_raw vacío"))
                    continue
            except Exception as e:
                logger.error(f"  ✗ Error en extract_raw: {e}")
                errors.append((civico_id, f"extract_raw: {e}"))
                continue

            # Guardar raw para debugging
            raw_path = month_dir / f"actividades_raw_{civico_id}.json"
            try:
                raw_path.write_text(
                    json.dumps(raw, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            except Exception as e:
                logger.warning(f"  ⚠ No se pudo guardar raw: {e}")

            # Parsear actividades
            try:
                activities = parser["parse_raw"](raw, month=month, civico=civico_id)
                if not activities:
                    logger.warning(f"  ⚠ parse_raw devolvió lista vacía para {civico_id}")
                    activities = []
            except Exception as e:
                logger.error(f"  ✗ Error en parse_raw: {e}")
                errors.append((civico_id, f"parse_raw: {e}"))
                continue

            logger.info(f"  ✓ {len(activities)} actividades parseadas para {civico_id}")

            # Agregar a diccionario (crea lista si no existe)
            if civico_id not in all_activities:
                all_activities[civico_id] = []
            
            all_activities[civico_id].extend(activities)

            # Validar este cívico antes de guardar
            civico_data = {civico_id: all_activities[civico_id]}
            try:
                validate_activities(civico_data, ACTIVITIES_SCHEMA)
            except Exception as e:
                logger.error(f"  ✗ Error de validación para {civico_id}: {e}")
                errors.append((civico_id, f"Schema: {e}"))
                # Remover las actividades inválidas
                del all_activities[civico_id]
                continue

            # Guardar actividades.json actualizado (incremental)
            try:
                actividades_file.write_text(
                    json.dumps(all_activities, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                logger.info(f"  ✓ Guardado en {actividades_file}")
            except Exception as e:
                logger.error(f"  ✗ Error guardando actividades.json: {e}")
                errors.append((civico_id, f"Guardar JSON: {e}"))
                continue

            # Marcar este link como procesado
            try:
                link["is_new"] = False
                links_data["links"] = links
                links_file.write_text(
                    json.dumps(links_data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                logger.info(f"  ✓ Marcado is_new=false en links.json")
            except Exception as e:
                logger.error(f"  ✗ Error actualizando links.json: {e}")
                errors.append((civico_id, f"Actualizar links: {e}"))

        except Exception as e:
            logger.error(f"❌ Error inesperado procesando {civico_id}: {e}")
            errors.append((civico_id, f"Inesperado: {e}"))

    # Resumen final
    logger.info("✅ Orquestrador completado")
    if errors:
        logger.warning(f"⚠ {len(errors)} cívicos con errores:")
        for civico, error in errors:
            logger.warning(f"  - {civico}: {error}")
    else:
        logger.info("✓ Todos los cívicos procesados correctamente")
    
    return all_activities

def main():
    parser = argparse.ArgumentParser(
        description="Orquestador de actividades de centros cívicos"
    )
    parser.add_argument(
        "month",
        help="Mes a procesar en formato YYYYMM (ej: 202512)",
    )
    parser.add_argument(
        "--data-path",
        default="data",
        help="Ruta base de datos (por defecto: data/)",
    )

    args = parser.parse_args()

    # Configurar logging: INFO a consola, WARNING a archivo
    month_dir = Path(args.data_path) / args.month
    month_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=month_dir / "warnings.log")

    run_orchestrator(
        month=args.month,
        base_data_path=Path(args.data_path),
    )


if __name__ == "__main__":
    main()
