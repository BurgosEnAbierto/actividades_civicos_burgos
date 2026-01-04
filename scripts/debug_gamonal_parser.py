from pathlib import Path
from src.parser.gamonal_norte.extract_raw import extract_raw_gamonal
from src.parser.gamonal_norte.parse_raw import parse_raw_gamonal

pdf = Path("data/202512/pdfs/GAMONAL_NORTE_AGENDA_DICIEMBRE_2025.pdf")

raw = extract_raw_gamonal(pdf)
acts = parse_raw_gamonal(raw, month="202512")

for a in acts:
    print(a)
