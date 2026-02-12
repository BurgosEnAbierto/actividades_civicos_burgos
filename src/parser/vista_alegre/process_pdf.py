import logging
import camelot

logger = logging.getLogger(__name__)


def process_pdf_vista_alegre(pdf_path):
    """
    Extrae filas raw desde el PDF de Vista Alegre.
    Devuelve una lista de [dia, texto_actividades]
    """
    logger.info("Extrayendo tablas (Camelot): %s", pdf_path.name)

    tables = camelot.read_pdf(str(pdf_path), pages="all")

    if not tables:
        logger.warning("No se detectaron tablas en %s", pdf_path.name)
        return []

    rows = []

    for table in tables:
        data = table.df.values.tolist()


        # Saltarse la primera tabla (Título)
        if table == tables[0]:
            continue
    
        for row in data:
            if len(row) < 2:
                continue

            # Saltarse la primera fila (Exposiciones sala de encuentro)
            if data.index(row) == 0:
                continue

            dia = row[0].strip()
            texto = row[1].replace("\n", "").strip()

            if dia:
                rows.append([dia, texto])

            dia = row[2].strip()
            texto = row[3].replace("\n", "").strip()

            if dia:
                rows.append([dia, texto])
            

    logger.debug("Filas raw extraídas: %d", len(rows))
    return rows
