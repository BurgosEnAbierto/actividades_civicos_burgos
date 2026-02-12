import re

CIVICO_PATTERNS = {
    "gamonal_norte": r"gamonal\s+norte",
    "rio_vena": r"r[ií]o\s+vena",
    "vista_alegre": r"vista\s+alegre",
    "capiscol": r"capiscol",
    "san_agustin": r"san\s+agust[ií]n",
    "huelgas": r"huelgas|el\s+pilar",
    "san_juan": r"san\s+juan",
}

def detect_civico_id(title: str) -> str | None:
    t = title.lower()
    for civico_id, pattern in CIVICO_PATTERNS.items():
        if re.search(pattern, t):
            return civico_id
    return None
