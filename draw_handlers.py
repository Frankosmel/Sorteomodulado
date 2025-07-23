# draw_handlers.py

import random
from telebot import TeleBot
from telebot.types import Message
from storage import load, save

def perform_draw(chat_id: str | int, bot: TeleBot, name: str = "Sorteo"):
    """
    Realiza el sorteo en el chat `chat_id`:
      - Lee los participantes de 'sorteo.json'
      - Elige uno al azar
      - Envía el anuncio al chat
      - Limpia la lista para futuros sorteos
    """
    chat_id_str = str(chat_id)
    participantes = load('sorteo').get(chat_id_str, {})

    if not participantes:
        # No hay quién sortear, aviso genérico
        bot.send_message(
            chat_id,
            "ℹ️ *No hay participantes para el sorteo.*",
            parse_mode='Markdown'
        )
        return

    # Elegir ganador
    user_id, info = random.choice(list(participantes.items()))
    nombre   = info.get('nombre', 'Usuario')
    username = info.get('username')
    if username:
        mention = f"@{username}"
    else:
        mention = f"[{nombre}](tg://user?id={user_id})"

    # Mensaje de resultado
    texto = (
        f"🎉 *{name} FINALIZADO!* 🎉\n\n"
        f"👉 _¡El ganador es {mention}!_\n\n"
        "🏆 ¡Felicidades!\n"
        "_Gracias por participar._"
    )
    bot.send_message(
        chat_id,
        texto,
        parse_mode='Markdown'
    )

    # Limpiar lista para el próximo sorteo
    all_sorteos = load('sorteo')
    all_sorteos[chat_id_str] = {}
    save('sorteo', all_sorteos)


def register_draw_handlers(bot: TeleBot):
    """
    Registra el comando /sortear para realizar un sorteo inmediato
    dentro del grupo donde se invoque.
    """
    @bot.message_handler(commands=['sortear'])
    def handle_sortear(msg: Message):
        # Usamos perform_draw para no duplicar lógica
        perform_draw(msg.chat.id, bot, name="Sorteo")
