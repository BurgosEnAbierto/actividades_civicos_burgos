"""
Parser genérico para cívicos sin implementación específica.

Este módulo proporciona una interfaz estándar que:
1. Extrae filas raw de PDF (usando Camelot)
2. Delega el parsing a parse_raw_ai()

Todos los cívicos pueden usar esta implementación,
independientemente del formato de su PDF.
"""

from src.parser.ai_parser import extract_raw_ai, parse_raw_ai

__all__ = ["extract_raw_ai", "parse_raw_ai"]
