import os

# Token del bot (prioriza la env var BOT_TOKEN, de lo contrario usa el literal)
TOKEN = os.getenv("BOT_TOKEN", "7823475152:AAEwBz6z5x0EIxN2XSXlVbFUX_fk_p4T1OI")

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

