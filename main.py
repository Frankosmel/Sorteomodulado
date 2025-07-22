# main.py

import logging
from telebot import TeleBot
from storage import ensure_files
from config import TOKEN, FILES
from group_handlers import register_group_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import register_draw_handlers
from admin_handlers import register_admin_handlers
from owner_handlers import register_owner_handlers
from template_handlers import register_template_handlers
from subscription_handlers import register_subscription_handlers, start_reminders
from scheduler import load_jobs, schedule_raffle

# ----------------------------
# CONFIGURACIÓN DE LOGGING
# ----------------------------
# Para ver INFO de scheduler y errores
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)

# ----------------------------
# INICIALIZACIÓN DE ARCHIVOS
# ----------------------------
# Crea los JSON vacíos si no existen
ensure_files()

# ----------------------------
# CREACIÓN DEL BOT
# ----------------------------
bot = TeleBot(TOKEN)

# ----------------------------
# REGISTRO DE MÓDULOS / HANDLERS
# ----------------------------

# 1) Handlers de grupos (activación, zona horaria, etc.)
register_group_handlers(bot)

# 2) Handlers de referidos y listas de participantes
register_referral_handlers(bot)

# 3) Handlers de sorteo (inscripción, lista, top, agendar)
register_raffle_handlers(bot)

# 4) Handlers de ejecución de sorteo y comando /sortear
register_draw_handlers(bot)

# 5) Panel de administración (autorizados, suscripciones, grupos, mensajes)
register_admin_handlers(bot)

# 6) Panel de propietario (misgrupos, gestión privada vía teclado)
register_owner_handlers(bot)

# 7) Plantillas por grupo (/set_template, /get_templates)
register_template_handlers(bot)

# 8) Suscripciones y recordatorios (/misuscripciones y aviso 5 días antes)
register_subscription_handlers(bot)

# ----------------------------
# SCHEDULER:  
# - Carga jobs guardados para sorteos programados
# - Inicia recordatorios diarios
# ----------------------------
load_jobs(bot)             # carga y lanza jobs de FILES['jobs']
start_reminders(bot)       # programa cron diario de recordatorios

# ----------------------------
# LIMPIEZA DE WEBHOOK Y POLLING
# ----------------------------
bot.remove_webhook()       # asegurar que no quede webhook
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
