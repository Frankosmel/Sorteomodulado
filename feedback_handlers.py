# feedback_handlers.py
from telebot import TeleBot
from telebot.types import ForceReply, Message
from config import ADMINS

def register_feedback_handlers(bot: TeleBot):
    @bot.message_handler(commands=['feedback'])
    def ask_feedback(msg: Message):
        bot.send_message(
            msg.chat.id,
            "💬 Por favor, escribe tu sugerencia o reporte:",
            reply_markup=ForceReply(selective=True)
        )

    @bot.message_handler(func=lambda m: m.reply_to_message and "escribe tu sugerencia" in m.reply_to_message.text)
    def receive_feedback(msg: Message):
        admin_id = ADMINS[0]
        usuario = msg.from_user
        texto = (
            f"📣 *Nuevo feedback*\n"
            f"De: [{usuario.first_name}](tg://user?id={usuario.id}) (ID {usuario.id})\n\n"
            f"> {msg.text}"
        )
        bot.send_message(admin_id, texto, parse_mode='Markdown')
        bot.reply_to(msg, "✅ ¡Gracias! Tu feedback ha sido enviado.")
