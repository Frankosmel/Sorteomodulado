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
        propios = {
            gid: info for gid, info in grupos.items()
            if info.get('activado_por') == uid
        }
        if not propios:
            return bot.reply_to(
                msg,
                "ℹ️ *No tienes ningún grupo activado.*\n\n"
                "Usa /misgrupos cada vez que necesites gestionar tus grupos.",
                parse_mode='Markdown'
            )
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for gid in propios:
            kb.add(KeyboardButton(f"Gestionar {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))
        bot.send_message(
            uid,
            "📂 *Tus Grupos Activos:*\n\n"
            "Selecciona uno para gestionar:",
            parse_mode='Markdown',
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.chat.type == 'private')
    def handle_owner_selection(msg):
        uid = msg.from_user.id
        text = msg.text.strip()
        grupos = load('grupos')

        # 🔙 Salir del menú
        if text == "🔙 Salir":
            return bot.send_message(
                uid,
                "✅ Menú cerrado. Para volver a abrirlo, envía /misgrupos.",
                reply_markup=ReplyKeyboardRemove()
            )

        # 🎛 Seleccionar grupo a gestionar
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(
                    msg,
                    "⚠️ *No puedes gestionar ese grupo.*",
                    parse_mode='Markdown'
                )

            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(
                KeyboardButton("👥 Ver participantes"),
                KeyboardButton("🏆 Ver top invitadores")
            )
            kb.row(
                KeyboardButton("🔄 Reiniciar sorteo"),
                KeyboardButton("🗑️ Borrar lista de sorteo")
            )
            kb.row(
                KeyboardButton("⏰ Agendar sorteo"),
                KeyboardButton("🌐 Cambiar zona horaria")
            )
            kb.add(KeyboardButton("🔙 Salir"))

            # Guardamos contexto de grupo en memoria
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid

            return bot.send_message(
                uid,
                f"⚙️ *Gestión Grupo {gid}*\n\n"
                "Selecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # Si no hay grupo en contexto, ignoramos
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return

        # 👥 Ver participantes
        if text == "👥 Ver participantes":
            partes = load('participantes').get(gid, {})
            if not partes:
                return bot.send_message(
                    uid,
                    "ℹ️ *No hay participantes registrados en este grupo.*",
                    parse_mode='Markdown'
                )
            msg_text = "👥 *Participantes:*\n\n"
            for uid2, info in partes.items():
                mention = f"@{info['username']}" if info.get('username') else info['nombre']
                msg_text += f"• {mention}\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # 🏆 Ver top invitadores
        if text == "🏆 Ver top invitadores":
            invs = load('invitaciones').get(gid, {})
            if not invs:
                return bot.send_message(
                    uid,
                    "📉 *No hay invitados registrados.*",
                    parse_mode='Markdown'
                )
            top = sorted(invs.items(), key=lambda x: x[1], reverse=True)[:10]
            msg_text = "🏆 *Top Invitadores:*\n\n"
            for i, (uid2, count) in enumerate(top, 1):
                msg_text += f"{i}. `{uid2}` → {count} invitado(s)\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # 🔄 Reiniciar sorteo (vaciar lista)
        if text == "🔄 Reiniciar sorteo":
            sorteos = load('sorteo')
            sorteos[gid] = {}
            save('sorteo', sorteos)
            return bot.send_message(
                uid,
                f"🔁 *Sorteo de {gid} reiniciado correctamente.*",
                parse_mode='Markdown'
            )

        # 🗑️ Borrar lista de sorteo
        if text == "🗑️ Borrar lista de sorteo":
            sorteos = load('sorteo')
            if gid in sorteos:
                del sorteos[gid]
                save('sorteo', sorteos)
                return bot.send_message(
                    uid,
                    f"🗑️ *Lista de sorteo de {gid} eliminada.*",
                    parse_mode='Markdown'
                )
            return bot.send_message(
                uid,
                "ℹ️ *No había lista de sorteo activa.*",
                parse_mode='Markdown'
            )

        # ⏰ Agendar sorteo
        if text == "⏰ Agendar sorteo":
            bot.send_message(
                uid,
                "⏰ *Agendar Sorteo*\n\n"
                "✏️ Envía la fecha y hora en formato:\n"
                "`YYYY-MM-DD_HH:MM`\n\n"
                "_Se usará la zona horaria configurada para este grupo._",
                parse_mode='Markdown'
            )
            # Un solo prompt para el ejemplo
            ejemplo = bot.send_message(uid, "`Ejemplo: 2025-07-22_10:30`", parse_mode='Markdown')
            return bot.register_next_step_handler(ejemplo, process_schedule)

        # 🌐 Cambiar zona horaria
        if text == "🌐 Cambiar zona horaria":
            instrucciones = (
                "🌐 *Cambiar Zona Horaria*\n\n"
                "✏️ Envía: `<chat_id>,<Zona>`\n"
                "_Ejemplo_: `-1001234567890,Europe/Madrid`\n\n"
                "📖 Más zonas: [TZ Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)"
            )
            prompt = bot.send_message(uid, instrucciones, parse_mode='Markdown', disable_web_page_preview=True)
            return bot.register_next_step_handler(prompt, cambiar_zona)

    def process_schedule(msg):
        uid = msg.from_user.id
        gid = bot.user_data.get(uid)
        text = msg.text.strip()
        try:
            # Parsear fecha-hora
            dt_naive = datetime.strptime(text, "%Y-%m-%d_%H:%M")
            # Cargar zona del grupo
            grp = load('grupos').get(gid, {})
            tzname = grp.get('timezone', 'UTC')
            dt = dt_naive.replace(tzinfo=ZoneInfo(tzname))
            # Programar sorteo
            schedule_raffle(bot, gid, dt)
            bot.send_message(
                uid,
                f"✅ *Sorteo programado para* `{dt.strftime('%Y-%m-%d %H:%M')}` *({tzname})*",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception:
            bot.reply_to(
                msg,
                "❌ *Formato inválido o zona no configurada.*\n"
                "Usa `YYYY-MM-DD_HH:MM` y asegúrate de haber cambiado la zona antes.",
                parse_mode='Markdown'
            )

    def cambiar_zona(msg):
        try:
            chat_id, tz = map(str.strip, msg.text.split(','))
            ZoneInfo(tz)  # valida que exista
            grupos = load('grupos')
            info = grupos.setdefault(chat_id, {})
            info['timezone'] = tz
            save('grupos', grupos)
            bot.send_message(
                msg.from_user.id,
                f"✅ *Zona horaria de `{chat_id}` actualizada a* _{tz}_",
                parse_mode='Markdown'
            )
        except Exception:
            bot.send_message(
                msg.from_user.id,
                "❌ *Formato o zona inválida.*\n"
                "Formato esperado: `-1001234567890,Europe/Madrid`",
                parse_mode='Markdown'
            )
