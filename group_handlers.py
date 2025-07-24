# group_handlers.py

from telebot import TeleBot
from telebot.types import Message
from storage import load, save
from auth import is_valid, register_group

def register_group_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_members(msg: Message):
        bot_id = bot.get_me().id
        chat_id = str(msg.chat.id)
        participantes = load('participantes')
        invitaciones  = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        # — Si añaden al BOT —
        if any(u.id == bot_id for u in msg.new_chat_members):
            adder = msg.from_user.id
            # ❌ No suscrito → rechazo inmediato
            if not is_valid(adder):
                bot.send_message(
                    msg.chat.id,
                    "⛔ Este grupo no está suscrito. Ve a mi chat privado (/start) para adquirir un plan."
                )
                bot.leave_chat(msg.chat.id)
                return

            # ✅ Registrar grupo (o avisar si excede límite)
            try:
                register_group(msg.chat.id, adder)

                # Añadir explícitamente 'activado_por' al grupo
                grupos = load("grupos")
                gid = str(msg.chat.id)
                grupos[gid] = grupos.get(gid, {})
                grupos[gid]["activado_por"] = adder
                save("grupos", grupos)

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
                return

        # — Nuevos miembros añadidos (no el bot) —
        for new_user in msg.new_chat_members:
            if new_user.id == bot_id:
                continue
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
