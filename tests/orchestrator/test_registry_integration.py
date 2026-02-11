"""
Tests para verificar que el orquestrador estructura correctamente los datos.
"""

import json
from pathlib import Path
import pytest
from src.parser.registry import CIVICOS


class TestOrchestratorStructure:
    """Verifica que el orquestrador estructura los datos correctamente"""

    def test_actividades_json_exists(self):
        """Prueba que actividades.json existe después de orquestrador"""
        activities_path = Path("docs/data/202601/actividades.json")
        assert activities_path.exists(), (
            f"No existe {activities_path}. Ejecuta: python src/orchestrator/main.py 202601"
        )

    def test_actividades_json_structure(self):
        """Prueba que actividades.json tiene estructura correcta"""
        activities_path = Path("docs/data/202601/actividades.json")
        if not activities_path.exists():
            pytest.skip("actividades.json no existe")

        actividades = json.loads(activities_path.read_text(encoding="utf-8"))
        assert isinstance(actividades, dict)

        # Verifica que tiene al menos algún cívico
        assert len(actividades) > 0

        # Verifica estructura por cívico
        for civico_id in CIVICOS:
            if civico_id in actividades:
                activities_list = actividades[civico_id]
                assert isinstance(activities_list, list)
                # Si hay actividades, verifica campos requeridos
                if activities_list:
                    for activity in activities_list:
                        assert "nombre" in activity
                        assert "publico" in activity
                        assert activity["nombre"] is not None
                        assert activity["publico"] is not None

    def test_all_civicos_have_consistent_schema(self):
        """Prueba que todas las actividades cumplen el schema"""
        from jsonschema import validate, ValidationError

        activities_path = Path("docs/data/202601/actividades.json")
        if not activities_path.exists():
            pytest.skip("actividades.json no existe")

        schema_path = Path("schemas/actividades.schema.v1.json")
        assert schema_path.exists()

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        actividades = json.loads(activities_path.read_text(encoding="utf-8"))

        errors = []
        for civico_id, activities_list in actividades.items():
            for idx, activity in enumerate(activities_list):
                try:
                    validate(instance=activity, schema=schema)
                except ValidationError as e:
                    errors.append(f"{civico_id}[{idx}]: {e.message}")

        assert not errors, f"Schema validation errors: {errors}"


class TestIsNewFlag:
    """Verifica que is_new se actualiza correctamente en links.json"""

    def test_links_json_exists(self):
        """Prueba que links.json existe"""
        links_path = Path("docs/data/202601/links.json")
        assert links_path.exists()

    def test_is_new_flag_lifecycle(self):
        """Prueba que is_new flag tiene valores correctos"""
        links_path = Path("docs/data/202601/links.json")
        links_data = json.loads(links_path.read_text(encoding="utf-8"))
        links = links_data.get("links", [])

        for link in links:
            assert "civico_id" in link
            assert "is_new" in link
            assert isinstance(link["is_new"], bool)

    def test_processed_links_are_marked_false(self):
        """Prueba que los links procesados están marcados como is_new=false"""
        activities_path = Path("docs/data/202601/actividades.json")
        links_path = Path("docs/data/202601/links.json")

        if not activities_path.exists():
            pytest.skip("actividades.json no existe")

        actividades = json.loads(activities_path.read_text(encoding="utf-8"))
        links_data = json.loads(links_path.read_text(encoding="utf-8"))
        links = links_data.get("links", [])

        # Si hay actividades, debería haber links procesados
        if actividades:
            processed_links = [link for link in links if not link.get("is_new")]
            assert len(processed_links) > 0, "Hay actividades pero todos los links son is_new=true"
