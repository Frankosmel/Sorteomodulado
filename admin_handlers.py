from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMINS, VIGENCIA_DIAS
from storage import load, save
from auth import add_authorized, remove_authorized, list_authorized
from datetime import datetime, timedelta

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(msg):
        if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
            return bot.reply_to(msg, "⛔ *Acceso denegado.* Usa este comando en privado.", parse_mode='Markdown')

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("📋 Ver autorizados"), KeyboardButton("➕ Autorizar usuario"))
        kb.row(KeyboardButton("➖ Desautorizar usuario"), KeyboardButton("🔄 Ver vencimientos"))
        kb.row(KeyboardButton("🗂 Ver grupos"), KeyboardButton("🔙 Salir"))

        bot.send_message(
            msg.chat.id,
            "👑 *Panel de Administración*\n\n"
            "Elige una opción con los botones:",
            parse_mode='Markdown',
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_admin(msg):
        text = msg.text.strip()
        uid = msg.from_user.id

        if text == "📋 Ver autorizados":
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay usuarios autorizados.*", parse_mode='Markdown')
            resp  = "👥 *Lista de Autorizados:*\n\n"
            for k, info in auth.items():
                exp = datetime.fromisoformat(info['vence']).date()
                resp += f"• ID `{k}` — vence el *{exp}*\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "➕ Autorizar usuario":
            prompt = bot.send_message(uid,
                "✏️ *Introduce el ID del usuario que deseas autorizar:*",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(prompt, process_authorize)

        if text == "➖ Desautorizar usuario":
            prompt = bot.send_message(uid,
                "✏️ *Introduce el ID del usuario que deseas desautorizar:*",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(prompt, process_deauthorize)

        if text == "🔄 Ver vencimientos":
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay usuarios autorizados.*", parse_mode='Markdown')
            resp  = "⏳ *Vencimientos Próximos:*\n\n"
            now = datetime.utcnow()
            for k, info in auth.items():
                dias = (datetime.fromisoformat(info['vence']) - now).days
                resp += f"• ID `{k}` — {dias} día(s) restantes\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "🗂 Ver grupos":
            grupos = load('grupos')
            if not grupos:
                return bot.send_message(uid, "ℹ️ *No hay grupos registrados.*", parse_mode='Markdown')
            resp  = "🗂 *Grupos Activos:*\n\n"
            for k, info in grupos.items():
                resp += f"• Grupo `{k}` — activado por `{info['activado_por']}` el {info['creado']}\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

    def process_authorize(msg):
        uid = msg.from_user.id
        user_id = msg.text.strip()
        if not user_id.isdigit():
            return bot.reply_to(msg, "❌ *ID inválido.* Debe ser un número.\nVuelve a intentarlo.", parse_mode='Markdown')
        user_id = int(user_id)
        add_authorized(user_id, msg.from_user.id)
        exp_date = (datetime.utcnow() + timedelta(days=VIGENCIA_DIAS)).date()
        bot.send_message(
            uid,
            f"✅ Usuario `{user_id}` autorizado hasta el *{exp_date}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def process_deauthorize(msg):
        uid = msg.from_user.id
        user_id = msg.text.strip()
        if not user_id.isdigit():
            return bot.reply_to(msg, "❌ *ID inválido.* Debe ser un número.\nVuelve a intentarlo.", parse_mode='Markdown')
        user_id = int(user_id)
        success = remove_authorized(user_id)
        if success:
            bot.send_message(uid, f"🗑️ Usuario `{user_id}` ha sido desautorizado.", parse_mode='Markdown')
        else:
            bot.send_message(uid, f"ℹ️ El usuario `{user_id}` no estaba autorizado.", parse_mode='Markdown')
