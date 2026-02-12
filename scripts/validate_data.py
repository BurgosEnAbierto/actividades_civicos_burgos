#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCHEMA_DIR = BASE_DIR / "schemas"


def load_json(path: Path):
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error leyendo {path}: {e}")


def validate_json(data: dict, schema: dict, label: str):
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        print(f"\n❌ Errores de validación en {label}:")
        for err in errors:
            path = " → ".join(map(str, err.path)) or "(root)"
            print(f"  - {path}: {err.message}")
        return False

    print(f"✅ {label} válido")
    return True


def validate_civicos():
    civicos_path = DATA_DIR / "civicos.json"
    schema_path = SCHEMA_DIR / "civicos.schema.v1.json"

    civicos = load_json(civicos_path)
    schema = load_json(schema_path)

    return validate_json(civicos, schema, "civicos.json")


def validate_actividades():
    schema_path = SCHEMA_DIR / "actividades.schema.v1.json"
    schema = load_json(schema_path)

    ok = True

    for month_dir in sorted(DATA_DIR.glob("[0-9][0-9][0-9][0-9][0-9][0-9]")):
        actividades_path = month_dir / "actividades.json"
        if not actividades_path.exists():
            continue

        actividades = load_json(actividades_path)
        label = f"{month_dir.name}/actividades.json"

        if not validate_json(actividades, schema, label):
            ok = False

    return ok


def main():
    print("🔍 Validando datos del proyecto Burgos Cívicos\n")

    ok_civicos = validate_civicos()
    ok_actividades = validate_actividades()

    if not (ok_civicos and ok_actividades):
        print("\n❌ Validación fallida")
        sys.exit(1)

    print("\n🎉 Todos los datos son válidos")


if __name__ == "__main__":
    main()
