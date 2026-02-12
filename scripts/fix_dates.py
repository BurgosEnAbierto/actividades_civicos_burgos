#!/usr/bin/env python3
"""
Script para corregir las fechas incorrectas en actividades.json
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def fix_dates(month: str, dry_run: bool = True):
    """
    Corrige y ordena las fechas en actividades.json para un mes específico
    """
    actividades_file = Path(f"docs/data/{month}/actividades.json")
    
    if not actividades_file.exists():
        print(f"❌ Archivo no existe: {actividades_file}")
        return 1
    
    # Extraer mes y año esperados
    year_expected = int(month[:4])
    month_expected = int(month[4:])
    
    with open(actividades_file) as f:
        data = json.load(f)
    
    fixed_count = 0
    
    # Procesar cada civico
    for civico, activities in data.items():
        if not isinstance(activities, list):
            continue
        
        for activity in activities:
            if not isinstance(activity, dict):
                continue
            
            fecha = activity.get("fecha", "")
            if not fecha:
                continue
            
            # Verificar si necesita corrección
            try:
                parts = fecha.split("/")
                if len(parts) == 3:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    
                    # Si el mes es incorrecto, corregir
                    if m != month_expected or y != year_expected:
                        # Cuando ambos d y m son válidos (1-12), preferir el que sea el mes correcto
                        # Si los dos son válidos pero ninguno es el mes correcto,
                        # asumir formato MM/DD/YYYY y invertir
                        
                        old_fecha = fecha
                        
                        if d == month_expected:
                            # El primer número es el mes correcto -> formato MM/DD/YYYY, invertir
                            activity["fecha"] = f"{m:02d}/{d:02d}/{y:04d}"
                        elif m == month_expected:
                            # El segundo número es el mes correcto -> formato DD/MM/YYYY, mantener
                            activity["fecha"] = f"{d:02d}/{m:02d}/{y:04d}"
                        else:
                            # Ninguno coincide, pero revisar si d > 12 (debe ser DD)
                            if d > 12:
                                activity["fecha"] = f"{d:02d}/{month_expected:02d}/{year_expected:04d}"
                            else:
                                # Ambos son válidos, asumir MM/DD y invertir
                                activity["fecha"] = f"{m:02d}/{d:02d}/{year_expected:04d}"
                        
                        if activity["fecha"] != old_fecha:
                            fixed_count += 1
                            if not dry_run:
                                print(f"  {civico}: {old_fecha} → {activity['fecha']}")
            except (ValueError, IndexError):
                pass

            # Ordenar actividades por fecha
            activities.sort(key=lambda x: tuple(map(int, x.get("fecha", "0/0/0").split("/")))[::-1])
    
    if dry_run:
        print(f"Se corregirían {fixed_count} fechas")
        print("Ejecutar con --apply para confirmar")
        return 0 if fixed_count == 0 else 1
    else:
        # Guardar el archivo corregido
        with open(actividades_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Guardado: {actividades_file}")
        print(f"Fechas corregidas: {fixed_count}")
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Uso:")
        print("  python scripts/fix_dates.py <mes>           # Preview")
        print("  python scripts/fix_dates.py <mes> --apply   # Aplicar cambios")
        print("\nEjemplo:")
        print("  python scripts/fix_dates.py 202602")
        print("  python scripts/fix_dates.py 202602 --apply")
        sys.exit(1)
    
    month = sys.argv[1]
    apply = "--apply" in sys.argv
    
    sys.exit(fix_dates(month, dry_run=not apply))
