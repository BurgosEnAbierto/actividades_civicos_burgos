from src.utils.detect_month import detect_month

def test_detect_december_2025():
    links = [{"title": "Gamonal Norte Agenda DICIEMBRE 2025"}]
    assert detect_month(links) == "202512"

def test_detect_two_digit_year():
    links = [{"title": "Agenda Enero 25"}]
    assert detect_month(links) == "202501"

def test_fallback_to_current_month():
    links = [{"title": "Agenda Centro Cívico"}]
    result = detect_month(links)
    assert len(result) == 6
    assert result.isdigit()
