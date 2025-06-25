from telebot import TeleBot
from storage import load, save
from config import FILES

def register_referral_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_referrals(msg):
        chat_id = str(msg.chat.id)
        participantes = load('participantes')
        invitaciones = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        for new_user in msg.new_chat_members:
            uid = str(new_user.id)
            adder = msg.from_user
            if uid not in participantes[chat_id]:
                participantes[chat_id][uid] = {
                    "nombre": new_user.first_name,
                    "username": new_user.username
                }
                inv_id = str(adder.id)
                invitaciones[chat_id][inv_id] = invitaciones[chat_id].get(inv_id, 0) + 1

        save('participantes', participantes)
        save('invitaciones', invitaciones)

def register_raffle_handlers(bot: TeleBot):
    @bot.message_handler(commands=['addsorteo'])
    def addsorteo(msg):
        chat_id = str(msg.chat.id)
        user = msg.from_user
        user_id = str(user.id)

        sorteos = load('sorteo')
        sorteos.setdefault(chat_id, {})

        if user_id in sorteos[chat_id]:
            bot.reply_to(msg, "🎉 Ya estás participando en el sorteo.")
            return

        sorteos[chat_id][user_id] = {
            "nombre": user.first_name,
            "username": user.username
        }
        save('sorteo', sorteos)
        bot.reply_to(
            msg,
            f"✅ ¡{user.first_name}, has sido registrado en el sorteo! 🎁"
        )

    @bot.message_handler(commands=['sorteo_lista'])
    def lista_sorteo(msg):
        chat_id = str(msg.chat.id)
        sorteos = load('sorteo').get(chat_id, {})

        if not sorteos:
            bot.reply_to(msg, "📭 Aún no hay participantes registrados.")
            return

        texto = "🎁 *Participantes del Sorteo:*\n\n"
        for uid, info in sorteos.items():
            username = info.get("username")
            nombre = info["nombre"]
            if username:
                texto += f"• @{username} — {nombre}\n"
            else:
                texto += f"• {nombre} — ID: {uid}\n"
        bot.reply_to(msg, texto, parse_mode='Markdown')

    @bot.message_handler(commands=['top'])
    def mostrar_top(msg):
        chat_id = str(msg.chat.id)
        invitaciones = load('invitaciones').get(chat_id, {})
        participantes = load('participantes').get(chat_id, {})

        if not invitaciones:
            bot.reply_to(msg, "📉 Aún nadie ha invitado a otros miembros.")
            return

        top = sorted(invitaciones.items(), key=lambda x: x[1], reverse=True)
        texto = "🏆 *Top Invitadores del Grupo:*\n\n"
        for i, (uid, count) in enumerate(top[:10], start=1):
            info = participantes.get(uid, {"nombre": "Usuario", "username": None})
            if info.get("username"):
                mention = f"@{info['username']} — {info['nombre']}"
            else:
                mention = f"{info['nombre']} — ID: {uid}"
            texto += f"{i}. {mention} — {count} invitado(s)\n"

        bot.reply_to(msg, texto, parse_mode='Markdown')

    @bot.message_handler(commands=['lista'])
    def mostrar_lista(msg):
        chat_id = str(msg.chat.id)
        datos = load('participantes').get(chat_id, {})

        if not datos:
            bot.reply_to(msg, "📭 Aún no se han registrado agregados.")
            return

        texto = "👥 *Usuarios agregados al grupo:*\n\n"
        for uid, info in datos.items():
            if info.get("username"):
                texto += f"• @{info['username']} — {info['nombre']}\n"
            else:
                texto += f"• {info['nombre']} — ID: {uid}\n"

        bot.reply_to(msg, texto, parse_mode='Markdown')
