from telebot import TeleBot
from telebot.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from config import ADMINS, STAFF_GROUP_ID, REPORT_CHANNEL_ID
from storage import load, save
from auth import remove_authorized, list_authorized

# ----------------- MENÚ PRINCIPAL ADMIN -----------------

def show_admin_menu(bot: TeleBot, uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("👥 Gestión de Usuarios"), KeyboardButton("📊 Planes y Pagos"))
    kb.row(KeyboardButton("👥 Grupo Staff"), KeyboardButton("📢 Canal Reportes"))
    kb.row(KeyboardButton("👨‍👩‍👧‍👦 Grupos"))
    bot.send_message(uid, "🔧 Panel de Administración — elige una opción:", reply_markup=kb)


# ----------------- SUBMENÚ GESTIÓN DE USUARIOS -----------------

def show_user_management_menu(bot: TeleBot, uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✅ Ver autorizados"), KeyboardButton("❌ Desautorizar usuario"))
    kb.row(KeyboardButton("🔙 Volver"))
    bot.send_message(uid, "👥 Gestión de Usuarios:", reply_markup=kb)


# ----------------- SUBMENÚ GESTIÓN DE GRUPOS -----------------

def show_group_management_menu(bot: TeleBot, uid: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✅ Ver grupos autorizados"))
    kb.row(KeyboardButton("🚫 Ver no autorizados"))
    kb.row(KeyboardButton("⛔ Salir de no autorizados"))
    kb.row(KeyboardButton("🔙 Volver"))
    bot.send_message(uid, "📋 Gestión de Grupos:", reply_markup=kb)


# ----------------- HANDLER PRINCIPAL -----------------

def register_group_handlers(bot: TeleBot):

    @bot.message_handler(func=lambda m: m.text == "👥 Gestión de Usuarios" and m.from_user.id in ADMINS)
    def menu_gestion_usuarios(m: Message):
        show_user_management_menu(bot, m.chat.id)

    @bot.message_handler(func=lambda m: m.text == "📊 Planes y Pagos" and m.from_user.id in ADMINS)
    def planes_pagos(m: Message):
        bot.send_message(m.chat.id, "💳 Aquí puedes configurar o revisar los planes de pago. (Funcionalidad en desarrollo)")

    @bot.message_handler(func=lambda m: m.text == "👥 Grupo Staff" and m.from_user.id in ADMINS)
    def grupo_staff(m: Message):
        bot.send_message(m.chat.id, f"👥 Grupo de staff actual:\n\n{STAFF_GROUP_ID}")

    @bot.message_handler(func=lambda m: m.text == "📢 Canal Reportes" and m.from_user.id in ADMINS)
    def canal_reportes(m: Message):
        bot.send_message(m.chat.id, f"📢 Canal de reportes actual:\n\n{REPORT_CHANNEL_ID}")

    @bot.message_handler(func=lambda m: m.text == "👨‍👩‍👧‍👦 Grupos" and m.from_user.id in ADMINS)
    def menu_grupos(m: Message):
        show_group_management_menu(bot, m.chat.id)

    @bot.message_handler(func=lambda m: m.text == "✅ Ver autorizados" and m.from_user.id in ADMINS)
    def ver_autorizados(m: Message):
        users = list_authorized()
        if not users:
            return bot.send_message(m.chat.id, "❌ No hay usuarios autorizados.")
        msg = "✅ *Usuarios autorizados:*\n\n"
        for uid, data in users.items():
            username = data.get("username", "")
            vencimiento = data.get("vence", "?")
            nombre = data.get("nombre", uid)
            msg += f"• {nombre} ({'@' + username if username else uid}) — vence: {vencimiento}\n"
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text == "❌ Desautorizar usuario" and m.from_user.id in ADMINS)
    def pedir_id_para_desautorizar(m: Message):
        bot.send_message(m.chat.id, "✏️ Escribe el ID del usuario que deseas desautorizar:")
        bot.register_next_step_handler(m, recibir_id_para_desautorizar)

    def recibir_id_para_desautorizar(m: Message):
        try:
            user_id = int(m.text.strip())
            if remove_authorized(user_id):
                bot.send_message(m.chat.id, f"✅ Usuario {user_id} desautorizado correctamente.")
            else:
                bot.send_message(m.chat.id, "❌ Ese usuario no estaba autorizado.")
        except:
            bot.send_message(m.chat.id, "⚠️ Debes enviar un número de ID válido.")

    @bot.message_handler(func=lambda m: m.text == "✅ Ver grupos autorizados" and m.from_user.id in ADMINS)
    def ver_grupos_autorizados(m: Message):
        grupos = load("grupos")
        autorizados = set(load("grupos_autorizados").get("groups", []))
        if not autorizados:
            return bot.send_message(m.chat.id, "❌ No hay grupos autorizados.")
        msg = "✅ *Grupos autorizados:*\n\n"
        for gid in autorizados:
            nombre = grupos.get(gid, {}).get("nombre", "Grupo")
            enlace = f"https://t.me/c/{str(gid)[4:]}"
            msg += f"• {gid} — {nombre}\n{enlace}\n"
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text == "🚫 Ver no autorizados" and m.from_user.id in ADMINS)
    def ver_no_autorizados(m: Message):
        grupos = load("grupos")
        autorizados = set(load("grupos_autorizados").get("groups", []))
        todos = set(grupos.keys())
        no_aut = todos - autorizados
        if not no_aut:
            return bot.send_message(m.chat.id, "✅ Todos los grupos están autorizados.")
        msg = "🚫 *Grupos no autorizados:*\n\n"
        for gid in no_aut:
            nombre = grupos.get(gid, {}).get("nombre", "Grupo")
            enlace = f"https://t.me/c/{str(gid)[4:]}"
            msg += f"• {gid} — {nombre}\n{enlace}\n"
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text == "⛔ Salir de no autorizados" and m.from_user.id in ADMINS)
    def salir_de_grupos(m: Message):
        grupos = load("grupos")
        autorizados = set(load("grupos_autorizados").get("groups", []))
        todos = set(grupos.keys())
        no_aut = todos - autorizados
        if not no_aut:
            return bot.send_message(m.chat.id, "✅ No hay grupos no autorizados para salir.")
        count = 0
        for gid in no_aut:
            try:
                bot.leave_chat(int(gid))
                count += 1
            except:
                continue
        bot.send_message(m.chat.id, f"✅ Se ha salido de {count} grupo(s) no autorizados.")

    @bot.message_handler(func=lambda m: m.text == "🔙 Volver" and m.from_user.id in ADMINS)
    def volver_menu_principal(m: Message):
        show_admin_menu(bot, m.chat.id)
