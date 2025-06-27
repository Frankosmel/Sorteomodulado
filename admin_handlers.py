from telebot import TeleBot from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove from config import ADMINS from storage import load from auth import add_authorized, remove_authorized, list_authorized, register_group from datetime import datetime, timedelta

def register_admin_handlers(bot: TeleBot): @bot.message_handler(commands=['admin']) def admin_panel(msg): if msg.chat.type != 'private' or msg.from_user.id not in ADMINS: return bot.reply_to(msg, "⛔ Acceso denegado o usa este comando en privado.")

kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        KeyboardButton("📋 Listar autorizados"), KeyboardButton("➕ Autorizar usuario")
    )
    kb.row(
        KeyboardButton("➖ Desautorizar usuario"), KeyboardButton("🔄 Ver vencimientos")
    )
    kb.row(
        KeyboardButton("🗂 Ver grupos"), KeyboardButton("🔙 Salir")
    )

    bot.send_message(msg.chat.id, "👑 Panel Admin — Elige una opción:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id in ADMINS)
def handle_admin(msg):
    text = msg.text
    uid = msg.from_user.id

    if text == "📋 Listar autorizados":
        autorizados = list_authorized()
        if not autorizados:
            return bot.send_message(uid, "ℹ️ No hay usuarios autorizados aún.")
        resp = "👥 *Usuarios Autorizados:*\n\n"
        for k, info in autorizados.items():
            exp_date = datetime.fromisoformat(info['vence']).date()
            resp += f"• ID `{k}` — vence {exp_date}\n"
        return bot.send_message(uid, resp, parse_mode='Markdown')

    if text == "➕ Autorizar usuario":
        return bot.send_message(
            uid,
            "✏️ Para autorizar, usa el comando:\n`/autorizar <user_id>`",
            parse_mode='Markdown'
        )

    if text == "➖ Desautorizar usuario":
        return bot.send_message(
            uid,
            "✏️ Para desautorizar, usa el comando:\n`/desautorizar <user_id>`",
            parse_mode='Markdown'
        )

    if text == "🔄 Ver vencimientos":
        autorizados = list_authorized()
        resp = "⏳ *Vencimientos próximos:*\n\n"
        now = datetime.utcnow()
        for k, info in autorizados.items():
            exp = datetime.fromisoformat(info['vence'])
            dias = (exp - now).days
            resp += f"• ID `{k}` — {dias} día(s) restantes\n"
        return bot.send_message(uid, resp, parse_mode='Markdown')

    if text == "🗂 Ver grupos":
        grupos = load('grupos')
        if not grupos:
            return bot.send_message(uid, "ℹ️ No hay grupos registrados.")
        resp = "🗂 *Grupos Activos:*\n\n"
        for k, info in grupos.items():
            resp += f"• Grupo `{k}` — activado por {info['activado_por']} el {info['creado']}\n"
        return bot.send_message(uid, resp, parse_mode='Markdown')

    if text == "🔙 Salir":
        return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(commands=['autorizar'])
def cmd_autorizar(message):
    if message.from_user.id not in ADMINS:
        return bot.reply_to(message, "⛔ No tienes permiso.")
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message, "❌ Uso: /autorizar <user_id>", parse_mode='Markdown')
    new_id = int(parts[1])
    add_authorized(new_id, message.from_user.id)
    exp_date = (datetime.utcnow() + timedelta(days=VIGENCIA_DIAS)).date()
    return bot.reply_to(
        message,
        f"✅ Usuario `{new_id}` autorizado hasta {exp_date}",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['desautorizar'])
def cmd_desautorizar(message):
    if message.from_user.id not in ADMINS:
        return bot.reply_to(message, "⛔ No tienes permiso.")
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message, "❌ Uso: /desautorizar <user_id>", parse_mode='Markdown')
    rem_id = int(parts[1])
    success = remove_authorized(rem_id)
    if success:
        return bot.reply_to(message, f"🗑️ Usuario `{rem_id}` desautorizado.", parse_mode='Markdown')
    else:
        return bot.reply_to(message, f"ℹ️ Usuario `{rem_id}` no existía.")

