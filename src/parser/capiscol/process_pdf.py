import logging
import camelot

logger = logging.getLogger(__name__)


def process_pdf_capiscol(pdf_path):
    """
    Extrae filas raw desde el PDF de Capiscol.
    Devuelve una lista de [dia, texto_actividades]
    
    Nota: Capiscol requiere flavor='stream' para detectar la estructura correcta
    (36 filas × 4 columnas con día y actividades alternadas)
    """
    logger.info("Extrayendo tablas (Camelot - stream): %s", pdf_path.name)

    # Usa stream flavor para detectar la estructura correcta
    tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")

    if not tables:
        logger.warning("No se detectaron tablas en %s", pdf_path.name)
        return []

    rows = []
    
    # La tabla con actividades es la segunda (índice 1)
    # Primera tabla (índice 0) es la de horarios/información general
    if len(tables) >= 2:
        table = tables[1]
        df = table.df
        
        # Estructura: columnas alternadas [día/vacío, actividad, día/vacío, actividad]
        # Procesar cada fila buscando pares (día, actividad)
        for idx, row in df.iterrows():
            # Combinar contenido de la fila
            # Formato: col0=día/vacío, col1=actividad, col2=día/vacío, col3=actividad
            for col_idx in range(0, len(row), 2):
                if col_idx + 1 < len(row):
                    dia = str(row.iloc[col_idx]).strip()
                    actividad = str(row.iloc[col_idx + 1]).strip()
                    
                    if dia and actividad and dia.upper() not in ["", "SALA"]:
                        # Normalizar el día (puede tener números de columnas, limpiar)
                        rows.append([dia, actividad])
    
    logger.debug("Filas raw extraídas: %d", len(rows))
    return rows
