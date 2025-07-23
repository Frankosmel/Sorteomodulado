# main.py

from storage import load
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# URL de suscripción
SUBSCRIBE_URL = "https://t.me/sorteos_fs_bot?start=subscribe"

# Carga la lista de usuarios autorizados desde autorizados.json
AUTH_USERS = set(load("autorizados")["users"])

@bot.message_handler(content_types=['new_chat_members'])
def guard_on_new_group(message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.get_me().id:
            actor = message.from_user
            if actor.id not in AUTH_USERS:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton(
                    "🔒 Suscríbete para activar",
                    url=SUBSCRIBE_URL
                ))
                bot.send_message(
                    message.chat.id,
                    f"🚫 @{actor.username or actor.first_name}, no estás autorizado para añadirme a este grupo.\n\n"
                    "Para usar el bot en grupos debes suscribirte antes.",
                    parse_mode='Markdown',
                    reply_markup=kb
                )
                bot.leave_chat(message.chat.id)
            return
