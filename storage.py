import json
from config import FILES

def ensure_files():
    """Crea todos los JSON vacíos si no existen."""
    for path in FILES.values():
        try:
            open(path, 'r').close()
        except FileNotFoundError:
            with open(path, 'w') as f:
                json.dump({}, f)

def load(key: str):
    """Carga el JSON asociado a FILES[key]."""
    path = FILES[key]
    with open(path, 'r') as f:
        return json.load(f)

def save(key: str, data):
    """Guarda `data` en el JSON asociado a FILES[key]."""
    path = FILES[key]
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
