# config.py
# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN CENTRAL DEL BOT
# - Mantiene el token fuera del repositorio (obligatorio por variable de entorno)
# - Define admins, archivos de estado, planes y parámetros de pago
# - Expone constantes para cálculos en main.py
# ──────────────────────────────────────────────────────────────────────────────

import os

# ──────────────────────────────────────────────────────────────────────────────
# TOKEN DEL BOT (OBLIGATORIO POR VARIABLE DE ENTORNO)
# NUNCA guardes el token en el repo. Cárgalo así en systemd:
# Environment=BOT_TOKEN=XXXXXXXXXXXX
# ──────────────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN or not TOKEN.strip():
    raise RuntimeError(
        "BOT_TOKEN no está definido en las variables de entorno. "
        "Configúralo en el servicio systemd (Environment=BOT_TOKEN=...) "
        "o exporta la variable antes de ejecutar el bot."
    )

# ──────────────────────────────────────────────────────────────────────────────
# ADMINISTRACIÓN
# - Lista de IDs que pueden usar /admin
# - Usuario de contacto para clientes
# ──────────────────────────────────────────────────────────────────────────────
ADMINS = [
    1383931339,
    7907625643,
]

CONTACT_ADMIN_USERNAME = "frankosmel"                 # sin @
SUPPORT_CHAT_LINK = "https://t.me/frankosmel"         # enlace directo al perfil/canal/grupo

# ──────────────────────────────────────────────────────────────────────────────
# ARCHIVOS DE ESTADO (JSON)
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# PLANES (USD) — MÁXIMO $4 — CON CUPOS DE GRUPOS Y VIGENCIAS
# Nota: 'label' es el texto que verá el usuario; 'key' se usa en lógica interna
# ──────────────────────────────────────────────────────────────────────────────
VIGENCIA_DIAS = 30  # fallback si un plan no define duración

PLANS = [
    {
        "key": "p_7d_1g_1us",
        "label": "🟢 7 días — 1 grupo — 1 usuario — $1.00",
        "price_usd": 1.00,
        "duration_days": 7,
        "max_groups": 1
    },
    {
        "key": "p_15d_1g_1us",
        "label": "🔵 15 días — 1 grupo — 1 usuario — $1.50",
        "price_usd": 1.50,
        "duration_days": 15,
        "max_groups": 1
    },
    {
        "key": "p_30d_1g_1us",
        "label": "🟣 30 días — 1 grupo — 1 usuario — $2.00",
        "price_usd": 2.00,
        "duration_days": 30,
        "max_groups": 1
    },
    {
        "key": "p_30d_2g_1us",
        "label": "🟠 30 días — 2 grupos — 1 usuario — $3.00",
        "price_usd": 3.00,
        "duration_days": 30,
        "max_groups": 2
    },
    {
        "key": "p_30d_3g_1us",
        "label": "🔴 30 días — 3 grupos — 1 usuario — $4.00",
        "price_usd": 4.00,
        "duration_days": 30,
        "max_groups": 3
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# PARÁMETROS DE PAGO Y CONVERSIONES
# - Transferencia CUP: 1 USD = 380 CUP
# - Saldo móvil: se calcula como (USD * 380) / 2.5 y se redondea HACIA ARRIBA
#   al múltiplo de 10 más cercano (p. ej. 152 → 160, 346 → 350).
# - PayPal: se calcula el monto BRUTO para que NETO llegue al price_usd,
#   usando los fees configurados abajo.
# ──────────────────────────────────────────────────────────────────────────────
USD_TO_CUP_TRANSFER = 380      # Transferencia CUP estándar
SALDO_DIVISOR        = 2.5     # Preferencia: 380 ÷ 2.5
ROUND_TO             = 10      # Redondeo hacia arriba al múltiplo de 10

# PayPal (ajusta si tu cuenta tiene otra estructura de fees)
PAYPAL_FEE_PCT   = 0.054       # 5.4%
PAYPAL_FEE_FIXED = 0.30        # $0.30 por transacción

# ──────────────────────────────────────────────────────────────────────────────
# MÉTODOS DE PAGO: TEXTOS E INSTRUCCIONES (MOSTRAR AL CLIENTE)
# Todos los datos críticos son fáciles de copiar por el usuario y por el admin.
# ──────────────────────────────────────────────────────────────────────────────
PAYMENT_INFO = {
    # SALDO MÓVIL — usa la regla 380/2.5 y redondeo hacia arriba a múltiplo de 10
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
    # TRANSFERENCIA CUP — tasa 380 por cada USD
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
    # PAYPAL — calculamos el bruto para que neto llegue al price_usd
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
