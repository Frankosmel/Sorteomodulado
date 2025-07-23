# main.py

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN, ADMINS, PLANS
from storage import ensure_files, load
from auth import is_valid

from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import (
    register_referral_handlers,
    register_raffle_handlers,
)
from draw_handlers import register_draw_handlers
from group_handlers import register_group_handlers
from payments_handlers import register_payment_handlers

from scheduler import load_jobs, start_reminders

# ————— Inicialización de archivos y bot —————
ensure_files()
bot = TeleBot(TOKEN)

# ————— Manejador del comando /start —————
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Solo en privado
    if message.chat.type != 'private':
        return bot.reply_to(message, "👋 Escríbeme en privado para ver tu menú.")

    uid = message.from_user.id

    # Menú de Administrador
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Menú de Usuarios con plan activo
    if is_valid(uid):
        return show_owner_menu(bot, uid)

    # Menú de Usuarios que han activado grupos
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

# ————— Registro de todos los handlers —————
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
register_draw_handlers(bot)      # Handler para /draw (sorteo)
register_group_handlers(bot)     # Evita añadidos no autorizados
register_payment_handlers(bot)

# ————— Scheduler y recordatorios —————
load_jobs(bot)
start_reminders(bot)

# ————— Iniciar polling —————
# Nos aseguramos de quitar cualquier webhook previo
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
