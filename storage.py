import os
import json
from config import FILES

def ensure_files():
    """
    Crea todos los archivos JSON listados en FILES si no existen.
    """
    for key, path in FILES.items():
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                # Para receipts.json, ponemos lista; para el resto, dict
                if key == "receipts":
                    json.dump({}, f, ensure_ascii=False, indent=2)
                else:
                    json.dump({}, f, ensure_ascii=False, indent=2)

def load(key):
    """
    Carga y devuelve el contenido JSON del archivo FILES[key].
    """
    path = FILES[key]
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save(key, data):
    """
    Serializa `data` como JSON en el archivo FILES[key].
    """
    path = FILES[key]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
