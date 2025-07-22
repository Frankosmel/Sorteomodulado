from telebot import TeleBot, Message
from telebot.types import ChatMemberUpdated
from dateutil import parser
from storage import load, save
from config import FILES
from scheduler import schedule_raffle

def register_referral_handlers(bot: TeleBot):
    """
    Detecta nuevos miembros en el grupo y cuenta quién los agregó.
    Guarda en:
      - participantes.json: datos básicos del miembro agregado.
      - invitaciones.json: contador de cuántos invita cada usuario.
    """
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_referrals(msg: Message):
        chat_id = str(msg.chat.id)
        # Carga o inicializa los datos
        participantes = load('participantes')
        invitaciones   = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        # Para cada usuario nuevo en el mensaje
        for new_user in msg.new_chat_members:
            uid   = str(new_user.id)
            adder = msg.from_user
            # Si aún no estaba registrado
            if uid not in participantes[chat_id]:
                participantes[chat_id][uid] = {
                    "nombre":   new_user.first_name,
                    "username": new_user.username
                }
                inv_id = str(adder.id)
                invitaciones[chat_id][inv_id] = (
                    invitaciones[chat_id].get(inv_id, 0) + 1
                )

        # Guarda cambios
        save('participantes', participantes)
        save('invitaciones', invitaciones)


def register_raffle_handlers(bot: TeleBot):
    """
    Maneja:
      - /addsorteo : registra al usuario en el sorteo activo.
      - /sorteo_lista : muestra lista de inscritos.
      - /top : ranking de invitadores.
      - /lista : muestra quiénes fueron agregados al grupo.
      - /agendar_sorteo : programa un sorteo futuro.
    """

    @bot.message_handler(commands=['addsorteo'])
    def addsorteo(msg: Message):
        chat_id = str(msg.chat.id)
        user    = msg.from_user
        user_id = str(user.id)

        sorteos = load('sorteo')
        sorteos.setdefault(chat_id, {})

        if user_id in sorteos[chat_id]:
            bot.reply_to(msg, "🎉 Ya estás participando en el sorteo.")
            return

        sorteos[chat_id][user_id] = {
            "nombre":   user.first_name,
            "username": user.username
        }
        save('sorteo', sorteos)

        bot.reply_to(
            msg,
            f"✅ ¡{user.first_name}, has sido registrado en el sorteo! 🎁"
        )


    @bot.message_handler(commands=['sorteo_lista'])
    def lista_sorteo(msg: Message):
        chat_id = str(msg.chat.id)
        sorteos = load('sorteo').get(chat_id, {})

        if not sorteos:
            bot.reply_to(msg, "📭 Aún no hay participantes registrados.")
            return

        texto = "🎁 *Participantes del Sorteo:*\n\n"
        for uid, info in sorteos.items():
            nombre   = info["nombre"]
            username = info.get("username")
            if username:
                texto += f"• @{username} — {nombre}\n"
            else:
                texto += f"• {nombre} — ID: {uid}\n"

        bot.reply_to(msg, texto, parse_mode='Markdown')


    @bot.message_handler(commands=['top'])
    def mostrar_top(msg: Message):
        chat_id       = str(msg.chat.id)
        invitaciones  = load('invitaciones').get(chat_id, {})
        participantes = load('participantes').get(chat_id, {})

        if not invitaciones:
            bot.reply_to(msg, "📉 Aún nadie ha invitado a otros miembros.")
            return

        top_list = sorted(
            invitaciones.items(),
            key=lambda x: x[1],
            reverse=True
        )
        texto = "🏆 *Top Invitadores del Grupo:*\n\n"
        for i, (uid, count) in enumerate(top_list[:10], start=1):
            info = participantes.get(uid, {"nombre": "Usuario", "username": None})
            nombre   = info["nombre"]
            username = info.get("username")
            if username:
                mention = f"@{username} — {nombre}"
            else:
                mention = f"{nombre} — ID: {uid}"
            texto += f"{i}. {mention} — {count} invitado(s)\n"

        bot.reply_to(msg, texto, parse_mode='Markdown')


    @bot.message_handler(commands=['lista'])
    def mostrar_lista(msg: Message):
        chat_id = str(msg.chat.id)
        datos   = load('participantes').get(chat_id, {})

        if not datos:
            bot.reply_to(msg, "📭 Aún no se han registrado agregados.")
            return

        texto = "👥 *Usuarios agregados al grupo:*\n\n"
        for uid, info in datos.items():
            nombre   = info["nombre"]
            username = info.get("username")
            if username:
                texto += f"• @{username} — {nombre}\n"
            else:
                texto += f"• {nombre} — ID: {uid}\n"

        bot.reply_to(msg, texto, parse_mode='Markdown')


    @bot.message_handler(commands=['agendar_sorteo'])
    def cmd_agendar_sorteo(msg: Message):
        """
        Programa un sorteo futuro:
          /agendar_sorteo <fecha y hora>
        Ejemplos:
          /agendar_sorteo mañana 9:00
          /agendar_sorteo 2025-07-22 14:00
        """
        partes = msg.text.split(' ', 1)
        if len(partes) < 2:
            return bot.reply_to(msg, "❌ Usa: /agendar_sorteo <fecha y hora>")

        raw = partes[1]
        try:
            # parser.parse acepta "mañana 9:00", "22/07/2025 14:00", etc.
            dt = parser.parse(raw, dayfirst=True)

            # Agenda el job
            schedule_raffle(bot, msg.chat.id, dt)

            bot.reply_to(
                msg,
                f"⏰ Sorteo programado para *{dt.strftime('%Y-%m-%d %H:%M')}*",
                parse_mode='Markdown'
            )
        except Exception:
            bot.reply_to(
                msg,
                "❌ No entendí la fecha/hora.\n"
                "Prueba: `2025-07-22 14:00` o `mañana 9:00`",
                parse_mode='Markdown'
)
