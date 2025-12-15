import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import hashlib
from pathlib import PosixPath
from datetime import datetime
from utils.parse_pdf_content import parse_activities, process_pdf


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

            # TODO: descargamos solo el PDF de Gamonal Norte por ahora. ProcessPDF and ParseActivities no están preparados para el resto, organizados diferentemente
            if "GAMONAL_NORTE" not in title.upper().replace(" ", "_"):
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


def download_pdf(url: str, output_folder: Path) -> Path:
    output_folder.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0] or "document.pdf"
    pdf_path = output_folder / filename

    print(f" → Descargando PDF: {filename}")
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    pdf_path.write_bytes(r.content)
    return pdf_path

def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    html = fetch_page(BASE_URL)
    links = extract_pdf_links(html)

    print("\nPDFs encontrados:")
    for item in links:
        print(f" - {item['title']} → {item['url']}")

    # Guardamos URLs
    save_links(links)

    pdf_output_folder = Path("data/pdfs")
    metadata_output = Path("data/pdf_data.json")

    pdf_metadata = {}

    for item in links:
        url = item["url"]

        # Descargar
        pdf_path = download_pdf(url, pdf_output_folder)

        # Hash + tamaño
        file_hash = compute_file_hash(pdf_path)
        size = pdf_path.stat().st_size
        timestamp = datetime.utcnow().isoformat()

        pdf_metadata[pdf_path.name] = {
            "title": item["title"],
            "url": url,
            "path": str(pdf_path),
            "hash": file_hash,
            "size_bytes": size,
            "downloaded_at": timestamp,
        }

    with metadata_output.open("w", encoding="utf-8") as f:
        json.dump(pdf_metadata, f, indent=2, ensure_ascii=False)

    print(f"\nMetadatos guardados en: {metadata_output}")

    # Parsear PDFs y extraer actividades
    metadata_output = Path("data/pdf_data.json")
    with metadata_output.open("w", encoding="utf-8") as f:
        json.dump(pdf_metadata, f, indent=2, ensure_ascii=False)

    all_activities = {}
    for pdf_name, meta in pdf_metadata.items():
        # Procesar PDF → texto
        parsed_text = process_pdf(PosixPath(meta["path"]))
        acts = parse_activities(parsed_text)
        all_activities[pdf_name] = acts

    activities_out = Path("data/activities.json")
    with activities_out.open("w", encoding="utf-8") as f:
        json.dump(all_activities, f, indent=2, ensure_ascii=False)

    print(f"Actividades procesadas → {activities_out}")


if __name__ == "__main__":
    main()