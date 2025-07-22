# draw_handlers.py

import random
from telebot import TeleBot
from telebot.types import ReplyKeyboardRemove
from storage import load, save
from config import FILES

def register_draw_handlers(bot: TeleBot):
    """
    Registra, en el privado del bot, la opción de 'Sortear ahora' para
    elegir instantáneamente un ganador de un sorteo ya inscrito en un grupo,
    y limpia la lista tras el sorteo.
    """

    @bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text == "🎲 Sortear ahora")
    def handle_manual_draw(msg):
        uid = msg.from_user.id
        # Identificar el grupo activo que gestiona este owner
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return bot.reply_to(
                msg,
                "⚠️ No has seleccionado aún un grupo. Usa “👥 Mis Grupos” y luego “Gestionar <ID>”."
            )

        # Carga los participantes del sorteo para ese grupo
        sorteos = load('sorteo').get(gid, {})
        if not sorteos:
            return bot.send_message(
                uid,
                "ℹ️ No hay participantes en el sorteo de ese grupo."
            )

        # Elegir ganador aleatorio
        ganador_id, info = random.choice(list(sorteos.items()))
        nombre = info.get('nombre', 'Usuario')
        username = info.get('username')
        mention = f"@{username}" if username else nombre

        # Anunciar ganador en el grupo
        bot.send_message(
            int(gid),
            (
                "🎉 *Resultado del Sorteo* 🎉\n\n"
                f"🥳 ¡Felicidades {mention}! 🎊\n\n"
                "Gracias a todos por participar."
            ),
            parse_mode='Markdown'
        )

        # Limpiar la lista de ese grupo
        todos = load('sorteo')
        todos[gid] = {}
        save('sorteo', todos)

        # Notificar al owner en privado
        bot.send_message(
            uid,
            f"✅ Sorteo manual para el grupo `{gid}` realizado.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    # --- Integrar el botón "🎲 Sortear ahora" en el submenú de owner ---
    # Asumimos que owner_handlers genera un ReplyKeyboardMarkup que incluya:
    #     KeyboardButton("🎲 Sortear ahora")
    # junto a "⏰ Agendar sorteo" y otros.
