# draw_handlers.py

from telebot import TeleBot
from datetime import datetime
import random
from storage import load, save
from config import FILES

def do_draw(bot: TeleBot, chat_id: str):
    """
    Realiza el sorteo en el chat indicado:
    1. Selecciona un ganador al azar de los inscritos.
    2. Envía mensaje de felicitación con mención e ID.
    3. Registra el resultado en historial.json.
    4. Vacía la lista de participantes para futuros sorteos.
    """
    chat_key = str(chat_id)
    sorteos = load('sorteo')
    participantes = sorteos.get(chat_key, {})

    # Si no hay inscritos
    if not participantes:
        bot.send_message(int(chat_id), "ℹ️ No hay participantes para el sorteo.")
        return

    # Elegir ganador
    winner_id, info = random.choice(list(participantes.items()))
    nombre   = info.get('nombre', 'Usuario')
    username = info.get('username')
    if username:
        mention = f"@{username}"
    else:
        # enlace de mención por ID si no hay username
        mention = f"[{nombre}](tg://user?id={winner_id})"

    # Anunciar ganador
    texto = (
        f"🎉 *¡Felicidades!* 🎉\n\n"
        f"El ganador es {mention}\n"
        f"— ID: `{winner_id}`"
    )
    bot.send_message(int(chat_id), texto, parse_mode='Markdown')

    # Registrar en historial
    historial = load('historial')
    historial.setdefault(chat_key, [])
    historial[chat_key].append({
        "winner_id":  winner_id,
        "timestamp":  datetime.utcnow().isoformat()
    })
    save('historial', historial)

    # Vaciar lista de participantes
    sorteos[chat_key] = {}
    save('sorteo', sorteos)
