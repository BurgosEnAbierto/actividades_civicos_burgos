"""
Extracción de raw para parser genérico.

Usa Camelot para extraer tablas del PDF.
Formato output: [[día, texto_actividades], ...]
"""

from pathlib import Path
from typing import List
import logging

try:
    import camelot
except ImportError:
    camelot = None

logger = logging.getLogger(__name__)


def extract_raw_generic(pdf_path: Path) -> List[List[str]]:
    """
    Extrae filas raw desde un PDF usando Camelot.
    
    Args:
        pdf_path: Ruta al PDF
    
    Returns:
        Lista de [día, texto_actividades]
    """
    if camelot is None:
        logger.error("Camelot no está disponible. Instala con: pip install camelot-py")
        return []
    
    logger.info(f"Extrayendo tablas (Camelot): {pdf_path.name}")
    
    try:
        tables = camelot.read_pdf(str(pdf_path), pages="all")
    except Exception as e:
        logger.error(f"Error extrayendo tablas con Camelot: {e}")
        return []
    
    if not tables:
        logger.warning(f"No se detectaron tablas en {pdf_path.name}")
        return []
    
    rows = []
    
    for table in tables:
        data = table.df.values.tolist()
        
        for row in data:
            if len(row) < 2:
                continue
            
            dia = str(row[0]).strip()
            texto = str(row[1]).replace("\n", "").strip()
            
            if dia:
                rows.append([dia, texto])
    
    logger.debug(f"Filas raw extraídas: {len(rows)}")
    return rows
