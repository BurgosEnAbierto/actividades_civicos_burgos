"""
Procesamiento de PDF para parser genérico.

Abstracción que permite procesar PDFs de cualquier cívico
sin necesidad de código específico.
"""

from pathlib import Path
from typing import List
from .extract_raw import extract_raw_generic


def process_pdf_generic(pdf_path: Path) -> List[List[str]]:
    """
    Procesa un PDF y devuelve filas raw.
    
    Esta función es el punto de entrada único para cualquier PDF.
    No depende del cívico ni del formato específico.
    
    Args:
        pdf_path: Ruta al PDF
    
    Returns:
        Lista de [día, texto_actividades]
    """
    return extract_raw_generic(pdf_path)
