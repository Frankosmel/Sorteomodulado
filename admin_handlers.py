from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMINS
from storage import load, save
from auth import add_authorized
from datetime import datetime

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(msg):
        if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
            bot.reply_to(msg, "⛔ Acceso denegado o usa este comando en privado.")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("👥 Ver autorizados"),
               KeyboardButton("➕ Agregar autorizado"))
        kb.add(KeyboardButton("⏳ Ver vencimientos"),
               KeyboardButton("🗂 Ver grupos"))
        kb.add(KeyboardButton("📤 Mensaje a grupos"),
               KeyboardButton("🔙 Salir"))

        bot.send_message(msg.chat.id, "👑 Panel Admin — Elige una opción:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id in ADMINS)
    def handle_admin(msg):
        text = msg.text
        uid = msg.from_user.id

        if text == "👥 Ver autorizados":
            auth = load('autorizados')
            resp = "📋 *Usuarios Autorizados:*\n\n"
            for k,v in auth.items():
                resp += f"- {v['nombre']} (ID {k}) vence {v['vence']}\n"
            bot.send_message(uid, resp, parse_mode='Markdown')

        elif text == "➕ Agregar autorizado":
            msg2 = bot.send_message(uid, "✏️ Envía: ID,nombre,plan (ej. `12345,Carlos,USD`)")
            bot.register_next_step_handler(msg2, agregar_autorizado)

        elif text == "⏳ Ver vencimientos":
            auth = load('autorizados')
            resp = "⏳ *Vencimientos próximos:*\n\n"
            hoy = datetime.utcnow()
            for k,v in auth.items():
                exp = datetime.fromisoformat(v['vence'])
                dias = (exp - hoy).days
                resp += f"- {v['nombre']} (ID {k}) → {dias} días restantes\n"
            bot.send_message(uid, resp, parse_mode='Markdown')

        elif text == "🗂 Ver grupos":
            gr = load('grupos')
            resp = "🗂 *Grupos Activos:*\n\n"
            for k,v in gr.items():
                resp += f"- Grupo ID {k} activado por {v['activado_por']} el {v['creado']}\n"
            bot.send_message(uid, resp, parse_mode='Markdown')

        elif text == "📤 Mensaje a grupos":
            msg2 = bot.send_message(uid, "✏️ Envía el mensaje que se reenviará a todos los grupos:")
            bot.register_next_step_handler(msg2, enviar_a_grupos)

        elif text == "🔙 Salir":
            bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

    def agregar_autorizado(msg):
        try:
            data = msg.text.split(',')
            uid, nombre, plan = data[0], data[1], data[2]
            add_authorized(uid, nombre, plan)
            bot.send_message(msg.from_user.id, f"✅ Usuario {nombre} (ID {uid}) autorizado correctamente.")
        except Exception:
            bot.send_message(msg.from_user.id, "❌ Formato incorrecto. Usa: ID,nombre,plan")

    def enviar_a_grupos(msg):
        texto = msg.text
        gr = load('grupos')
        for chat_id in gr.keys():
            try:
                bot.send_message(int(chat_id), texto)
            except:
                pass
        bot.send_message(msg.from_user.id, "✅ Mensaje enviado a todos los grupos.")
