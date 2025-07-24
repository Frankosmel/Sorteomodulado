import re
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMINS, PLANS
from utils import ensure_files
from storage import load
from auth import is_valid
from owner_handlers import show_owner_menu, register_owner_handlers
from admin_handlers import show_admin_menu, register_admin_handlers
from raffle_handlers import register_raffle_handlers
from draw_handlers import register_draw_handlers
from group_handlers import register_group_handlers
from payments_handlers import register_payment_handlers
from scheduler import load_jobs, start_reminders

# ————— Inicialización de archivos y bot —————
ensure_files()
bot = TeleBot(TOKEN)

# ————— Función para escapar caracteres conflictivos en Markdown —————
def escape_md(text):
    return re.sub(r'([_*()~`>#+=|{}.!-])', r'\\\1', text)

# ————— URL de suscripción —————
BOT_USERNAME = bot.get_me().username
SUBSCRIBE_URL = f"https://t.me/{BOT_USERNAME}?start=subscribe"

# ————— Carga de usuarios autorizados y grupos autorizados —————
auth_data = load("autorizados")
AUTH_USERS = set(auth_data.get("users", []))

grupos_aut_data = load("grupos_autorizados")
AUTH_GROUPS = set(grupos_aut_data.get("groups", []))

# ————— Manejador del comando /start —————
@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != 'private':
        return bot.reply_to(message, "👋 Escríbeme en privado para ver tu menú.")

    uid = message.from_user.id

    # Si es administrador
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Si es dueño de algún grupo autorizado o usuario autorizado
    if uid in AUTH_USERS or is_valid(uid):
        return show_owner_menu(bot, uid)

    # Si no está validado pero activó algún grupo
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # Mostrar planes de suscripción
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

# ————— Manejador general para mensajes en grupos no autorizados —————
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def handle_group_message(message):
    if str(message.chat.id) not in AUTH_GROUPS:
        try:
            bot.reply_to(
                message,
                "⚠️ Este grupo no está autorizado para utilizar el bot.\n\n"
                "Contacta con el administrador para activarlo. Solo se permiten grupos autorizados."
            )
        except Exception:
            pass

# ————— Registro de todos los handlers —————
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
register_draw_handlers(bot)
register_group_handlers(bot)
register_payment_handlers(bot)

# ————— Scheduler y recordatorios —————
load_jobs(bot)
start_reminders(bot)

# ————— Iniciar polling —————
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
