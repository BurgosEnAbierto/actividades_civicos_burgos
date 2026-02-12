import jsonschema

def validate_activities(activities_by_civic: dict, schema: dict) -> None:
    """
    activities_by_civic:
    {
        "gamonal_norte": [ {...}, {...} ],
        "san_agustin":   [ {...} ]
    }
    """
    jsonschema.validate(instance=activities_by_civic, schema=schema)
