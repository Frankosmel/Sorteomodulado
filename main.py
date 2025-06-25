import os
from datetime import datetime
from telebot import TeleBot

from config import TOKEN
from storage import ensure_files
from group_handlers import register_group_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from admin_handlers import register_admin_handlers
from owner_handlers import register_owner_handlers
from draw_handlers import register_draw_handlers
from scheduler import load_jobs, schedule_raffle
from reminder_handlers import start_reminders, register_subscription_handlers

# — Inicialización —
ensure_files()
bot = TeleBot(TOKEN)

# — Registrar módulos existentes —
register_group_handlers(bot)
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
register_draw_handlers(bot)
register_subscription_handlers(bot)

# — Handler para programar sorteos —
@bot.message_handler(commands=['agendar_sorteo'])
def agendar_sorteo(msg):
    """
    Formato: /agendar_sorteo YYYY-MM-DD_HH:MM
    Programa un sorteo automático para la fecha/hora indicada.
    """
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(msg, "❌ Formato inválido. Usa: /agendar_sorteo YYYY-MM-DD_HH:MM")
        return
    try:
        run_at = datetime.fromisoformat(parts[1].replace('_', 'T'))
        schedule_raffle(bot, str(msg.chat.id), run_at)
        bot.reply_to(msg, f"✅ Sorteo agendado para {run_at}")
    except Exception:
        bot.reply_to(msg, "❌ Fecha/hora inválida. Usa: /agendar_sorteo YYYY-MM-DD_HH:MM")

# — Arrancar jobs programados y recordatorios —
load_jobs(bot)
start_reminders(bot)

# — Comandos de inicio —
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "👋 ¡Hola! En el grupo usa /addsorteo, /top, /lista o /agendar_sorteo.\n"
        "En privado: /admin, /misgrupos, /misuscripciones."
    )

# — Asegurar polling limpio —
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
