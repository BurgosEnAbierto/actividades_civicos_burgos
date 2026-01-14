def map_activity_to_schema(activity: dict) -> dict:
    """
    Convierte una actividad parseada al schema canónico de activities.json.
    Mapea campos internos a los nombres esperados en el schema.
    """
    return {
        "nombre": activity["nombre"],
        "descripcion": activity.get("descripcion"),
        "fecha": activity["fecha"],
        "fecha_fin": activity.get("fecha_fin"),
        "hora": activity["hora"],
        "hora_fin": activity.get("hora_fin"),
        "requiere_inscripcion": activity["requiere_inscripcion"],
        "lugar": activity.get("lugar"),
        "publico": activity["publico"],
        "edad_minima": activity.get("edad_min"),
        "edad_maxima": activity.get("edad_max"),
        "precio": activity.get("precio"),
    }

