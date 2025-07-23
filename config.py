# config.py

import os

# Token del bot (prioriza la variable de entorno BOT_TOKEN, de lo contrario usa el valor directo)
TOKEN = os.getenv("BOT_TOKEN", "7823475152:AAEwBz6z5x0EIxN2XSXlVbFUX_fk_p4T1OI")

# IDs de super-administradores
ADMINS = [1383931339, 7907625643]

# Duración del plan mensual en días
VIGENCIA_DIAS = 30

# Duración del plan trimestral en días (3 meses)
VIGENCIA_TRIMESTRAL = 90

# Rutas de los archivos de datos JSON
FILES = {
    "autorizados":    "autorizados.json",    # usuarios autorizados y fecha de vencimiento
    "grupos":         "grupos.json",         # configuración de grupos (activados, timezone, owner)
    "participantes":  "participantes.json",  # historial de quién añade a quién
    "invitaciones":   "invitaciones.json",   # contadores de invitaciones por usuario
    "sorteo":         "sorteo.json",         # participantes del sorteo actual
    "jobs":           "jobs.json",           # sorteos programados por fecha
    "historial":      "historial.json",      # registro de sorteos ya ejecutados (opcional)
    "receipts":       "receipts.json"        # comprobantes de pago y estado (pending, awaiting_approval, approved, rejected)
}
