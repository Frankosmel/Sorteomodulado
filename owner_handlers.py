from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import schedule_raffle, cancel_scheduled_raffle
from zoneinfo import ZoneInfo
from datetime import datetime

def show_owner_menu(bot: TeleBot, chat_id: int):
    grupos = load('grupos')
    propios = {gid:info for gid,info in grupos.items() if info.get('activado_por') == chat_id}
    if not propios:
        return bot.send_message(chat_id, "ℹ️ No tienes grupos activos.")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for gid in propios:
        kb.add(KeyboardButton(f"Gestionar {gid}"))
    kb.add(KeyboardButton("🔙 Salir"))
    bot.send_message(
        chat_id,
        "📂 *Tus Grupos Activos:*\nSelecciona uno para gestionar:",
        parse_mode='Markdown',
        reply_markup=kb
    )

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner(msg):
        uid    = msg.from_user.id
        text   = msg.text.strip()
        grupos = load('grupos')
        propios = {gid:info for gid,info in grupos.items() if info.get('activado_por') == uid}

        # 🔙 Salir
        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # 🎲 Gestionar Sorteos (desde menú general)
        if text == "🎲 Gestionar Sorteos":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🎯 Sortear ahora"), KeyboardButton("⏰ Agendar sorteo"))
            kb.add(KeyboardButton("🗑️ Cancelar sorteo"), KeyboardButton("🔙 Volver"))
            return bot.send_message(
                uid,
                "🎲 *Gestión de Sorteos*\n\nElige una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # 🎯 Sortear ahora
        if text == "🎯 Sortear ahora":
            if not propios:
                return bot.reply_to(msg, "ℹ️ No tienes grupos para sortear.")
            bot.send_message(uid,
                "✏️ Envía: `<chat_id>`\n_Se elegirá un ganador aleatorio._",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(msg, process_draw_now)

        # ⏰ Agendar sorteo
        if text == "⏰ Agendar sorteo":
            if not propios:
                return bot.reply_to(msg, "ℹ️ No tienes grupos para programar.")
            bot.send_message(uid,
                "⏰ *Agendar Sorteo*\n"
                "✏️ Envía: `<chat_id> YYYY-MM-DD_HH:MM`\n"
                "_Ejemplo_: `-1001234567890 2025-07-25_15:30`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(msg, process_schedule)

        # 🗑️ Cancelar sorteo
        if text == "🗑️ Cancelar sorteo":
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

        # Cancelar específico
        if text.startswith("Cancelar "):
            jid = text.split(maxsplit=1)[1]
            cancel_scheduled_raffle(bot, jid)
            return bot.send_message(uid, f"🗑️ Sorteo `{jid}` eliminado.", reply_markup=ReplyKeyboardRemove())

        # 🔧 Gestión de grupo individual
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("🎯 Sortear ahora"), KeyboardButton("⏰ Agendar sorteo"))
            kb.add(KeyboardButton("🗑️ Cancelar sorteo"), KeyboardButton("🌐 Cambiar zona horaria"))
            kb.add(KeyboardButton("🔙 Volver"))
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid
            return bot.send_message(
                uid,
                f"🎲 *Gestión de Sorteos para el grupo {gid}*\nSelecciona una opción:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # 🌐 Cambiar zona horaria
        if text == "🌐 Cambiar zona horaria":
            bot.send_message(uid,
                "🌐 *Cambiar Zona Horaria*\n"
                "✏️ Envía: `<chat_id>,<Zona>`\n"
                "_Ejemplo_: `-1001234567890,Europe/Madrid`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(msg, cambiar_zona)

    # — Funciones auxiliares —
    def process_schedule(msg):
        uid = msg.from_user.id
        partes = msg.text.split()
        if len(partes) != 2:
            return bot.reply_to(msg,
                "❌ Formato inválido.\nUso: `<chat_id> YYYY-MM-DD_HH:MM`",
                parse_mode='Markdown'
            )
        chat_id, text = partes
        try:
            dt_naive = datetime.strptime(text, "%Y-%m-%d_%H:%M")
        except ValueError:
            return bot.reply_to(msg,
                "❌ Fecha u hora no válidas.\nFormato: `YYYY-MM-DD_HH:MM`",
                parse_mode='Markdown'
            )
        grp = load('grupos').get(chat_id,{})
        tzname = grp.get('timezone','UTC')
        try:
            tz = ZoneInfo(tzname)
        except:
            return bot.send_message(uid,
                f"❌ Zona `{tzname}` inválida.\nUsa /start→Gestionar Sorteos→🌐 Cambiar zona.",
                parse_mode='Markdown'
            )
        run_at = dt_naive.replace(tzinfo=tz)
        bot.send_message(uid,
            "✏️ *Ahora envía un nombre* para identificar este sorteo:",
            parse_mode='Markdown'
        )
        return bot.register_next_step_handler(msg, lambda m: _finalize_schedule(m, chat_id, run_at))

    def _finalize_schedule(msg, chat_id, run_at):
        uid = msg.from_user.id
        name = msg.text.strip()
        schedule_raffle(bot, chat_id, run_at, name)
        bot.send_message(uid,
            f"✅ Sorteo «{name}» programado para *{run_at.strftime('%Y-%m-%d %H:%M')}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def process_draw_now(msg):
        chat_id = msg.text.strip()
        _perform_draw(chat_id, bot, name="Sorteo Rápido")

    def cambiar_zona(msg):
        try:
            chat_id, tz = map(str.strip, msg.text.split(','))
            ZoneInfo(tz)
            gr = load('grupos')
            gr[chat_id]['timezone'] = tz
            save('grupos', gr)
            bot.send_message(msg.from_user.id,
                f"✅ Zona de `{chat_id}` actualizada a *{tz}*.",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        except:
            bot.send_message(msg.from_user.id,
                "❌ Formato o zona inválida.\nUso: `<chat_id>,<Zona>`",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
        )
