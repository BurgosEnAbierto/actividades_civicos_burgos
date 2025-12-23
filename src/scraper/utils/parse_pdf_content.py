import re
from datetime import datetime
import calendar
from pathlib import Path
import camelot

# Regexes para extraer información

# meses españoles
MONTHS = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}

# rangos tipo "19-21 h" o "19 - 21 h"
RE_HOUR_RANGE = re.compile(
    r"(\d{1,2}(?::\d{2}|.\d{2})?)\s*-\s*(\d{1,2}(?::\d{2}|.\d{2})?)\s*h\.?",
    re.IGNORECASE
)

# hora simple
RE_HOUR_SINGLE = re.compile(
    r"(\d{1,2}(?::\d{2}|.\d{2})?)\s*h\.?",
    re.IGNORECASE
)

# público habitual
RE_PUBLIC = re.compile(r"P[úu]blico:\s*(.*)", re.IGNORECASE)

# público cuando ponen solo ":" sin “Público:”
RE_PUBLIC_ALT = re.compile(
    r":\s*(adultos?|niñ[^\s]+.*|famil[^\s]+.*)$",
    re.IGNORECASE
)

# rango fechas "9 al 16 de diciembre"
RE_DATE_RANGE = re.compile(
    r"(\d{1,2})\s+al\s+(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚñ]+)",
    re.IGNORECASE
)

# Días de la semana en español → weekday()
DAY_MAP = {
    "LUNES": 0, "MARTES": 1,
    "MIERCOLES": 2, "MIÉRCOLES": 2,
    "JUEVES": 3, "VIERNES": 4,
    "SABADO": 5, "SÁBADO": 5,
    "DOMINGO": 6,
}


def starts_new_activity(line):
    l = line.strip()
    if l.startswith("(*)"):
        return True
    if l.startswith("*)"):
        return True
    if l.startswith("(") and "*)" in l:
        return True
    # actividad sin (*)
    # TODO
    return False

def split_cell_into_activities(cell_text):
    """
    Divide una celda potencialmente con varias actividades en textos individuales.

    Reglas:
    - Una actividad nueva empieza cuando aparece:
        * '(*' al inicio de línea
        * '*)' al inicio de línea
        * '(' al inicio de línea y contiene '*)'
    - Agrupa líneas hasta encontrar el inicio de la siguiente actividad.
    """

    # sustituir (\n*) por (*)
    cell_text = cell_text.replace("(\n*)", "(*)", 1)

    # normalización de saltos de línea
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

def process_pdf(path: Path) -> dict:
    """Procesa un PDF usando camelot-py para extraer tablas.
    Devuelve una lista de filas unificadas provenientes de todas las tablas.
    Cada celda tendrá los saltos de línea eliminados.
    """

    print(f" → Procesando PDF con Camelot: {path.name}")


    try:
        tables = camelot.read_pdf(path)
    except Exception as e:
        print(f"⚠ Error al leer PDF con Camelot: {e}")
        return {"raw_rows": [], "error": str(e)}


    rows = []


    for table in tables:
        df = table.df
        for _, row in df.iterrows():
            rows.append(row)

    return rows


def normalize_hour(h):
    """Convierte 19, 19., 19.00, 19:00 en 19:00"""
    h = h.replace(".", ":")
    if ":" not in h:
        h = f"{h}:00"
    return h

def parse_activity(activity_text, day_name, day_num, default_year, default_month):
    warnings = []

    text = activity_text.strip()

    # --- Fecha base ---
    try:
        dt = datetime(default_year, default_month, day_num)
    except ValueError:
        warnings.append(f"WARNING: fecha inválida: {day_name} {day_num}")
        return None

    fecha = dt.strftime("%d/%m/%Y")
    fecha_fin = None

    # --- Inscripción ---
    requiere = text.startswith("(*)")
    if requiere:
        text = text.replace("(*)", "", 1).strip()

    # --- Rango de fechas (9 al 16 de X) ---
    mdate = RE_DATE_RANGE.search(text)
    if mdate:
        d1, d2, month_name = mdate.groups()
        month_name = month_name.upper()
        if month_name in MONTHS:
            try:
                fecha_fin = datetime(
                    default_year, MONTHS[month_name], int(d2)
                ).strftime("%d/%m/%Y")
            except ValueError:
                warnings.append(f"WARNING: fecha_fin inválida: {text}")

    # --- Horas ---
    hora = hora_fin = None
    hora_match = None
    name_end = None

    # eliminar rangos de fechas antes de buscar horas
    text_for_hours = text
    if mdate:
        text_for_hours = (
            text[: mdate.start()] + text[mdate.end():]
        )

    # rango horario REAL: requiere ':' o '.' o 'h'
    mrange = re.search(
        r"(\d{1,2}(?:[:.]\d{2})?)\s*-\s*(\d{1,2}(?:[:.]\d{2})?)\s*h?",
        text_for_hours,
        re.IGNORECASE,
    )

    if mrange and (
        ":" in mrange.group(1)
        or ":" in mrange.group(2)
        or "." in mrange.group(1)
        or "." in mrange.group(2)
        or "h" in mrange.group(0).lower()
    ):
        hora = normalize_hour(mrange.group(1))
        hora_fin = normalize_hour(mrange.group(2))
        hora_match = mrange
        name_end = mrange.start()
    else:
        msingle = re.search(
            r"(\d{1,2}(?:[:.]\d{2})?)\s*h",
            text_for_hours,
            re.IGNORECASE,
        )
        if msingle:
            hora = normalize_hour(msingle.group(1))
            hora_fin = None
            hora_match = msingle
            name_end = msingle.start()
        elif not mdate:
            warnings.append(f"WARNING: sin hora: {activity_text}")

    # --- Nombre ---
    # Nota: si hay rango de fechas y no hay hora, el nombre acaba antes del rango de fechas
    if name_end is not None:
        nombre = text[:name_end]
    elif mdate:
        nombre = text[: mdate.start()]
    else:
        nombre = text

    nombre = nombre.strip().rstrip(".")

    # --- Público ---
    publico = None
    mpub = RE_PUBLIC.search(text)
    if mpub:
        publico = mpub.group(1).strip()
    else:
        if ":" in text:
            publico = text.split(":")[-1].strip()

    if not publico:
        warnings.append(f"WARNING: sin público: {activity_text}")

    # --- Lugar ---
    lugar = None

    if hora_match:
        fragment = text[hora_match.end():]
    elif mdate and "Horario de" in text:
        fragment = text.split("Horario de", 1)[1]
    else:
        fragment = None

    if fragment:
        if mpub:
            fragment = fragment[: mpub.start() - (len(text) - len(fragment))]

        if ":" in fragment:
            fragment = fragment.rsplit(":", 1)[0]

        lugar = fragment.strip(" .:")

    if not lugar:
        warnings.append(f"WARNING: lugar no detectado en: {activity_text}")

    return {
        "fecha": fecha,
        "fecha_fin": fecha_fin,
        "requiere_inscripcion": requiere,
        "nombre": nombre,
        "hora": hora,
        "hora_fin": hora_fin,
        "lugar": lugar,
        "publico": publico,
        "warnings": warnings,
    }

def parse_dt(a):
    try:
        return datetime.strptime(a["fecha"], "%d/%m/%Y")
    except:
        return datetime.max


def sort_key(a):
    try:
        dt = datetime.strptime(a["fecha"], "%d/%m/%Y")
        if a.get("hora"):
            h, m = a["hora"].split(":")
            return dt.replace(hour=int(h), minute=int(m))
        return dt
    except Exception:
        return datetime.max

def parse_activities(raw_rows):
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

    now = datetime.now()
    default_year = now.year
    default_month = now.month

    for row in raw_rows:
        if len(row) < 2:
            print(f"WARNING: fila inválida (menos de 2 columnas): {row}")
            continue

        row[0] = row[0].replace("\n", "")
        day_cell = row[0].strip()
        text_cell = row[1]

        # --- Extraer día de la semana y número ---
        try:
            parts = day_cell.split()
            day_name = parts[0].upper()
            day_num = int(parts[1])
        except Exception:
            print(f"WARNING: no se pudo parsear el día en fila: {row}")
            continue

        # --- Separar múltiples actividades dentro de la celda ---
        activity_texts = split_cell_into_activities(text_cell)

        if len(activity_texts) > 1:
            print(
                f"INFO: {day_cell} contiene {len(activity_texts)} actividades"
            )

        # --- Parsear cada actividad individual ---
        for activity_text in activity_texts:
            act = parse_activity(
                activity_text=activity_text,
                day_name=day_name,
                day_num=day_num,
                default_year=default_year,
                default_month=default_month,
            )

            if len(act["warnings"]) > 0:   
                print(
                    f"WARNINGS ({len(act["warnings"])}) en {day_cell} - {activity_text}"
                )
                for warning in act["warnings"]:
                    print(f"W: {warning}")

            if act:
                actividades.append(act)

    actividades.sort(key=sort_key)
    return actividades