import json
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN, ADMINS, PLANS, FILES
from storage import ensure_files, load
from auth import is_valid

from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import register_draw_handlers
from group_handlers import register_group_handlers
from payments_handlers import register_payment_handlers

from scheduler import load_jobs, start_reminders

# ————— Inicialización de archivos y bot —————
ensure_files()
bot = TeleBot(TOKEN)

# ————— URL de suscripción —————
BOT_USERNAME = bot.get_me().username
SUBSCRIBE_URL = f"https://t.me/{BOT_USERNAME}?start=subscribe"

# ————— Carga la lista de usuarios autorizados —————
auth_data = load("autorizados")
AUTH_USERS = set(auth_data.get("users", []))

# ————— Handler: Bot agregado a grupo —————
@bot.message_handler(content_types=['new_chat_members'])
def guard_on_new_group(message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.get_me().id:
            actor = message.from_user
            if actor.id not in AUTH_USERS:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🔒 Suscríbete para activar", url=SUBSCRIBE_URL))
                bot.send_message(
                    message.chat.id,
                    f"🚫 @{actor.username or actor.first_name}, no estás autorizado para añadirme a este grupo.\n\n"
                    "Para usar el bot en grupos debes suscribirte antes.",
                    parse_mode='Markdown',
                    reply_markup=kb
                )
                bot.leave_chat(message.chat.id)
            return

# ————— Comando /start —————
@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != 'private':
        return bot.reply_to(message, "👋 Escríbeme en privado para ver tu menú.")

    uid = message.from_user.id

    # Si es admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Si tiene plan activo
    if is_valid(uid):
        return show_owner_menu(bot, uid)

    # Si ha activado al menos un grupo
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # Si no tiene plan ni grupos: mostrar planes
    kb = InlineKeyboardMarkup(row_width=1)
    for plan in PLANS:
        kb.add(InlineKeyboardButton(plan['label'], callback_data=plan['key']))
    kb.add(InlineKeyboardButton("💬 Soporte", url="https://t.me/franosmel"))

    bot.send_message(
        uid,
        "📦 *Planes de Suscripción*\n\n"
        "Elige el que mejor se adapte a tus necesidades para activar el bot en tus grupos:",
        parse_mode='Markdown',
        reply_markup=kb
    )

# ————— Registro de handlers —————
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
register_draw_handlers(bot)
register_group_handlers(bot)
register_payment_handlers(bot)

# ————— Scheduler —————
load_jobs(bot)
start_reminders(bot)

# ————— Inicio del bot —————
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
