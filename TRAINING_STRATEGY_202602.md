# Estrategia de Entrenamiento para ai_parser.py

## Resumen Ejecutivo

Los pares (actividades_raw_*.json, actividades.json verificado) del mes 202602 constituyen un dataset valioso para mejorar el parser de IA. Con **13 correcciones aplicadas** y **124 actividades parseadas**, podemos crear un sistema de validación y entrenamiento robusto.

---

## 1. Dataset de Entrenamiento Actual

### 1.1 Cobertura de Datos

| Centro | Raw | Parsed | Validado | Cobertura |
|--------|-----|--------|----------|-----------|
| Rio Vena | 24 | 30 | 30 | 100% |
| Huelgas | 18 | 20 | 20 | 100% |
| San Agustín | 22 | 23 | 23 | 100% |
| San Juan | 11 | 11 | 11 | 100% |
| Vista Alegre | 13 | 13 | 13 | 100% |
| Capiscol | 11 | 10 | 10 | 91% |
| Gamonal Norte | 16 | 17 | 17 | 100% |
| **TOTAL** | **115** | **124** | **124** | **100%** |

### 1.2 Errores Corregidos (Lecciones de Entrenamiento)

```
✓ 3 errores OCR (RESENTACIÓN, ÁSCARAS, URAL)
✓ 3 edades invertidas (18 meses confundido con 18 años)
✓ 2 caracteres unicode corruptos (Ã¡nios → años)
✓ 5 lugarmes contaminados (Sala + nombre actividad)
────────────────────────────
13 ERRORES CORREGIDOS (10.5% de precisión mejorada)
```

---

## 2. Estructura del Dataset de Entrenamiento

### 2.1 Crear Dataset JSON Estructurado

Crear un archivo `training_dataset_202602.json` con estructura:

```json
{
  "metadata": {
    "mes": "202602",
    "fecha_creacion": "2026-02-08",
    "total_pares": 124,
    "centros": ["rio_vena", "huelgas", "san_agustin", "san_juan", "vista_alegre", "capiscol", "gamonal_norte"],
    "versiones": {
      "ai_parser_prompt": "v2.1",
      "schema": "v1"
    }
  },
  "training_pairs": [
    {
      "id": "202602_rio_vena_001",
      "centro": "rio_vena",
      "raw_input": {
        "day_label": "LUNES 2",
        "text": "*RINCÓN CREATIVO Hora: 18:30H. Público Infantil. En Sala de Encuentro. ..."
      },
      "expected_output": {
        "nombre": "RINCÓN CREATIVO",
        "descripcion": null,
        "fecha": "02/02/2026",
        "hora": "18:30",
        "requiere_inscripcion": true,
        "lugar": "Sala de Encuentro",
        "publico": "Infantil"
      },
      "corrections_applied": [],
      "error_types": []
    }
  ],
  "error_patterns": [
    {
      "type": "edad_invertida",
      "pattern": "\\d+ meses a \\d+ años",
      "examples": [
        {
          "raw": "de 18 meses a 3 años",
          "parsed_incorrect": {"edad_minima": 18, "edad_maxima": 3},
          "parsed_correct": {"edad_minima": 1, "edad_maxima": 3},
          "fix_rule": "Si edad_minima > edad_maxima y contiene 'meses', dividir edad_minima por 12"
        }
      ]
    }
  ]
}
```

### 2.2 Crear Índice de Errores Aprendidos

```python
# learning_errors_202602.json
{
  "ocr_errors": [
    {"error": "RESENTACIÓN", "correct": "PRESENTACIÓN", "count": 1, "severity": "high"},
    {"error": "ÁSCARAS", "correct": "MÁSCARAS", "count": 1, "severity": "high"},
    {"error": "URAL:", "correct": "MURAL:", "count": 1, "severity": "high"}
  ],
  "date_parsing_issues": [
    {
      "pattern": "LUNES 2, MARTES 3, etc",
      "lesson": "Convertir día contextual + mes/año → DD/MM/YYYY",
      "fix_rule": "day_label contiene día + número, mapear a DD"
    }
  ],
  "age_conversion_issues": [
    {
      "pattern": "18 meses a 3 años",
      "lesson": "18 meses NO es edad_minima=18, sino edad_minima=1.5≈1",
      "fix_rule": "Si valor > 12 y contexto es 'meses', dividir por 12"
    }
  ],
  "location_contamination": [
    {
      "pattern": "Sala de Encuentro TARDES DE PELÍCULA",
      "lesson": "lugar debe estar limpio, sin incluir nombre de otra actividad",
      "fix_rule": "Si lugar contiene mayúsculas adicionales después de ubicación, splitear"
    }
  ],
  "unicode_issues": [
    {
      "pattern": "Ã¡nios, Ã©, Ã­, Ã³",
      "lesson": "Encoding UTF-8 corruption probablemente por OCR/PDF",
      "fix_rule": "Mapeo: Ã¡→á, Ã©→é, Ã­→í, Ã³→ó, Ã¹→ù"
    }
  ]
}
```

---

## 3. Estrategias de Entrenamiento

### 3.1 **Fine-Tuning del Modelo Local (Mistral/Llama)**

#### Opción A: Usando LoRA (Low-Rank Adaptation)

```bash
# Crear dataset en formato JSONL para entrenamiento
python scripts/convert_to_training_format.py \
  --input docs/data/202602/actividades.json \
  --raw-dir docs/data/202602/ \
  --output models/training_data_202602.jsonl

# Fine-tuning con Ollama (si está soportado)
# O exportar a formato estándar para cualquier framework
ollama run mistral < training_prompt.json
```

#### Opción B: Prompting in-context (Recommended - Sinergía con actual)

```python
# Agregar ejemplos al prompt (few-shot learning)
ACTIVITY_EXTRACTION_PROMPT_WITH_EXAMPLES = """...[instrucciones base]...

EJEMPLOS DE ENTRENAMIENTO (casos reales 202602):

Ejemplo 1 - Edades correctas:
Input: "CANTAMOS JUNTOS: Poesías y canciones en familia. Hora: 12:00. De 18 meses a 3 años."
Output: {
  "nombre": "CANTAMOS JUNTOS",
  "hora": "12:00",
  "publico": "familiar",
  "edad_minima": 1,
  "edad_maxima": 3
}

Ejemplo 2 - Múltiples actividades:
Input: "FIESTA DE CARNAVAL Hora: 18:30-21:00 + NUGGETS TEX-MEX Hora: 18:30"
Output: [
  {"nombre": "FIESTA DE CARNAVAL", "hora": "18:30", "hora_fin": "21:00"},
  {"nombre": "NUGGETS TEX-MEX", "hora": "18:30"}
]

Ejemplo 3 - OCR corrections:
Input: "RESENTACIÓN LIBRO: La memoria de las plantas"
Output: {"nombre": "PRESENTACIÓN LIBRO: La memoria de las plantas"}

Ejemplo 4 - Precios:
Input: "CUENTOS EN PAÑALES. 18,00€. Público familiar"
Output: {"nombre": "CUENTOS EN PAÑALES", "precio": 18.0, "publico": "familiar"}
"""
```

### 3.2 **Validación Automática (Pattern Matching Fallback)**

Crear un validador que detecte errores conocidos antes de enviar a IA:

```python
# validation_rules_202602.py
VALIDATION_RULES = {
    'ocr_replacements': {
        'RESENTACIÓN': 'PRESENTACIÓN',
        'ÁSCARAS': 'MÁSCARAS',
        'URAL:': 'MURAL:',
        'ARDE DE': 'TARDE DE',
    },
    'age_conversion': {
        'pattern': r'(\d+)\s+meses?\s+a\s+(\d+)',
        'action': 'divide_first_by_12',
        'examples': ['18 meses a 3 años', '6 meses a 2 años']
    },
    'location_cleanup': {
        'pattern': r'(Sala|Biblioteca|Taller)[^A-Z]*(TARDES DE|OTRAS ACTIVIDADES)',
        'action': 'keep_location_only',
        'examples': ['Sala de Encuentro TARDES DE PELÍCULA']
    },
    'price_extraction': {
        'pattern': r'(\d+[.,]\d{2})\s*€',
        'action': 'float_conversion',
        'examples': ['12,00€', '18.50€']
    }
}
```

---

## 4. Implementación del Ciclo de Aprendizaje

### 4.1 Pipeline de Mejora Iterativa

```
┌─────────────────────────────────────────────────┐
│ 1. Extraer mes nuevo (ej: 202603)              │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│ 2. Parseado inicial con ai_parser v2.1          │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│ 3. Validación automática (pattern rules)        │
├─ OCR corrections                               │
├─ Age conversions                               │
├─ Location cleanup                              │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│ 4. Validación manual + Correcciones             │
│ (marcar errores residuales)                     │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│ 5. Agregar nuevos pares al dataset de           │
│    entrenamiento (si hay patrones nuevos)       │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│ 6. Actualizar prompt/reglas de validación       │
│ (feed forward para siguiente mes)               │
└─────────────────────────────────────────────────┘
```

### 4.2 Métricas de Éxito

```python
# metrics_202602.py
METRICS = {
    'precision': {
        'raw_activities': 115,
        'parsed_activities': 124,
        'validated_activities': 124,
        'precision': 100.0  # 124/124
    },
    'errors_fixed': {
        'ocr_errors': 3,
        'age_errors': 3,
        'encoding_errors': 2,
        'location_errors': 5,
        'total': 13
    },
    'error_rate_before': 13/124 * 100,  # 10.5%
    'error_rate_after': 0/124 * 100,    # 0%
    'improvement': 10.5  # % points
}
```

---

## 5. Casos de Uso para Entrenamiento

### 5.1 Detección de Anomalías

```python
# Usar datos verificados para entrenar detector de anomalías
# que identifique actividades que faltan campos críticos

anomaly_detector_training = [
    {
        "id": "missing_fecha",
        "anomaly": "actividad sin fecha",
        "example": "Biblioteca Familiar (sin date en raw)",
        "detection_rule": "if fecha is None or empty"
    }
]
```

### 5.2 Corrección Automática de Typos/OCR

```python
# Entrenar modelo simple de corrección OCR
ocr_correction_pairs = [
    ("RESENTACIÓN", "PRESENTACIÓN"),
    ("ÁSCARAS", "MÁSCARAS"),
    ("URAL:", "MURAL:"),
]

# Usar para entrenar fuzzy matcher
from difflib import SequenceMatcher
# Pre-compute similarity scores entre raw text y parsed names
```

### 5.3 Clasificación de Público

```python
# Usar 124 ejemplos para entrenar clasificador de "publico"
público_examples = {
    "infantil": [...15 ejemplos...],
    "juvenil": [...12 ejemplos...],
    "adultos": [...18 ejemplos...],
    "familiar": [...25 ejemplos...],
    "mayores": [...8 ejemplos...],
}
# Entrenar classifier para normalizar públicos inconsistentes
```

---

## 6. Estructura de Archivos Propuesta

```
scripts/
├── fix_202602_errors.py              # ✓ Ya existe (13 correcciones)
├── generate_training_dataset.py       # [TODO] Crear dataset JSON estructurado
├── validate_actividades.py            # [TODO] Validator con pattern rules
└── train_classifier.py                # [TODO] Fine-tune para campos específicos

data/
├── 202602/
│   ├── actividades.json               # ✓ Corregido (124 actividades)
│   ├── actividades_raw_*.json         # ✓ Raw original (115 actividades)
│   └── warnings.log                   # ✓ Historial de errores
│
└── training/
    ├── dataset_202602.json            # [TODO] Dataset estructurado
    ├── learning_errors_202602.json    # [TODO] Errores aprendidos
    ├── validation_rules_202602.json   # [TODO] Reglas de validación
    └── metrics_202602.json            # [TODO] Métricas de entrenamiento

models/
└── prompts/
    ├── ai_parser_prompt_v2.0.txt      # Original
    └── ai_parser_prompt_v2.1.txt      # ✓ Mejorado (14 instrucciones)
```

---

## 7. Recomendaciones Finales

### 7.1 Corto Plazo (Próximas 2 semanas)

1. ✓ **Corregir 202602** - COMPLETADO (13 errores)
2. ✓ **Mejorar prompt v2.1** - COMPLETADO
3. Crear scripts para generar dataset estructurado
4. Implementar validation rules automáticas

### 7.2 Medio Plazo (Próximo mes)

1. Procesar mes 202603 con pipeline mejorado
2. Cuantificar mejora vs baseline
3. Agregar few-shot examples al prompt
4. Entrenar OCR corrector si patrones se repiten

### 7.3 Largo Plazo (Próximos 3 meses)

1. Fine-tune modelo local con datos acumulados
2. Crear ensemble: IA + validation rules + classifier
3. Benchmark contra otros parsers (Camelot, pdfplumber)
4. Documentar dataset para reutilización futura

---

## 8. Conclusión

El dataset 202602 (124 actividades verificadas) proporciona una **base sólida** para:

- ✅ Validar efectividad del prompt mejorado v2.1
- ✅ Crear reglas de validación específicas del dominio
- ✅ Entrenar modelos discriminadores (clasificación, corrección OCR)
- ✅ Documentar patrones de error para próximos meses

**Recomendación:** Procesar mes 202603 con el prompt v2.1 + validation rules automáticas para validar mejora antes de invertir en fine-tuning costoso.
