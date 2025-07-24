from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import ADMINS, FILES, PLANS, STAFF_GROUP_ID, REPORT_CHANNEL_ID
from storage import load, save

PENDING_AUTH = {}

def show_admin_menu(bot: TeleBot, user_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👥 Gestión de Usuarios", callback_data="admin_users"),
        InlineKeyboardButton("👨‍👩‍👧‍👦 Grupos", callback_data="admin_groups"),
        InlineKeyboardButton("📦 Planes y Pagos", callback_data="admin_planes"),
        InlineKeyboardButton("📢 Canal de Reportes", callback_data="admin_report_channel"),
        InlineKeyboardButton("🧑‍💻 Grupo Staff", callback_data="admin_staff_group")
    )
    bot.send_message(user_id, "🛠 *Panel de Administración*", parse_mode="Markdown", reply_markup=kb)

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=["admin"])
    def cmd_admin(msg: Message):
        if msg.from_user.id in ADMINS:
            show_admin_menu(bot, msg.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_users")
    def submenu_usuarios(c):
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Autorizar", callback_data="auth_user"),
            InlineKeyboardButton("🚫 Desautorizar", callback_data="unauth_user"),
            InlineKeyboardButton("👁 Revisar autorizados", callback_data="list_auth_users"),
            InlineKeyboardButton("🔙 Volver", callback_data="back_admin")
        )
        bot.edit_message_text("👥 *Gestión de Usuarios*", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_groups")
    def submenu_grupos(c):
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("📋 Ver autorizados", callback_data="list_auth_groups"),
            InlineKeyboardButton("🚫 Ver no autorizados", callback_data="list_unauth_groups"),
            InlineKeyboardButton("🔚 Salir de no autorizados", callback_data="exit_unauth_groups"),
            InlineKeyboardButton("🔙 Volver", callback_data="back_admin")
        )
        bot.edit_message_text("👨‍👩‍👧‍👦 *Gestión de Grupos*", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "admin_planes")
    def submenu_planes(c):
        bot.edit_message_text("🧾 En desarrollo: módulo de planes y pagos", c.message.chat.id, c.message.message_id, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Volver", callback_data="back_admin")
        ))

    @bot.callback_query_handler(func=lambda c: c.data == "admin_report_channel")
    def submenu_report(c):
        bot.edit_message_text(f"📢 *Canal de Reportes actual:*\n`{REPORT_CHANNEL_ID}`", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Volver", callback_data="back_admin")
        ))

    @bot.callback_query_handler(func=lambda c: c.data == "admin_staff_group")
    def submenu_staff(c):
        bot.edit_message_text(f"🧑‍💻 *Grupo de Staff actual:*\n`{STAFF_GROUP_ID}`", c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔙 Volver", callback_data="back_admin")
        ))

    @bot.callback_query_handler(func=lambda c: c.data == "back_admin")
    def back_to_main(c):
        show_admin_menu(bot, c.from_user.id)

    @bot.callback_query_handler(func=lambda c: c.data == "auth_user")
    def pedir_id_usuario(c):
        bot.send_message(c.from_user.id, "✏️ Envía el ID del *usuario* que deseas autorizar:", parse_mode="Markdown")
        PENDING_AUTH[c.from_user.id] = {"step": "await_user_id"}

    @bot.callback_query_handler(func=lambda c: c.data == "unauth_user")
    def pedir_id_desautorizar(c):
        bot.send_message(c.from_user.id, "✏️ Envía el ID del *usuario* que deseas desautorizar:", parse_mode="Markdown")
        PENDING_AUTH[c.from_user.id] = {"step": "unauth_user"}

    @bot.message_handler(func=lambda m: m.from_user.id in PENDING_AUTH)
    def pasos_autorizacion(msg: Message):
        step = PENDING_AUTH[msg.from_user.id].get("step")

        if step == "await_user_id":
            try:
                uid = int(msg.text)
                PENDING_AUTH[msg.from_user.id] = {"step": "await_group_id", "user_id": uid}
                bot.send_message(msg.chat.id, "✅ Ahora reenvíame *cualquier mensaje* desde el grupo donde se activará el bot.", parse_mode="Markdown")
            except:
                bot.send_message(msg.chat.id, "⚠️ El ID del usuario debe ser numérico.")

        elif step == "await_group_id":
            if not msg.forward_from_chat or msg.forward_from_chat.type != "supergroup":
                return bot.send_message(msg.chat.id, "⚠️ Debes reenviar un *mensaje* desde el grupo.", parse_mode="Markdown")
            gid = msg.forward_from_chat.id
            uid = PENDING_AUTH[msg.from_user.id]["user_id"]

            autorizados = load("autorizados")
            usuarios = set(autorizados.get("users", []))
            usuarios.add(uid)
            autorizados["users"] = list(usuarios)
            save("autorizados", autorizados)

            grupos_aut = load("grupos_autorizados")
            grupos = set(grupos_aut.get("grupos", []))
            grupos.add(gid)
            grupos_aut["grupos"] = list(grupos)
            save("grupos_autorizados", grupos_aut)

            grupos_nom = load("grupos")
            grupos_nom[str(gid)] = msg.forward_from_chat.title
            save("grupos", grupos_nom)

            kb = InlineKeyboardMarkup()
            for p in PLANS:
                kb.add(InlineKeyboardButton(p['label'], callback_data=f"asignar_plan|{uid}|{gid}|{p['key']}"))
            bot.send_message(msg.chat.id, "🎯 Elige el *plan* que tendrá este usuario:", reply_markup=kb, parse_mode="Markdown")
            del PENDING_AUTH[msg.from_user.id]

        elif step == "unauth_user":
            try:
                uid = int(msg.text)
                autorizados = load("autorizados")
                users = set(autorizados.get("users", []))
                if uid in users:
                    users.remove(uid)
                    autorizados["users"] = list(users)
                    save("autorizados", autorizados)
                    bot.send_message(msg.chat.id, "✅ Usuario desautorizado correctamente.")
                else:
                    bot.send_message(msg.chat.id, "⚠️ Ese usuario no está autorizado.")
            except:
                bot.send_message(msg.chat.id, "⚠️ El ID debe ser numérico.")
            del PENDING_AUTH[msg.from_user.id]

    @bot.callback_query_handler(func=lambda c: c.data.startswith("asignar_plan"))
    def asignar_plan(c):
        _, uid, gid, plan_key = c.data.split("|")
        jobs = load("jobs")
        jobs[uid] = {
            "chat_id": int(gid),
            "plan": plan_key
        }
        save("jobs", jobs)
        bot.answer_callback_query(c.id, "✅ Plan asignado.")
        bot.edit_message_text("✅ Plan asignado correctamente.", c.message.chat.id, c.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data == "list_auth_users")
    def listar_autorizados(c):
        autorizados = load("autorizados")
        ids = autorizados.get("users", [])
        if not ids:
            return bot.answer_callback_query(c.id, "Ningún usuario autorizado.")
        texto = "*Usuarios autorizados:*\n\n" + "\n".join(f"• `{i}`" for i in ids)
        bot.send_message(c.from_user.id, texto, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data == "list_auth_groups")
    def listar_grupos_autorizados(c):
        grupos_aut = load("grupos_autorizados")
        nombres = load("grupos")
        ids = grupos_aut.get("grupos", [])
        if not ids:
            return bot.answer_callback_query(c.id, "Ningún grupo autorizado.")
        texto = "*Grupos autorizados:*\n\n"
        for gid in ids:
            nombre = nombres.get(str(gid), "Sin nombre")
            texto += f"• `{gid}` — {nombre}\n"
        bot.send_message(c.from_user.id, texto, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data == "list_unauth_groups")
    def listar_no_autorizados(c):
        updates = bot.get_updates(limit=100)
        grupos_aut = load("grupos_autorizados").get("grupos", [])
        nombres = load("grupos")
        activos = set()

        for u in updates:
            if u.message and u.message.chat.type == "supergroup":
                activos.add(u.message.chat.id)

        no_aut = [gid for gid in activos if gid not in grupos_aut]
        if not no_aut:
            return bot.send_message(c.from_user.id, "✅ Todos los grupos activos están autorizados.")

        texto = "*Grupos NO autorizados activos:*\n\n"
        for gid in no_aut:
            nombre = nombres.get(str(gid), "Desconocido")
            texto += f"• `{gid}` — {nombre}\n"
        bot.send_message(c.from_user.id, texto, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data == "exit_unauth_groups")
    def salir_de_no_autorizados(c):
        updates = bot.get_updates(limit=100)
        grupos_aut = load("grupos_autorizados").get("grupos", [])
        activos = set()

        for u in updates:
            if u.message and u.message.chat.type == "supergroup":
                activos.add(u.message.chat.id)

        no_aut = [gid for gid in activos if gid not in grupos_aut]
        for gid in no_aut:
            try:
                bot.leave_chat(gid)
            except:
                pass

        bot.send_message(c.from_user.id, f"🔚 Bot salió de {len(no_aut)} grupos no autorizados.")
