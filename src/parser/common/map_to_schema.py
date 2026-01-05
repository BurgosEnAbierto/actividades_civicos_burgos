def map_activity_to_schema(activity: dict) -> dict:
    """
    Convierte una actividad parseada al schema canónico de activities.json
    """
    return {
        "Nombre": activity["nombre"],
        "Descripción": activity.get("descripcion"),
        "Fecha": activity["fecha"],
        "Fecha fin": activity.get("fecha_fin"),
        "Hora": activity["hora"],
        "Hora fin": activity.get("hora_fin"),
        "Requiere inscripción": activity["requiere_inscripcion"],
        "Lugar": activity.get("lugar"),
        "Público": activity["publico"],
        "Edad mínima": activity.get("edad_min"),
        "Edad máxima": activity.get("edad_max"),
        "Precio": activity.get("precio"),
    }

