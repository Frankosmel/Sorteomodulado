from telebot import TeleBot
from storage import load, save
from config import FILES, ADMINS
from datetime import datetime
from zoneinfo import ZoneInfo
import random

def register_referral_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_referrals(msg):
        chat_id = str(msg.chat.id)
        participantes = load('participantes')
        invitaciones  = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        for new_user in msg.new_chat_members:
            uid   = str(new_user.id)
            adder = msg.from_user
            if uid not in participantes[chat_id]:
                participantes[chat_id][uid] = {
                    "nombre":   new_user.first_name,
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
        user    = msg.from_user
        user_id = str(user.id)

        grupos_aut = load('grupos_autorizados').get("grupos", [])
        usuarios_aut = load('autorizados').get("users", [])

        # Verificar que el grupo esté autorizado
        if chat_id not in grupos_aut:
            return bot.reply_to(msg, "🚫 Este grupo no está autorizado para usar el bot.")
        
        # Verificar que el usuario también esté autorizado o sea admin
        if user_id not in usuarios_aut and user_id not in map(str, ADMINS):
            return bot.reply_to(msg, "⛔ No estás autorizado para usar esta función.")

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
    def lista_sorteo(msg):
        chat_id = str(msg.chat.id)
        user_id = str(msg.from_user.id)

        grupos_aut = load('grupos_autorizados').get("grupos", [])
        usuarios_aut = load('autorizados').get("users", [])

        if chat_id not in grupos_aut:
            return bot.reply_to(msg, "🚫 Este grupo no está autorizado para usar el bot.")
        
        if user_id not in usuarios_aut and user_id not in map(str, ADMINS):
            return bot.reply_to(msg, "⛔ No estás autorizado para usar esta función.")

        sorteos = load('sorteo').get(chat_id, {})

        if not sorteos:
            bot.reply_to(msg, "📭 Aún no hay participantes registrados.")
            return

        texto = "🎁 *Participantes del Sorteo:*\n\n"
        for uid, info in sorteos.items():
            username = info.get("username")
            nombre   = info["nombre"]
            if username:
                texto += f"• @{username} — {nombre}\n"
            else:
                texto += f"• {nombre} — ID: {uid}\n"
        bot.reply_to(msg, texto, parse_mode='Markdown')

def _perform_draw(chat_id: str, bot: TeleBot, name: str):
    """
    Ejecuta un sorteo:
     1) Elige ganador aleatorio de `sorteo.json` para chat_id.
     2) Envía mensaje al grupo con nombre.
     3) Borra la lista de participantes para ese chat.
    """
    grupos_aut = load('grupos_autorizados').get("grupos", [])
    if chat_id not in grupos_aut:
        return bot.send_message(int(chat_id), "🚫 Este grupo no está autorizado para hacer sorteos.")

    sorteos = load('sorteo').get(chat_id, {})
    if not sorteos:
        return bot.send_message(int(chat_id), "ℹ️ No hay participantes para sortear.")
    ganador_id, info = random.choice(list(sorteos.items()))
    nombre   = info.get('nombre')
    username = info.get('username')
    mention = f"@{username}" if username else f"[{nombre}](tg://user?id={ganador_id})"
    bot.send_message(
        int(chat_id),
        f"🎉 *¡Ganador del sorteo “{name}”!* 🎉\n\n{mention}",
        parse_mode='Markdown'
    )
    # limpiar lista
    all_sorteos = load('sorteo')
    all_sorteos.pop(chat_id, None)
    save('sorteo', all_sorteos)
