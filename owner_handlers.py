from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load
from config import ADMINS
from scheduler import set_group_timezone
from datetime import datetime

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(commands=['misgrupos'])
    def mis_grupos(msg):
        if msg.chat.type != 'private': return
        uid = msg.from_user.id
        gr = load('grupos')
        own = {gid: info for gid, info in gr.items() if info.get('activado_por') == uid}
        if not own:
            bot.reply_to(msg, "ℹ️ No tienes grupos activos.")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for gid in own:
            kb.add(KeyboardButton(f"Gestionar {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))
        kb.add(KeyboardButton("🌐 Cambiar zona"))  # Nuevo botón

        bot.send_message(uid, "📂 Tus Grupos Activos:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_owner_selection(msg):
        uid  = msg.from_user.id
        text = msg.text.strip()
        gr   = load('grupos')

        if text == "🔙 Salir":
            bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())
            return

        if text.startswith("Gestionar "):
            gid = text.split()[1]
            if gid not in gr or gr[gid].get('activado_por') != uid:
                bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")
                return
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"))
            kb.add(KeyboardButton("🏆 Ver top invitadores"))
            kb.add(KeyboardButton("🔄 Reiniciar sorteo"))
            kb.add(KeyboardButton("🗑️ Borrar lista de sorteo"))
            kb.add(KeyboardButton("🔙 Volver"))
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid
            bot.send_message(uid, f"⚙️ Gestionando Grupo {gid}:", reply_markup=kb)
            return

        if text == "🌐 Cambiar zona":
            # Pide formato TZ
            msg2 = bot.send_message(uid, "✏️ Envía: <chat_id>,<Zona> (ej. -1001234567890,America/Havana)")
            bot.register_next_step_handler(msg2, cambiar_zona)
            return

        # Gestión tras haber seleccionado grupo
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return

        # ... aquí van tus opciones existentes (ver participantes, top, reiniciar, borrar)...

    def cambiar_zona(msg):
        try:
            data = msg.text.split(',')
            chat_id, tz = data[0].strip(), data[1].strip()
            # Valida ZoneInfo
            from zoneinfo import ZoneInfo
            _ = ZoneInfo(tz)
            set_group_timezone(chat_id, tz)
            bot.send_message(msg.from_user.id,
                f"✅ Zona horaria para grupo {chat_id} cambiada a {tz}")
        except Exception:
            bot.send_message(msg.from_user.id,
                "❌ Error: formato incorrecto o zona inválida.\n"
                "Ejemplo: -1001234567890,America/Havana")
