import os

# Token del bot (por defecto en variable de entorno o valor directo)
TOKEN = os.getenv("7996381032:AAHGXxjLHdPp1n77RomiRZQO1L0sAzPJIyo", "7996381032:AAHGXxjLHdPp1n77RomiRZQO1L0sAzPJIyo")

# IDs de super-administradores
ADMINS = [1383931339, 7907625643]

# Duración del plan mensual en días
VIGENCIA_DIAS = 30

# Rutas de los archivos de datos JSON
FILES = {
    "autorizados":    "autorizados.json",
    "grupos":         "grupos.json",
    "participantes":  "participantes.json",
    "invitaciones":   "invitaciones.json",
    "sorteo":         "sorteo.json",
    "jobs":           "jobs.json",
    "historial":      "historial.json"
}
