# main.py

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMINS
from storage import ensure_files, load
from auth import is_valid
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import do_draw
from scheduler import load_jobs, start_reminders
from receipts import register_payment_handlers   # ← nuevo

# Inicializar archivos JSON y bot
ensure_files()
bot = TeleBot(TOKEN)

# ——— Interceptamos /start PARA DAR MENÚ ———
@bot.message_handler(commands=['start'])
def handle_start(msg):
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # Super-admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Owner de al menos un grupo
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # No autorizado → muestro planes con botones inline
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌟 1 mes — 1 grupo — 300 CUP", callback_data="plan_1m1g"),
        InlineKeyboardButton("✨ 1 mes — 2 grupos — 550 CUP", callback_data="plan_1m2g"),
        InlineKeyboardButton("⚡ 1 mes — 3 grupos — 700 CUP", callback_data="plan_1m3g"),
        InlineKeyboardButton("🔥 3 meses — 3 grupos — 1 800 CUP", callback_data="plan_3m3g"),
        InlineKeyboardButton("💬 Contactar al soporte", url="https://t.me/franosmel")
    )
    bot.send_message(
        uid,
        "📦 *Planes de Suscripción*\n\n"
        "Elige el que mejor se adapte a tus necesidades para activar el bot en tus grupos:",
        parse_mode='Markdown',
        reply_markup=kb
    )

# ——— Registrar resto de handlers ———
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
register_payment_handlers(bot)   # ← registrar pagos
do_draw(bot)
load_jobs(bot)
start_reminders(bot)

# Webhook off + polling
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
