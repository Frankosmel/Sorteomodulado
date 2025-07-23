# main.py

from telebot import TeleBot
from config import TOKEN, ADMINS
from storage import ensure_files, load
from auth import is_valid
from admin_handlers import register_admin_handlers, show_admin_menu
from owner_handlers import register_owner_handlers, show_owner_menu
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from draw_handlers import do_draw                      # ← import correcto
from scheduler import load_jobs, start_reminders
from payments_handlers import register_payment_handlers  # si tienes pagos

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

    # Si no estás autorizado: muestro planes de suscripción
    from config import PLANS  # import dinámico para evitar ciclo
    from payments_handlers import register_payment_handlers

    kb = None
    try:
        # Build inline keyboard de planes
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(row_width=1)
        for plan in PLANS:
            kb.add(InlineKeyboardButton(plan['label'], callback_data=plan['key']))
        kb.add(InlineKeyboardButton("💬 Contactar al soporte", url="https://t.me/franosmel"))
    except:
        kb = None

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
do_draw(bot)                  # registra los manejadores de dibujado
load_jobs(bot)                # carga y programa los jobs pendientes
start_reminders(bot)          # arranca recordatorios diarios
register_payment_handlers(bot)  # registra el flujo de pagos

# Desactivar webhooks y usar polling
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
