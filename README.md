# 📘 Agenda de actividades de los centros cívicos de Burgos – Scraper, Parser y Visualización

## 🧠 Motivación

El proyecto **Burgos Cívicos** nace de una carencia: la agenda mensual de actividades de los Centros Cívicos del Ayuntamiento de Burgos **no debería necesitar un proyecto externo**.  
La información ya existe y se publica cada mes, pero lo hace en forma de **PDFs estáticos y poco accesibles**, lo que dificulta su uso, búsqueda y reutilización por parte de los ciudadanos.

Este proyecto busca **mejorar la transparencia y accesibilidad** creando un sistema que:
- Descarga los PDFs oficiales del Ayuntamiento.
- Los transforma en datos estructurados y abiertos.
- Permite consultarlos fácilmente por fecha, público, centro o tipo de actividad.

En resumen, **pone a disposición de todos los burgaleses una agenda verdaderamente usable**, algo que debería venir de serie con los datos públicos del Ayuntamiento.

---

## 📑 Índice

- 📘 Burgos Cívicos – Scraper, Parser y Visualización
  - [🧠 Motivación](#-motivación)
  - [🧩 Arquitectura general](#-arquitectura-general)
  - [📁 Estructura del repositorio](#-estructura-del-repositorio)
  - [🕷️ 1. Scraper](#️-1-scraper)
  - [📥 2. Downloader & Parser](#-2-downloader--parser)
  - [🤖 2.4 Parser con IA](#-24-parser-con-ia-ollama--mistral)
  - [🧪 2.5 Testing](#-testing)
  - [🌐 3. Web](#-3-web)
  - [🏛️ Datos fijos: centros cívicos](#️-datos-fijos-centros-cívicos)

---

## 🧩 Arquitectura general

El proyecto se divide claramente en tres grandes bloques, con responsabilidades bien separadas:

- **Scraper** – detección de nuevos PDFs publicados por el Ayuntamiento  
- **Downloader & Parser** – descarga y transformación de PDFs a datos estructurados  
- **Web** – visualización y consulta de las actividades  

Además, existe una carpeta `data/` que actúa como almacén de datos versionado por mes.

---

## 📁 Estructura del repositorio

```
burgos-civicos/
├── src/
│   ├── scraper/ # Descubrimiento de PDFs nuevos
│   │   ├── fetch_page.py
│   │   ├── parse_links.py
│   │   └── main.py
│   │
├── downloader/
│   ├── __init__.py
│   └── download_pdf.py
│
├── parser/
│   ├── __init__.py
│   ├── registry.py           # Plugin registry para todos los cívicos
│   ├── ai_parser.py          # Parser genérico basado en IA (Ollama+Mistral)
│   ├── gamonal_norte/        # Parser específico (regex)
│   │   ├── __init__.py
│   │   ├── extract_raw.py
│   │   ├── parse_raw.py
│   │   └── process_pdf.py
│   └── generic/              # Parser genérico (Camelot+IA) para otros cívicos
│       ├── __init__.py
│       ├── extract_raw.py
│       └── process_pdf.py
|
├── utils/ # Funciones comunes (hash, fechas, schemas…)
│   └── common.py
│
├── data/
│   ├── civicos.json # Datos fijos de los centros cívicos
│   └── yyyymm/ # Datos por mes
│       ├── links.json # Metadatos de PDFs detectados
│       ├── pdfs/ # PDFs descargados
│       │   ├── gamonal_norte.pdf
│       │   └── …
│       ├── actividades_raw_<civico>.json
│       └── actividades.json # Actividades estructuradas finales
│
├── schemas/ # JSON Schemas
│   ├── civicos.schema.json
│   ├── actividades.schema.json
│   └── links.schema.json
│
├── web/ # Frontend (HTML + JS)
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── README.md
└── requirements.txt

```

---

## 🕷️ 1. Scraper

### Responsabilidad

El scraper **NO descarga PDFs ni los procesa**. Su única misión es:

- Descargar la página HTML del Ayuntamiento  
- Detectar los enlaces a los PDFs de agendas mensuales  
- Identificar centro cívico + mes/año de cada PDF  
- Generar un archivo de metadatos mensual  
- Detectar si ese mes ya fue procesado previamente  

### Entrada

URL pública del Ayuntamiento con la agenda de centros cívicos.

### Salida

`data/yyyymm/links.json`

**Ejemplo:**

```json
{
  "meta": {
    "month": "202601",
    "scraped_at": "2025-12-29T11:30:00Z",
    "source": "https://www.aytoburgos.es/..."
  },
  "links": [
    {
      "civico_id": "gamonal_norte",
      "title": "Gamonal Norte – Agenda Enero 2026",
      "url": "...",
      "filename": "...pdf",
      "is_new": true
    },
    {
      "civico_id": "capiscol",
      "title": "Capiscol – Agenda Enero 2026",
      "url": "...",
      "filename": "...pdf",
      "is_new": false
    }
  ]
}
```

### Ejecución

Se ejecuta periódicamente (cron, GitHub Actions, etc.).

**Frecuencia recomendada:**  
Diaria, especialmente últimos y primeros días de mes.

**Lógica clave:**

- Si `data/yyyymm/links.json` no existe → se considera un mes nuevo.  
- Si existe pero el contenido es distinto → se actualiza.  
- Solo en esos casos se dispara el siguiente bloque.

---

## 📥 2. Downloader & Parser

Este bloque solo se ejecuta cuando hay un mes nuevo.

### 2.1 Descarga de PDFs

- Lee `data/yyyymm/links.json`.  
- Descarga cada PDF a:  
  `data/yyyymm/pdfs/<civico>.pdf`.
- Puede usar hash para evitar descargas duplicadas.

### 2.2 Extracción de actividades (RAW)

Cada PDF se procesa según su estructura concreta (Camelot, pdfplumber, heurísticas específicas).

**Resultado:**

Para cada centro cívico:  
`data/yyyymm/actividades_raw_<civico>.json`

**Formato unificado (lista de textos de actividades):**

```json
[
  "(*) La hora del cuento: Carta a Papá Noel. 19 h. Biblioteca familiar: niñ@s de 4 a 7 años",
  "Yoga en parejas. 19:30 h. Sala de encuentro. Público: adultos"
]

```

> Este paso **no interpreta el significado**, solo normaliza el texto.

### 2.3 Parser estructurado

- Toma todas las listas RAW.  
- Aplica el parser semántico.  
- Genera un único archivo consolidado:  
  `data/yyyymm/actividades.json`.

**Características:**

- Todas las actividades con el mismo esquema.
- Agrupadas por ID de centro cívico
- Campos:
  - nombre (valor obligatorio) [string]
  - descripción [string]
  - fecha (valor obligatorio) / fecha_fin  [dd/mm/aaaa]
  - hora / hora_fin  [hh:mm]
  - público (valor obligatorio) [string]
  - lugar [string]
  - requiere inscripción (valor obligatorio) [booleano]
  - edad mínima, máxima [número]
  - precio [número]
- Reglas:
  - Si no hay hora → hora = null, hora_fin = null
  - Si hay rango de fechas:
    - fecha = inicio
    - fecha_fin = fin
  - Si no se detecta lugar, usar null (no string vacío)
  - publico nunca debe ser null

**Validado mediante:**  
`schemas/actividades.schema.json`

**Ejemplo:**
```json
{
  "gamonal_norte": [
    {
      "nombre": "La hora del cuento",
      "descripcion": "Carta a Papá Noel",
      "fecha": "03/12/2025",
      "fecha_fin": null,
      "hora": "19:00",
      "hora_fin": null,
      "requiere_inscripcion": true,
      "lugar": "Biblioteca familiar",
      "publico": "niñ@s de 4 a 7 años",
      "edad_minima": 4,
      "edad_maxima": 7,
      "precio": null
    }
  ]
}
```

---

## 🤖 2.4 Parser con IA (Ollama + Mistral)

El proyecto incluye un **parser basado en IA** que resuelve dos problemas principales:

1. **Formato PDF variable:** Cada cívico puede cambiar la estructura de su PDF mes a mes
2. **Cambios mensuales:** El mismo cívico puede formatear diferente cada mes

### Características

- **Ejecuta localmente:** Usa Ollama + Mistral 7B (sin API remota)
- **Estructura garantizada:** Prompt engineering para output JSON consistente  
- **Normalización:** Limpia formatos de hora, fecha, prefijos (*), etc.
- **Fallback inteligente:** Si existe parser específico lo usa, sino usa IA

### Uso

**Verificar que Ollama está disponible:**
```bash
curl http://localhost:11434/api/tags
```

**Descargar modelo Mistral (primera vez ~4.4GB):**
```bash
ollama pull mistral
```

**Ejecutar orquestrador (procesa automáticamente con IA):**
```bash
python src/orchestrator/main.py 202601
```

### Cívicos actuales

| Cívico | Parser | Método |
|--------|--------|--------|
| `gamonal_norte` | Específico (regex) | Regex pattern matching |
| `rio_vena` | AI | Ollama + Mistral |
| `vista_alegre` | AI | Ollama + Mistral |
| `capiscol` | AI | Ollama + Mistral |
| `san_agustin` | AI | Ollama + Mistral |
| `huelgas` | AI | Ollama + Mistral |
| `san_juan` | AI | Ollama + Mistral |

---

## 🧪 2.5 Testing

### Ubicación de tests

Todos los tests unitarios están en `tests/` (sin scripts adicionales de verificación).

### Ejecutar tests

```bash
.venv/bin/python -m pytest -v
```

---

## 🌐 3. Web

La carpeta `web/` contiene una aplicación estática (**HTML + JS**) que:

- Carga `data/yyyymm/actividades.json`.  
- Muestra por defecto el último mes disponible.  
- Permite:
  - Seleccionar meses anteriores  
  - Filtrar por centro, día, público, horario  
  - Ver detalle completo de una actividad  

> Este bloque no depende de Python.

---

## 🏛️ Datos fijos: centros cívicos

Archivo mantenido manualmente:  
`data/civicos.json`

**Incluye:**

- ID del centro  
- Nombre  
- Dirección  
- Coordenadas  
- Otros metadatos  

**Validado mediante:**  
`schemas/civicos.schema.json`
