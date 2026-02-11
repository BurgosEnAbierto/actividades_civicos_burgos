# Análisis de Precisión - actividades.json (202602)

## Problemas Detectados

### 1. **RINCÓN CREATIVO - Fecha incompleta (2/2026)**
- **Raw**: `*RINCÓN CREATIVO Hora: 18:30H. Público Infantil. En Sala de Encuentro. TARDES DE PELICULA: ...`
- **Problema**: IA parseó fecha como `2/2026` (sin día)
- **Causa**: El raw no especifica el día claramente. El raw dice "LUNES 2" pero la IA interpretó solo "2"
- **Solución**: La IA debe inferir el día del contexto. Aquí "LUNES 2" significa 02/02/2026 (segundo lunes del mes)
- **Parseada correctamente**: Sí, está en actividades.json como "02/02/2026"

### 2. **CUENTOS EN PAÑALES - JSON inválido en día 12**
- **Raw**: `(*) Cuentos en pañales. 18:00 h. Público familiar (1 y 3 años + adulto)`
- **Problema**: IA falló al generar JSON válido
- **Causa**: Posiblemente quiso incluir el símbolo "*" en el JSON o tuvo issue con comillas
- **Status**: No parseada - PÉRDIDA DE ACTIVIDAD

### 3. **Fechas con formato incompleto "02/2026"**
- **Problema**: Múltiples actividades con fecha incompleta
- **Causa**: IA extrae mes/año del prompt pero no extrae correctamente el día del texto raw
- **Ejemplos**: "Guía de Lectura", "Día: telefónicamente"

### 4. **Título cortado**
- **Raw**: `Guía de Lectura y Centro de Interés: "Una mente Maravillosa"`
- **Parseada como**: `Guña de Lectura y Centro de Interés: "Una mente Maravillosa"`
- **Problema**: Hay un error de OCR en el raw (`Guña` en lugar de `Guía`)

### 5. **Biblioteca Familiar - Fecha vacía**
- **Problema**: Una actividad se parseó sin fecha
- **Causa**: El raw probablemente no especifica claramente la fecha

### 6. **Múltiples actividades en un mismo día**
- **Raw Day 28**: Contiene 3 actividades separadas: MAGIA FAMILIAR + NUGGETS TEX-MEX + HORA DEL CUENTO
- **Status**: Parseadas correctamente como 3 actividades separadas

## Estadísticas por Centro

| Centro | Raw | Parsed | Delta |
|--------|-----|--------|-------|
| Rio Vena | 24 | 30 | +6 |
| Huelgas | 18 | 20 | +2 |
| San Agustín | 22 | 23 | +1 |
| San Juan | 11 | 11 | 0 |
| Vista Alegre | 13 | 13 | 0 |
| Capiscol | 11 | 10 | -1 |
| Gamonal Norte | 16 | 17 | +1 |

**Total**: 115 raw vs 124 parsed (9 más parseadas, probable: 1 perdida + 10 de multiplicidad)

## Problemas con el Prompt Actual

### Problemas identificados:

1. **No captura bien días cuando vienen con texto "LUNES 2"**
   - El prompt recibe `day: "LUNES 2"` pero necesita convertir a fecha DD/MM/YYYY
   - Falta lógica para mapear "LUNES 2" → "02"

2. **No maneja bien asteriscos en múltiples contextos**
   - `(*) NOMBRE` → requiere inscripción ✓
   - `*NOMBRE` → también requiere inscripción ✓
   - Pero genera JSON inválido cuando hay comillas especiales

3. **No detecta cuando hay múltiples actividades en un text**
   - A veces funciona pero no siempre
   - El raw tiene múltiples títulos en MAYÚSCULAS pero la IA no siempre las separa

4. **Falta información sobre precios**
   - Algunos raw tienen precios (ej: "12,00€") pero no se extraen
   - El prompt no instruye explícitamente a buscar precios

5. **Caracteres especiales y OCR errors**
   - `Guña` (OCR error) permanece en parsed
   - `ELIA&UXÍA` genera problemas con caracteres especiales

6. **No valida fechas incompletas**
   - El parsing normaliza "2/2026" a "02/2026" pero falta el día
   - No hay fallback para inferir el día correcto

## Recomendaciones

### Para correcciones inmediatas en actividades.json:
1. Corregir "Guña" → "Guía" (OCR error visible)
2. Investigar y agregar CUENTOS EN PAÑALES perdida del día 12
3. Verificar RINCÓN CREATIVO - ¿está correctamente fechada como 02/02/2026?
4. Buscar actividades sin fecha completa

### Para mejorar ai_parser.py:
1. Mejorar extracción de día cuando el contexto es "LUNES 2", "MARTES 3", etc.
2. Agregar instrucciones explícitas sobre precios
3. Mejorar manejo de caracteres especiales
4. Agregar validación de fecha con fallback

### Para entrenamiento futuro:
Los pares (raw, actividades corregidas) pueden servir como dataset para:
- Fine-tuning de modelo local
- Validación de reglas pattern-matching
- Entrenamiento de modelo discriminador de calidad
