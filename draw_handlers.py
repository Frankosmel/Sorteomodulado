"""
Handlers para el comando /draw usando pyTelegramBotAPI (TeleBot).
"""

import random
from telebot import TeleBot
from telebot.types import Message
from config import ADMINS
from storage import load

def _perform_draw(chat_id: int, bot: TeleBot, name: str = "Sorteo") -> None:
    """
    Ejecuta un sorteo en el grupo especificado leyendo participantes.json
    """
    participantes = load("participantes")
    grupo = str(chat_id)

    if grupo not in participantes or not participantes[grupo]:
        return bot.send_message(chat_id, "❌ La lista de participantes está vacía.")

    user_id, data = random.choice(list(participantes[grupo].items()))
    nombre = data.get("nombre", "Desconocido")
    username = data.get("username")

    mención = f"@{username}" if username else f"[{nombre}](tg://user?id={user_id})"

    bot.send_message(
        chat_id,
        f"🏆 *{name}*\n\n🎉 ¡El ganador es {mención}!\n🆔 ID: `{user_id}`",
        parse_mode='Markdown'
    )

def realizar_sorteo(bot: TeleBot, chat_id: int, name: str = "Sorteo") -> None:
    """
    Función reutilizable para realizar sorteo desde otro módulo.
    Aplica validaciones como en /draw.
    """
    grupos_aut = load("grupos_autorizados").get("grupos", [])
    if str(chat_id) not in grupos_aut:
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

        grupos_aut = load("grupos_autorizados").get("grupos", [])
        usuarios_aut = load("autorizados").get("users", [])

        if str(chat_id) not in grupos_aut:
            return bot.reply_to(message, "🚫 Este grupo no está autorizado para usar el bot.")

        if str(user_id) not in usuarios_aut and user_id not in ADMINS:
            return bot.reply_to(message, "⛔ No estás autorizado para usar esta función.")

        _perform_draw(chat_id, bot, name="Sorteo Directo")
