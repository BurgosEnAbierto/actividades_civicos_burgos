import logging
import camelot
import re

logger = logging.getLogger(__name__)


def process_pdf_gamonal(pdf_path):
    """
    Extrae filas raw desde el PDF de Gamonal Norte.
    Devuelve una lista de [dia, texto_actividades]
    
    Soporta dos estructuras:
    1. Enero 2026: Dos tablas de 2 columnas (día | descripción)
    2. Febrero 2026: Una tabla de 5 columnas con layout de dos columnas por página
       Layout: [día_izq, desc_izq, columna_vacía, día_der, desc_der]
    """
    logger.info("Extrayendo tablas (Camelot): %s", pdf_path.name)

    tables = camelot.read_pdf(str(pdf_path), pages="all")

    if not tables:
        logger.warning("No se detectaron tablas en %s", pdf_path.name)
        return []

    rows = []

    for table in tables:
        data = table.df.values.tolist()
        num_cols = len(data[0]) if data else 0
        
        logger.debug(f"Procesando tabla con {num_cols} columnas y {len(data)} filas")
        
        # Detectar estructura: 2 columnas (simple) o 5 columnas (dos columnas lado a lado)
        if num_cols == 2:
            # Estructura simple: [día, descripción]
            rows.extend(_process_two_column_structure(data))
        elif num_cols == 5:
            # Estructura de dos columnas por página: [día_izq, desc_izq, espacio, día_der, desc_der]
            rows.extend(_process_five_column_structure(data))
        else:
            logger.warning(f"Estructura inesperada: {num_cols} columnas. Intentando estructura simple.")
            rows.extend(_process_two_column_structure(data))

    logger.debug("Filas raw extraídas: %d", len(rows))
    return rows


def _process_two_column_structure(data):
    """
    Procesa tabla de 2 columnas: [día, descripción]
    """
    rows = []
    for row in data:
        if len(row) < 2:
            continue

        dia = row[0].strip()
        texto = row[1].replace("\n", "").strip()

        if dia:
            rows.append([dia, texto])
    
    return rows


def _process_five_column_structure(data):
    """
    Procesa tabla de 5 columnas con layout de dos columnas por página:
    [día_izq, desc_izq, columna_vacía, día_der, desc_der]
    
    Cada fila contiene dos días con sus descripciones.
    """
    rows = []
    
    for row in data:
        if len(row) < 5:
            continue
        
        # Columna izquierda: [0] día, [1] descripción
        dia_izq = row[0].strip()
        texto_izq = row[1].replace("\n", "").strip() if row[1] else ""
        
        # Columna derecha: [3] día, [4] descripción
        dia_der = row[3].strip() if len(row) > 3 else ""
        texto_der = row[4].replace("\n", "").strip() if len(row) > 4 and row[4] else ""
        
        # Agregar lado izquierdo si hay día
        if dia_izq and texto_izq:
            rows.append([dia_izq, texto_izq])
        
        # Agregar lado derecho si hay día
        if dia_der and texto_der:
            rows.append([dia_der, texto_der])
    
    return rows
