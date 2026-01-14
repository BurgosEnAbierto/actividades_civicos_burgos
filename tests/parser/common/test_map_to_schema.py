from src.parser.common.map_to_schema import map_activity_to_schema

def test_map_activity_to_schema_with_ages():
    activity = {
        "nombre": "La hora del cuento",
        "descripcion": None,
        "fecha": "03/12/2025",
        "fecha_fin": None,
        "hora": "19:00",
        "hora_fin": None,
        "requiere_inscripcion": True,
        "lugar": "Biblioteca familiar",
        "publico": "niños de 4 a 7 años",
        "edad_min": 4,
        "edad_max": 7,
        "precio": None,
    }

    mapped = map_activity_to_schema(activity)

    assert mapped["edad_minima"] == 4
    assert mapped["edad_maxima"] == 7
    assert mapped["precio"] is None