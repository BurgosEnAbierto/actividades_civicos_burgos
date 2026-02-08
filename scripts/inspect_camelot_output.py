#!/usr/bin/env python3
"""
Script para inspeccionar output de Camelot para cada cívico.
Útil para crear process_pdf específico para cada uno.

Uso:
    python scripts/inspect_camelot_output.py <mes> [civico]
    
Ejemplo:
    python scripts/inspect_camelot_output.py 202601              # Todos los cívicos
    python scripts/inspect_camelot_output.py 202601 gamonal_norte # Un cívico específico
"""

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import camelot
from src.parser.registry import CIVICOS


def inspect_civico_pdfs(month: str, civico_id: Optional[str] = None):
    """
    Inspecciona output de Camelot para PDFs de un mes.
    
    Args:
        month: Mes en formato YYYYMM (ej: 202601)
        civico_id: ID del cívico específico o None para todos
    """
    pdfs_dir = Path(f"data/{month}/pdfs")
    
    if not pdfs_dir.exists():
        print(f"❌ Directorio no existe: {pdfs_dir}")
        return 1
    
    # Buscar PDFs
    if civico_id:
        # Buscar PDF específico de un cívico
        civicos_to_check = [civico_id] if civico_id in CIVICOS else []
        if not civicos_to_check:
            print(f"❌ Cívico no encontrado: {civico_id}")
            return 1
    else:
        civicos_to_check = sorted(CIVICOS)
    
    # Buscar PDFs recursivamente (pueden estar en subdirectorios)
    pdf_files = list(pdfs_dir.glob("**/*.pdf"))
    
    print(f"\n{'='*80}")
    print(f"📊 INSPECCIÓN DE CAMELOT OUTPUT - Mes {month}")
    print(f"{'='*80}\n")
    
    for pdf_path in sorted(pdf_files):
        pdf_name = pdf_path.stem
        
        # Detectar cívico de la ruta o nombre del archivo
        # Pueden estar en subdirectorio o directamente en pdfs/
        civico_from_path = None
        parts = pdf_path.parts
        
        if "pdfs" in parts:
            pdfs_idx = parts.index("pdfs")
            # Si hay elemento después de "pdfs"
            if pdfs_idx + 1 < len(parts):
                next_part = parts[pdfs_idx + 1]
                # Si el siguiente es un directorio (no es el PDF)
                if pdfs_idx + 2 < len(parts):  
                    civico_from_path = next_part
                else:
                    # next_part es el PDF, tenemos que detectar el civico de otra forma
                    # Intentar extraer del nombre del PDF
                    civico_from_path = None
        
        # Si no detectamos civico de ruta, intentar extraer del nombre del archivo
        if not civico_from_path and civico_id:
            # Buscar coincidencia flexible: el civico_id podría estar en el nombre
            # Convertir guiones a espacios para búsqueda
            pdf_name_normalized = pdf_name.lower().replace("+", " ").replace("_", " ").replace("-", " ")
            civico_normalized = civico_id.lower().replace("_", " ").replace("-", " ")
            if civico_normalized in pdf_name_normalized:
                civico_from_path = civico_id
        
        # Skip si especificamos un cívico y no coincide
        if civico_id:
            if civico_from_path is None:
                # No encontramos coincidencia en la ruta, también intentar verificar en CIVICOS
                if civico_id in CIVICOS:
                    # El civico existe pero no lo encontramos en los PDFs disponibles
                    # Skip para este PDF
                    continue
                else:
                    # civico_id no es válido, mostrar error
                    if pdf_path == pdf_files[0]:  # Solo mostrar una vez
                        print(f"⚠️  Cívico '{civico_id}' no es válido. Cívicos disponibles:")
                        for civ in sorted(CIVICOS):
                            print(f"   - {civ}")
                    continue
            elif civico_from_path != civico_id:
                # Ya tenemos un civico_from_path pero no coincide
                continue
        
        print(f"\n{'─'*80}")
        print(f"📄 {pdf_path.relative_to(pdfs_dir)}")
        print(f"{'─'*80}")
        print(f"Tamaño: {pdf_path.stat().st_size / 1024:.1f} KB")
        
        try:
            # Leer PDF con Camelot
            tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")
            print(f"✅ Detectadas {len(tables)} tablas")
            
            # Mostrar análisis de cada tabla
            for table_idx, table in enumerate(tables):
                print(f"\n  🔸 Tabla {table_idx + 1}:")
                print(f"     ├─ Dimensiones: {table.shape[0]} filas × {table.shape[1]} columnas")
                print(f"     ├─ Confianza (Lattice): {table.accuracy:.1%}")
                
                # Mostrar primeras filas
                print(f"     ├─ Primeras filas:")
                df = table.df
                for row_idx in range(min(5, len(df))):
                    print(f"     │  [{row_idx}] {df.iloc[row_idx].tolist()}")
                
                if len(df) > 5:
                    print(f"     │  ... ({len(df) - 5} filas más)")
                
                # Verificar columnas detectadas
                print(f"     └─ Columnas ({df.shape[1]}):")
                for col_idx, col_name in enumerate(df.columns):
                    print(f"        [{col_idx}] {col_name}")
            
            # Intenta con stream flavor si lattice no detectó mucho
            if len(tables) == 0:
                print(f"\n  ⚠️  Probando con flavor='stream'...")
                tables_stream = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")
                print(f"  ✅ Stream: {len(tables_stream)} tablas")
                for table_idx, table in enumerate(tables_stream):
                    print(f"     └─ Tabla {table_idx + 1}: {table.shape[0]}x{table.shape[1]}")
        
        except Exception as e:
            print(f"❌ Error procesando {pdf_name}: {e}")
            import traceback
            traceback.print_exc()
    
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    month = sys.argv[1]
    civico_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    return inspect_civico_pdfs(month, civico_id)


if __name__ == "__main__":
    sys.exit(main())
