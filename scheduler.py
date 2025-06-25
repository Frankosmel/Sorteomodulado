import random
from telebot import TeleBot
from storage import load, save
from config import FILES, ADMINS
from datetime import datetime

HISTORIAL_FILE = FILES["historial"]

# Asegura que exista historial.json
try:
    with open(HISTORIAL_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(HISTORIAL_FILE, 'w') as f:
        f.write("{}")

def register_draw_handlers(bot: TeleBot):
    @bot.message_handler(commands=['sortear'])
    def sortear(msg):
        if msg.from_user.id not in ADMINS:
            bot.reply_to(msg, "⛔ No tienes permiso para sortear.")
            return
        do_draw(bot, str(msg.chat.id))

def do_draw(bot: TeleBot, chat_id: str):
    """
    Ejecuta el sorteo en el grupo: elige al azar y anuncia al ganador.
    """
    participantes = load('sorteo').get(chat_id, {})
    if not participantes:
        bot.send_message(int(chat_id), "❌ No hay participantes para sortear.")
        return

    ganador_id, info = random.choice(list(participantes.items()))
    nombre = info['nombre']
    username = info.get('username')

    if username:
        mention = f"@{username}"
    else:
        mention = f"[{nombre}](tg://user?id={ganador_id})"

    texto = (
        f"🎉 ¡Felicidades {mention}! Eres el ganador del sorteo 🎁\n"
        f"ID: {ganador_id}"
    )
    bot.send_message(int(chat_id), texto, parse_mode='Markdown')

    # Guardar en historial
    historial = load('historial')
    historial.setdefault(chat_id, []).append({
        "ganador_id": ganador_id,
        "nombre": nombre,
        "timestamp": datetime.utcnow().isoformat()
    })
    save('historial', historial)
