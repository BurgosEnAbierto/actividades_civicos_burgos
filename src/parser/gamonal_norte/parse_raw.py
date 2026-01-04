from .parse_activities import parse_activities_gamonal


def parse_raw_gamonal(raw, *, month):
    return parse_activities_gamonal(raw, month=month)
