import os
import json

def ensure_files():
    """
    Crea los archivos y carpetas necesarias si no existen.
    """
    os.makedirs("data", exist_ok=True)

    archivos = {
        "autorizados.json": {"users": []},
        "grupos.json": {},
        "jobs.json": {},
        "participants.json": []
    }

    for archivo, contenido in archivos.items():
        ruta = os.path.join("data", archivo)
        if not os.path.exists(ruta):
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(contenido, f, indent=2)
