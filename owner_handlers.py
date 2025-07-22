# owner_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import schedule_raffle
from config import FILES
from zoneinfo import ZoneInfo, available_timezones
from datetime import datetime

# Pre-construimos un dict de macrozonas a zonas filtradas
_MACROZONAS = {
    "Africa":     [tz for tz in available_timezones() if tz.startswith("Africa/")],
    "America":    [tz for tz in available_timezones() if tz.startswith("America/")],
    "Asia":       [tz for tz in available_timezones() if tz.startswith("Asia/")],
    "Atlantic":   [tz for tz in available_timezones() if tz.startswith("Atlantic/")],
    "Australia":  [tz for tz in available_timezones() if tz.startswith("Australia/")],
    "Europe":     [tz for tz in available_timezones() if tz.startswith("Europe/")],
    "Pacific":    [tz for tz in available_timezones() if tz.startswith("Pacific/")],
}

def register_owner_handlers(bot: TeleBot):

    # Paso 1: Mostrar lista de grupos del owner
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
        bot.send_message(
            uid,
            "📂 *Tus Grupos Activos:*\nSelecciona uno para gestionar:",
            parse_mode='Markdown',
            reply_markup=kb
        )

    # Paso 2: Manejar selección de grupo y sub-opciones
    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner_selection(msg):
        uid = msg.from_user.id
        text = msg.text.strip()
        grupos = load('grupos')

        # 🔙 Salir completo
        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # Selección de un grupo
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
            # Guardamos en user_data el grupo activo
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid
            return bot.send_message(
                uid,
                f"⚙️ *Gestión Grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # Contexto de grupo activo
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return

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

        # 🏆 Ver top invitadores
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
            bot.send_message(
                uid,
                "⏰ *Agendar Sorteo*\n"
                "✏️ Envía fecha y hora en formato `YYYY-MM-DD_HH:MM`.\n"
                "_Se usará la zona horaria configurada para el grupo._",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                bot.send_message(uid, "Ejemplo: `2025-07-22_10:30`"),
                process_schedule
            )

        # 🌐 Cambiar zona horaria: mostramos macrozonas
        if text == "🌐 Cambiar zona horaria":
            kb1 = ReplyKeyboardMarkup(resize_keyboard=True)
            for macro in _MACROZONAS.keys():
                kb1.add(KeyboardButton(macro))
            kb1.add(KeyboardButton("🔙 Salir"))
            return bot.send_message(
                uid,
                "🌐 *Cambiar Zona Horaria*\n"
                "Selecciona macrozona:",
                parse_mode='Markdown',
                reply_markup=kb1
            )

        # Nivel 2: selección de macrozona
        if text in _MACROZONAS:
            zonas = _MACROZONAS[text]
            kb2 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for tz in zonas[:12]:
                kb2.add(KeyboardButton(tz))
            # si hay más, los agrupamos en otra página
            if len(zonas) > 12:
                kb2.add(KeyboardButton("Más…"))
            kb2.add(KeyboardButton("🔙 Salir"))
            # guardamos la lista completa en user_data
            bot.user_data[uid + "_tz_list"] = zonas
            bot.user_data[uid + "_tz_page"] = 0
            return bot.send_message(
                uid,
                f"⏱ *{text}*: selecciona tu zona horaria:",
                parse_mode='Markdown',
                reply_markup=kb2
            )

        # Paginación “Más…” de zonas
        if text == "Más…" and bot.user_data.get(uid + "_tz_list"):

            zonas = bot.user_data[uid + "_tz_list"]
            page = bot.user_data.get(uid + "_tz_page", 0) + 1
            start = page * 12
            kb3 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for tz in zonas[start:start + 12]:
                kb3.add(KeyboardButton(tz))
            if start + 12 < len(zonas):
                kb3.add(KeyboardButton("Más…"))
            kb3.add(KeyboardButton("🔙 Salir"))
            bot.user_data[uid + "_tz_page"] = page
            return bot.send_message(
                uid,
                "🔄 *Siguiente listado de zonas:*",
                parse_mode='Markdown',
                reply_markup=kb3
            )

        # Nivel 3: selección concreta de zona
        if text in available_timezones():
            try:
                # aplicamos la zona
                Zona = text
                grupos = load('grupos')
                grupos[bot.user_data[uid]]['timezone'] = Zona
                save('grupos', grupos)
                return bot.send_message(
                    uid,
                    f"✅ Zona de `{bot.user_data[uid]}` actualizada a *{Zona}*.",
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardRemove()
                )
            except Exception:
                return bot.send_message(
                    uid,
                    "❌ Error guardando la zona. Intenta de nuevo.",
                    parse_mode='Markdown'
                )

    # ----------------- Helpers internos -----------------

    def process_schedule(msg):
        uid = msg.from_user.id
        gid = bot.user_data.get(uid)
        text = msg.text.strip()
        try:
            from datetime import datetime
            dt = datetime.strptime(text, "%Y-%m-%d_%H:%M")
            grp = load('grupos').get(gid, {})
            tzname = grp.get('timezone', 'UTC')
            dt = dt.replace(tzinfo=ZoneInfo(tzname))
            schedule_raffle(bot, gid, dt)
            return bot.send_message(
                uid,
                f"✅ Sorteo programado para *{dt.strftime('%Y-%m-%d %H:%M')}* ({tzname}).",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception:
            return bot.reply_to(
                msg,
                "❌ Formato inválido o zona no configurada.\nUsa `YYYY-MM-DD_HH:MM`.",
                parse_mode='Markdown'
            )
