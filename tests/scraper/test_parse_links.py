from pathlib import Path
from src.scraper.parse_links import extract_pdf_links

FIXTURE = Path("tests/fixtures/agenda_page.html")

def test_extract_pdf_links():
    html = FIXTURE.read_text(encoding="utf-8")
    links = extract_pdf_links(html)

    assert len(links) == 2

    assert links[0]["civico_id"] == "gamonal_norte"
    assert links[0]["filename"].endswith(".pdf")
    assert links[0]["url"].startswith("https://www.aytoburgos.es")

    assert links[1]["civico_id"] == "capiscol"
