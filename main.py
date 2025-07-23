# main.py

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMINS, PLANS
from storage import ensure_files, load
from auth import is_valid
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import register_draw_handlers
from scheduler import load_jobs, start_reminders
from payments_handlers import register_payment_handlers

# Inicializar archivos JSON
ensure_files()

# Crear instancia del bot
bot = TeleBot(TOKEN)

# ——— /start ———
@bot.message_handler(commands=['start'])
def handle_start(msg):
    # Solo privado
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # Super-admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Owner (tiene al menos un grupo activo)
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # No autorizado → muestro planes
    kb = InlineKeyboardMarkup(row_width=1)
    for plan in PLANS:
        kb.add(InlineKeyboardButton(plan['label'], callback_data=plan['key']))
    kb.add(InlineKeyboardButton("💬 Contactar al soporte", url="https://t.me/frankosmel"))

    bot.send_message(
        uid,
        "📦 *Planes de Suscripción*\n\n"
        "Elige el plan que quieras contratar:",
        parse_mode='Markdown',
        reply_markup=kb
    )

# ——— Registro de handlers ———
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
register_draw_handlers(bot)
register_payment_handlers(bot)
load_jobs(bot)
start_reminders(bot)

# Desactivar webhooks y usar polling
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
