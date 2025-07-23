# main.py

import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ————— URL de suscripción con tu bot @sorteos_fs_bot —————
SUBSCRIBE_URL = "https://t.me/sorteos_fs_bot?start=subscribe"

# ————— Carga usuarios autorizados —————
with open("authorized_users.json", "r") as f:
    AUTH_USERS = set(json.load(f)["users"])

# ————— Handler para cuando el bot es añadido a un grupo —————
@bot.message_handler(content_types=['new_chat_members'])
def guard_on_new_group(message):
    # Recorre la lista de nuevos miembros
    for new_member in message.new_chat_members:
        # Si el que entra es el bot mismo...
        if new_member.id == bot.get_me().id:
            actor = message.from_user
            # Y quien lo añadió NO está autorizado...
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
                # y el bot sale del grupo
                bot.leave_chat(message.chat.id)
            # Si está autorizado, no hace nada y permanece
            return
