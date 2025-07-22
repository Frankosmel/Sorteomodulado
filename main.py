# main.py

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMINS
from storage import ensure_files, load
from auth import is_valid
from admin_handlers import show_admin_menu, register_admin_handlers
from owner_handlers import show_owner_menu, register_owner_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import do_draw
from scheduler import load_jobs, start_reminders

# — Inicializar archivos y bot —
ensure_files()
bot = TeleBot(TOKEN)

# — Interceptar /start y mostrar menú o planes —
@bot.message_handler(commands=['start'])
def handle_start(msg):
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # 1️⃣ Super-admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # 2️⃣ Owner (tiene al menos un grupo activo)
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # 3️⃣ NO autorizado → mostrar planes y botón de contacto
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💬 Contactar @frankosmel", url="https://t.me/frankosmel"))
    text = (
        "ℹ️ *¡Bienvenido!* Para usar este bot debes suscribirte:\n\n"
        "🟢 *Planes de 1 mes:*\n"
        " • Básico (1 grupo): 500 CUP\n"
        " • Dúo (2 grupos): 900 CUP\n"
        " • Trío (3 grupos): 1 200 CUP\n\n"
        "🔵 *Planes de 3 meses:*\n"
        " • Básico (1 grupo): 1 300 CUP\n"
        " • Dúo (2 grupos): 2 300 CUP\n"
        " • Trío (3 grupos): 3 000 CUP\n\n"
        "Pulsa el botón y envíame un mensaje para adquirir tu suscripción."
    )
    bot.send_message(uid, text, parse_mode='Markdown', reply_markup=kb)

# — Registrar todos los handlers —
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
do_draw(bot)
load_jobs(bot)
start_reminders(bot)

# — Polling —
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
