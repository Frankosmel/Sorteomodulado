# owner_handlers.py

from telebot import TeleBot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from storage import load, save
from scheduler import schedule_raffle
from zoneinfo import ZoneInfo
from datetime import datetime

def show_owner_menu(bot: TeleBot, chat_id: int):
    """Envía el menú principal de owner a `chat_id`."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("👥 Mis Grupos"))
    kb.add(KeyboardButton("🎲 Sorteos"))        # ← Nueva opción
    kb.add(KeyboardButton("🔙 Salir"))
    bot.send_message(
        chat_id,
        "👤 *Panel de Owner*\n\n"
        "Selecciona una opción:",
        parse_mode='Markdown',
        reply_markup=kb
    )

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner(msg):
        uid  = msg.from_user.id
        text = msg.text.strip()
        grupos = load('grupos')
        propios = {
            gid:info for gid,info in grupos.items()
            if info.get('activado_por') == uid
        }

        # ➤ SALIR
        if text == "🔙 Salir":
            return bot.send_message(
                uid,
                "✅ Menú cerrado.",
                reply_markup=ReplyKeyboardRemove()
            )

        # ➤ MIS GRUPOS
        if text == "👥 Mis Grupos":
            if not propios:
                return bot.reply_to(
                    msg,
                    "ℹ️ No tienes ningún grupo activado."
                )
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for gid in propios:
                kb.add(KeyboardButton(f"Gestionar {gid}"))
            kb.add(KeyboardButton("🔙 Salir"))
            return bot.send_message(
                uid,
                "📂 *Tus Grupos Activos:*\nSelecciona uno para gestionar:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # ➤ SORTEOS (nuevo)
        if text == "🎲 Sorteos":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("⏰ Agendar sorteo"))
            kb.add(KeyboardButton("🎯 Realizar sorteo ahora"))
            kb.add(KeyboardButton("🔙 Salir"))
            return bot.send_message(
                uid,
                "🎲 *Gestión de Sorteos*\n\n"
                "Elige una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # ——————————————————————————————————————————
        # Contexto de SORTEOS
        if text == "⏰ Agendar sorteo":
            # Recordamos al owner si no tiene grupos
            if not propios:
                return bot.reply_to(msg, "ℹ️ No tienes grupos para programar.")
            bot.send_message(
                uid,
                "⏰ *Agendar Sorteo*\n"
                "✏️ Envía: `<chat_id> YYYY-MM-DD_HH:MM`\n"
                "_Ejemplo_: `-1001234567890 2025-07-25_15:30`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                msg, process_schedule
            )

        if text == "🎯 Realizar sorteo ahora":
            if not propios:
                return bot.reply_to(msg, "ℹ️ No tienes grupos para sortear.")
            bot.send_message(
                uid,
                "✏️ Envía: `<chat_id>`\n"
                "Se elegirá aleatoriamente un participante.",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                msg, process_draw_now
            )

        # ——————————————————————————————————————————
        # Contexto de GESTIÓN de GRUPO (como antes)
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

            return bot.send_message(
                uid,
                f"⚙️ *Gestión Grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # ——————————————————————————————————————————
        # GESTIÓN DE SUBMENÚ de GRUPO
        gid = getattr(bot, 'user_data', {}).get(uid)
        if gid:
            # Ver participantes
            if text == "👥 Ver participantes":
                partes = load('participantes').get(gid, {})
                if not partes:
                    return bot.send_message(uid, "ℹ️ No hay participantes.")
                msg_text = "👥 *Participantes:*\n"
                for uid2, info in partes.items():
                    mention = (
                        f"@{info['username']}"
                        if info.get('username') else info['nombre']
                    )
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

            # Agendar sorteo desde menú de grupo (igual a 🎲→Agendar)
            if text == "⏰ Agendar sorteo":
                bot.send_message(
                    uid,
                    "⏰ *Agendar Sorteo*\n"
                    "✏️ Envía: `<chat_id> YYYY-MM-DD_HH:MM`\n"
                    "_Ejemplo_: `-1001234567890 2025-07-25_15:30`",
                    parse_mode='Markdown'
                )
                return bot.register_next_step_handler(
                    msg, process_schedule
                )

            # Cambiar zona horaria
            if text == "🌐 Cambiar zona horaria":
                bot.send_message(
                    uid,
                    "🌐 *Cambiar Zona Horaria*\n"
                    "✏️ Envía: `<chat_id>,<Zona>`\n"
                    "_Ejemplo_: `-1001234567890,Europe/Madrid`",
                    parse_mode='Markdown'
                )
                return bot.register_next_step_handler(
                    msg, cambiar_zona
                )

    # ——————————————————————————————————————————
    # Funciones auxiliares para SORTEO PROGRAMADO
    def process_schedule(msg):
        uid  = msg.from_user.id
        partes = msg.text.split()
        if len(partes) != 2:
            return bot.reply_to(
                msg,
                "❌ Formato inválido.\n"
                "Uso: `<chat_id> YYYY-MM-DD_HH:MM`",
                parse_mode='Markdown'
            )
        chat_id, text = partes
        try:
            dt_naive = datetime.strptime(text, "%Y-%m-%d_%H:%M")
        except ValueError:
            return bot.reply_to(
                msg,
                "❌ Fecha u hora no válidas.\n"
                "Formato: `YYYY-MM-DD_HH:MM`",
                parse_mode='Markdown'
            )
        # zona del grupo
        grp = load('grupos').get(chat_id, {})
        tzname = grp.get('timezone', 'UTC')
        try:
            tz = ZoneInfo(tzname)
        except:
            return bot.reply_to(
                msg,
                f"❌ Zona `{tzname}` inválida.\n"
                "Usa `/misgrupos` → Cambiar zona.",
                parse_mode='Markdown'
            )
        run_at = dt_naive.replace(tzinfo=tz)
        schedule_raffle(bot, chat_id, run_at)
        bot.send_message(
            uid,
            f"✅ Sorteo programado para *{run_at.strftime('%Y-%m-%d %H:%M')}* ({tzname}).",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    # ——————————————————————————————————————————
    # Función para sorteo inmediato
    def process_draw_now(msg):
        uid     = msg.from_user.id
        chat_id = msg.text.strip()
        participantes = load('sorteo').get(chat_id, {})
        if not participantes:
            return bot.reply_to(msg, "ℹ️ No hay participantes para sortear.", parse_mode='Markdown')
        import random
        ganador_id, info = random.choice(list(participantes.items()))
        nombre   = info.get('nombre')
        username = info.get('username')
        mention = f"@{username}" if username else f"[{nombre}](tg://user?id={ganador_id})"
        bot.send_message(
            int(chat_id),
            f"🎉 *¡Ganador del sorteo!* 🎉\n\n{mention}",
            parse_mode='Markdown'
        )
        # limpiar sorteo
        sorteos = load('sorteo')
        sorteos.pop(chat_id, None)
        save('sorteo', sorteos)
        # confirmar en PV
        bot.send_message(
            uid,
            f"✅ Sorteo realizado en `{chat_id}`: {mention}",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    # ——————————————————————————————————————————
    # Cambiar zona horaria
    def cambiar_zona(msg):
        try:
            chat_id, tz = map(str.strip, msg.text.split(','))
            ZoneInfo(tz)
            gr = load('grupos')
            gr[chat_id]['timezone'] = tz
            save('grupos', gr)
            bot.send_message(
                msg.from_user.id,
                f"✅ Zona de `{chat_id}` actualizada a *{tz}*.",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception:
            bot.send_message(
                msg.from_user.id,
                "❌ Formato o zona inválida.\n"
                "Uso: `<chat_id>,<Zona>`",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
        )
