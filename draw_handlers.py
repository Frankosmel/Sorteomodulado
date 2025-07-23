# draw_handlers.py

"""
Handlers para el comando /draw usando pyTelegramBotAPI (TeleBot).
"""

import os
import json
import random
from telebot import TeleBot
from telebot.types import Message

PARTICIPANTS_FILE = os.getenv('PARTICIPANTS_FILE', 'participants.json')

def register_draw_handlers(bot: TeleBot) -> None:
    """
    Registra el comando /draw en la instancia TeleBot.
    """

    @bot.message_handler(commands=['draw'])
    def do_draw(message: Message) -> None:
        # Carga participantes
        try:
            with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
                participants = json.load(f)
        except FileNotFoundError:
            return bot.reply_to(
                message,
                "❌ No se encontró participants.json."
            )
        except json.JSONDecodeError:
            return bot.reply_to(
                message,
                "❌ JSON malformado en participants.json."
            )

        if not participants:
            return bot.reply_to(
                message,
                "❌ La lista de participantes está vacía."
            )

        winner = random.choice(participants)
        name = winner.get('name', 'Desconocido')
        uid  = winner.get('id', '')

        bot.send_message(
            message.chat.id,
            f"🏆 ¡El ganador es *{name}*! ID: `{uid}`",
            parse_mode='Markdown'
        )
