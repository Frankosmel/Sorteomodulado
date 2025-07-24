from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from storage import load, save
from auth import is_valid, register_group
import re

def escape_md(text):
    return re.sub(r'([_*()~`>#+=|{}.!-])', r'\\\1', text)

def register_group_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_members(msg: Message):
        bot_id = bot.get_me().id
        chat_id = str(msg.chat.id)
        participantes = load('participantes')
        invitaciones  = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        # URL de suscripción (solo se construye aquí dentro)
        BOT_USERNAME = bot.get_me().username
        SUBSCRIBE_URL = f"https://t.me/{BOT_USERNAME}?start=subscribe"

        for new_user in msg.new_chat_members:

            # — Si el nuevo miembro es el BOT —
            if new_user.id == bot_id:
                actor = msg.from_user
                autorizados = load("autorizados")
                if str(actor.id) not in autorizados:
                    actor_name = escape_md(actor.username or actor.first_name)
                    kb = InlineKeyboardMarkup()
                    kb.add(InlineKeyboardButton("🔒 Suscríbete para activar", url=SUBSCRIBE_URL))
                    bot.send_message(
                        msg.chat.id,
                        f"🚫 {actor_name}, no estás autorizado para añadirme a este grupo.\n\n"
                        "Para usar el bot en grupos debes suscribirte antes.",
                        parse_mode='Markdown',
                        reply_markup=kb
                    )
                    bot.leave_chat(msg.chat.id)
                    return

                # ✅ Está autorizado: registrar grupo
                if not is_valid(actor.id):
                    bot.send_message(
                        msg.chat.id,
                        "⛔ Este grupo no está suscrito. Ve a mi chat privado (/start) para adquirir un plan."
                    )
                    bot.leave_chat(msg.chat.id)
                    return

                try:
                    register_group(msg.chat.id, actor.id)
                    bot.send_message(
                        msg.chat.id,
                        "✅ Bot activado en este grupo. ¡Gracias por tu compra! 🎉"
                    )
                except ValueError:
                    bot.send_message(
                        msg.chat.id,
                        "⚠️ Has alcanzado el límite de grupos de tu plan.\n"
                        "Si quieres más, adquiere otro plan en /start."
                    )
                    bot.leave_chat(msg.chat.id)
                return  # ya manejó al bot, salir

            # — Si se añadió un usuario normal —
            uid = str(new_user.id)
            adder = msg.from_user
            if uid not in participantes[chat_id]:
                participantes[chat_id][uid] = {
                    "nombre":   new_user.first_name,
                    "username": new_user.username
                }
                inv_id = str(adder.id)
                invitaciones[chat_id][inv_id] = invitaciones[chat_id].get(inv_id, 0) + 1

        save('participantes', participantes)
        save('invitaciones', invitaciones)
