from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMINS, PLANS
from storage import ensure_files, load
from auth import is_valid
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import do_draw            # debe existir do_draw(bot)
from scheduler import load_jobs, start_reminders
from payments_handlers import register_payment_handlers

# Inicializar archivos JSON y bot
ensure_files()
bot = TeleBot(TOKEN)

# ——— /start — interceptamos para mostrar el menú según tu rol ———
@bot.message_handler(commands=['start'])
def handle_start(msg):
    # Solo válido en chat privado
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # 1) Super‐admin → panel Admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # 2) Usuario con plan activo → panel Owner
    if is_valid(uid):
        return show_owner_menu(bot, uid)

    # 3) Si no tiene plan activo, le mostramos suscripciones
    kb = InlineKeyboardMarkup(row_width=1)
    for plan in PLANS:
        kb.add(InlineKeyboardButton(plan['label'], callback_data=plan['key']))
    kb.add(InlineKeyboardButton("💬 Contactar al soporte", url="https://t.me/franosmel"))

    bot.send_message(
        uid,
        "📦 *Planes de Suscripción*\n\n"
        "Elige el que mejor se adapte a tus necesidades para activar el bot en tus grupos:",
        parse_mode='Markdown',
        reply_markup=kb
    )

# ——— Registrar todos los módulos/handlers ———
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
do_draw(bot)
register_payment_handlers(bot)

# — Scheduler y recordatorios de suscripción ——
load_jobs(bot)
start_reminders(bot)

# — Iniciar bot ——
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
