from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import schedule_raffle, cancel_scheduled_raffle
from zoneinfo import ZoneInfo
from datetime import datetime

def show_owner_menu(bot: TeleBot, chat_id: int):
    grupos = load('grupos')
    propios = {gid: info for gid, info in grupos.items() if info.get('activado_por') == chat_id}
    if not propios:
        return bot.send_message(chat_id, "ℹ️ No tienes grupos activos.")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for gid in propios:
        kb.add(KeyboardButton(f"Gestionar {gid}"))
    kb.add(KeyboardButton("🔙 Salir"))
    bot.send_message(
        chat_id,
        "📂 *Tus Grupos Activos*\n\nSelecciona uno para gestionar:",
        parse_mode='Markdown',
        reply_markup=kb
    )

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(func=lambda m: m.chat.type == 'private')
    def handle_owner(msg):
        uid = msg.from_user.id
        text = msg.text.strip()

        # Asegurar almacenamiento temporal
        bot.user_data = getattr(bot, 'user_data', {})

        grupos = load('grupos')
        propios = {gid: info for gid, info in grupos.items() if info.get('activado_por') == uid}

        if text == "🔙 Salir":
            bot.user_data.pop(uid, None)
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        if text == "🔙 Volver":
            return show_owner_menu(bot, uid)

        if text == "🎲 Gestionar Sorteos":
            gid = bot.user_data.get(uid)
            if not gid:
                return bot.send_message(uid, "⚠️ Primero selecciona un grupo para gestionar.")
            if not is_user_and_group_authorized(uid, gid):
                return bot.send_message(uid, "🚫 No estás autorizado para gestionar este grupo.")
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🎯 Sortear ahora"), KeyboardButton("⏰ Agendar sorteo"))
            kb.add(KeyboardButton("🗑️ Cancelar sorteo"), KeyboardButton("🔙 Volver"))
            return bot.send_message(
                uid,
                f"🎲 *Gestión de Sorteos para el grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        if text == "🎯 Sortear ahora":
            gid = bot.user_data.get(uid)
            if not gid or not is_user_and_group_authorized(uid, gid):
                return bot.send_message(uid, "🚫 No estás autorizado para gestionar este grupo.")
            _perform_draw(gid, bot, name="Sorteo Rápido")
            return

        if text == "⏰ Agendar sorteo":
            gid = bot.user_data.get(uid)
            if not gid or not is_user_and_group_authorized(uid, gid):
                return bot.send_message(uid, "🚫 No estás autorizado para gestionar este grupo.")
            bot.send_message(uid,
                "⏰ *Agendar Sorteo*\n"
                "✏️ Envía la fecha y hora en formato: `YYYY-MM-DD_HH:MM`\n"
                "_Ejemplo_: `2025-07-25_15:30`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(msg, lambda m: process_schedule(m, gid))

        if text == "🗑️ Cancelar sorteo":
            gid = bot.user_data.get(uid)
            if not gid or not is_user_and_group_authorized(uid, gid):
                return bot.send_message(uid, "🚫 No estás autorizado para cancelar sorteos.")
            jobs = load('jobs')
            if not jobs:
                return bot.send_message(uid, "ℹ️ No hay sorteos programados.")
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for jid, info in jobs.items():
                name = info.get('name', jid)
                kb.add(KeyboardButton(f"Cancelar {jid}"))
            kb.add(KeyboardButton("🔙 Volver"))
            return bot.send_message(
                uid,
                "🗑️ *Cancelar Sorteo*\nSelecciona uno:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        if text.startswith("Cancelar "):
            jid = text.split(maxsplit=1)[1]
            cancel_scheduled_raffle(bot, jid)
            return bot.send_message(uid, f"🗑️ Sorteo `{jid}` eliminado.", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")
            bot.user_data[uid] = gid
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🎯 Sortear ahora"), KeyboardButton("⏰ Agendar sorteo"))
            kb.add(KeyboardButton("🗑️ Cancelar sorteo"), KeyboardButton("🌐 Cambiar zona horaria"))
            kb.add(KeyboardButton("🔙 Volver"))
            return bot.send_message(
                uid,
                f"🎲 *Gestión de Sorteos para el grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        if text == "🌐 Cambiar zona horaria":
            gid = bot.user_data.get(uid)
            if not gid or not is_user_and_group_authorized(uid, gid):
                return bot.send_message(uid, "🚫 No estás autorizado para este grupo.")
            bot.send_message(uid,
                "🌐 *Cambiar Zona Horaria*\n"
                "✏️ Envía la nueva zona en formato: `Continent/City`\n"
                "_Ejemplo_: `America/Havana`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(msg, lambda m: cambiar_zona(m, gid))

    # — Funciones auxiliares —

    def is_user_and_group_authorized(user_id, group_id):
        grupos_aut = load("grupos_autorizados").get("grupos", [])
        users_aut = list(load("autorizados").keys())
        return str(group_id) in grupos_aut and str(user_id) in users_aut

    def process_schedule(msg, gid):
        uid = msg.from_user.id
        text = msg.text.strip()
        try:
            dt_naive = datetime.strptime(text, "%Y-%m-%d_%H:%M")
        except ValueError:
            return bot.reply_to(msg,
                "❌ Fecha u hora no válidas.\nFormato: `YYYY-MM-DD_HH:MM`",
                parse_mode='Markdown'
            )
        gr = load('grupos').get(gid, {})
        tzname = gr.get('timezone', 'UTC')
        try:
            tz = ZoneInfo(tzname)
        except:
            return bot.send_message(uid,
                f"❌ Zona `{tzname}` inválida.\nUsa 🌐 Cambiar zona.",
                parse_mode='Markdown'
            )
        run_at = dt_naive.replace(tzinfo=tz)
        bot.send_message(uid,
            "✏️ *Ahora envía un nombre* para identificar este sorteo:",
            parse_mode='Markdown'
        )
        return bot.register_next_step_handler(msg, lambda m: _finalize_schedule(m, gid, run_at))

    def _finalize_schedule(msg, gid, run_at):
        uid = msg.from_user.id
        name = msg.text.strip()
        schedule_raffle(bot, gid, run_at, name)
        bot.send_message(uid,
            f"✅ Sorteo «{name}» programado para *{run_at.strftime('%Y-%m-%d %H:%M')}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def cambiar_zona(msg, gid):
        tz = msg.text.strip()
        try:
            ZoneInfo(tz)
            gr = load('grupos')
            if gid in gr:
                gr[gid]['timezone'] = tz
                save('grupos', gr)
                bot.send_message(msg.from_user.id,
                    f"✅ Zona de `{gid}` actualizada a *{tz}*.",
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardRemove()
                )
        except:
            bot.send_message(msg.from_user.id,
                "❌ Zona inválida.\nUsa el formato correcto, ej: `America/Havana`",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )

    def _perform_draw(gid, bot, name="Sorteo"):
        from draw_handlers import realizar_sorteo
        realizar_sorteo(bot, gid, name)
