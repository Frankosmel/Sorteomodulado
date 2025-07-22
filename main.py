# main.py

from telebot import TeleBot
from config import TOKEN, ADMINS
from storage import ensure_files, load
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers, _perform_draw
from scheduler import load_jobs, start_reminders

# Inicializar archivos JSON y bot
ensure_files()
bot = TeleBot(TOKEN)

# ——— Interceptamos /start PARA DAR MENÚ ———
@bot.message_handler(commands=['start'])
def handle_start(msg):
    # Solo en privado
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # Si eres super-admin, muestro panel Admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Si eres owner (tienes al menos un grupo activado)
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # Si no tienes rol, muestras planes disponibles
    bot.send_message(
        uid,
        "ℹ️ *No estás suscrito.*\n\n"
        "📦 *Planes disponibles:*\n"
        "• 1 mes — 1 grupo — 500 CUP\n"
        "• 2 meses — 2 grupos — 900 CUP (10 % dto)\n"
        "• 3 meses — 3 grupos — 1 200 CUP (20 % dto)\n\n"
        "Para suscribirte, contacta a @franosmel",
        parse_mode='Markdown'
    )

# ——— Registrar resto de handlers ———
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)

# Manejador de sorteo inmediato
@bot.message_handler(commands=['sortear'])
def cmd_sortear(msg):
    chat_id = str(msg.chat.id)
    _perform_draw(chat_id, bot, name="Sorteo")

# Scheduler
load_jobs(bot)
start_reminders(bot)

# Desactivar webhooks y usar polling
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
