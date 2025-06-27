from telebot import TeleBot from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove from config import ADMINS from auth import add_authorized, remove_authorized, list_authorized, is_valid, register_group from datetime import datetime

def register_admin_handlers(bot: TeleBot): @bot.message_handler(commands=['admin']) def admin_panel(msg): if msg.chat.type != 'private' or msg.from_user.id not in ADMINS: return bot.reply_to(msg, "⛔ Acceso denegado o usa este comando en privado.")

kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📋 Listar autorizados"), KeyboardButton("➕ Autorizar usuario"))
    kb.add(KeyboardButton("➖ Desautorizar usuario"), KeyboardButton("🔄 Ver vencimientos"))
    kb.add(KeyboardButton("🗂 Ver grupos"), KeyboardButton("🔙 Salir"))

    bot.send_message(msg.chat.id, "👑 Panel Admin — Elige una opción:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id in ADMINS)
def handle_admin(msg):
    text = msg.text
    uid = msg.from_user.id

    if text == "📋 Listar autorizados":
        autorizados = list_authorized()
        if not autorizados:
            return bot.send_message(uid, "ℹ️ No hay usuarios autorizados aún.")
        resp = "👥 *Usuarios Autorizados:*

" for k, info in autorizados.items(): exp = datetime.fromisoformat(info['vence']).date() resp += f"• ID {k} — vence {exp}\n" return bot.send_message(uid, resp, parse_mode='Markdown')

if text == "➕ Autorizar usuario":
        prompt = bot.send_message(uid,
            "✏️ Envía solo el ID del usuario a autorizar:\n`/autorizar <user_id>`",
            parse_mode='Markdown'
        )
        return bot.register_next_step_handler(prompt, lambda m: bot.send_message(uid, "Usa el comando directamente: `/autorizar <user_id>`"))

    if text == "➖ Desautorizar usuario":
        prompt = bot.send_message(uid,
            "✏️ Envía solo el ID del usuario a desautorizar:\n`/desautorizar <user_id>`",
            parse_mode='Markdown'
        )
        return bot.register_next_step_handler(prompt, lambda m: bot.send_message(uid, "Usa el comando directamente: `/desautorizar <user_id>`"))

    if text == "🔄 Ver vencimientos":
        autorizados = list_authorized()
        hoy = datetime.utcnow()
        resp = "⏳ *Vencimientos próximos:*

" for k, info in autorizados.items(): exp = datetime.fromisoformat(info['vence']) dias = (exp - hoy).days resp += f"• ID {k} — {dias} día(s) restantes\n" return bot.send_message(uid, resp, parse_mode='Markdown')

if text == "🗂 Ver grupos":
        grupos = load('grupos')
        if not grupos:
            return bot.send_message(uid, "ℹ️ No hay grupos registrados.")
        resp = "🗂 *Grupos Activos:*

" for k, info in grupos.items(): resp += f"• Grupo {k} — activado por {info['activado_por']} el {info['creado']}\n" return bot.send_message(uid, resp, parse_mode='Markdown')

if text == "🔙 Salir":
        return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(commands=['autorizar'])
def cmd_autorizar(message):
    if message.from_user.id not in ADMINS:
        return bot.reply_to(message, "⛔ No tienes permiso.")
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message,
            "❌ Uso: `/autorizar <user_id>`", parse_mode='Markdown'
        )
    new_id = int(parts[1])
    add_authorized(new_id, message.from_user.id)
    bot.reply_to(message,
        f"✅ Usuario `{new_id}` autorizado hasta `{(datetime.utcnow()+timedelta(days=VIGENCIA_DIAS)).date()}`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['desautorizar'])
def cmd_desautorizar(message):
    if message.from_user.id not in ADMINS:
        return bot.reply_to(message, "⛔ No tienes permiso.")
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message,
            "❌ Uso: `/desautorizar <user_id>`", parse_mode='Markdown'
        )
    rem_id = int(parts[1])
    success = remove_authorized(rem_id)
    if success:
        bot.reply_to(message, f"🗑️ Usuario `{rem_id}` desautorizado.", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"ℹ️ Usuario `{rem_id}` no existía.")

