import json
from pathlib import Path
from src.validators.validate_activities import validate_activities

def test_activities_schema_validation():
    schema_path = Path(__file__).parents[2] / "schemas" / "actividades.schema.v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    data = {
        "gamonal_norte": [
            {
                "nombre": "Yoga",
                "descripcion": None,
                "fecha": "04/12/2025",
                "fecha_fin": None,
                "hora": "19:30",
                "hora_fin": None,
                "requiere_inscripcion": True,
                "lugar": "Sala",
                "publico": "adultos",
                "edad_minima": None,
                "edad_maxima": None,
                "precio": None,
            }
        ]
    }

    validate_activities(data, schema)
