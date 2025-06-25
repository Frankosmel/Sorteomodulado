import os
from datetime import datetime
from telebot import TeleBot
from dateutil.parser import parse

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

# — Handler para programar sorteos (formatos flexibles) —
@bot.message_handler(commands=['agendar_sorteo'])
def agendar_sorteo(msg):
    """
    /agendar_sorteo <fecha>
    Acepta:
      • YYYY-MM-DD HH:MM[:SS]
      • YYYY-MM-DDTHH:MM[:SS]
      • 'tomorrow 15:00', 'in 2h', etc.
    """
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(msg,
            "❌ Debes indicar fecha/hora.\n"
            "Ejemplo: /agendar_sorteo 2025-06-26 08:22\n"
            "o /agendar_sorteo tomorrow 15:00"
        )
    try:
        dt = parse(parts[1], dayfirst=False)
        schedule_raffle(bot, str(msg.chat.id), dt)
        bot.reply_to(msg,
            f"✅ Sorteo programado para {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception:
        bot.reply_to(msg,
            "❌ No pude entender esa fecha/hora.\n"
            "Usa ISO (2025-06-26 08:22) o expresiones como 'tomorrow 15:00'."
        )

# — Cargar jobs programados y arrancar recordatorios —
load_jobs(bot)
start_reminders(bot)

# — Comando /start —
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "👋 ¡Hola! En el grupo usa:\n"
        "  /addsorteo, /top, /lista, /agendar_sorteo\n"
        "En privado usa:\n"
        "  /admin, /misgrupos, /misuscripciones, /sortear"
    )

# — Asegurar polling limpio —
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
