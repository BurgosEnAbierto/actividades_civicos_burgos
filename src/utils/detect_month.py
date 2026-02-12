import re
from datetime import datetime, timezone

MONTHS = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

def detect_month(links: list[dict]) -> str:
    for item in links:
        title = item["title"].lower()

        for name, mm in MONTHS.items():
            if name in title:
                year_match = re.search(r"(20\d{2}|\d{2})", title)
                if not year_match:
                    continue

                year = year_match.group(1)
                if len(year) == 2:
                    year = f"20{year}"

                return f"{year}{mm}"

    # fallback: mes actual
    now = datetime.now(timezone.utc)
    return f"{now.year}{now.month:02d}"
