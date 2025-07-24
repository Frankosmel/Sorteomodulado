from telebot import TeleBot from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton from config import ADMINS, STAFF_GROUP_ID, REPORT_CHANNEL_ID from storage import load, save from auth import remove_authorized, list_authorized

----------------- MENÚ PRINCIPAL ADMIN -----------------

def show_admin_menu(bot: TeleBot, uid: int): kb = InlineKeyboardMarkup(row_width=2) kb.add( InlineKeyboardButton("👥 Gestión de Usuarios", callback_data="admin_users"), InlineKeyboardButton("📊 Planes y Pagos", callback_data="admin_planes"), InlineKeyboardButton("👥 Grupo Staff", callback_data="admin_staff"), InlineKeyboardButton("📢 Canal Reportes", callback_data="admin_reportes"), InlineKeyboardButton("👨‍👩‍👧‍👦 Grupos", callback_data="admin_grupos") ) bot.send_message(uid, "🔧 Panel de Administración — elige una opción:", reply_markup=kb)

----------------- SUBMENÚ GESTIÓN DE USUARIOS -----------------

def show_user_management_menu(bot: TeleBot, cid: int): kb = InlineKeyboardMarkup(row_width=2) kb.add( InlineKeyboardButton("✅ Ver autorizados", callback_data="ver_autorizados"), InlineKeyboardButton("❌ Desautorizar usuario", callback_data="desautorizar_usuario"), InlineKeyboardButton("🔙 Atrás", callback_data="admin_back") ) bot.edit_message_text("👥 Gestión de Usuarios:", cid, cid, reply_markup=kb)

----------------- SUBMENÚ GESTIÓN DE GRUPOS -----------------

def show_group_management_menu(bot: TeleBot, cid: int): kb = InlineKeyboardMarkup(row_width=1) kb.add( InlineKeyboardButton("✅ Ver autorizados", callback_data="grupos_ver_autorizados"), InlineKeyboardButton("🚫 Ver no autorizados", callback_data="grupos_ver_no_autorizados"), InlineKeyboardButton("⛔ Salir de no autorizados", callback_data="grupos_salir_no_autorizados"), InlineKeyboardButton("🔙 Atrás", callback_data="admin_back") ) bot.edit_message_text("📋 Gestión de Grupos:", cid, cid, reply_markup=kb)

----------------- HANDLER PRINCIPAL -----------------

def register_admin_handlers(bot: TeleBot):

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return bot.answer_callback_query(call.id, "⛔ Acceso denegado.", show_alert=True)

    if call.data == "admin_users":
        return show_user_management_menu(bot, call.message.chat.id)

    elif call.data == "admin_grupos":
        return show_group_management_menu(bot, call.message.chat.id)

    elif call.data == "admin_planes":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("💳 Aquí puedes configurar o revisar los planes de pago. (Funcionalidad en desarrollo)", call.message.chat.id, call.message.message_id)

    elif call.data == "admin_staff":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f"👥 Grupo de staff actual:

{STAFF_GROUP_ID}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

elif call.data == "admin_reportes":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f"📢 Canal de reportes actual:

{REPORT_CHANNEL_ID}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

elif call.data == "admin_back":
        show_admin_menu(bot, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data == "ver_autorizados")
def ver_autorizados(call: CallbackQuery):
    users = list_authorized()
    if not users:
        return bot.edit_message_text("❌ No hay usuarios autorizados.", call.message.chat.id, call.message.message_id)

    msg = "✅ *Usuarios autorizados:*

" for uid, data in users.items(): username = data.get("username", "") vencimiento = data.get("vence", "?") nombre = data.get("nombre", uid) msg += f"\n• {nombre} ({'@' + username if username else uid}) — vence: {vencimiento}"

bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "desautorizar_usuario")
def desautorizar_usuario(call: CallbackQuery):
    bot.edit_message_text("✏️ Escribe el ID del usuario que deseas desautorizar:", call.message.chat.id, call.message.message_id)

    @bot.message_handler(func=lambda m: str(m.chat.id) == str(call.message.chat.id))
    def recibir_id(m: Message):
        try:
            user_id = int(m.text.strip())
            if remove_authorized(user_id):
                bot.reply_to(m, f"✅ Usuario {user_id} desautorizado correctamente.")
            else:
                bot.reply_to(m, "❌ Ese usuario no estaba autorizado.")
        except:
            bot.reply_to(m, "⚠️ Debes enviar un número de ID válido.")
        bot.clear_step_handler_by_chat_id(m.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("grupos_"))
def grupos_callback(call: CallbackQuery):
    grupos = load("grupos")
    autorizados = set(load("grupos_autorizados").get("groups", []))
    todos = set(grupos.keys())

    if call.data == "grupos_ver_autorizados":
        if not autorizados:
            return bot.edit_message_text("❌ No hay grupos autorizados.", call.message.chat.id, call.message.message_id)
        msg = "✅ *Grupos autorizados:*

" for gid in autorizados: nombre = grupos.get(gid, {}).get("nombre", "Grupo") enlace = f"https://t.me/c/{str(gid)[4:]} " msg += f"\n• {gid} — {nombre}\n{enlace}" bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

elif call.data == "grupos_ver_no_autorizados":
        no_aut = todos - autorizados
        if not no_aut:
            return bot.edit_message_text("✅ Todos los grupos están autorizados.", call.message.chat.id, call.message.message_id)
        msg = "🚫 *Grupos no autorizados:*

" for gid in no_aut: nombre = grupos.get(gid, {}).get("nombre", "Grupo") enlace = f"https://t.me/c/{str(gid)[4:]} " msg += f"\n• {gid} — {nombre}\n{enlace}" bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

elif call.data == "grupos_salir_no_autorizados":
        no_aut = todos - autorizados
        if not no_aut:
            return bot.edit_message_text("✅ No hay grupos no autorizados para salir.", call.message.chat.id, call.message.message_id)

        for gid in no_aut:
            try:
                bot.leave_chat(int(gid))
            except:
                continue
        bot.edit_message_text(f"✅ Se ha salido de {len(no_aut)} grupo(s) no autorizados.", call.message.chat.id, call.message.message_id)

    elif call.data == "admin_back":
        show_admin_menu(bot, call.from_user.id)

