#!/usr/bin/env python3
"""
Script para generar feeds RSS de actividades de centros cívicos.
Genera:
- feed.xml: Feed general con todos los meses/cívicos
- feeds/feed-{civico_id}.xml: Feeds individuales por cívico
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from urllib.parse import urljoin

# Rutas
DOCS_DIR = Path(__file__).parent.parent / "docs"
DATA_DIR = DOCS_DIR / "data"
FEEDS_DIR = DOCS_DIR / "feeds"
CIVICOS_FILE = DATA_DIR / "civicos.json"

# URL base del sitio
BASE_URL = "https://burgosenabierto.github.io/actividades_civicos_burgos/"
PAGE_URL = BASE_URL + "index.html"

# Nombres meses en español
MONTH_NAMES = {
    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
}


def load_civicos():
    """Carga la información de civicos."""
    if not CIVICOS_FILE.exists():
        return {}
    with open(CIVICOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_month_year_display(month_str):
    """Convierte 202604 a 'Abril 2026'."""
    if len(month_str) != 6:
        return month_str
    year = month_str[:4]
    month = month_str[4:]
    month_name = MONTH_NAMES.get(month, month)
    return f"{month_name} {year}"


def load_activities_for_month(month_str):
    """Carga todas las actividades de un mes."""
    month_dir = DATA_DIR / month_str
    activities_file = month_dir / "actividades.json"
    
    if not activities_file.exists():
        return {}
    
    with open(activities_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_links_for_month(month_str):
    """Carga los links (metadata) de un mes."""
    month_dir = DATA_DIR / month_str
    links_file = month_dir / "links.json"
    
    if not links_file.exists():
        return None
    
    with open(links_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_available_months():
    """Retorna lista de meses disponibles, ordenada descendente (más reciente primero)."""
    months = []
    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            if item.is_dir() and item.name.isdigit() and len(item.name) == 6:
                months.append(item.name)
    return sorted(months, reverse=True)


def format_activity_html(activity):
    """Formatea una actividad como HTML para el RSS."""
    html = f"<strong>{activity['nombre']}</strong><br/>"
    
    if activity.get('fecha'):
        html += f"📅 {activity['fecha']}"
        if activity.get('hora'):
            html += f" a las {activity['hora']}"
        html += "<br/>"
    
    if activity.get('publico'):
        html += f"👥 Público: {activity['publico']}<br/>"
    
    if activity.get('edad_minima') or activity.get('edad_maxima'):
        ages = []
        if activity.get('edad_minima'):
            ages.append(f"{activity['edad_minima']}+")
        if activity.get('edad_maxima'):
            ages.append(f"hasta {activity['edad_maxima']}")
        if ages:
            html += f"🎂 Edad: {', '.join(ages)}<br/>"
    
    if activity.get('requiere_inscripcion'):
        html += "✅ <strong>Requiere inscripción</strong><br/>"
    
    return html + "<br/>"


def create_rss_item(title, description, link, pubdate, civico_data=None):
    """Crea un elemento item para RSS."""
    item = Element('item')
    
    title_elem = SubElement(item, 'title')
    title_elem.text = title
    
    desc_elem = SubElement(item, 'description')
    desc_elem.text = description
    
    link_elem = SubElement(item, 'link')
    link_elem.text = link
    
    pubdate_elem = SubElement(item, 'pubDate')
    pubdate_elem.text = pubdate
    
    if civico_data:
        author_elem = SubElement(item, 'author')
        author_elem.text = civico_data.get('email', 'info@burgosenabierto.es')
    
    return item


def generate_general_feed(months_data):
    """Genera el feed principal (feed.xml) con todos los meses/cívicos."""
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = SubElement(rss, 'channel')
    
    title_elem = SubElement(channel, 'title')
    title_elem.text = "Actividades Centros Cívicos Burgos"
    
    link_elem = SubElement(channel, 'link')
    link_elem.text = PAGE_URL
    
    desc_elem = SubElement(channel, 'description')
    desc_elem.text = "Feed de actividades publicadas en los centros cívicos de Burgos"
    
    lang_elem = SubElement(channel, 'language')
    lang_elem.text = "es-es"
    
    # Atom self link
    atom_link = SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', urljoin(BASE_URL, 'feed.xml'))
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # Items ordenados por fecha(más reciente primero)
    for item_data in months_data:
        item = create_rss_item(
            title=item_data['title'],
            description=item_data['description'],
            link=item_data['link'],
            pubdate=item_data['pubdate'],
            civico_data=item_data.get('civico_data')
        )
        channel.append(item)
    
    return rss


def generate_civico_feed(civico_id, civico_name, months_data):
    """Genera un feed individual por cívico."""
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = SubElement(rss, 'channel')
    
    title_elem = SubElement(channel, 'title')
    title_elem.text = f"Actividades {civico_name}"
    
    link_elem = SubElement(channel, 'link')
    link_elem.text = PAGE_URL
    
    desc_elem = SubElement(channel, 'description')
    desc_elem.text = f"Feed de actividades publicadas en {civico_name}"
    
    lang_elem = SubElement(channel, 'language')
    lang_elem.text = "es-es"
    
    # Atom self link
    atom_link = SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', urljoin(BASE_URL, f'feeds/feed-{civico_id}.xml'))
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # Items filtrados por civico
    for item_data in months_data:
        if item_data.get('civico_id') == civico_id:
            item = create_rss_item(
                title=item_data['title'],
                description=item_data['description'],
                link=item_data['link'],
                pubdate=item_data['pubdate'],
                civico_data=item_data.get('civico_data')
            )
            channel.append(item)
    
    return rss


def prettify_xml(elem):
    """Añade saltos de línea y espacios al XML para legibilidad."""
    from xml.dom import minidom
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def main():
    """Función principal."""
    print("🔄 Generando feeds RSS...")
    
    civicos = load_civicos()
    months = get_available_months()
    
    if not months:
        print("⚠️  No se encontraron meses con datos.")
        return
    
    print(f"📅 Se encontraron {len(months)} meses: {', '.join(months)}")
    
    # Recolectar todos los items para el feed general
    all_items = []
    
    # Procesar cada mes
    for month_str in months:
        activities = load_activities_for_month(month_str)
        links = load_links_for_month(month_str)
        
        if not activities:
            continue
        
        month_display = get_month_year_display(month_str)
        
        # Obtener fecha de pubDate del links.json
        pubdate = None
        if links and links.get('meta', {}).get('scraped_at'):
            try:
                scraped_dt = datetime.fromisoformat(links['meta']['scraped_at'])
                pubdate = scraped_dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
            except:
                pass
        
        if not pubdate:
            pubdate = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Procesar cada cívico en el mes
        for civico_id, civico_activities in activities.items():
            if not civico_activities:
                continue
            
            civico_info = civicos.get(civico_id, {})
            civico_name = civico_info.get('nombre', civico_id.replace('_', ' ').title())
            
            # Generar descripción con listado de actividades
            description = f"<h3>{civico_name} - {month_display}</h3>\n"
            description += f"<p><strong>Totales:</strong> {len(civico_activities)} actividades</p>\n"
            description += "<h4>Próximas actividades:</h4>\n"
            
            # Mostrar solo las primeras 5 actividades en el RSS
            for i, activity in enumerate(civico_activities[:5]):
                description += format_activity_html(activity)
            
            if len(civico_activities) > 5:
                description += f"<p><em>...y {len(civico_activities) - 5} más</em></p>\n"
            
            description += f"<p><a href='{PAGE_URL}?month={month_str}'>Ver todas las actividades</a></p>"
            
            # Crear item
            item_data = {
                'title': f"Actividades {civico_name} - {month_display}",
                'description': description,
                'link': f"{PAGE_URL}?month={month_str}",
                'pubdate': pubdate,
                'civico_id': civico_id,
                'civico_data': civico_info
            }
            
            all_items.append(item_data)
    
    # Crear directorio de feeds
    FEEDS_DIR.mkdir(exist_ok=True)
    
    # Generar feed general
    print("📝 Generando feed.xml (general)...")
    general_rss = generate_general_feed(all_items)
    general_xml = prettify_xml(general_rss)
    
    feed_file = DOCS_DIR / "feed.xml"
    with open(feed_file, 'w', encoding='utf-8') as f:
        f.write(general_xml)
    print(f"✅ Feed general guardado: {feed_file}")
    
    # Generar feeds individuales por cívico
    civicos_in_data = set(item['civico_id'] for item in all_items)
    
    for civico_id in sorted(civicos_in_data):
        civico_info = civicos.get(civico_id, {})
        civico_name = civico_info.get('nombre', civico_id.replace('_', ' ').title())
        
        print(f"📝 Generando feed-{civico_id}.xml ({civico_name})...")
        civico_rss = generate_civico_feed(civico_id, civico_name, all_items)
        civico_xml = prettify_xml(civico_rss)
        
        civico_feed_file = FEEDS_DIR / f"feed-{civico_id}.xml"
        with open(civico_feed_file, 'w', encoding='utf-8') as f:
            f.write(civico_xml)
        print(f"✅ Feed de {civico_name} guardado: {civico_feed_file}")
    
    print("\n✨ Feeds RSS generados exitosamente!")
    print(f"📍 Feed general: {BASE_URL}feed.xml")
    print("📍 Feeds por cívico:")
    for civico_id in sorted(civicos_in_data):
        civico_info = civicos.get(civico_id, {})
        civico_name = civico_info.get('nombre', civico_id)
        print(f"   - {civico_name}: {BASE_URL}feeds/feed-{civico_id}.xml")


if __name__ == '__main__':
    main()
