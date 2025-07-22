# owner_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import schedule_raffle
from config import FILES
from zoneinfo import ZoneInfo, available_timezones
from datetime import datetime

# Define tus macrozonas y sus zonas
MACRO_ZONAS = {
    "Africa":    [z.split("/")[1] for z in available_timezones() if z.startswith("Africa/")],
    "America":   [z.split("/")[1] for z in available_timezones() if z.startswith("America/")],
    "Asia":      [z.split("/")[1] for z in available_timezones() if z.startswith("Asia/")],
    "Europe":    [z.split("/")[1] for z in available_timezones() if z.startswith("Europe/")],
    "Indian":    [z.split("/")[1] for z in available_timezones() if z.startswith("Indian/")],
    "Pacific":   [z.split("/")[1] for z in available_timezones() if z.startswith("Pacific/")],
    "Etc":       [z.split("/")[1] for z in available_timezones() if z.startswith("Etc/")],
}

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

        # 🔙 Salir
        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # Gestionar <chat_id>
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")

            # menú principal de gestión
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"),
                   KeyboardButton("🏆 Ver top invitadores"))
            kb.add(KeyboardButton("🔄 Reiniciar sorteo"),
                   KeyboardButton("🗑️ Borrar lista de sorteo"))
            kb.add(KeyboardButton("⏰ Agendar sorteo"),
                   KeyboardButton("🌐 Cambiar zona horaria"))
            kb.add(KeyboardButton("🔙 Salir"))

            # guarda contexto
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = {'gid': gid}

            return bot.send_message(uid,
                f"⚙️ *Gestión Grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # requiere contexto de grupo
        context = getattr(bot, 'user_data', {}).get(uid)
        if not context:
            return

        gid = context['gid']

        # 👥 Ver participantes
        if text == "👥 Ver participantes":
            partes = load('participantes').get(gid, {})
            if not partes:
                return bot.send_message(uid, "ℹ️ No hay participantes.")
            msg_text = "👥 *Participantes:*\n"
            for uid2, info in partes.items():
                mention = f"@{info['username']}" if info.get('username') else info['nombre']
                msg_text += f"• {mention}\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # 🏆 Top invitadores
        if text == "🏆 Ver top invitadores":
            invs = load('invitaciones').get(gid, {})
            if not invs:
                return bot.send_message(uid, "📉 No hay invitados.")
            top = sorted(invs.items(), key=lambda x:x[1], reverse=True)[:10]
            msg_text = "🏆 *Top Invitadores:*\n"
            for i,(uid2,count) in enumerate(top,1):
                msg_text += f"{i}. `{uid2}` → {count}\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # 🔄 Reiniciar sorteo
        if text == "🔄 Reiniciar sorteo":
            sorteos = load('sorteo')
            sorteos[gid] = {}
            save('sorteo', sorteos)
            return bot.send_message(uid, f"🔁 Sorteo de {gid} reiniciado.")

        # 🗑️ Borrar lista
        if text == "🗑️ Borrar lista de sorteo":
            sorteos = load('sorteo')
            if gid in sorteos:
                del sorteos[gid]
                save('sorteo', sorteos)
                return bot.send_message(uid, f"🗑️ Lista de {gid} eliminada.")
            return bot.send_message(uid, "ℹ️ No había lista activa.")

        # ⏰ Agendar sorteo
        if text == "⏰ Agendar sorteo":
            bot.send_message(uid,
                "⏰ *Agendar Sorteo*\n"
                "✏️ Envía fecha y hora en formato `YYYY-MM-DD_HH:MM`.\n"
                "_Se usará la zona horaria configurada para el grupo._",
                parse_mode='Markdown'
            )
            prompt = bot.send_message(uid, "Ejemplo: `2025-07-22_10:30`")
            return bot.register_next_step_handler(prompt, process_schedule)

        # 🌐 Cambiar zona horaria (menu macrozonas)
        if text == "🌐 Cambiar zona horaria":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for macro in MACRO_ZONAS.keys():
                kb.add(KeyboardButton(macro))
            kb.add(KeyboardButton("🔙 Salir"))
            return bot.send_message(uid,
                "🌐 *Elige Macrozona*: selecciona la región principal:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # Macrozona seleccionada: mostrar sub-zonas de tres en tres
        if text in MACRO_ZONAS:
            zones = MACRO_ZONAS[text]
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            # fila de tres
            for i in range(0, len(zones), 3):
                row = [
                    KeyboardButton(z) for z in zones[i:i+3]
                ]
                kb.row(*row)
            kb.add(KeyboardButton("🔙 Salir"))
            # guarda macro en contexto
            bot.user_data[uid]['macro'] = text
            return bot.send_message(uid,
                f"🌐 *Zonas en {text}* (sin prefijo):",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # Zona específica elegida: aplicar y guardar
        if 'macro' in context and text in MACRO_ZONAS.get(context['macro'], []):
            chat_id = gid
            tz_full = f"{context['macro']}/{text}"
            # valida
            try:
                ZoneInfo(tz_full)
            except Exception:
                return bot.send_message(uid,
                    "❌ Zona inválida. Intenta de nuevo o usa 🔙 Salir.",
                    parse_mode='Markdown'
                )
            # guarda
            grupos = load('grupos')
            grupos[str(chat_id)]['timezone'] = tz_full
            save('grupos', grupos)
            bot.user_data[uid].pop('macro', None)
            return bot.send_message(uid,
                f"✅ Zona horaria de *{chat_id}* actualizada a *{tz_full}*",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )

    def process_schedule(msg):
        uid = msg.from_user.id
        context = bot.user_data.get(uid, {})
        gid = context.get('gid')
        text = msg.text.strip()
        try:
            dt = datetime.strptime(text, "%Y-%m-%d_%H:%M")
            grp = load('grupos').get(gid, {})
            tzname = grp.get('timezone', 'UTC')
            dt = dt.replace(tzinfo=ZoneInfo(tzname))
            schedule_raffle(bot, gid, dt)
            bot.send_message(uid,
                f"✅ Sorteo programado para *{dt.strftime('%Y-%m-%d %H:%M')}* ({tzname}).",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception:
            bot.reply_to(msg,
                "❌ Formato inválido o zona no configurada.\n"
                "Usa `YYYY-MM-DD_HH:MM` y asegúrate de tener zona.",
                parse_mode='Markdown'
        )
