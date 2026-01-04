import json
from pathlib import Path
from unittest.mock import patch

from src.orchestrator.main import run_orchestrator


@patch("src.orchestrator.main.download_pdf")
@patch("src.orchestrator.main.get_parser")
def test_orchestrator_basic(mock_get_parser, mock_download, tmp_path):
    month = "202512"
    data_dir = tmp_path / "data" / month
    data_dir.mkdir(parents=True)

    links = [
        {
            "civico_id": "gamonal_norte",
            "url": "https://example.com/a.pdf",
            "is_new": True,
        }
    ]

    (data_dir / "links.json").write_text(json.dumps(links), encoding="utf-8")

    mock_download.return_value = tmp_path / "a.pdf"

    mock_get_parser.return_value = {
        "extract_raw": lambda p: [["MIERCOLES 3", "Yoga. 19 h. Público: adultos"]],
        "parse_raw": lambda raw, month: [{"nombre": "Yoga"}],
    }

    with patch("src.orchestrator.main.DATA_DIR", tmp_path / "data"):
        run_orchestrator(month)

    out = data_dir / "actividades.json"
    assert out.exists()
