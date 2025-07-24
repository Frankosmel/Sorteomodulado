from telebot import TeleBot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    Message
)
from config import ADMINS, PLANS, VIGENCIA_DIAS
from storage import load, save
from auth import add_authorized, remove_authorized, list_authorized
from datetime import datetime, timedelta
import re

# Para almacenar temporalmente al usuario que vamos a autorizar
PENDING_AUTH = {}

def _escape_md(text: str) -> str:
    return re.sub(r'([_*[\]()~`>#+=|{}.!\\-])', r'\\\1', str(text))

# MENÚ PRINCIPAL DE ADMINISTRADOR
def show_admin_menu(bot: TeleBot, uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👥 Gestión de Usuarios", "👨‍👩‍👧‍👦 Grupos")
    kb.row("📊 Planes y Pagos")
    kb.row("📢 Canal de Reportes", "👥 Grupo Staff")
    bot.send_message(uid, "🔧 Panel de administración, elige una opción:", reply_markup=kb)

# GESTIÓN DE USUARIOS
def show_user_management_menu(bot: TeleBot, uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("✅ Ver autorizados", "❌ Desautorizar usuario")
    kb.row("🔙 Volver")
    bot.send_message(uid, "👥 Gestión de usuarios:", reply_markup=kb)

# GESTIÓN DE GRUPOS
def show_group_management_menu(bot: TeleBot, uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📋 Ver autorizados", "🚫 Ver no autorizados")
    kb.row("🔚 Salir de no autorizados")
    kb.row("🔙 Volver")
    bot.send_message(uid, "📋 Gestión de grupos:", reply_markup=kb)

# HANDLERS
def register_admin_handlers(bot: TeleBot):

    @bot.message_handler(func=lambda m: m.text in [
        "👥 Gestión de Usuarios", "📊 Planes y Pagos",
        "📢 Canal de Reportes", "👥 Grupo Staff",
        "👨‍👩‍👧‍👦 Grupos"
    ])
    def admin_menu_handler(m: Message):
        if m.from_user.id not in ADMINS:
            return bot.reply_to(m, "⛔ No tienes permiso para acceder a este menú.")

        if m.text == "👥 Gestión de Usuarios":
            show_user_management_menu(bot, m.chat.id)

        elif m.text == "📊 Planes y Pagos":
            bot.send_message(m.chat.id, "💳 Aquí puedes configurar o revisar los planes de pago. (Funcionalidad en desarrollo)")

        elif m.text == "📢 Canal de Reportes":
            bot.send_message(m.chat.id, f"📢 Canal actual de reportes:\n`{_escape_md(str(load('config').get('report_channel_id', 'No definido')))`", parse_mode="Markdown")

        elif m.text == "👥 Grupo Staff":
            bot.send_message(m.chat.id, f"👥 Grupo staff actual:\n`{_escape_md(str(load('config').get('staff_group_id', 'No definido')))`", parse_mode="Markdown")

        elif m.text == "👨‍👩‍👧‍👦 Grupos":
            show_group_management_menu(bot, m.chat.id)

    @bot.message_handler(func=lambda m: m.text in [
        "✅ Ver autorizados", "❌ Desautorizar usuario", "🔙 Volver"
    ])
    def user_submenu_handler(m: Message):
        if m.text == "✅ Ver autorizados":
            users = list_authorized()
            if not users:
                return bot.send_message(m.chat.id, "❌ No hay usuarios autorizados.")
            msg = "✅ *Usuarios autorizados:*\n"
            for uid, data in users.items():
                username = data.get("username", "")
                vencimiento = data.get("vence", "?")
                nombre = data.get("nombre", uid)
                msg += f"\n• {nombre} ({'@' + username if username else uid}) — vence: {vencimiento}"
            bot.send_message(m.chat.id, msg, parse_mode="Markdown")

        elif m.text == "❌ Desautorizar usuario":
            bot.send_message(m.chat.id, "✏️ Envía el ID del usuario que deseas desautorizar:")
            bot.register_next_step_handler(m, procesar_desautorizacion)

        elif m.text == "🔙 Volver":
            show_admin_menu(bot, m.chat.id)

    def procesar_desautorizacion(m: Message):
        try:
            user_id = int(m.text.strip())
            if remove_authorized(user_id):
                bot.send_message(m.chat.id, f"✅ Usuario {user_id} desautorizado correctamente.")
            else:
                bot.send_message(m.chat.id, "❌ Ese usuario no estaba autorizado.")
        except:
            bot.send_message(m.chat.id, "⚠️ Debes enviar un número de ID válido.")
        show_user_management_menu(bot, m.chat.id)

    @bot.message_handler(func=lambda m: m.text in [
        "📋 Ver autorizados", "🚫 Ver no autorizados",
        "🔚 Salir de no autorizados", "🔙 Volver"
    ])
    def group_submenu_handler(m: Message):
        grupos = load("grupos")
        autorizados = set(load("grupos_autorizados").get("groups", []))
        todos = set(grupos.keys())

        if m.text == "📋 Ver autorizados":
            if not autorizados:
                return bot.send_message(m.chat.id, "❌ No hay grupos autorizados.")
            msg = "✅ *Grupos autorizados:*\n"
            for gid in autorizados:
                nombre = grupos.get(gid, {}).get("nombre", "Grupo")
                enlace = f"https://t.me/c/{str(gid)[4:]}"
                msg += f"\n• {gid} — {nombre}\n{enlace}"
            bot.send_message(m.chat.id, msg, parse_mode="Markdown")

        elif m.text == "🚫 Ver no autorizados":
            no_aut = todos - autorizados
            if not no_aut:
                return bot.send_message(m.chat.id, "✅ Todos los grupos están autorizados.")
            msg = "🚫 *Grupos no autorizados:*\n"
            for gid in no_aut:
                nombre = grupos.get(gid, {}).get("nombre", "Grupo")
                enlace = f"https://t.me/c/{str(gid)[4:]}"
                msg += f"\n• {gid} — {nombre}\n{enlace}"
            bot.send_message(m.chat.id, msg, parse_mode="Markdown")

        elif m.text == "🔚 Salir de no autorizados":
            no_aut = todos - autorizados
            if not no_aut:
                return bot.send_message(m.chat.id, "✅ No hay grupos no autorizados para salir.")
            for gid in no_aut:
                try:
                    bot.leave_chat(int(gid))
                except:
                    continue
            bot.send_message(m.chat.id, f"✅ Se ha salido de {len(no_aut)} grupo(s) no autorizados.")

        elif m.text == "🔙 Volver":
            show_admin_menu(bot, m.chat.id)
