from telebot import TeleBot
from storage import load, save
from auth import is_valid, register_group

def register_group_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_members(msg):
        bot_id = bot.get_me().id
        chat_id = str(msg.chat.id)
        participantes = load('participantes')
        invitaciones = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        # Si el bot fue agregado, validamos y registramos el grupo
        if any(u.id == bot_id for u in msg.new_chat_members):
            adder = msg.from_user.id
            if not is_valid(adder):
                bot.send_message(
                    msg.chat.id,
                    "⛔ Acceso no autorizado o pago vencido. Contacta para renovar."
                )
                bot.leave_chat(msg.chat.id)
                return
            register_group(msg.chat.id, adder)
            bot.send_message(
                msg.chat.id,
                "✅ Bot activado en este grupo. ¡Gracias por tu pago! 🎉"
            )

        # Para cada NUEVO usuario añadido al grupo (no el bot)
        for new_user in msg.new_chat_members:
            if new_user.id == bot_id:
                continue
            uid = str(new_user.id)
            adder = msg.from_user
            # Registra al participante
            if uid not in participantes[chat_id]:
                participantes[chat_id][uid] = {
                    "nombre": new_user.first_name,
                    "username": new_user.username
                }
                # Incrementa conteo de invitaciones
                inv_id = str(adder.id)
                invitaciones[chat_id][inv_id] = invitaciones[chat_id].get(inv_id, 0) + 1

        save('participantes', participantes)
        save('invitaciones', invitaciones)
