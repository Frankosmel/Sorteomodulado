# main.py

from telebot import TeleBot
from telebot.types import Message, ChatMemberUpdated
from config import TOKEN, ADMINS
from storage import ensure_files
from auth import is_valid, register_group, get_info, remaining_days
from admin_handlers import register_admin_handlers, show_admin_menu
from datetime import datetime

bot = TeleBot(TOKEN, parse_mode="Markdown")

# --- Cuando cambian los permisos del bot en un chat (agregado a un grupo) ---
@bot.my_chat_member_handler(func=lambda upd: True)
def on_my_chat_member(upd: ChatMemberUpdated):
    try:
        new_status = upd.new_chat_member.status  # 'member', 'administrator', etc.
        chat = upd.chat
        actor = upd.from_user  # quien lo agregó
        chat_id = chat.id

        if new_status not in ("member", "administrator"):
            return

        # Solo quien paga (autorizado vigente) puede activar
        if not is_valid(actor.id):
            try:
                bot.send_message(actor.id, "⛔ No estás autorizado para activar el bot en grupos.")
            except Exception:
                pass
            bot.leave_chat(chat_id)
            return

        # Registrar grupo (aplica límites según plan)
        try:
            register_group(chat_id, actor.id)
        except ValueError as e:
            try:
                bot.send_message(actor.id, f"⚠️ No se pudo activar en este grupo: {str(e)}")
            except Exception:
                pass
            bot.leave_chat(chat_id)
            return

        # Confirmaciones
        try:
            bot.send_message(actor.id, f"✅ Bot activado en el grupo *{chat.title or chat_id}*.")
        except Exception:
            pass
        try:
            bot.send_message(chat_id, "🤖 Bot activado correctamente. Gracias.")
        except Exception:
            pass

    except Exception as ex:
        print("[my_chat_member error]", ex)

# --- /activar dentro del grupo (por si el bot ya estaba) ---
@bot.message_handler(commands=["activar"])
def cmd_activar(msg: Message):
    if msg.chat.type not in ("group", "supergroup"):
        return bot.reply_to(msg, "Este comando se usa dentro de grupos.")

    user_id = msg.from_user.id
    chat_id = msg.chat.id

    if not is_valid(user_id):
        return bot.reply_to(msg, "⛔ No estás autorizado para activar el bot en grupos.")

    try:
        register_group(chat_id, user_id)
    except ValueError as e:
        return bot.reply_to(msg, f"⚠️ No se pudo activar en este grupo: {str(e)}")

    return bot.reply_to(msg, "✅ Grupo activado correctamente para tu suscripción.")

# --- /start y /status en privado ---
@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    if is_valid(msg.from_user.id):
        info = get_info(msg.from_user.id)
        dias = remaining_days(msg.from_user.id)
        bot.reply_to(msg,
            f"✅ Ya estás autorizado.\n"
            f"Plan: *{info.get('plan','—')}*\n"
            f"Vence: *{info.get('vence','—')}*\n"
            f"Días restantes: *{dias}*"
        )
    else:
        bot.reply_to(msg,
            "👋 Hola. Aún no estás autorizado para usar el bot.\n"
            "Contacta a un administrador para adquirir un plan y activar tu acceso."
        )

@bot.message_handler(commands=["status"])
def cmd_status(msg: Message):
    if is_valid(msg.from_user.id):
        info = get_info(msg.from_user.id)
        dias = remaining_days(msg.from_user.id)
        bot.reply_to(msg,
            f"📊 *Estado de tu suscripción*\n\n"
            f"Plan: *{info.get('plan','—')}*\n"
            f"Vence: *{info.get('vence','—')}*\n"
            f"Días restantes: *{dias}*"
        )
    else:
        bot.reply_to(msg, "ℹ️ No tienes una suscripción activa.")

@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
        return bot.reply_to(msg, "⛔ *Acceso denegado.* Usa /admin en privado.")
    show_admin_menu(bot, msg.chat.id)

def main():
    ensure_files()
    register_admin_handlers(bot)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    main()
