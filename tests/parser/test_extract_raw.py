"""
Tests para verificar que todos los extract_raw funcionan correctamente.
"""

import pytest
from pathlib import Path
from src.parser.registry import get_parser, CIVICOS


class TestExtractRaw:
    """Verifica que extract_raw devuelve [[día, texto], ...]"""

    @pytest.mark.parametrize("civico_id", sorted(CIVICOS))
    def test_extract_raw_format(self, civico_id):
        """Prueba que extract_raw devuelve lista con formato correcto"""
        # Skip si no hay PDFs de ejemplo
        pdfs_dir = Path("data/202601/pdfs")
        pdf_paths = list(pdfs_dir.glob(f"{civico_id}/*.pdf")) or list(
            pdfs_dir.glob(f"examples/*{civico_id.upper()}*")
        )

        if not pdf_paths:
            pytest.skip(f"PDF no disponible para {civico_id}")

        parser = get_parser(civico_id)
        extract_raw = parser["extract_raw"]
        pdf_path = pdf_paths[0]

        # Ejecuta extract_raw
        result = extract_raw(pdf_path)

        # Verifica que es lista
        assert isinstance(result, list), f"extract_raw devuelve {type(result)}"

        # Verifica que no está vacía
        assert len(result) > 0, f"extract_raw devuelve lista vacía para {civico_id}"

        # Verifica estructura: cada item es [día, texto]
        for idx, item in enumerate(result):
            assert isinstance(item, (list, tuple)), (
                f"{civico_id}[{idx}]: item no es list/tuple"
            )
            assert len(item) == 2, f"{civico_id}[{idx}]: item no tiene 2 elementos"
            assert isinstance(item[0], str), f"{civico_id}[{idx}]: día no es string"
            assert isinstance(item[1], str), f"{civico_id}[{idx}]: texto no es string"
            # Al menos uno debe tener contenido
            assert (
                len(item[0]) > 0 or len(item[1]) > 0
            ), f"{civico_id}[{idx}]: día y texto ambos vacíos"

    def test_extract_raw_returns_reasonable_count(self):
        """Verifica que extract_raw retorna cantidad razonable de filas"""
        pdfs_dir = Path("data/202601/pdfs")
        for civico_id in CIVICOS:
            pdf_paths = list(pdfs_dir.glob(f"{civico_id}/*.pdf")) or list(
                pdfs_dir.glob(f"examples/*{civico_id.upper()}*")
            )

            if not pdf_paths:
                continue

            parser = get_parser(civico_id)
            extract_raw = parser["extract_raw"]
            result = extract_raw(pdf_paths[0])

            # Debe tener entre 5 y 100 filas (actividades razonables para un mes)
            assert (
                5 <= len(result) <= 100
            ), f"{civico_id}: {len(result)} filas fuera de rango"
