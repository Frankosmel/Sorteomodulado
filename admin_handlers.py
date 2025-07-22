# admin_handlers.py

import telebot
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMINS, VIGENCIA_DIAS
from storage import load
from auth import add_authorized, remove_authorized, list_authorized
from datetime import datetime, timedelta

def show_admin_menu(bot: TeleBot, chat_id: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("👥 Autorizados"), KeyboardButton("➕ Autorizar"),
        KeyboardButton("➖ Desautorizar"), KeyboardButton("⏳ Vencimientos"),
        KeyboardButton("🗂 Grupos"),       KeyboardButton("📤 Mensajes"),
        KeyboardButton("❌ Salir")
    )
    bot.send_message(
        chat_id,
        "👑 *Panel de Administración*\n\n"
        "Selecciona una opción:",
        parse_mode='Markdown',
        reply_markup=kb
    )

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_admin(msg):
        text = msg.text.strip()
        uid = msg.from_user.id

        # Salir
        if text == "❌ Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # Autorizados
        if text == "👥 Autorizados":
            bot.send_message(uid,
                "📋 *Autorizados*: muestra usuarios y fecha de vencimiento.",
                parse_mode='Markdown'
            )
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay autorizados.*", parse_mode='Markdown')
            resp = "👥 *Lista de Autorizados:*\n\n"
            for k, info in auth.items():
                exp = datetime.fromisoformat(info['vence']).date()
                usuario = info.get('username','')
                resp += f"• {usuario} (`{k}`) — vence el *{exp}*\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # Autorizar
        if text == "➕ Autorizar":
            bot.send_message(uid,
                "➕ *Autorizar*: añade un usuario.\n"
                "✏️ Envía: `ID,@usuario`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                bot.send_message(uid, "Ejemplo: `12345,@pepito`"),
                process_authorize
            )

        # Desautorizar
        if text == "➖ Desautorizar":
            bot.send_message(uid,
                "➖ *Desautorizar*: quita acceso.\n"
                "✏️ Envía solo el `ID`",
                parse_mode='Markdown'
            )
            return bot.register_next_step_handler(
                bot.send_message(uid, "Ejemplo: `12345`"),
                process_deauthorize
            )

        # Vencimientos
        if text == "⏳ Vencimientos":
            bot.send_message(uid,
                "⏳ *Vencimientos*: días restantes por suscripción.",
                parse_mode='Markdown'
            )
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay autorizados.*", parse_mode='Markdown')
            resp = "⏳ *Días Restantes:*\n\n"
            now = datetime.utcnow()
            for k, info in auth.items():
                dias = (datetime.fromisoformat(info['vence']) - now).days
                usuario = info.get('username','')
                resp += f"• {usuario} (`{k}`) — {dias} día(s)\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # Grupos
        if text == "🗂 Grupos":
            bot.send_message(uid,
                "🗂 *Grupos*: chats activos y quién los activó.",
                parse_mode='Markdown'
            )
            grupos = load('grupos')
            if not grupos:
                return bot.send_message(uid, "ℹ️ *No hay grupos registrados.*", parse_mode='Markdown')
            resp = "🗂 *Grupos Activos:*\n\n"
            for k, info in grupos.items():
                resp += f"• `{k}` — activado por `{info['activado_por']}` el {info['creado']}\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # Mensajes
        if text == "📤 Mensajes":
            kb2 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            kb2.add(
                KeyboardButton("💬 A autorizados"), KeyboardButton("💬 A grupos"),
                KeyboardButton("❌ Salir")
            )
            return bot.send_message(
                uid,
                "📤 *Mensajes*:\n"
                "→ *A autorizados*: envía texto a todos.\n"
                "→ *A grupos*: envía texto a todos los grupos.",
                parse_mode='Markdown',
                reply_markup=kb2
            )

    # — Funciones auxiliares —
    def process_authorize(msg):
        uid = msg.from_user.id
        parts = [p.strip() for p in msg.text.split(',')]
        if len(parts)!=2 or not parts[0].isdigit() or not parts[1].startswith('@'):
            return bot.reply_to(msg, "❌ Formato inválido. Usa `ID,@usuario`.", parse_mode='Markdown')
        user_id = int(parts[0]); username = parts[1]
        add_authorized(user_id, username)
        exp_date = (datetime.utcnow() + timedelta(days=VIGENCIA_DIAS)).date()
        bot.send_message(
            uid,
            f"✅ {username} (`{user_id}`) autorizado hasta *{exp_date}*.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def process_deauthorize(msg):
        uid = msg.from_user.id
        if not msg.text.isdigit():
            return bot.reply_to(msg, "❌ ID inválido.", parse_mode='Markdown')
        user_id = int(msg.text)
        success = remove_authorized(user_id)
        text = "desautorizado" if success else "no estaba autorizado"
        bot.send_message(
            uid,
            f"🗑️ Usuario `{user_id}` {text}.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def send_to_authorized(msg):
        texto = msg.text
        for k in list_authorized().keys():
            try: bot.send_message(int(k), texto)
            except: pass
        bot.send_message(msg.from_user.id, "✅ Enviado a autorizados.", reply_markup=ReplyKeyboardRemove())

    def send_to_groups(msg):
        texto = msg.text
        for chat_id in load('grupos').keys():
            try: bot.send_message(int(chat_id), texto)
            except: pass
        bot.send_message(msg.from_user.id, "✅ Reenviado a grupos.", reply_markup=ReplyKeyboardRemove())
