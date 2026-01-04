from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict

class CivicoParser(ABC):
    civico_id: str

    @abstractmethod
    def extract_raw(self, pdf_path: Path) -> List[str]:
        """
        Devuelve una lista de textos raw (actividades sin parsear)
        """
        pass

    @abstractmethod
    def parse_raw(
        self, raw_activities: List[str], *, month: str
    ) -> List[Dict]:
        """
        Devuelve actividades estructuradas
        """
        pass
