from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, STAFF_GROUP_ID, REPORT_CHANNEL_ID
from storage import load, save

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id in ADMINS)
    def handle_admin_menu(msg):
        uid = msg.from_user.id
        text = msg.text.strip()

        if text == "/admin":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Gestión de Usuarios"))
            kb.add(KeyboardButton("👨‍👩‍👧‍👦 Grupos"))
            kb.add(KeyboardButton("📦 Planes y Pagos"))
            kb.add(KeyboardButton("📢 Canal de Reportes"), KeyboardButton("🧑‍💻 Grupo Staff"))
            return bot.send_message(uid, "⚙️ Panel de administración", reply_markup=kb)

        # Submenú de Gestión de Usuarios
        if text == "👥 Gestión de Usuarios":
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ Autorizar", callback_data="admin_autorizar"),
                InlineKeyboardButton("❌ Desautorizar", callback_data="admin_desautorizar"),
                InlineKeyboardButton("👀 Revisar autorizados", callback_data="admin_ver_autorizados"),
                InlineKeyboardButton("🔙 Volver", callback_data="admin_volver")
            )
            return bot.send_message(uid, "👥 Elige una acción:", reply_markup=kb)

        # Submenú de Grupos
        if text == "👨‍👩‍👧‍👦 Grupos":
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("📋 Ver autorizados", callback_data="admin_grupos_autorizados"),
                InlineKeyboardButton("🚫 Ver no autorizados", callback_data="admin_grupos_no_aut"),
                InlineKeyboardButton("🔚 Salir de no autorizados", callback_data="admin_salir_no_aut"),
                InlineKeyboardButton("🔙 Volver", callback_data="admin_volver")
            )
            return bot.send_message(uid, "👨‍👩‍👧‍👦 Gestión de grupos:", reply_markup=kb)

        if text == "📦 Planes y Pagos":
            return bot.send_message(uid, "📦 Aquí se mostrará la gestión de pagos y vencimientos (por implementar).")

        if text == "📢 Canal de Reportes":
            return bot.send_message(uid, f"📢 Canal configurado: `{REPORT_CHANNEL_ID}`", parse_mode='Markdown')

        if text == "🧑‍💻 Grupo Staff":
            return bot.send_message(uid, f"🧑‍💻 Grupo de staff configurado: `{STAFF_GROUP_ID}`", parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
    def handle_admin_callbacks(cq):
        uid = cq.from_user.id
        data = cq.data

        if data == "admin_volver":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Gestión de Usuarios"))
            kb.add(KeyboardButton("👨‍👩‍👧‍👦 Grupos"))
            kb.add(KeyboardButton("📦 Planes y Pagos"))
            kb.add(KeyboardButton("📢 Canal de Reportes"), KeyboardButton("🧑‍💻 Grupo Staff"))
            return bot.send_message(uid, "🔙 Volviendo al panel principal:", reply_markup=kb)

        if data == "admin_ver_autorizados":
            users = load("autorizados").get("users", [])
            if not users:
                return bot.send_message(uid, "❌ No hay usuarios autorizados.")
            lista = "\n".join(f"• `{u}`" for u in users)
            return bot.send_message(uid, f"👥 *Usuarios autorizados:*\n\n{lista}", parse_mode='Markdown')

        if data == "admin_autorizar":
            bot.send_message(uid, "✏️ Envía el ID del usuario que deseas autorizar:")
            return bot.register_next_step_handler_by_chat_id(uid, process_autorizar)

        if data == "admin_desautorizar":
            bot.send_message(uid, "✏️ Envía el ID del usuario que deseas desautorizar:")
            return bot.register_next_step_handler_by_chat_id(uid, process_desautorizar)

        if data == "admin_grupos_autorizados":
            grupos = load("grupos_autorizados").get("grupos", [])
            if not grupos:
                return bot.send_message(uid, "❌ No hay grupos autorizados.")
            detalles = []
            todos = load("grupos")
            for gid in grupos:
                ginfo = todos.get(str(gid), {})
                nombre = ginfo.get("nombre", "¿Nombre?")
                enlace = ginfo.get("enlace", "")
                detalles.append(f"• `{gid}` - {nombre}\n{enlace}" if enlace else f"• `{gid}` - {nombre}")
            txt = "\n\n".join(detalles)
            return bot.send_message(uid, f"📋 *Grupos autorizados:*\n\n{txt}", parse_mode='Markdown')

        if data == "admin_grupos_no_aut":
            activos = bot.get_my_commands(scope=None)
            current_chats = [chat.id for chat in bot.get_updates()]
            autorizados = set(load("grupos_autorizados").get("grupos", []))
            no_aut = []
            for gid in current_chats:
                if gid < 0 and gid not in autorizados:
                    no_aut.append(gid)
            if not no_aut:
                return bot.send_message(uid, "✅ No hay grupos no autorizados.")
            txt = "\n".join(f"• `{gid}`" for gid in no_aut)
            return bot.send_message(uid, f"🚫 *Grupos no autorizados:*\n\n{txt}", parse_mode='Markdown')

        if data == "admin_salir_no_aut":
            updates = bot.get_updates()
            all_chats = [upd.message.chat.id for upd in updates if upd.message and upd.message.chat.type in ["group", "supergroup"]]
            autorizados = set(load("grupos_autorizados").get("grupos", []))
            salidos = []
            for gid in set(all_chats):
                if gid not in autorizados:
                    try:
                        bot.send_message(gid, "👋 Este bot ha sido desactivado en este grupo por no estar autorizado.")
                        bot.leave_chat(gid)
                        salidos.append(gid)
                    except:
                        continue
            if not salidos:
                return bot.send_message(uid, "✅ No se encontró ningún grupo no autorizado activo.")
            txt = "\n".join(f"• `{gid}`" for gid in salidos)
            return bot.send_message(uid, f"🚪 El bot ha salido de los siguientes grupos no autorizados:\n\n{txt}", parse_mode='Markdown')

    # — Funciones auxiliares —
    def process_autorizar(msg):
        uid = msg.from_user.id
        try:
            nuevo = int(msg.text.strip())
        except:
            return bot.send_message(uid, "❌ ID inválido. Solo números.")
        autorizados = load("autorizados")
        lista = set(autorizados.get("users", []))
        lista.add(nuevo)
        autorizados["users"] = list(lista)
        save("autorizados", autorizados)
        return bot.send_message(uid, f"✅ Usuario `{nuevo}` autorizado.", parse_mode='Markdown')

    def process_desautorizar(msg):
        uid = msg.from_user.id
        try:
            obj = int(msg.text.strip())
        except:
            return bot.send_message(uid, "❌ ID inválido. Solo números.")
        autorizados = load("autorizados")
        lista = set(autorizados.get("users", []))
        if obj in lista:
            lista.remove(obj)
            autorizados["users"] = list(lista)
            save("autorizados", autorizados)
            return bot.send_message(uid, f"✅ Usuario `{obj}` desautorizado.", parse_mode='Markdown')
        else:
            return bot.send_message(uid, "⚠️ Ese usuario no estaba autorizado.")
