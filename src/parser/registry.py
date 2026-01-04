from src.parser.gamonal_norte.extract_raw import extract_raw_gamonal
from src.parser.gamonal_norte.parse_raw import parse_raw_gamonal


_PARSERS = {
    "gamonal_norte": {
        "extract_raw": extract_raw_gamonal,
        "parse_raw": parse_raw_gamonal,
    }
}


def get_parser(civico_id: str):
    if civico_id not in _PARSERS:
        raise ValueError(f"No hay parser registrado para {civico_id}")
    return _PARSERS[civico_id]
