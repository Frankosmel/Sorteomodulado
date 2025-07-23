import os

# Token del bot (prioriza la variable de entorno BOT_TOKEN; si no existe, usa el valor por defecto)
TOKEN = os.getenv("BOT_TOKEN", "7823475152:AAEwBz6z5x0EIxN2XSXlVbFUX_fk_p4T1OI")

# IDs de super-administradores (quienes pueden autorizar usuarios y validar pagos)
ADMINS = [1383931339, 7907625643]

# Duración estándar de la suscripción en días (para cálculo de vencimiento tras autorizar)
VIGENCIA_DIAS = 30

# Rutas de todos los archivos JSON que usa el bot
FILES = {
    "autorizados":    "autorizados.json",    # quienes pueden usar comandos en grupos
    "grupos":         "grupos.json",         # información de grupos activados
    "participantes":  "participantes.json",  # quiénes han entrado a cada grupo
    "invitaciones":   "invitaciones.json",   # conteo de invitaciones por usuario
    "sorteo":         "sorteo.json",         # participantes de cada sorteo
    "jobs":           "jobs.json",           # sorteos programados
    "historial":      "historial.json",      # (opcional) historial de sorteos
    "receipts":       "receipts.json"        # recibos/datos de pago pendientes o validados
}
