# draw_handlers.py

import random
from datetime import datetime
from telebot import TeleBot
from storage import load, save
from template_handlers import render_template

def register_draw_handlers(bot: TeleBot):
    """
    Manejadores relacionados con la ejecución de sorteos:
      - do_draw: función interna que efectúa el sorteo.
      - /sortear: comando manual para disparar el sorteo al instante.
    """

    def do_draw(chat_id: int):
        """
        Elige un ganador al azar entre los inscritos en el sorteo de `chat_id`,
        envía el mensaje de ganador usando plantilla si existe o texto por defecto,
        guarda al ganador en historial y limpia la lista de participantes.
        """
        chat_key = str(chat_id)
        sorteos = load('sorteo')
        inscritos = sorteos.get(chat_key, {})

        if not inscritos:
            return  # No hay participantes

        # Selección aleatoria
        ganador_id, info = random.choice(list(inscritos.items()))
        username = info.get('username')
        nombre   = info.get('nombre', 'Usuario')
        ganador_mention = f"@{username}" if username else f"[{nombre}](tg://user?id={ganador_id})"

        # Timestamp actual
        ahora = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        # Renderizar mensaje usando plantilla 'winner' si existe
        texto = render_template(
            chat_id, 'winner',
            USUARIO=ganador_mention,
            CHAT=chat_id,
            GANADOR=ganador_mention,
            FECHA=ahora
        ) or f"🎉 ¡Felicidades {ganador_mention}! Has sido el ganador del sorteo."

        # Enviar mensaje al grupo
        bot.send_message(chat_id, texto, parse_mode='Markdown')

        # Registrar en historial
        historial = load('historial')
        historial.setdefault(chat_key, []).append({
            "ganador_id":     ganador_id,
            "nombre":         nombre,
            "username":       username,
            "fecha_utc":      ahora
        })
        save('historial', historial)

        # Limpiar lista de inscritos para próximos sorteos
        sorteos[chat_key] = {}
        save('sorteo', sorteos)


    @bot.message_handler(commands=['sortear'])
    def cmd_sortear(msg):
        """
        Sorteo manual inmediato:
          /sortear
        Solo dispara do_draw para el chat actual.
        """
        chat_id = msg.chat.id
        do_draw(chat_id)


    # Exponer la función interna para el scheduler
    bot.do_draw = do_draw
