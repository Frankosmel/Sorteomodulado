# owner_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import schedule_raffle
from config import FILES
from zoneinfo import ZoneInfo
from datetime import datetime

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(commands=['misgrupos'])
    def mis_grupos(msg):
        if msg.chat.type != 'private':
            return
        uid = msg.from_user.id
        grupos = load('grupos')
        propios = {gid:info for gid,info in grupos.items() if info.get('activado_por') == uid}
        if not propios:
            return bot.reply_to(msg, "ℹ️ No tienes ningún grupo activado.")
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for gid in propios:
            kb.add(KeyboardButton(f"Gestionar {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))
        bot.send_message(uid,
            "📂 *Tus Grupos Activos:*\nSelecciona uno para gestionar:",
            parse_mode='Markdown',
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner_selection(msg):
        uid = msg.from_user.id
        text = msg.text.strip()
        grupos = load('grupos')

        # Salir
        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # Selección de grupo
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")

            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"))
            kb.add(KeyboardButton("🏆 Ver top invitadores"))
            kb.add(KeyboardButton("🔄 Reiniciar sorteo"))
            kb.add(KeyboardButton("🗑️ Borrar lista de sorteo"))
            kb.add(KeyboardButton("⏰ Agendar sorteo"))
            kb.add(KeyboardButton("🌐 Cambiar zona horaria"))
            kb.add(KeyboardButton("🔙 Salir"))

            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid

            return bot.send_message(uid,
                f"⚙️ *Gestión Grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # Contexto de grupo
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return

        # Ver participantes
        if text == "👥 Ver participantes":
            partes = load('participantes').get(gid, {})
            if not partes:
                return bot.send_message(uid, "ℹ️ No hay participantes.")
            msg_text = "👥 *Participantes:*\n"
            for uid2, info in partes.items():
                mention = f"@{info['username']}" if info.get('username') else info['nombre']
                msg_text += f"• {mention}\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # Ver top invitadores
        if text == "🏆 Ver top invitadores":
            invs = load('invitaciones').get(gid, {})
            if not invs:
                return bot.send_message(uid, "📉 No hay invitados.")
            top = sorted(invs.items(), key=lambda x:x[1], reverse=True)[:10]
            msg_text = "🏆 *Top Invitadores:*\n"
            for i,(uid2,count) in enumerate(top,1):
                msg_text += f"{i}. `{uid2}` → {count}\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # Reiniciar sorteo
        if text == "🔄 Reiniciar sorteo":
            sorteos = load('sorteo')
            sorteos[gid] = {}
            save('sorteo', sorteos)
            return bot.send_message(uid, f"🔁 Sorteo de {gid} reiniciado.")

        # Borrar lista
        if text == "🗑️ Borrar lista de sorteo":
            sorteos = load('sorteo')
            if gid in sorteos:
                del sorteos[gid]
                save('sorteo', sorteos)
                return bot.send_message(uid, f"🗑️ Lista de {gid} eliminada.")
            return bot.send_message(uid, "ℹ️ No había lista activa.")

        # Agendar sorteo (botón)
        if text == "⏰ Agendar sorteo":
            bot.send_message(uid,
                "⏰ *Agendar Sorteo*\n"
                "✏️ Envía fecha y hora en formato `YYYY-MM-DD_HH:MM`.\n"
                "_Se usará la zona horaria configurada para el grupo._",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(bot.send_message(uid, "Ejemplo: `2025-07-22_10:30`"), process_schedule)

        # Cambiar zona horaria
        if text == "🌐 Cambiar zona horaria":
            bot.send_message(uid,
                "🌐 *Cambiar Zona Horaria*\n"
                "✏️ Envía: `<chat_id>,<Zona>`\n"
                "_Ejemplo_: `-1001234567890,Europe/Madrid`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(bot.send_message(uid, "Zona válida: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"), cambiar_zona)

    def process_schedule(msg):
        uid = msg.from_user.id
        gid = bot.user_data.get(uid)
        text = msg.text.strip()
        try:
            # parse input
            dt = datetime.strptime(text, "%Y-%m-%d_%H:%M")
            # load tz
            grp = load('grupos').get(gid, {})
            tzname = grp.get('timezone', 'UTC')
            dt = dt.replace(tzinfo=ZoneInfo(tzname))
            # schedule
            schedule_raffle(bot, gid, dt)
            bot.send_message(uid,
                f"✅ Sorteo programado para *{dt.strftime('%Y-%m-%d %H:%M')}* ({tzname}).",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            bot.reply_to(msg,
                "❌ Formato inválido o zona no configurada.\n"
                "Usa `YYYY-MM-DD_HH:MM` y asegúrate de tener zona.",
                parse_mode='Markdown'
            )

    def cambiar_zona(msg):
        try:
            chat_id, tz = map(str.strip, msg.text.split(','))
            ZoneInfo(tz)  # valida
            gr = load('grupos')
            gr[chat_id]['timezone'] = tz
            save('grupos', gr)
            bot.send_message(msg.from_user.id,
                f"✅ Zona de `{chat_id}` actualizada a *{tz}*.",
                parse_mode='Markdown'
            )
        except Exception:
            bot.send_message(msg.from_user.id,
                "❌ Formato o zona inválida.\n"
                "Formato: `-1001234567890,Europe/Madrid`",
                parse_mode='Markdown'
        )
