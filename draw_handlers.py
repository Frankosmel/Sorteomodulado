# draw_handlers.py

import random
from telebot import TeleBot
from telebot.types import Message
from storage import load, save
from config import FILES

def do_draw(bot: TeleBot):
    """
    Registra en el bot el comando /sortear:
    - Lee los participantes del grupo.
    - Elige uno al azar.
    - Envía un mensaje anunciando al ganador.
    """
    @bot.message_handler(commands=['sortear'])
    def handle_sortear(msg: Message):
        chat_id = str(msg.chat.id)
        sorteos = load('sorteo').get(chat_id, {})

        # Si no hay participantes
        if not sorteos:
            return bot.reply_to(
                msg,
                "ℹ️ *No hay participantes en el sorteo.*",
                parse_mode='Markdown'
            )

        # Elegir ganador
        user_id, info = random.choice(list(sorteos.items()))
        nombre   = info.get('nombre', 'Usuario')
        username = info.get('username')
        # Formatear mención
        if username:
            mention = f"@{username}"
        else:
            mention = f"[{nombre}](tg://user?id={user_id})"

        # Mensaje “bonito” de anuncio
        text = (
            "🎉 *¡SORTEO FINALIZADO!* 🎉\n\n"
            f"👉 El ganador de este sorteo es: {mention}\n\n"
            "¡Felicidades! 🏆\n"
            "_Gracias a todos por participar._"
        )

        bot.send_message(
            msg.chat.id,
            text,
            parse_mode='Markdown'
        )

        # Opcional: vaciar lista para el siguiente sorteo
        sorteos_all = load('sorteo')
        sorteos_all[chat_id] = {}
        save('sorteo', sorteos_all)
