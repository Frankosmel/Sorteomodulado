# main.py

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMINS, PLANS
from storage import ensure_files, load
from auth import is_valid
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import do_draw
from scheduler import load_jobs, start_reminders
from payments_handlers import register_payment_handlers

# ——— Inicialización ———
ensure_files()
bot = TeleBot(TOKEN)


# ——— /start: menú según rol o planes para nuevos usuarios ———
@bot.message_handler(commands=['start'])
def handle_start(msg):
    # Solo en privado
    if msg.chat.type != 'private':
        return bot.reply_to(msg, "👋 Escríbeme en privado para ver tu menú.")
    uid = msg.from_user.id

    # Si eres super‐admin, muestro panel de Admin
    if uid in ADMINS:
        return show_admin_menu(bot, uid)

    # Si eres owner (tienes al menos un grupo activado)
    grupos = load('grupos')
    for gid, info in grupos.items():
        if info.get('activado_por') == uid:
            return show_owner_menu(bot, uid)

    # Si tienes suscripción válida pero ningún grupo todavía
    if is_valid(uid):
        return bot.send_message(
            uid,
            "✅ Tienes suscripción activa pero aún no has añadido el bot a ningún grupo.\n"
            "🔗 Invita al bot a tus grupos o contacta al soporte si necesitas ayuda."
        )

    # Si no estás autorizado: muestro planes de suscripción
    kb = InlineKeyboardMarkup(row_width=1)
    for plan in PLANS:
        kb.add(InlineKeyboardButton(plan['label'], callback_data=plan['key']))
    kb.add(InlineKeyboardButton("💬 Contactar al soporte", url="https://t.me/frankosmel"))

    bot.send_message(
        uid,
        "📦 *Planes de Suscripción*\n\n"
        "Elige el plan que mejor se adapte a tus necesidades para activar el bot en tus grupos:",
        parse_mode='Markdown',
        reply_markup=kb
    )


# ——— Registro de todos los manejadores ———
register_referral_handlers(bot)        # invita y cuenta participantes
register_raffle_handlers(bot)          # /addsorteo, /sorteo_lista, /top, /lista
register_admin_handlers(bot)           # menú y comandos de administración
register_owner_handlers(bot)           # menú y comandos de owner
do_draw(bot)                           # manejo de /sortear y visualizaciones
register_payment_handlers(bot)         # flujo de contratación de planes
load_jobs(bot)                         # carga y programa jobs pendientes
start_reminders(bot)                   # recordatorios de suscripción

# ——— Desactivar webhooks y usar long polling ———
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
```0
