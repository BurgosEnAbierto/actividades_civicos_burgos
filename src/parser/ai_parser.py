"""
Parser basado en IA generativa (Ollama + Mistral/Llama)

Este módulo proporciona un parser robusto y generalizable para cualquier
centro cívico, independientemente del formato del PDF.

Ventajas:
- No depende de regexes frágiles
- Se adapta a variaciones de formato mes a mes
- Funciona para múltiples cívicos sin código específico
- Usa modelos locales (sin coste ni latencia de API)

Flujo:
1. extract_raw_ai() → Lee PDF y devuelve [día, texto] (igual que otros)
2. parse_raw_ai() → Toma [día, texto] y llama a IA para parsear
3. Validación contra schema
"""

import json
import logging
import requests
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuración de Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"  # Cambiar a "llama2" si prefieres

# Prompt que instruye al modelo cómo extraer datos estructurados
ACTIVITY_EXTRACTION_PROMPT = """Eres un parser JSON de actividades. DEVUELVE SOLO JSON VÁLIDO.

INSTRUCCIONES:
1. DEVUELVE UN ARRAY DE JSON (incluso si es una sola actividad)
2. CADA JSON DEBE TENER: nombre, descripcion, fecha, fecha_fin, hora, hora_fin, requiere_inscripcion, lugar, publico, edad_minima, edad_maxima, precio
3. DEVUELVE SOLO JSON VÁLIDO - sin markdown, sin explicación, sin comentarios
4. USO DE COMILLAS CORRECTAS: todas las cadenas en COMILLAS DOBLES, nunca comillas simples o caracteres especiales
5. Limpiar asteriscos: quitar "(*)" o "*)" del inicio del nombre
6. FORMATO DE HORAS: "HH:MM" o null (ejemplo: "19:00"). Convertir horas en formato "HH,MM" (con coma) a "HH:MM"
7. FORMATO DE FECHAS: "DD/MM/YYYY" o null. El día viene en contexto (ej: "LUNES 2" = 02/02/2026). Extraer el número.
8. requiere_inscripcion: boolean true/false (true si texto original empieza con "(*)" o contiene "Con inscripción")
9. publico: NUNCA null ni vacío, extraer qué público es. Ejemplos: "adultos", "infantil", "familiar", "juvenil"
10. edades: números (1-120) o null. IMPORTANTE: "18 meses" = edad_minima: 1, NO 18. Los "meses" se convierten dividiendo por 12.
11. precio: número (float) o null. Buscar: "€", "euros", "€ precio", "12,00€" → 12.0

Día: {day}
Mes/Año: {month_year}
Texto: {text}

RESPUESTA VÁLIDA EJEMPLO:
[{{"nombre": "Yoga", "descripcion": "Clase de yoga", "fecha": "17/01/2026", "fecha_fin": null, "hora": "19:00", "hora_fin": "20:00", "requiere_inscripcion": true, "lugar": "Sala A", "publico": "adultos", "edad_minima": null, "edad_maxima": null, "precio": null}}]

AHORA DEVUELVE EL JSON VÁLIDO PARA EL TEXTO ARRIBA (SIN MARKDOWN, SOLO JSON):"""


def check_ollama_health() -> bool:
    """Verifica si Ollama está disponible y el modelo está cargado"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama no disponible: {e}")
        return False


def get_available_models() -> List[str]:
    """Obtiene lista de modelos disponibles en Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        data = response.json()
        return [m.get("name", "").split(":")[0] for m in data.get("models", [])]
    except Exception as e:
        logger.error(f"Error obteniendo modelos: {e}")
        return []


def parse_activity_with_ai(
    day: str,
    text: str,
    month_year: str,
    model: str = OLLAMA_MODEL,
    civico: str = ""
) -> Optional[List[Dict]]:
    """
    Usa Ollama para parsear una actividad/celda.
    
    Args:
        day: Día del mes (ej: "17")
        text: Texto bruto de la actividad
        month_year: Mes y año (ej: "202512")
        model: Modelo de Ollama a usar
        civico: ID del civico para logging (opcional)
    
    Returns:
        Lista de actividades parseadas o None si falla
    """
    
    # Formatear fecha para el prompt
    year = int(month_year[:4])
    month = int(month_year[4:])
    month_year_formatted = f"{month:02d}/{year}"
    
    prompt = ACTIVITY_EXTRACTION_PROMPT.format(
        day=day,
        month_year=month_year_formatted,
        text=text
    )
    
    try:
        civico_str = f" [{civico}]" if civico else ""
        logger.info(f"Enviando a IA (modelo: {model}){civico_str}: día={day}")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,  # Bajo para respuestas consistentes
            },
            timeout=300  # 5 minutos para primera carga y procesamiento
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "response" not in result:
            logger.error("Respuesta sin 'response' key")
            return None
        
        raw_response = result["response"].strip()
        logger.debug(f"Respuesta IA: {raw_response[:200]}...")
        
        # Extrae JSON de la respuesta (puede estar envuelto en markdown)
        json_start = raw_response.find("[")
        json_end = raw_response.rfind("]") + 1
        
        if json_start == -1 or json_end <= json_start:
            logger.warning(f"No se encontró JSON en respuesta: {raw_response[:100]}")
            return None
        
        json_str = raw_response[json_start:json_end]
        
        # Función auxiliar para recuperar JSON con múltiples estrategias
        def parse_json_with_recovery(json_str):
            """Intenta parsear JSON con varias estrategias de recuperación"""
            
            # Estrategia 1: Parseo directo
            try:
                return json.loads(json_str), None
            except json.JSONDecodeError as e:
                first_error = e
            
            # Estrategia 2: Reemplazar comillas simples por dobles
            try:
                json_str_cleaned = json_str.replace("'", '"')
                return json.loads(json_str_cleaned), "reemplazar comillas simples"
            except json.JSONDecodeError:
                pass
            
            # Estrategia 3: Eliminar comas finales
            try:
                json_str_cleaned = json_str.replace(",]", "]").replace(",}", "}")
                return json.loads(json_str_cleaned), "eliminar comas finales"
            except json.JSONDecodeError:
                pass
            
            # Estrategia 4: Escapar newlines y tabs dentro de strings
            try:
                # Reemplazar \n y \t literales dentro de strings por espacios
                json_str_cleaned = json_str.replace("\\n", " ").replace("\\t", " ")
                return json.loads(json_str_cleaned), "escapar newlines/tabs"
            except json.JSONDecodeError:
                pass
            
            # Estrategia 5: Procesar escapes inválidos (ej: \P, \C, etc)
            try:
                # Encontrar todos los escapes inválidos y reemplazarlos por espacio
                json_str_cleaned = re.sub(r'\\[^"\\\n\r\t/bfntu]', ' ', json_str)
                return json.loads(json_str_cleaned), "escapar caracteres inválidos"
            except json.JSONDecodeError:
                pass
            
            # Si todas las estrategias fallan
            return None, first_error
        
        activities, strategy = parse_json_with_recovery(json_str)
        
        if activities is None:
            logger.error(f"JSON inválido de IA en día {day}")
            logger.debug(f"JSON inválido (primeros 300 chars): {json_str[:300]}")
            logger.debug(f"JSON inválido (últimos 300 chars): {json_str[-300:]}")
            return None
        
        if strategy:
            logger.info(f"JSON recuperado usando estrategia: {strategy}")
        
        
        # Asegurar que es una lista
        if not isinstance(activities, list):
            activities = [activities]
        
        # Normalizar y validar cada actividad
        validated = []
        for act in activities:
            if not isinstance(act, dict):
                logger.warning(f"Actividad no es dict: {act}")
                continue
            
            # Verificar campos mínimos antes de normalizar
            if not all(k in act for k in ["nombre", "fecha", "requiere_inscripcion", "publico"]):
                logger.warning(f"Campos mínimos faltantes en: {act}")
                continue
            
            # Normalizar
            act = _normalize_activity(act, day, int(month_year[4:]), int(month_year[:4]))
            
            # Validar después de normalizar
            is_valid, error_msg = _validate_normalized_activity(act)
            if is_valid:
                validated.append(act)
            else:
                logger.warning(f"Validación fallida: {error_msg} - {act.get('nombre', 'sin nombre')}")
        
        return validated if validated else None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error llamando a Ollama: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return None


def _validate_normalized_activity(activity: dict) -> tuple[bool, str]:
    """
    Valida que una actividad normalizada cumpla con nuestro esquema esperado.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        # Campos requeridos
        required_fields = {
            "nombre": str,
            "fecha": str,
            "requiere_inscripcion": bool,
            "publico": str,
        }
        
        for field, expected_type in required_fields.items():
            if field not in activity:
                return False, f"Campo requerido faltante: {field}"
            
            value = activity[field]
            if not isinstance(value, expected_type):
                return False, f"{field}: esperado {expected_type.__name__}, recibido {type(value).__name__}"
            
            if expected_type == str and not value.strip():
                return False, f"{field}: no puede estar vacío"
        
        # Validar formato de fecha: DD/MM/YYYY
        fecha = activity["fecha"].strip()
        if len(fecha) != 10 or fecha[2] != "/" or fecha[5] != "/":
            return False, f"fecha: formato inválido '{fecha}' (esperado DD/MM/YYYY)"
        
        try:
            from datetime import datetime
            datetime.strptime(fecha, "%d/%m/%Y")
        except ValueError:
            return False, f"fecha: fecha inválida '{fecha}'"
        
        # Campos opcionales con tipos específicos
        if activity.get("fecha_fin") is not None:
            fecha_fin = activity["fecha_fin"]
            if not isinstance(fecha_fin, str):
                return False, f"fecha_fin: debe ser string o null, recibido {type(fecha_fin).__name__}"
            if fecha_fin and (len(fecha_fin) != 10 or fecha_fin[2] != "/" or fecha_fin[5] != "/"):
                return False, f"fecha_fin: formato inválido '{fecha_fin}'"
        
        # Validar horas: formato HH:MM o null
        for field in ["hora", "hora_fin"]:
            if activity.get(field) is not None:
                hora = activity[field]
                if not isinstance(hora, str):
                    return False, f"{field}: debe ser string o null, recibido {type(hora).__name__}"
                if hora and not (len(hora) == 5 and hora[2] == ":" and hora[:2].isdigit() and hora[3:].isdigit()):
                    return False, f"{field}: formato inválido '{hora}' (esperado HH:MM)"
        
        # Validar edades: int o null
        for field in ["edad_minima", "edad_maxima"]:
            if activity.get(field) is not None:
                edad = activity[field]
                if not isinstance(edad, int):
                    return False, f"{field}: debe ser int o null, recibido {type(edad).__name__}"
                if edad < 0 or edad > 120:
                    return False, f"{field}: edad inválida {edad}"
        
        # Validar precio: float/int o null
        if activity.get("precio") is not None:
            precio = activity["precio"]
            if not isinstance(precio, (int, float)):
                return False, f"precio: debe ser number o null, recibido {type(precio).__name__}"
            if precio < 0:
                return False, f"precio: no puede ser negativo"
        
        # Validar booleans
        if not isinstance(activity.get("requiere_inscripcion"), bool):
            return False, f"requiere_inscripcion: debe ser boolean"
        
        # Campos de texto opcionales
        for field in ["descripcion", "lugar"]:
            if activity.get(field) is not None:
                value = activity[field]
                if not isinstance(value, str):
                    return False, f"{field}: debe ser string o null, recibido {type(value).__name__}"
        
        return True, ""
    
    except Exception as e:
        return False, f"Error interno en validación: {str(e)}"


def _normalize_activity(activity: dict, day: str, month: int, year: int) -> dict:
    """
    Normaliza y limpia una actividad parseada por IA.
    
    Correcciones:
    - Asegura que los campos son strings (la IA a veces devuelve listas)
    - Elimina * o (*) del inicio del nombre
    - Normaliza horas (19H -> 19:00)
    - Asegura formato DD/MM/YYYY de fechas
    - Valida que publico no sea vacío
    - Convierte edad_minima/maxima a int si es necesario
    """
    
    # Función auxiliar para convertir campos a string
    def ensure_string(value, default=""):
        if value is None:
            return default
        if isinstance(value, list):
            # Si es una lista, unir con ", "
            return ", ".join(str(v).strip() for v in value if v).strip()
        return str(value).strip()
    
    # Asegurar que campos clave son strings
    for field in ["nombre", "fecha", "hora", "hora_fin", "publico", "descripcion", "lugar"]:
        if field in activity:
            activity[field] = ensure_string(activity[field])
    
    # Limpiar nombre
    nombre = activity.get("nombre", "").strip()
    for prefix in ["(*)", "(*", "*)", "* "]:
        if nombre.startswith(prefix):
            nombre = nombre[len(prefix):].strip()
    activity["nombre"] = nombre
    
    # Normalizar hora
    for field in ["hora", "hora_fin"]:
        hora = activity.get(field)
        if hora and isinstance(hora, str):
            hora = hora.upper().strip()
            # Si está vacío después de strip, establecer a None
            if not hora:
                activity[field] = None
                continue
            
            # Convertir "19H" o "19.30" a "19:00" o "19:30"
            if "H" in hora:
                hora = hora.replace("H", "").strip()
            if "." in hora:
                hora = hora.replace(".", ":")
            # Si es solo dos dígitos, agregar :00
            if ":" not in hora and len(hora) <= 2:
                hora = f"{hora}:00"
            # Validar formato HH:MM
            try:
                if len(hora.split(":")) == 2:
                    h, m = [x.strip() for x in hora.split(":")]
                    # Validar que h y m no sean vacíos
                    if not h or not m:
                        activity[field] = None
                        continue
                    h, m = int(h), int(m)
                    if 0 <= h <= 23 and 0 <= m <= 59:
                        activity[field] = f"{h:02d}:{m:02d}"
                    else:
                        activity[field] = None
                else:
                    activity[field] = None
            except (ValueError, AttributeError):
                activity[field] = None
        else:
            # Si no hay hora, establecer a None (no string vacío)
            activity[field] = None
    
    # Asegurar fecha en formato DD/MM/YYYY
    fecha = activity.get("fecha", "").strip()
    if fecha and len(fecha) == 10 and fecha[2] == "/" and fecha[5] == "/":
        try:
            parts = fecha.split("/")
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            
            # Validar que año sea razonable (1900-2100)
            if y < 1900 or y > 2100:
                # Año está fuera de rango, usar contexto
                activity["fecha"] = f"{day:02d}/{month:02d}/{year:04d}"
            # Caso 1: El primer número > 12, debe ser DD (formato correcto)
            elif d > 12 and 1 <= m <= 12:
                activity["fecha"] = f"{d:02d}/{m:02d}/{y:04d}"
            # Caso 2: El segundo número > 12, debe ser DD (invertir)
            elif 1 <= d <= 12 and m > 12:
                activity["fecha"] = f"{m:02d}/{d:02d}/{y:04d}"
            # Caso 3: Ambos son 1-12, usar el contexto
            elif 1 <= d <= 12 and 1 <= m <= 12:
                # El día esperado es importante: si coincide con d, es DD/MM
                # Si coincide con m, es MM/DD (invertir)
                day_int = int(day)
                month_int = int(month)
                
                if d == day_int:
                    # Formato correcto DD/MM/YYYY
                    activity["fecha"] = f"{d:02d}/{m:02d}/{y:04d}"
                elif m == day_int:
                    # Formato invertido MM/DD/YYYY, invertir
                    activity["fecha"] = f"{m:02d}/{d:02d}/{y:04d}"
                elif d == month_int:
                    # Parece que el primer número es el mes, invertir
                    activity["fecha"] = f"{m:02d}/{d:02d}/{y:04d}"
                elif m == month_int:
                    # El segundo número coincide con el mes esperado, mantener
                    activity["fecha"] = f"{d:02d}/{m:02d}/{y:04d}"
                else:
                    # Ninguno coincide perfectamente, pero preferir que el mes sea el contexto
                    # y el día sea razonable (1-31)
                    if m == month_int and 1 <= d <= 31:
                        activity["fecha"] = f"{d:02d}/{m:02d}/{y:04d}"
                    elif d == month_int and 1 <= m <= 31:
                        activity["fecha"] = f"{m:02d}/{d:02d}/{y:04d}"
                    else:
                        # Asumir DD/MM/YYYY
                        activity["fecha"] = f"{d:02d}/{m:02d}/{y:04d}"
            else:
                # Formato inválido, usar contexto
                activity["fecha"] = f"{day:02d}/{month:02d}/{year:04d}"
        except (ValueError, IndexError):
            # Si no se puede parsear, usar el contexto del mes/día
            activity["fecha"] = f"{day:02d}/{month:02d}/{year:04d}"
    elif not fecha:
        # Si no hay fecha, usar el contexto
        activity["fecha"] = f"{day:02d}/{month:02d}/{year:04d}"
    else:
        # Formato inesperado, usar el contexto
        activity["fecha"] = f"{day:02d}/{month:02d}/{year:04d}"
    
    # Validar publico no sea vacío
    publico = activity.get("publico", "").strip()
    if not publico:
        publico = "Sin especificar"
    activity["publico"] = publico
    
    # Convertir edades a int - extraer número de strings como "18 meses" o "(+5años)"
    for field in ["edad_minima", "edad_maxima"]:
        edad = activity.get(field)
        if edad is not None and not isinstance(edad, int):
            try:
                # Convertir a string y extraer primer número encontrado
                edad_str = str(edad).strip()
                if edad_str:
                    # Buscar números (pueden tener + o -)
                    numbers = re.findall(r'[+-]?\d+', edad_str)
                    if numbers:
                        age_value = int(numbers[0])
                        # Validar que sea razonable (0-150)
                        if 0 <= age_value <= 150:
                            activity[field] = age_value
                        else:
                            activity[field] = None
                    else:
                        activity[field] = None
                else:
                    activity[field] = None
            except (ValueError, TypeError, AttributeError):
                activity[field] = None
    
    # Convertir precio a float/int si es necesario
    precio = activity.get("precio")
    if precio is not None and not isinstance(precio, (int, float)):
        try:
            # Limpiar strings de espacios y caracteres comunes
            precio_str = str(precio).strip().replace("€", "").strip()
            if precio_str:
                # Extraer número del string (puede haber texto como "5 euros")
                numbers = re.findall(r'\d+\.?\d*', precio_str)
                if numbers:
                    activity["precio"] = float(numbers[0])
                else:
                    activity["precio"] = None
            else:
                activity["precio"] = None
        except (ValueError, TypeError, AttributeError):
            activity["precio"] = None
    
    # Limpiar campos opcionales: convertir strings vacíos a None
    optional_fields = ["descripcion", "lugar", "fecha_fin"]
    for field in optional_fields:
        value = activity.get(field)
        if isinstance(value, str) and not value.strip():
            activity[field] = None
    
    return activity


def parse_raw_ai(raw_rows: List[List[str]], *, month: str, civico: str = "") -> List[Dict]:
    """
    Parsea filas raw usando IA.
    
    Args:
        raw_rows: Lista de [día, texto] extraído del PDF
        month: Mes en formato YYYYMM
        civico: ID del civico para logging (opcional)
    
    Returns:
        Lista de actividades estructuradas
    """
    actividades = []
    
    # Verificar Ollama disponible
    if not check_ollama_health():
        logger.error("Ollama no está disponible. Instálalo con: ollama serve")
        logger.error(f"Descarga un modelo: ollama pull {OLLAMA_MODEL}")
        return []
    
    for row in raw_rows:
        if len(row) < 2:
            logger.warning(f"Fila inválida: {row}")
            continue
        
        day_cell = row[0].strip()
        text_cell = row[1].strip()
        
        # Extraer número de día
        try:
            # Formato: "MIERCOLES 17" o similar
            day_parts = day_cell.split()
            day_num = day_parts[-1]  # Último elemento es el día
        except Exception as e:
            civico_str = f" [{civico}]" if civico else ""
            logger.warning(f"No se pudo extraer día{civico_str} de '{day_cell}': {e}")
            continue
        
        # Llamar a IA
        parsed_activities = parse_activity_with_ai(
            day=day_num,
            text=text_cell,
            month_year=month,
            civico=civico
        )
        
        if parsed_activities:
            actividades.extend(parsed_activities)
        else:
            civico_str = f" [{civico}]" if civico else ""
            logger.warning(f"IA no pudo parsear{civico_str}: {text_cell[:50]}")
    
    # Validar y filtrar actividades con validación completa
    valid_activities = []
    civico_str = f" [{civico}]" if civico else ""
    for act in actividades:
        is_valid, error_msg = _validate_normalized_activity(act)
        if is_valid:
            valid_activities.append(act)
        else:
            logger.warning(f"Actividad descartada{civico_str}: {error_msg} - {act.get('nombre', 'sin nombre')}")
    
    # Ordenar por fecha
    valid_activities.sort(key=_sort_key)
    return valid_activities


def _sort_key(activity: dict):
    """Clave de ordenamiento por fecha y hora"""
    try:
        fecha_str = activity.get("fecha", "").strip()
        # Validar formato DD/MM/YYYY
        if not fecha_str or len(fecha_str) != 10:
            return datetime.max
        
        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
        if activity.get("hora"):
            try:
                h, m = activity["hora"].split(":")
                return dt.replace(hour=int(h), minute=int(m))
            except (ValueError, AttributeError):
                return dt
        return dt
    except (ValueError, AttributeError, TypeError):
        return datetime.max


def extract_raw_ai(pdf_path: Path) -> List[List[str]]:
    """
    Extrae tablas de PDF igual que con Camelot.
    
    Nota: Esta función es agnóstica al cívico porque asume que todos
    devuelven un formato común [día, texto].
    
    Para ahora, reutiliza la lógica de Gamonal, pero en el futuro
    podría usar OCR u otro método.
    """
    import camelot
    
    logger.info(f"Extrayendo tablas (Camelot): {pdf_path.name}")
    
    tables = camelot.read_pdf(str(pdf_path), pages="all")
    
    if not tables:
        logger.warning(f"No se detectaron tablas en {pdf_path.name}")
        return []
    
    rows = []
    
    for table in tables:
        data = table.df.values.tolist()
        
        for row in data:
            if len(row) < 2:
                continue
            
            dia = row[0].strip()
            texto = row[1].replace("\n", "").strip()
            
            if dia:
                rows.append([dia, texto])
    
    logger.debug(f"Filas raw extraídas: {len(rows)}")
    return rows
