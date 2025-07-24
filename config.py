# config.py

import os

# Token del bot (prioriza la env var BOT_TOKEN, de lo contrario usa el valor directo)
TOKEN = os.getenv("BOT_TOKEN", "7823475152:AAEwBz6z5x0EIxN2XSXlVbFUX_fk_p4T1OI")

# IDs de super‐administradores (pueden usar /admin)
ADMINS = [
    1383931339,  # Tu ID
    7907625643,  # Otro super‐admin
]

# ID del canal de reportes automáticos (usado por admin_handlers)
REPORT_CHANNEL_ID = -1002125544275  # reemplaza por tu canal real si deseas

# ID del grupo de staff donde se reciben logs y alertas internas
STAFF_GROUP_ID = -1002605404513  # reemplaza por tu grupo real

# Duración estándar de cada mes de suscripción, en días
VIGENCIA_DIAS = 30

# Definición de rutas de todos los datos JSON
FILES = {
    "autorizados":        "autorizados.json",
    "grupos":             "grupos.json",
    "grupos_autorizados": "grupos_autorizados.json",  # ✅ Añadido correctamente
    "participantes":      "participantes.json",
    "invitaciones":       "invitaciones.json",
    "sorteo":             "sorteo.json",
    "jobs":               "jobs.json",
    "historial":          "historial.json",
    "receipts":           "receipts.json",  # necesario para payment handlers
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
        "label": "✨ 1 mes — 2 grupos — 950 CUP",  # 5% descuento
        "price": int(500 * 2 * 0.95),
        "duration_days": 30,
        "max_groups": 2
    },
    {
        "key": "plan_1m3g",
        "label": "⚡ 1 mes — 3 grupos — 1 350 CUP",  # 10% descuento
        "price": int(500 * 3 * 0.90),
        "duration_days": 30,
        "max_groups": 3
    },
    {
        "key": "plan_3m3g",
        "label": "🔥 3 meses — 3 grupos — 2 550 CUP",  # 15% descuento
        "price": int(500 * 3 * 3 * 0.85),
        "duration_days": 90,
        "max_groups": 3
    },
]

# Datos de pago para mostrar en el bot
PAYMENT_INFO = {
    "tarjeta":     "9204 1299 7691 8161",
    "sms_num":     "56246700",
    "saldo_movil": "56246700"
}
