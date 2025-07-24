"""
Handlers para el comando /draw usando pyTelegramBotAPI (TeleBot).
"""

import os
import json
import random
from telebot import TeleBot
from telebot.types import Message

PARTICIPANTS_FILE = os.getenv('PARTICIPANTS_FILE', 'participants.json')

def _perform_draw(chat_id: int, bot: TeleBot, name: str = "Sorteo") -> None:
    """
    Ejecuta un sorteo en el grupo especificado leyendo participants.json
    """
    try:
        with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
            participants = json.load(f)
    except FileNotFoundError:
        return bot.send_message(chat_id, "❌ No se encontró el archivo participants.json.")
    except json.JSONDecodeError:
        return bot.send_message(chat_id, "❌ El archivo participants.json está mal formado.")

    if not participants:
        return bot.send_message(chat_id, "❌ La lista de participantes está vacía.")

    winner = random.choice(participants)
    name_winner = winner.get('name', 'Desconocido')
    uid = winner.get('id', '')

    bot.send_message(
        chat_id,
        f"🏆 *{name}*\n\n🎉 ¡El ganador es *{name_winner}*! ID: `{uid}`",
        parse_mode='Markdown'
    )

def register_draw_handlers(bot: TeleBot) -> None:
    """
    Registra el comando /draw en la instancia TeleBot.
    """
    @bot.message_handler(commands=['draw'])
    def do_draw(message: Message) -> None:
        _perform_draw(message.chat.id, bot, name="Sorteo Directo")
