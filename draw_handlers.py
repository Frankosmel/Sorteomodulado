# draw_handlers.py

"""
Módulo de handlers para el comando /draw (sorteo) usando pyTelegramBotAPI (TeleBot).
Define la lógica del sorteo y registra el handler en el bot.
"""

import os
import json
import random
from telebot import TeleBot
from telebot.types import Message

# Ruta al JSON de participantes (puedes cambiar vía env var)
PARTICIPANTS_FILE = os.getenv('PARTICIPANTS_FILE', 'participants.json')

def register_draw_handlers(bot: TeleBot) -> None:
    """
    Registra el handler para el comando /draw en la instancia TeleBot.
    Llamar desde main.py: register_draw_handlers(bot)
    """

    @bot.message_handler(commands=['draw'])
    def do_draw(message: Message) -> None:
        """
        Ejecuta el sorteo: 
        - Carga participantes de JSON
        - Elige uno al azar
        - Responde con el ganador o informa errores
        """
        # 1) Intentar cargar la lista
        try:
            with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
                participants = json.load(f)
        except FileNotFoundError:
            bot.reply_to(
                message,
                "❌ No se encontró la lista de participantes.\n"
                "Asegúrate de que exista 'participants.json'."
            )
            return
        except json.JSONDecodeError:
            bot.reply_to(
                message,
                "❌ Error al leer la lista de participantes.\n"
                "JSON malformado en 'participants.json'."
            )
            return

        # 2) Revisar que no esté vacía
        if not participants:
            bot.reply_to(
                message,
                "❌ La lista de participantes está vacía.\n"
                "Agrega participantes antes de usar /draw."
            )
            return

        # 3) Seleccionar ganador al azar
        winner = random.choice(participants)
        name = winner.get('name', 'Desconocido')
        user_id = winner.get('id', '')

        # 4) Anunciar ganador
        text = (
            f"🏆 ¡El ganador es *{name}*!\n"
            f"ID: `{user_id}`"
        )
        bot.send_message(
            chat_id=message.chat.id,
            text=text,
            parse_mode='Markdown'
        )
