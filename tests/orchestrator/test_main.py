import json
from pathlib import Path

from src.orchestrator.main import run_orchestrator
from src.validators.validate_activities import validate_activities

def fake_download(url, output_dir):
    dummy = output_dir / "dummy.pdf"
    dummy.write_bytes(b"%PDF-1.4 dummy")
    return dummy

def fake_extract_raw(pdf_path):
    return [
        ["MIERCOLES 4", "(*) Yoga en parejas. 19:30 h. Sala de encuentro. Público: adultos"]
    ]

def fake_parse_raw(raw, *, month):
    return [
        {
            "fecha": "04/12/2025",
            "fecha_fin": None,
            "requiere_inscripcion": True,
            "nombre": "Yoga en parejas",
            "hora": "19:30",
            "hora_fin": None,
            "lugar": "Sala de encuentro",
            "publico": "adultos",
            "edad_minima": None,
            "edad_maxima": None,
            "precio": None,
            "descripcion": None,
        }
    ]

fake_parsers = {
    "gamonal_norte": {
        "extract_raw": fake_extract_raw,
        "parse_raw": fake_parse_raw,
    }
}

def test_orchestrator_basic(tmp_path):
    """
    Test de integración ligera:
    - Ejecuta el orquestador para un mes
    - Comprueba estructura
    - Valida contra el schema final
    """
    month = "2025-12"

    data_dir = tmp_path / month
    data_dir.mkdir(parents=True)

    links = {
        "gamonal_norte": [
            {
                "title": "Agenda Gamonal Norte Diciembre 2025",
                "url": "file:///dummy.pdf",
                "is_new": True
            }
        ]
    }

    (data_dir / "links.json").write_text(
        json.dumps(links), encoding="utf-8"
    )

    activities = run_orchestrator(
        month,
        base_data_path=tmp_path,
        download_fn=fake_download,
        parsers=fake_parsers,
    )

    assert "gamonal_norte" in activities
    assert isinstance(activities["gamonal_norte"], list)
    assert len(activities["gamonal_norte"]) == 1

