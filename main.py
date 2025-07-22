# main.py

from telebot import TeleBot
from config import TOKEN
from storage import ensure_files
from group_handlers import register_group_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from admin_handlers import register_admin_handlers
from owner_handlers import register_owner_handlers
from draw_handlers import do_draw        # <-- Importamos do_draw, no register_draw_handlers
from scheduler import load_jobs, schedule_raffle, start_reminders

# Inicializar archivos JSON y bot
ensure_files()
bot = TeleBot(TOKEN)

# Registrar manejadores
register_group_handlers(bot)
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)

# Cargar y arrancar scheduler de sorteos programados
load_jobs(bot)

# Arrancar recordatorios de suscripciones
start_reminders(bot)

# /start
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "👋 ¡Hola! Usa tus comandos en el grupo o /admin en privado.")

# Desactivar webhooks y usar polling
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
