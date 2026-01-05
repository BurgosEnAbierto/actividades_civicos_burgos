from src.parser.gamonal_norte.parse_activities import parse_activity

def test_parse_simple_activity():
    act = parse_activity(
        activity_text="(*) Yoga en parejas. 19:30 h. Sala de encuentro. Público: adultos",
        day_num=4,
        default_year=2025,
        default_month=12,
    )


    assert act["requiere_inscripcion"] is True
    assert act["hora"] == "19:30"
    assert act["hora_fin"] is None
    assert act["lugar"] == "Sala de encuentro"
    assert act["publico"] == "adultos"
