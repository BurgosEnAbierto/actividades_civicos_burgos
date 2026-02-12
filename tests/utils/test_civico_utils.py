from src.utils.civico_utils import detect_civico_id

def test_detect_gamonal_norte():
    title = "GAMONAL NORTE AGENDA DICIEMBRE 2025"
    assert detect_civico_id(title) == "gamonal_norte"

def test_detect_rio_vena():
    title = "Agenda Centro Cívico Río Vena Enero 2026"
    assert detect_civico_id(title) == "rio_vena"
    
def test_detect_none():
    title = "ACTIVIDAD CULTURAL BURGOS"
    assert detect_civico_id(title) is None
