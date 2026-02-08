#!/usr/bin/env python3
"""
Script para verificar que las fechas en actividades.json son correctas
Busca actividades con fechas que no correspondan al mes procesado
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def verify_dates(month: str):
    """
    Verifica las fechas en actividades.json para un mes específico
    
    Args:
        month: Mes en formato YYYYMM (ej: 202602)
    """
    actividades_file = Path(f"data/{month}/actividades.json")
    
    if not actividades_file.exists():
        print(f"❌ Archivo no existe: {actividades_file}")
        return 1
    
    # Extraer mes y año esperados
    year_expected = int(month[:4])
    month_expected = int(month[4:])
    
    with open(actividades_file) as f:
        data = json.load(f)
    
    # Si es dict (por civico), convertir a lista plana
    if isinstance(data, dict):
        activities_list = []
        for civico, activities in data.items():
            if isinstance(activities, list):
                for activity in activities:
                    if isinstance(activity, dict):
                        activity["civico"] = civico
                        activities_list.append(activity)
        data = activities_list
    
    print(f"\n{'='*80}")
    print(f"📅 VERIFICACIÓN DE FECHAS - {month}")
    print(f"{'='*80}\n")
    print(f"Total actividades: {len(data)}")
    print(f"Mes esperado: {month_expected:02d}/{year_expected}\n")
    
    # Agrupar por civico y fecha
    civicos = defaultdict(lambda: defaultdict(list))
    incorrect_dates = []
    
    for activity in data:
        civico = activity.get("civico", "desconocido")
        fecha = activity.get("fecha", "")
        nombre = activity.get("nombre", "sin nombre")
        
        civicos[civico][fecha].append(nombre[:60])
        
        # Verificar formato y mes
        if fecha:
            try:
                parts = fecha.split("/")
                if len(parts) == 3:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    if m != month_expected or y != year_expected:
                        incorrect_dates.append({
                            "civico": civico,
                            "fecha": fecha,
                            "nombre": nombre[:60],
                            "mes_esperado": f"{month_expected:02d}/{year_expected}",
                            "mes_actual": f"{m:02d}/{y}"
                        })
            except (ValueError, IndexError):
                pass
    
    # Mostrar resumen por cívico
    print(f"{'─'*80}")
    print("📊 RESUMEN POR CÍVICO:")
    print(f"{'─'*80}\n")
    
    for civico in sorted(civicos.keys()):
        dates_dict = civicos[civico]
        total_civico = sum(len(activities) for activities in dates_dict.values())
        
        # Contar fechas correctas
        correct_count = 0
        for fecha, activities in dates_dict.items():
            if fecha:
                try:
                    parts = fecha.split("/")
                    if len(parts) == 3:
                        m, y = int(parts[1]), int(parts[2])
                        if m == month_expected and y == year_expected:
                            correct_count += len(activities)
                except (ValueError, IndexError):
                    pass
        
        status = "✅" if correct_count == total_civico else "⚠️"
        print(f"{status} {civico}:")
        print(f"   Total: {total_civico} actividades")
        print(f"   Correctas: {correct_count}")
        
        if correct_count != total_civico:
            print(f"   Fechas encontradas:")
            for fecha in sorted(dates_dict.keys()):
                print(f"     - {fecha}: {len(dates_dict[fecha])} actividades")
        print()
    
    # Si hay fechas incorrectas, mostrarlas
    if incorrect_dates:
        print(f"{'─'*80}")
        print(f"❌ FECHAS INCORRECTAS ({len(incorrect_dates)}):")
        print(f"{'─'*80}\n")
        
        for item in incorrect_dates[:10]:  # Mostrar primeras 10
            print(f"• {item['civico']}")
            print(f"  Actividad: {item['nombre']}")
            print(f"  Fecha encontrada: {item['fecha']}")
            print(f"  Esperado: {item['mes_esperado']}")
            print()
        
        if len(incorrect_dates) > 10:
            print(f"... y {len(incorrect_dates) - 10} más\n")
        
        return 1
    
    print(f"{'─'*80}")
    print("✅ TODAS LAS FECHAS SON CORRECTAS")
    print(f"{'─'*80}\n")
    
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Uso: python scripts/verify_dates.py <mes>")
        print("Ejemplo: python scripts/verify_dates.py 202602")
        sys.exit(1)
    
    month = sys.argv[1]
    sys.exit(verify_dates(month))
