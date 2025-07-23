# config.py

import os

# Token del bot (prioriza la env var BOT_TOKEN, de lo contrario usa el valor directo)
TOKEN = os.getenv("BOT_TOKEN", "7823475152:AAEwBz6z5x0EIxN2XSXlVbFUX_fk_p4T1OI")

# IDs de super‐administradores (pueden usar /admin)
ADMINS = [
    1383931339,  # Tu ID
    7907625643,  # Otro super‐admin
]

# Duración del plan básico en días
VIGENCIA_DIAS = 30

# Definición de rutas de todos los datos JSON
FILES = {
    "autorizados":    "autorizados.json",    # Usuarios autorizados y fechas de vencimiento
    "grupos":         "grupos.json",         # Grupos donde está activo el bot
    "participantes":  "participantes.json",  # Quienes han sido añadidos al grupo
    "invitaciones":   "invitaciones.json",   # Conteo de invitaciones por usuario
    "sorteo":         "sorteo.json",         # Participantes apuntados al sorteo activo
    "jobs":           "jobs.json",           # Sorteos programados por fecha/hora
    "historial":      "historial.json",      # Historial de sorteos realizados
    "receipts":       "receipts.json",       # Recibos de pago y confirmaciones
}

# Precios y descripción de planes para /start en privado (solo clientes no autorizados)
PLANS = [
    {
        "key": "plan_1m1g",
        "label": "🌟 1 mes — 1 grupo — 500 CUP",
        "price": 500,
        "duration_days": 30,
        "max_groups": 1
    },
    {
        "key": "plan_1m2g",
        "label": "✨ 1 mes — 2 grupos — 900 CUP",
        "price": 900,
        "duration_days": 30,
        "max_groups": 2
    },
    {
        "key": "plan_1m3g",
        "label": "⚡ 1 mes — 3 grupos — 1 200 CUP",
        "price": 1200,
        "duration_days": 30,
        "max_groups": 3
    },
    {
        "key": "plan_3m3g",
        "label": "🔥 3 meses — 3 grupos — 3 000 CUP",
        "price": 3000,
        "duration_days": 90,
        "max_groups": 3
    },
]

# Datos de pago para mostrar en el bot
PAYMENT_INFO = {
    "tarjeta": "9204 1299 7691 8161",
    "sms_num": "56246700",
    "saldo_movil": "56246700"
}
