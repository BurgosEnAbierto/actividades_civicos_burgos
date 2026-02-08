from src.parser.gamonal_norte.extract_raw import extract_raw_gamonal
from src.parser.gamonal_norte.parse_raw import parse_raw_gamonal
from src.parser.rio_vena.extract_raw import extract_raw_rio_vena
from src.parser.vista_alegre.extract_raw import extract_raw_vista_alegre
from src.parser.capiscol.extract_raw import extract_raw_capiscol
from src.parser.san_agustin.extract_raw import extract_raw_san_agustin
from src.parser.huelgas.extract_raw import extract_raw_huelgas
from src.parser.san_juan.extract_raw import extract_raw_san_juan
from src.parser.generic.extract_raw import extract_raw_generic
from src.parser.ai_parser import parse_raw_ai

# Lista de todos los cívicos
CIVICOS = {
    "rio_vena",
    "vista_alegre",
    "capiscol",
    "san_agustin",
    "huelgas",
    "gamonal_norte",
    "san_juan",
}

# Parsers específicos por cívico (si existen)
_PARSERS = {
    "gamonal_norte": {
        "extract_raw": extract_raw_gamonal,
        "parse_raw": parse_raw_ai,
    },
    "rio_vena": {
        "extract_raw": extract_raw_rio_vena,
        "parse_raw": parse_raw_ai,
    },
    "vista_alegre": {
        "extract_raw": extract_raw_vista_alegre,
        "parse_raw": parse_raw_ai,
    },
    "capiscol": {
        "extract_raw": extract_raw_capiscol,
        "parse_raw": parse_raw_ai,
    },
    "san_agustin": {
        "extract_raw": extract_raw_san_agustin,
        "parse_raw": parse_raw_ai,
    },
    "huelgas": {
        "extract_raw": extract_raw_huelgas,
        "parse_raw": parse_raw_ai,
    },
    "san_juan": {
        "extract_raw": extract_raw_san_juan,
        "parse_raw": parse_raw_ai,
    },
}

# Parser genérico (AI) como fallback para todos los cívicos
_DEFAULT_PARSER = {
    "extract_raw": extract_raw_generic,
    "parse_raw": parse_raw_ai,
}


def get_parser(civico_id: str):
    """
    Obtiene el parser para un cívico.
    
    Si existe parser específico, lo usa.
    En caso contrario, usa el parser genérico basado en IA.
    
    Args:
        civico_id: ID del cívico (ej: "gamonal_norte")
    
    Returns:
        Dict con extract_raw y parse_raw
    
    Raises:
        ValueError: Si el cívico no existe
    """
    if civico_id not in CIVICOS:
        raise ValueError(f"Cívico no registrado: {civico_id}. Opciones: {CIVICOS}")
    
    # Usar parser específico si existe, sino usar genérico
    return _PARSERS.get(civico_id, _DEFAULT_PARSER)

