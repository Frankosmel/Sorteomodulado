# main.py

from telebot import TeleBot
from config import TOKEN, ADMINS
from storage import ensure_files, load
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import register_draw_handlers
from scheduler import load_jobs, start_reminders

# Inicializar archivos JSON y bot
ensure_files()
bot = TeleBot(TOKEN)

# ——— /start: menú según rol ———
@bot.message_handler(commands=['start'])
def handle_start(msg):
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # Super‐admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Owner: busca grupos que activó
    grupos = load('grupos')
    propios = {gid:info for gid,info in grupos.items() if info.get('activado_por') == uid}
    if propios:
        return show_owner_menu(bot, uid)

    # No autorizado
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("💳 Ver planes disponibles", url="https://t.me/Frankosmel")
    )
    bot.send_message(
        uid,
        "ℹ️ *No estás autorizado.*\n\n"
        "Para activar tu suscripción, haz clic en el botón:",
        parse_mode='Markdown',
        reply_markup=kb
    )

# ——— Registrar todos los handlers ———
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_draw_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)

# ——— Scheduler ———
load_jobs(bot)
start_reminders(bot)

# Desactivar webhooks y usar polling
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
