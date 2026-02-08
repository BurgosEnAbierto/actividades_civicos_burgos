#!/usr/bin/env python3
"""
Generar dataset de entrenamiento estructurado a partir de:
- actividades_raw_*.json (inputs crudos)
- actividades.json verificado (outputs esperados)

Output: training_dataset_202602.json
"""

import json
import re
from pathlib import Path
from datetime import datetime

def generate_training_dataset():
    """Generar dataset de entrenamiento estructurado"""
    
    # Cargar datos
    with open('data/202602/actividades.json', 'r', encoding='utf-8') as f:
        actividades_verified = json.load(f)
    
    civicos = [
        'rio_vena', 'huelgas', 'san_agustin', 'san_juan', 
        'vista_alegre', 'capiscol', 'gamonal_norte'
    ]
    
    raw_data = {}
    for civico in civicos:
        raw_file = f'data/202602/actividades_raw_{civico}.json'
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data[civico] = json.load(f)
    
    # Construir dataset
    training_pairs = []
    error_patterns = {
        'ocr_errors': [],
        'age_conversion': [],
        'location_contamination': [],
        'date_parsing': [],
        'unicode_issues': [],
        'price_extraction': []
    }
    
    pair_id = 0
    
    # Por cada centro
    for civico in civicos:
        activities = actividades_verified.get(civico, [])
        raw_items = raw_data.get(civico, [])
        
        # Mapear raw → verified (heurística simple)
        raw_by_day = {}
        for day_label, text in raw_items:
            if text.strip():
                raw_by_day[day_label] = text
        
        # Para cada actividad verificada
        for act_idx, act in enumerate(activities):
            pair_id += 1
            
            # Encontrar raw correspondiente (by date y nombre)
            matching_raw = None
            for day_label, text in raw_items:
                if text.strip() and act['nombre'][:30].upper() in text.upper():
                    matching_raw = (day_label, text)
                    break
            
            pair = {
                "id": f"202602_{civico}_{pair_id:03d}",
                "centro": civico,
                "raw_input": {
                    "day_label": matching_raw[0] if matching_raw else "Unknown",
                    "text": matching_raw[1] if matching_raw else "N/A"
                },
                "expected_output": {
                    "nombre": act['nombre'],
                    "descripcion": act.get('descripcion'),
                    "fecha": act['fecha'],
                    "fecha_fin": act.get('fecha_fin'),
                    "hora": act.get('hora'),
                    "hora_fin": act.get('hora_fin'),
                    "requiere_inscripcion": act['requiere_inscripcion'],
                    "lugar": act.get('lugar'),
                    "publico": act['publico'],
                    "edad_minima": act.get('edad_minima'),
                    "edad_maxima": act.get('edad_maxima'),
                    "precio": act.get('precio')
                },
                "corrections_applied": _detect_corrections(act),
                "error_types": _detect_error_types(act)
            }
            
            training_pairs.append(pair)
            
            # Registrar patrones de error detectados
            _register_error_patterns(act, error_patterns)
    
    # Construir dataset final
    dataset = {
        "metadata": {
            "mes": "202602",
            "fecha_creacion": datetime.now().isoformat(),
            "total_pares": len(training_pairs),
            "centros": civicos,
            "total_actividades": sum(len(actividades_verified.get(c, [])) for c in civicos),
            "total_raw_entries": sum(len([x for x in raw_data.get(c, []) if x[1].strip()]) for c in civicos),
            "versiones": {
                "ai_parser_prompt": "v2.1",
                "schema": "v1"
            }
        },
        "training_pairs": training_pairs,
        "error_patterns": error_patterns,
        "statistics": {
            "total_pairs": len(training_pairs),
            "pairs_with_corrections": sum(1 for p in training_pairs if p['corrections_applied']),
            "pairs_with_errors": sum(1 for p in training_pairs if p['error_types']),
        }
    }
    
    # Guardar
    output_file = Path('data/202602/training_dataset_202602.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Dataset de entrenamiento generado: {output_file}")
    print(f"  - {len(training_pairs)} pares de entrenamiento")
    print(f"  - {dataset['statistics']['pairs_with_corrections']} con correcciones")
    print(f"  - {dataset['statistics']['pairs_with_errors']} con errores detectados")

def _detect_corrections(act):
    """Detectar si esta actividad tuvo correcciones aplicadas"""
    corrections = []
    
    name = act['nombre']
    
    if 'PRESENTACIÓN' in name and 'RESENTACIÓN' not in name:
        corrections.append("OCR correction: RESENTACIÓN → PRESENTACIÓN")
    if 'MÁSCARAS' in name and 'ÁSCARAS' not in name:
        corrections.append("OCR correction: ÁSCARAS → MÁSCARAS")
    if 'MURAL:' in name and 'URAL:' not in name:
        corrections.append("OCR correction: URAL: → MURAL:")
    
    edad_min = act.get('edad_minima')
    edad_max = act.get('edad_maxima')
    
    if edad_min and edad_max and edad_min < edad_max and edad_min <= 3:
        if '18 meses' in act.get('publico', ''):
            corrections.append("Age correction: 18 meses → edad_minima: 1")
    
    if act.get('lugar') and 'TARDES DE' not in act.get('lugar', ''):
        corrections.append("Location cleanup: removed activity name from location")
    
    return corrections

def _detect_error_types(act):
    """Detectar tipos de errores en los datos"""
    error_types = []
    
    # Check for potential issues
    if not act.get('fecha'):
        error_types.append("missing_fecha")
    
    if not act.get('publico'):
        error_types.append("missing_publico")
    
    edad_min = act.get('edad_minima')
    edad_max = act.get('edad_maxima')
    
    if edad_min and edad_max and edad_min > edad_max:
        error_types.append("age_min_greater_than_max")
    
    if act.get('lugar') and 'TARDES DE' in act.get('lugar', ''):
        error_types.append("location_contaminated")
    
    return error_types

def _register_error_patterns(act, error_patterns):
    """Registrar patrones de error encontrados"""
    
    # OCR errors
    name = act['nombre']
    if any(x in name for x in ['RESENTACIÓN', 'ÁSCARAS', 'URAL:']):
        error_patterns['ocr_errors'].append({
            "text": name,
            "activity": act.get('nombre')[:30]
        })
    
    # Age conversion
    if '18 meses' in (act.get('publico') or ''):
        error_patterns['age_conversion'].append({
            "publico": act.get('publico'),
            "edad_minima": act.get('edad_minima'),
            "edad_maxima": act.get('edad_maxima')
        })
    
    # Location contamination
    lugar = act.get('lugar')
    if lugar and 'TARDES DE' in lugar:
        error_patterns['location_contamination'].append({
            "lugar": act.get('lugar'),
            "activity": act.get('nombre')[:30]
        })
    
    # Price extraction
    if act.get('precio') is not None:
        error_patterns['price_extraction'].append({
            "precio": act.get('precio'),
            "publico": act.get('publico')
        })

if __name__ == '__main__':
    try:
        generate_training_dataset()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
