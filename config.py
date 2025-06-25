import os

# Token del bot (mejor usar variable de entorno en producción)
TOKEN = os.getenv("BOT_TOKEN", "7996381032:AAHGXxjLHdPp1n77RomiRZQO1L0sAzPJIyo")

# IDs de administradores que pueden usar el panel
ADMINS = [1383931339, 7907625643]

# Duración del plan mensual en días
VIGENCIA_DIAS = 30

# Rutas de los archivos de datos
FILES = {
    "autorizados":    "autorizados.json",
    "grupos":         "grupos.json",
    "participantes":  "participantes.json",
    "invitaciones":   "invitaciones.json",
    "sorteo":         "sorteo.json"
}
