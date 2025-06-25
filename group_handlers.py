from telebot import TeleBot
from storage import load, save
from auth import is_valid, register_group

def register_group_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_members(msg):
        # Detecta si el bot fue agregado al grupo
        bot_id = bot.get_me().id
        if any(u.id == bot_id for u in msg.new_chat_members):
            adder = msg.from_user.id
            # Verifica autorización
            if not is_valid(adder):
                bot.send_message(
                    msg.chat.id,
                    "⛔ Acceso no autorizado o pago vencido. Contacta para renovar."
                )
                bot.leave_chat(msg.chat.id)
                return
            # Registra el grupo
            register_group(msg.chat.id, adder)
            bot.send_message(
                msg.chat.id,
                "✅ Bot activado en este grupo. ¡Gracias por tu pago! 🎉"
            )
        # Aquí podrías añadir lógica de referidos si lo deseas
