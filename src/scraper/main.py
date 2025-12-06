import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re


BASE_URL = "https://www.aytoburgos.es/es/servicios-y-programas/-/asset_publisher/rCUegBWr9yud/content/agendacivicos"
OUTPUT_FILE = Path("data/urls.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

def fetch_page(url: str) -> str:
    print(f"Descargando página: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text


def extract_pdf_links(html: str) -> list:
    """Extrae enlaces a PDFs **solo** de la SEGUNDA sección 'section.documents'.


    - Seleccionamos la segunda ocurrencia de <section class="documents">.
    - Buscamos dentro de esa sección todos los <ul class="documents"> y sus <a>.
    - Detectamos PDFs cuando la ruta contiene '.pdf' seguido de fin de ruta o de un separador
    (por ejemplo: '.pdf', '.pdf/', '.pdf?…', etc.).
    - Limpiamos el título quitando el sufijo '(pdf ... kB)'.
    """
    soup = BeautifulSoup(html, "html.parser")


    sections = soup.select("section.documents")
    if len(sections) < 2:
        print("⚠ No se encontró la segunda sección de documentos (section.documents)")
        return []


    target_section = sections[1]


    # Todos los ULs dentro de la segunda sección
    document_lists = target_section.select("ul.documents")
    if not document_lists:
        print("⚠ No se encontraron listas de documentos dentro de la segunda sección")
        return []


    links = []
    pdf_pattern = re.compile(r"\.pdf($|[/?#])", flags=re.IGNORECASE)


    for ul in document_lists:
        for a in ul.select("li a"):
            href = a.get("href") or ""
            # Normaliza espacios y NBSP
            title = a.get_text(separator=' ', strip=True).replace(' ', ' ')


            if not href:
                continue


            # Detecta si la URL contiene .pdf (aunque no termine en .pdf)
            if not pdf_pattern.search(href):
                continue


            full_url = f"https://www.aytoburgos.es{href}" if href.startswith("/") else href


            # Limpia títulos como: 'GAMONAL NORTE AGENDA DICIEMBRE 2025(pdf 947,2 kB)'
            title_clean = re.sub(r"\(pdf.*\)$", "", title, flags=re.IGNORECASE).strip()
            
            links.append({"title": title_clean, "url": full_url})
    
    return links


def save_links(links: list):
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)
    print(f"Guardado en {OUTPUT_FILE}")


def main():
    html = fetch_page(BASE_URL)
    links = extract_pdf_links(html)


    print("\nPDFs encontrados:")
    for item in links:
        print(f" - {item['title']} → {item['url']}")


    save_links(links)


if __name__ == "__main__":
    main()