# owner_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import schedule_raffle
from config import FILES
from zoneinfo import available_timezones, ZoneInfo
from datetime import datetime

# Define las macro-zonas y, para cada una, filtramos de zoneinfo.available_timezones()
MACROZONES = {
    "Africa":    [tz for tz in available_timezones() if tz.startswith("Africa/")],
    "America":   [tz for tz in available_timezones() if tz.startswith("America/")],
    "Asia":      [tz for tz in available_timezones() if tz.startswith("Asia/")],
    "Atlantic":  [tz for tz in available_timezones() if tz.startswith("Atlantic/")],
    "Australia": [tz for tz in available_timezones() if tz.startswith("Australia/")],
    "Europe":    [tz for tz in available_timezones() if tz.startswith("Europe/")],
    "Pacific":   [tz for tz in available_timezones() if tz.startswith("Pacific/")],
}

def register_owner_handlers(bot: TeleBot):
    # Paso 1: Muesta los grupos que gestionas
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

    # Paso 2: Manejo de todas las opciones de propietario
    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner_selection(msg):
        uid  = msg.from_user.id
        text = msg.text.strip()
        grupos = load('grupos')

        # 🔙 Salir de menú
        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # Seleccionar grupo
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")
            # Construye menú principal de gestión
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"),
                   KeyboardButton("🏆 Ver top invitadores"),
                   KeyboardButton("🔄 Reiniciar sorteo"))
            kb.add(KeyboardButton("🗑️ Borrar lista de sorteo"),
                   KeyboardButton("⏰ Agendar sorteo"),
                   KeyboardButton("🌐 Cambiar zona horaria"))
            kb.add(KeyboardButton("🔙 Salir"))
            # Guarda contexto de grupo
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = {"group": gid}
            return bot.send_message(uid,
                f"⚙️ *Gestión Grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # A partir de aquí necesitamos tener el grupo en contexto
        ctx = getattr(bot, 'user_data', {}).get(uid)
        if not ctx or 'group' not in ctx:
            return

        gid = ctx['group']

        # 📂 Ver participantes
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

        # 🗑️ Borrar lista de sorteo
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
            return bot.register_next_step_handler(
                bot.send_message(uid, "Ejemplo: `2025-07-22_10:30`"),
                process_schedule
            )

        # 🌐 Cambiar zona horaria — Paso 1: macro-zona
        if text == "🌐 Cambiar zona horaria":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            # Ponemos 3 botones por fila
            macro_list = list(MACROZONES.keys()) + ["Atrás"]
            for i in range(0, len(macro_list), 3):
                kb.row(*(KeyboardButton(name) for name in macro_list[i:i+3]))
            bot.send_message(uid,
                "🌐 *Cambiar Zona Horaria*\n"
                "Selecciona primero la _macro-zona_:",
                parse_mode='Markdown',
                reply_markup=kb
            )
            return bot.register_next_step_handler(bot.send_message(uid, "Elige: Africa, America, ..."), process_macrozone)

    # --- Maneja selección de macro-zona ---
    def process_macrozone(msg):
        uid   = msg.from_user.id
        macro = msg.text.strip()
        if macro == "Atrás":
            return handle_owner_selection(msg)  # vuelve al menú principal
        if macro not in MACROZONES:
            return bot.reply_to(msg, "⚠️ Macro-zona inválida. Elige una de la lista.")
        # guarda macro en contexto
        bot.user_data[uid]['macro'] = macro
        # construye teclado de zonas (3xN)
        tzs = MACROZONES[macro]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(0, len(tzs), 3):
            kb.row(*(KeyboardButton(t) for t in tzs[i:i+3]))
        kb.add(KeyboardButton("Atrás"))
        bot.send_message(uid,
            f"🌐 *{macro}* — selecciona tu zona:",
            parse_mode='Markdown',
            reply_markup=kb
        )
        return bot.register_next_step_handler(bot.send_message(uid, "Elige por ejemplo: America/Havana"), process_specific_zone)

    # --- Maneja selección de zona final ---
    def process_specific_zone(msg):
        uid  = msg.from_user.id
        text = msg.text.strip()
        ctx  = bot.user_data.get(uid, {})
        gid  = ctx.get('group')
        macro= ctx.get('macro')
        if text == "Atrás":
            return handle_owner_selection(msg)  # regresa al menú principal
        if not macro or text not in MACROZONES.get(macro, []):
            return bot.reply_to(msg, "⚠️ Zona inválida. Elige una de la lista.")
        # guarda en grupos.json
        grupos = load('grupos')
        grupos[gid]['timezone'] = text
        save('grupos', grupos)
        bot.send_message(uid,
            f"✅ Zona de `{gid}` actualizada a *{text}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    # --- Función que dispara el sorteo programado ---
    def process_schedule(msg):
        uid  = msg.from_user.id
        ctx  = bot.user_data.get(uid, {})
        gid  = ctx.get('group')
        text = msg.text.strip()
        try:
            dt = datetime.strptime(text, "%Y-%m-%d_%H:%M")
            tzname = load('grupos').get(gid, {}).get('timezone', 'UTC')
            dt = dt.replace(tzinfo=ZoneInfo(tzname))
            schedule_raffle(bot, gid, dt)
            bot.send_message(uid,
                f"✅ Sorteo programado para *{dt.strftime('%Y-%m-%d %H:%M')}* ({tzname}).",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception:
            bot.reply_to(msg,
                "❌ Formato inválido. Usa `YYYY-MM-DD_HH:MM` y asegúrate de tener zona.",
                parse_mode='Markdown'
        )
