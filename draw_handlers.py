import random
from telebot import TeleBot
from storage import load, save
from config import FILES, ADMINS

HISTORIAL_FILE = FILES.get("historial", "historial.json")

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

        chat_id = str(msg.chat.id)
        participantes = load('sorteo').get(chat_id, {})
        if not participantes:
            bot.reply_to(msg, "❌ No hay participantes para sortear.")
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
        bot.send_message(msg.chat.id, texto, parse_mode='Markdown')

        # Guardar en historial
        historial = load('historial') if 'historial' in FILES else {}
        historial.setdefault(chat_id, []).append({
            "ganador_id": ganador_id,
            "nombre": nombre,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        })
        save('historial', historial)
