# draw_handlers.py
"""
Módulo de handlers para el comando /draw (sorteo) en el bot.
- Ejecuta un sorteo aleatorio entre participantes.
- Registra el handler en la aplicación.
"""
import json
import random
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application

# Archivo JSON donde se almacenan los participantes
PARTICIPANTS_FILE = os.getenv('PARTICIPANTS_FILE', 'participants.json')


async def do_draw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Ejecuta el sorteo: elige aleatoriamente un participante y anuncia el ganador.
    Si no existen participantes, informa al usuario.
    """
    # 1) Cargar la lista de participantes
    try:
        with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
            participants = json.load(f)
    except FileNotFoundError:
        await update.message.reply_text(
            "❌ No se encontró la lista de participantes. "
            "Asegúrate de que haya un archivo participants.json válido."
        )
        return
    except json.JSONDecodeError:
        await update.message.reply_text(
            "❌ Error al leer la lista de participantes. El archivo JSON está malformado."
        )
        return

    # 2) Validar contenido
    if not participants:
        await update.message.reply_text(
            "❌ La lista de participantes está vacía. "
            "Agrega participantes antes de hacer el sorteo."
        )
        return

    # 3) Seleccionar ganador
    winner = random.choice(participants)
    name = winner.get('name', 'Desconocido')
    user_id = winner.get('id', '')

    # 4) Anunciar ganador
    message = (
        f"🏆 <b>¡El ganador es {name}!</b>\n"
        f"ID: <code>{user_id}</code>"
    )
    await update.message.reply_html(message)


def register_draw_handlers(application: Application) -> None:
    """
    Registra el handler para el comando /draw en la aplicación.
    Llamar desde main.py luego de crear la instancia de Application.
    """
    draw_cmd = CommandHandler('draw', do_draw)
    application.add_handler(draw_cmd)
