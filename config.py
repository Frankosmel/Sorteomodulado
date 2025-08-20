# config.py
# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN CENTRAL DEL BOT
# - Token por variable de entorno (no hardcodear)
# - Admins, contacto, archivos de estado
# - Planes y parámetros de pago
# ──────────────────────────────────────────────────────────────────────────────

import os

# ───────── TOKEN (obligatorio por entorno) ─────────
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN or not TOKEN.strip():
    raise RuntimeError(
        "BOT_TOKEN no está definido en las variables de entorno. "
        "Configúralo en systemd con: Environment=BOT_TOKEN=..."
    )

# ───────── Administración ─────────
ADMINS = [
    1383931339,
    7907625643,
]

CONTACT_ADMIN_USERNAME = "frankosmel"            # sin @
SUPPORT_CHAT_LINK = "https://t.me/frankosmel"    # enlace de contacto

# ───────── Archivos de estado (JSON) ─────────
FILES = {
    "autorizados":    "autorizados.json",
    "grupos":         "grupos.json",
    "participantes":  "participantes.json",
    "invitaciones":   "invitaciones.json",
    "sorteo":         "sorteo.json",
    "jobs":           "jobs.json",
    "historial":      "historial.json",
    "receipts":       "receipts.json",
}

# ───────── Planes (USD, ≤ $4) ─────────
VIGENCIA_DIAS = 30  # fallback

PLANS = [
    { "key": "p_7d_1g_1us",  "label": "🟢 7 días — 1 grupo — 1 usuario — $1.00",  "price_usd": 1.00, "duration_days": 7,  "max_groups": 1 },
    { "key": "p_15d_1g_1us", "label": "🔵 15 días — 1 grupo — 1 usuario — $1.50", "price_usd": 1.50, "duration_days": 15, "max_groups": 1 },
    { "key": "p_30d_1g_1us", "label": "🟣 30 días — 1 grupo — 1 usuario — $2.00", "price_usd": 2.00, "duration_days": 30, "max_groups": 1 },
    { "key": "p_30d_2g_1us", "label": "🟠 30 días — 2 grupos — 1 usuario — $3.00", "price_usd": 3.00, "duration_days": 30, "max_groups": 2 },
    { "key": "p_30d_3g_1us", "label": "🔴 30 días — 3 grupos — 1 usuario — $4.00", "price_usd": 4.00, "duration_days": 30, "max_groups": 3 },
]

# ───────── Conversión y comisiones ─────────
USD_TO_CUP_TRANSFER = 380      # Transferencia CUP
SALDO_DIVISOR        = 2.5     # Regla saldo: 380 ÷ 2.5
ROUND_TO             = 10      # Redondeo hacia arriba al múltiplo de 10

PAYPAL_FEE_PCT   = 0.054       # 5.4%
PAYPAL_FEE_FIXED = 0.30        # $0.30

# ───────── Métodos de pago: textos e instrucciones ─────────
PAYMENT_INFO = {
    "saldo": {
        "label": "📱 Saldo móvil",
        "numero": "63785631",
        "instruccion": (
            "Paga con *saldo móvil*.\n"
            "1) Envía el *monto indicado (CUP)* al número de saldo móvil.\n"
            "2) Envía la *captura obligatoria* por aquí.\n"
            "Número de saldo: 63785631"
        )
    },
    "cup": {
        "label": "💵 Transferencia CUP",
        "tarjeta": "9204 1299 7691 8161",
        "numero_confirmacion": "56246700",
        "instruccion": (
            "Realiza una *transferencia CUP* por el *monto indicado (CUP)* a la tarjeta:\n"
            "Tarjeta: 9204 1299 7691 8161\n"
            "Número a confirmar (obligatorio): 56246700\n"
            "Luego, envía la *captura obligatoria* por aquí."
        )
    },
    "paypal": {
        "label": "🅿️ PayPal",
        "email": "paypalfrancho@gmail.com",
        "nombre": "Daikel Gonzáles Quintero",
        "instruccion": (
            "Paga por *PayPal* la *cantidad exacta (USD)* indicada (incluye comisiones).\n"
            "Correo: paypalfrancho@gmail.com\n"
            "Nombre: Daikel Gonzáles Quintero\n"
            "Luego, envía la *captura obligatoria* por aquí."
        )
    },
}
