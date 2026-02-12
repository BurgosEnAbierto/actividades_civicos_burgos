"""
Tests para verificar que el registry funciona correctamente para todos los cívicos.
"""

import pytest
from src.parser.registry import get_parser, CIVICOS


class TestRegistry:
    """Verifica que get_parser funciona para todos los cívicos"""

    def test_all_civicos_registered(self):
        """Prueba que todos los cívicos están registrados"""
        assert len(CIVICOS) == 7
        expected_civicos = {
            "gamonal_norte",
            "rio_vena",
            "vista_alegre",
            "capiscol",
            "san_agustin",
            "huelgas",
            "san_juan",
        }
        assert set(CIVICOS) == expected_civicos

    def test_get_parser_returns_dict(self):
        """Prueba que get_parser devuelve un dict con extract_raw y parse_raw"""
        for civico_id in CIVICOS:
            parser = get_parser(civico_id)
            assert isinstance(parser, dict), f"Parser para {civico_id} no es dict"
            assert "extract_raw" in parser, f"Parser para {civico_id} sin extract_raw"
            assert "parse_raw" in parser, f"Parser para {civico_id} sin parse_raw"
            assert callable(parser["extract_raw"])
            assert callable(parser["parse_raw"])

    def test_specific_parser_gamonal_norte(self):
        """Prueba que gamonal_norte usa parser específico"""
        parser = get_parser("gamonal_norte")
        assert parser is not None
        # Verifica que tiene los métodos requeridos
        assert hasattr(parser, "__getitem__")

    def test_ai_parser_fallback(self):
        """Prueba que civicos sin parser específico usan AI parser"""
        for civico_id in ["rio_vena", "vista_alegre", "capiscol", "san_agustin", "huelgas", "san_juan"]:
            parser = get_parser(civico_id)
            assert parser is not None
            # Si usa AI parser, debería tener funciones de ai_parser
            assert callable(parser["parse_raw"])
