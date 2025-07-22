# admin_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMINS, VIGENCIA_DIAS
from storage import load
from auth import add_authorized, remove_authorized, list_authorized
from datetime import datetime, timedelta

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(msg):
        # Solo en privado y para super‐admins
        if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
            return bot.reply_to(
                msg,
                "⛔ *Acceso denegado.* Usa /admin en privado.",
                parse_mode='Markdown'
            )

        # Teclado principal de administración
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(
            KeyboardButton("Autorizados"),
            KeyboardButton("Autorizar"),
            KeyboardButton("Desautorizar")
        )
        kb.row(
            KeyboardButton("Vencimientos"),
            KeyboardButton("Grupos"),
            KeyboardButton("Mensajes")
        )
        kb.row(KeyboardButton("Salir"))

        bot.send_message(
            msg.chat.id,
            "👑 *Panel de Administración*\n\n"
            "Selecciona una opción con los botones:",
            parse_mode='Markdown',
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_admin(msg):
        text = msg.text.strip()
        uid = msg.from_user.id

        # SALIR
        if text == "Salir":
            return bot.send_message(
                uid,
                "✅ Menú cerrado.",
                reply_markup=ReplyKeyboardRemove()
            )

        # AUTORIZADOS
        if text == "Autorizados":
            bot.send_message(
                uid,
                "📋 *Autorizados*: muestra todos los usuarios con acceso y su fecha de vencimiento.",
                parse_mode='Markdown'
            )
            auth = list_authorized()
            if not auth:
                return bot.send_message(
                    uid,
                    "ℹ️ *No hay usuarios autorizados.*",
                    parse_mode='Markdown'
                )
            resp = "👥 *Lista de Autorizados:*\n\n"
            for k, info in auth.items():
                exp = datetime.fromisoformat(info['vence']).date()
                usuario = info.get('username', '')
                resp += f"• {usuario} (`{k}`) — vence el *{exp}*\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # AUTORIZAR
        if text == "Autorizar":
            bot.send_message(
                uid,
                "➕ *Autorizar*: añade un nuevo usuario.\n"
                "✏️ Envía: `ID,@usuario`",
                parse_mode='Markdown'
            )
            example = bot.send_message(uid, "Ejemplo: `12345,@pepito`")
            return bot.register_next_step_handler(example, process_authorize)

        # DESAUTORIZAR
        if text == "Desautorizar":
            bot.send_message(
                uid,
                "➖ *Desautorizar*: quita acceso a un usuario.\n"
                "✏️ Envía solo el `ID`.",
                parse_mode='Markdown'
            )
            example = bot.send_message(uid, "Ejemplo: `12345`")
            return bot.register_next_step_handler(example, process_deauthorize)

        # VENCIMIENTOS
        if text == "Vencimientos":
            bot.send_message(
                uid,
                "⏳ *Vencimientos*: muestra cuántos días quedan a cada suscripción.",
                parse_mode='Markdown'
            )
            auth = list_authorized()
            if not auth:
                return bot.send_message(
                    uid,
                    "ℹ️ *No hay usuarios autorizados.*",
                    parse_mode='Markdown'
                )
            resp = "⏳ *Días Restantes:*\n\n"
            now = datetime.utcnow()
            for k, info in auth.items():
                dias = (datetime.fromisoformat(info['vence']) - now).days
                usuario = info.get('username', '')
                resp += f"• {usuario} (`{k}`) — {dias} día(s)\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # GRUPOS
        if text == "Grupos":
            bot.send_message(
                uid,
                "🗂 *Grupos*: lista los chats donde el bot está activo y quién lo activó.",
                parse_mode='Markdown'
            )
            grupos = load('grupos')
            if not grupos:
                return bot.send_message(
                    uid,
                    "ℹ️ *No hay grupos registrados.*",
                    parse_mode='Markdown'
                )
            resp = "🗂 *Grupos Activos:*\n\n"
            for k, info in grupos.items():
                resp += (
                    f"• `{k}` — activado por `{info['activado_por']}` "
                    f"el {info['creado']}\n"
                )
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # MENSAJES (sub-menú)
        if text == "Mensajes":
            kb2 = ReplyKeyboardMarkup(resize_keyboard=True)
            kb2.row(
                KeyboardButton("A autorizados"),
                KeyboardButton("A grupos")
            )
            kb2.row(KeyboardButton("Salir"))
            return bot.send_message(
                uid,
                "📤 *Mensajes*:\n\n"
                "→ *A autorizados*: envía texto a todos los usuarios autorizados.\n"
                "→ *A grupos*: envía texto a todos los grupos activos.\n"
                "→ *Salir*: vuelve al menú principal.",
                parse_mode='Markdown',
                reply_markup=kb2
            )

        # SUB-MENÚ: A AUTORIZADOS
        if text == "A autorizados":
            bot.send_message(
                uid,
                "✏️ *Escribe el mensaje* que enviarás a todos los autorizados:",
                parse_mode='Markdown'
            )
            example = bot.send_message(uid, "Ejemplo: ¡Recordatorio!")
            return bot.register_next_step_handler(example, send_to_authorized)

        # SUB-MENÚ: A GRUPOS
        if text == "A grupos":
            bot.send_message(
                uid,
                "✏️ *Escribe el mensaje* que reenviarás a todos los grupos:",
                parse_mode='Markdown'
            )
            example = bot.send_message(uid, "Ejemplo: Nuevo sorteo hoy!")
            return bot.register_next_step_handler(example, send_to_groups)

    # — Funciones auxiliares —
    def process_authorize(msg):
        uid = msg.from_user.id
        parts = [p.strip() for p in msg.text.split(',')]
        if len(parts)!=2 or not parts[0].isdigit() or not parts[1].startswith('@'):
            return bot.reply_to(
                msg,
                "❌ *Formato inválido.* Usa `ID,@usuario`.",
                parse_mode='Markdown'
            )
        user_id = int(parts[0])
        username = parts[1]
        add_authorized(user_id, username)
        exp_date = (datetime.utcnow() + timedelta(days=VIGENCIA_DIAS)).date()
        bot.send_message(
            uid,
            f"✅ {username} (`{user_id}`) autorizado hasta el *{exp_date}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def process_deauthorize(msg):
        uid = msg.from_user.id
        if not msg.text.isdigit():
            return bot.reply_to(
                msg,
                "❌ *ID inválido.* Debe ser número.",
                parse_mode='Markdown'
            )
        user_id = int(msg.text)
        success = remove_authorized(user_id)
        resultado = "desautorizado" if success else "no estaba autorizado"
        bot.send_message(
            uid,
            f"🗑️ Usuario `{user_id}` {resultado}.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def send_to_authorized(msg):
        texto = msg.text
        for k in list_authorized().keys():
            try:
                bot.send_message(int(k), texto)
            except Exception:
                pass
        bot.send_message(
            msg.from_user.id,
            "✅ Mensaje enviado a todos los autorizados.",
            reply_markup=ReplyKeyboardRemove()
        )

    def send_to_groups(msg):
        texto = msg.text
        for chat_id in load('grupos').keys():
            try:
                bot.send_message(int(chat_id), texto)
            except Exception:
                pass
        bot.send_message(
            msg.from_user.id,
            "✅ Mensaje reenviado a todos los grupos.",
            reply_markup=ReplyKeyboardRemove()
                        )
