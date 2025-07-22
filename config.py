import os

# Token del bot (prioriza la variable de entorno BOT_TOKEN, de lo contrario usa el valor directo)
TOKEN = os.getenv(
    "BOT_TOKEN",
    "7823475152:AAEwBz6z5x0EIxN2XSXlVbFUX_fk_p4T1OI"
)

# IDs de super-administradores (tienen acceso al panel de administración)
ADMINS = [
    1383931339,  # Tu ID
    7907625643   # Otro administrador
]

# Duración del plan mensual en días (para vencimiento de autorizaciones)
VIGENCIA_DIAS = 30

# Rutas de los archivos de datos JSON
# Cada uno guarda el estado persistente de una funcionalidad
FILES = {
    # Usuarios autorizados a instalar el bot y sus planes
    "autorizados":    "autorizados.json",

    # Grupos donde el bot está activo y quién lo activó
    "grupos":         "grupos.json",

    # Participantes detectados por referidos en cada grupo
    "participantes":  "participantes.json",

    # Contador de cuántos invitados sumó cada usuario
    "invitaciones":   "invitaciones.json",

    # Lista de inscritos en el sorteo por grupo
    "sorteo":         "sorteo.json",

    # Tareas agendadas (jobs) para sorteos programados
    "jobs":           "jobs.json",

    # Historial de ganadores y fechas de sorteo
    "historial":      "historial.json",

    # Plantillas personalizables por grupo (/set_template, /get_templates)
    "templates":      "templates.json"
}
