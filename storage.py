import json
import os
from config import FILES

def ensure_files():
    """
    Crea todos los JSON (vacíos) si no existen.
    """
    for path in FILES.values():
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)

def load(file_key):
    """
    Carga y devuelve el contenido del JSON indicado por la clave.
    """
    with open(FILES[file_key], 'r') as f:
        return json.load(f)

def save(file_key, data):
    """
    Guarda el diccionario `data` en el JSON indicado por la clave.
    """
    with open(FILES[file_key], 'w') as f:
        json.dump(data, f, indent=2)
