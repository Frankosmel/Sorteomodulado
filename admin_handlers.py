# admin_handlers.py

from telebot import TeleBot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMINS, PLANS, VIGENCIA_DIAS
from storage import load
from auth import add_authorized, remove_authorized, list_authorized
from datetime import datetime, timedelta

# Para almacenar temporalmente al usuario que vamos a autorizar
PENDING_AUTH = {}

def show_admin_menu(bot: TeleBot, chat_id: int):
    """Envía el teclado principal de admin a `chat_id`."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("Autorizados"), KeyboardButton("Autorizar"), KeyboardButton("Desautorizar"))
    kb.row(KeyboardButton("Vencimientos"),   KeyboardButton("Grupos"),    KeyboardButton("Mensajes"))
    kb.row(KeyboardButton("Salir"))
    bot.send_message(
        chat_id,
        "👑 *Panel de Administración*\n\nSelecciona una opción:",
        parse_mode='Markdown',
        reply_markup=kb
    )

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(msg):
        if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
            return bot.reply_to(msg, "⛔ *Acceso denegado.* Usa /admin en privado.", parse_mode='Markdown')
        show_admin_menu(bot, msg.chat.id)

    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_admin(msg):
        text = msg.text.strip()
        uid = msg.from_user.id

        if text == "Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        if text == "Autorizados":
            bot.send_message(uid,
                "📋 *Autorizados*: muestra todos los usuarios con acceso y su fecha de vencimiento.",
                parse_mode='Markdown'
            )
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay usuarios autorizados.*", parse_mode='Markdown')
            resp = "👥 *Lista de Autorizados:*\n\n"
            for k, info in auth.items():
                exp = datetime.fromisoformat(info['vence']).date()
                usuario = info.get('username', '')
                plan = info.get('plan', '—')
                resp += f"• {usuario} (`{k}`) — plan *{plan}* vence el *{exp}*\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "Autorizar":
            bot.send_message(uid,
                "➕ *Autorizar*: añade un nuevo usuario.\n"
                "✏️ Envía: `ID,@usuario`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                bot.send_message(uid, "Ejemplo: `12345,@pepito`"),
                process_authorize
            )

        if text == "Desautorizar":
            bot.send_message(uid,
                "➖ *Desautorizar*: quita acceso a un usuario.\n"
                "✏️ Envía solo el `ID`.",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                bot.send_message(uid, "Ejemplo: `12345`"),
                process_deauthorize
            )

        if text == "Vencimientos":
            bot.send_message(uid,
                "⏳ *Vencimientos*: muestra cuántos días quedan a cada suscripción.",
                parse_mode='Markdown'
            )
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay usuarios autorizados.*", parse_mode='Markdown')
            resp = "⏳ *Días Restantes:*\n\n"
            now = datetime.utcnow()
            for k, info in auth.items():
                dias = (datetime.fromisoformat(info['vence']) - now).days
                usuario = info.get('username', '')
                plan = info.get('plan', '—')
                resp += f"• {usuario} (`{k}`) — plan *{plan}*: {dias} día(s)\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "Grupos":
            bot.send_message(uid,
                "🗂 *Grupos*: lista los chats donde el bot está activo y quién lo activó.",
                parse_mode='Markdown'
            )
            grupos = load('grupos')
            if not grupos:
                return bot.send_message(uid, "ℹ️ *No hay grupos registrados.*", parse_mode='Markdown')
            resp = "🗂 *Grupos Activos:*\n\n"
            for k, info in grupos.items():
                resp += f"• `{k}` — activado por `{info['activado_por']}` el {info['creado']}\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "Mensajes":
            kb2 = ReplyKeyboardMarkup(resize_keyboard=True)
            kb2.row(KeyboardButton("A autorizados"), KeyboardButton("A grupos"))
            kb2.row(KeyboardButton("Salir"))
            return bot.send_message(
                uid,
                "📤 *Mensajes*:\n"
                "→ *A autorizados*: envía texto a todos los usuarios autorizados.\n"
                "→ *A grupos*: envía texto a todos los grupos activos.",
                parse_mode='Markdown',
                reply_markup=kb2
            )

        if text == "A autorizados":
            bot.send_message(uid, "✏️ *Escribe el mensaje* que enviarás a todos los autorizados:", parse_mode='Markdown')
            return bot.register_next_step_handler(bot.send_message(uid, "Ejemplo: ¡Recordatorio!"), send_to_authorized)

        if text == "A grupos":
            bot.send_message(uid, "✏️ *Escribe el mensaje* que enviarás a todos los grupos:", parse_mode='Markdown')
            return bot.register_next_step_handler(bot.send_message(uid, "Ejemplo: Nuevo sorteo hoy!"), send_to_groups)

    # — Funciones auxiliares — #

    def process_authorize(msg):
        uid = msg.from_user.id
        parts = [p.strip() for p in msg.text.split(',')]
        if len(parts)!=2 or not parts[0].isdigit() or not parts[1].startswith('@'):
            return bot.reply_to(msg, "❌ Formato inválido. Usa `ID,@usuario`.", parse_mode='Markdown')
        user_id = int(parts[0]); username = parts[1]
        # Guardamos temporalmente y pedimos plan
        PENDING_AUTH[uid] = {"user_id": user_id, "username": username}
        kb = InlineKeyboardMarkup(row_width=1)
        for plan in PLANS:
            kb.add(InlineKeyboardButton(plan['label'], callback_data=f"auth_plan_{plan['key']}"))
        bot.send_message(
            uid,
            "🌟 *Selecciona el plan* para este usuario:",
            parse_mode='Markdown',
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("auth_plan_"))
    def on_auth_plan_selected(cq):
        admin_id = cq.from_user.id
        bot.answer_callback_query(cq.id)
        pending = PENDING_AUTH.get(admin_id)
        if not pending:
            return bot.send_message(admin_id, "⚠️ Sesión expirada. Vuelve a Autorizar.", parse_mode='Markdown')
        plan_key = cq.data.replace("auth_plan_", "")
        # Buscamos datos del plan
        plan = next((p for p in PLANS if p["key"]==plan_key), None)
        if not plan:
            return bot.send_message(admin_id, "❌ Plan inválido.", parse_mode='Markdown')
        # Calculamos fecha de vencimiento
        duration = plan.get("duration_days", VIGENCIA_DIAS)
        vence_date = (datetime.utcnow() + timedelta(days=duration)).isoformat()
        # Guardamos
        add_authorized(pending["user_id"], pending["username"], plan_key, vence_date)
        # Confirmación
        bot.send_message(
            admin_id,
            f"✅ Usuario {pending['username']} (`{pending['user_id']}`) autorizado con plan *{plan['label']}* hasta *{vence_date[:10]}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        # Limpiamos
        del PENDING_AUTH[admin_id]

    def process_deauthorize(msg):
        uid = msg.from_user.id
        if not msg.text.isdigit():
            return bot.reply_to(msg, "❌ ID inválido. Debe ser número.", parse_mode='Markdown')
        user_id = int(msg.text)
        success = remove_authorized(user_id)
        text = "desautorizado" if success else "no estaba autorizado"
        bot.send_message(uid, f"🗑️ Usuario `{user_id}` {text}.", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

    def send_to_authorized(msg):
        texto = msg.text
        for k in list_authorized().keys():
            try: bot.send_message(int(k), texto)
            except: pass
        bot.send_message(msg.from_user.id, "✅ Mensaje enviado a todos los autorizados.", reply_markup=ReplyKeyboardRemove())

    def send_to_groups(msg):
        texto = msg.text
        for chat_id in load('grupos').keys():
            try: bot.send_message(int(chat_id), texto)
            except: pass
        bot.send_message(msg.from_user.id, "✅ Mensaje reenviado a todos los grupos.", reply_markup=ReplyKeyboardRemove())
