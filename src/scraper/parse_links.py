from bs4 import BeautifulSoup
import re
from src.utils.civico_utils import detect_civico_id

PDF_PATTERN = re.compile(r"\.pdf($|[/?#])", re.IGNORECASE)

def extract_pdf_links(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    sections = soup.select("section.documents")
    if len(sections) < 2:
        return []

    target = sections[1]
    links = []

    for a in target.select("ul.documents li a"):
        href = a.get("href")
        if not href or not PDF_PATTERN.search(href):
            continue

        title_raw = a.get_text(separator=" ", strip=True)
        title = re.sub(r"\(pdf.*\)$", "", title_raw, flags=re.I).strip()

        civico_id = detect_civico_id(title)
        if not civico_id:
            continue

        url = (
            f"https://www.aytoburgos.es{href}"
            if href.startswith("/")
            else href
        )

        links.append({
            "civico_id": civico_id,
            "title": title,
            "url": url,
            "filename": url.split("/")[-1].split("?")[0],
        })

    return links
