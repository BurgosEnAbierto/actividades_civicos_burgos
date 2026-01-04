import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

MONTHS = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}

RE_PUBLIC = re.compile(r"P[úu]blico:\s*(.*)", re.IGNORECASE)

RE_DATE_RANGE = re.compile(
    r"(\d{1,2})\s+al\s+(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚñ]+)",
    re.IGNORECASE
)


def starts_new_activity(line: str) -> bool:
    l = line.strip()
    return (
        l.startswith("(*)")
        or l.startswith("*)")
        or (l.startswith("(") and "*)" in l)
    )


def split_cell_into_activities(cell_text: str) -> list[str]:
    """
    Divide una celda potencialmente con varias actividades en textos individuales.

    Reglas:
    - Una actividad nueva empieza cuando aparece:
        * '(*' al inicio de línea
        * '*)' al inicio de línea
        * '(' al inicio de línea y contiene '*)'
    - Agrupa líneas hasta encontrar el inicio de la siguiente actividad.
    """
    cell_text = cell_text.replace("(\n*)", "(*)", 1)
    lines = [l.strip() for l in cell_text.split("\n") if l.strip()]

    blocks = []
    current = []

    for line in lines:
        if starts_new_activity(line) and current:
            if line.startswith("*)"):
                line = line.replace("*)", "(*)", 1)
            blocks.append(" ".join(current))
            current = [line]
        elif line != "(":
            current.append(line)

    if current:
        blocks.append(" ".join(current))

    return blocks


def normalize_hour(h: str) -> str:
    """Convierte 19, 19., 19.00, 19:00 en 19:00"""
    h = h.replace(".", ":")
    if ":" not in h:
        h = f"{h}:00"
    return h


def parse_activity(activity_text, *, day_num, default_year, default_month):
    warnings = []
    text = activity_text.strip()

    # Fecha base
    try:
        fecha_dt = datetime(default_year, default_month, day_num)
    except ValueError:
        logger.warning("Fecha inválida: día=%s mes=%s", day_num, default_month)
        return None

    fecha = fecha_dt.strftime("%d/%m/%Y")
    fecha_fin = None

    # Inscripción
    requiere = text.startswith("(*)")
    if requiere:
        text = text.replace("(*)", "", 1).strip()

    # Rango de fechas
    mdate = RE_DATE_RANGE.search(text)
    if mdate:
        d1, d2, month_name = mdate.groups()
        month_name = month_name.upper()
        if month_name in MONTHS:
            fecha = datetime(default_year, MONTHS[month_name], int(d1)).strftime("%d/%m/%Y")
            fecha_fin = datetime(default_year, MONTHS[month_name], int(d2)).strftime("%d/%m/%Y")
        text = text[: mdate.start()].strip()

    # Horas
    hora = hora_fin = None
    mrange = re.search(
        r"(\d{1,2}(?:[:.]\d{2})?)\s*-\s*(\d{1,2}(?:[:.]\d{2})?)\s*h?",
        text,
        re.IGNORECASE,
    )

    if mrange:
        hora = normalize_hour(mrange.group(1))
        hora_fin = normalize_hour(mrange.group(2))
        text = text.replace(mrange.group(0), "").strip()
    else:
        msingle = re.search(r"(\d{1,2}(?:[:.]\d{2})?)\s*h", text, re.IGNORECASE)
        if msingle:
            hora = normalize_hour(msingle.group(1))
            text = text.replace(msingle.group(0), "").strip()
        else:
            warnings.append("sin hora")

    # Público
    publico = None
    mpub = RE_PUBLIC.search(text)
    if mpub:
        publico = mpub.group(1).strip()
        text = text[: mpub.start()].strip()
    elif ":" in text:
        publico = text.split(":")[-1].strip()

    if not publico:
        warnings.append("sin público")

    # Lugar
    lugar = None
    if "." in text:
        parts = [p.strip() for p in text.split(".") if p.strip()]
        if len(parts) >= 2:
            nombre = parts[0]
            lugar = parts[1]
        else:
            nombre = text
    else:
        nombre = text

    if not lugar:
        warnings.append("lugar no detectado")

    for w in warnings:
        logger.warning("%s → %s", w, activity_text)

    return {
        "fecha": fecha,
        "fecha_fin": fecha_fin,
        "requiere_inscripcion": requiere,
        "nombre": nombre.rstrip("."),
        "hora": hora,
        "hora_fin": hora_fin,
        "lugar": lugar,
        "publico": publico,
        "warnings": warnings,
    }


def sort_key(a):
    try:
        dt = datetime.strptime(a["fecha"], "%d/%m/%Y")
        if a.get("hora"):
            h, m = a["hora"].split(":")
            return dt.replace(hour=int(h), minute=int(m))
        return dt
    except Exception:
        return datetime.max


def parse_activities_gamonal(raw_rows, *, month):
    """
    raw_rows: lista de filas Camelot, por ejemplo:
        [
          ["MIERCOLES 17", "(*) Café tertulia ..."],
          ["JUEVES 18", "(*) La hora del cuento ..."],
          ...
        ]

    Devuelve una lista de actividades estructuradas.
    """
    actividades = []
    default_year = int(month[:4])
    default_month = int(month[4:])

    for row in raw_rows:
        if len(row) < 2:
            logger.warning("Fila inválida: %s", row)
            continue

        day_cell = row[0].replace("\n", "").strip()
        text_cell = row[1]

        try:
            _, day_num = day_cell.split()
            day_num = int(day_num)
        except Exception:
            logger.warning("No se pudo parsear día: %s", day_cell)
            continue

        blocks = split_cell_into_activities(text_cell)

        if len(blocks) > 1:
            logger.info("%s contiene %d actividades", day_cell, len(blocks))

        for block in blocks:
            act = parse_activity(
                block,
                day_num=day_num,
                default_year=default_year,
                default_month=default_month,
            )
            if act:
                actividades.append(act)

    actividades.sort(key=sort_key)
    return actividades
