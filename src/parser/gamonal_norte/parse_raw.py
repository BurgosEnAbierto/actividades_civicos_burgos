from src.parser.gamonal_norte.parse_activities import parse_activities_gamonal
from src.parser.common.map_to_schema import map_activity_to_schema


def parse_raw_gamonal(raw, *, month, civico=""):
    parsed = parse_activities_gamonal(raw, month=month)
    return [map_activity_to_schema(a) for a in parsed]
