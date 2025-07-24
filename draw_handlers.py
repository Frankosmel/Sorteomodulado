"""
Handlers para el comando /draw usando pyTelegramBotAPI (TeleBot).
"""

import os
import json
import random
from telebot import TeleBot
from telebot.types import Message
from config import ADMINS
from storage import load

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

def realizar_sorteo(bot: TeleBot, chat_id: int, name: str = "Sorteo") -> None:
    """
    Función reutilizable para realizar sorteo desde otro módulo.
    Aplica validaciones como en /draw.
    """
    grupos_aut = load("grupos_autorizados").get("grupos", [])
    usuarios_aut = load("autorizados").get("users", [])

    # Si se llama desde botones privados, no se conoce el user_id, así que se omite
    if chat_id not in grupos_aut:
        return bot.send_message(chat_id, "🚫 Este grupo no está autorizado para realizar sorteos.")
    
    _perform_draw(chat_id, bot, name)

def register_draw_handlers(bot: TeleBot) -> None:
    """
    Registra el comando /draw en la instancia TeleBot.
    """
    @bot.message_handler(commands=['draw'])
    def do_draw(message: Message) -> None:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Validación de acceso
        grupos_aut = load("grupos_autorizados").get("grupos", [])
        usuarios_aut = load("autorizados").get("users", [])

        if chat_id not in grupos_aut:
            return bot.reply_to(message, "🚫 Este grupo no está autorizado para usar el bot.")

        if user_id not in usuarios_aut and user_id not in ADMINS:
            return bot.reply_to(message, "⛔ No estás autorizado para usar esta función.")

        _perform_draw(chat_id, bot, name="Sorteo Directo")
