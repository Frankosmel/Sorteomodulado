# main.py

from telebot import TeleBot
from telebot.types import Message, ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, ADMINS, CONTACT_ADMIN_USERNAME, SUPPORT_CHAT_LINK
from storage import ensure_files
from auth import is_valid, register_group, get_info, remaining_days
from admin_handlers import register_admin_handlers, show_admin_menu
from datetime import datetime

bot = TeleBot(TOKEN, parse_mode="Markdown")

# --------- Teclado de usuario (privado) ----------
def user_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("💳 Ver planes"), KeyboardButton("📊 Mi estado"))
    kb.row(KeyboardButton("📞 Contactar administrador"))
    return kb

@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    if msg.chat.type != 'private':
        return
    if is_valid(msg.from_user.id):
        info = get_info(msg.from_user.id)
        dias = remaining_days(msg.from_user.id)
        bot.send_message(
            msg.chat.id,
            f"✅ Ya estás autorizado.\n"
            f"Plan: *{info.get('plan_label', info.get('plan','—'))}*\n"
            f"Vence: *{info.get('vence','—')}*\n"
            f"Días restantes: *{dias}*",
            reply_markup=user_menu_kb()
        )
    else:
        bot.send_message(
            msg.chat.id,
            "👋 Hola. Aún no estás autorizado para usar el bot.\n"
            "Puedes ver los planes disponibles o contactar al administrador.",
            reply_markup=user_menu_kb()
        )

@bot.message_handler(commands=["status"])
def cmd_status(msg: Message):
    if msg.chat.type != 'private':
        return
    if is_valid(msg.from_user.id):
        info = get_info(msg.from_user.id)
        dias = remaining_days(msg.from_user.id)
        bot.send_message(
            msg.chat.id,
            f"📊 *Estado de tu suscripción*\n\n"
            f"Plan: *{info.get('plan_label', info.get('plan','—'))}*\n"
            f"Vence: *{info.get('vence','—')}*\n"
            f"Días restantes: *{dias}*",
            reply_markup=user_menu_kb()
        )
    else:
        bot.send_message(msg.chat.id, "ℹ️ No tienes una suscripción activa.", reply_markup=user_menu_kb())

@bot.message_handler(commands=["planes"])
def cmd_planes(msg: Message):
    if msg.chat.type != 'private':
        return
    from config import PLANS, PAYMENT_INFO
    text = "💳 *Planes disponibles (USD)*\n\n"
    for p in PLANS:
        text += f"{p['label']}\n"
    text += "\n🧾 *Pago*: " + (PAYMENT_INFO.get("observacion",""))
    bot.send_message(msg.chat.id, text, reply_markup=user_menu_kb())

@bot.message_handler(func=lambda m: m.chat.type=='private' and m.text in ["💳 Ver planes", "📊 Mi estado", "📞 Contactar administrador"])
def handle_user_buttons(msg: Message):
    if msg.text == "💳 Ver planes":
        return cmd_planes(msg)
    if msg.text == "📊 Mi estado":
        return cmd_status(msg)
    if msg.text == "📞 Contactar administrador":
        link = SUPPORT_CHAT_LINK or f"https://t.me/{CONTACT_ADMIN_USERNAME}"
        return bot.send_message(
            msg.chat.id,
            f"📞 Contacto: @{CONTACT_ADMIN_USERNAME}\nEnlace: {link}",
            reply_markup=user_menu_kb()
        )

# --- Cuando agregan al bot a un grupo (activación por usuario autorizado) ---
@bot.my_chat_member_handler(func=lambda upd: True)
def on_my_chat_member(upd: ChatMemberUpdated):
    try:
        new_status = upd.new_chat_member.status
        chat = upd.chat
        actor = upd.from_user
        chat_id = chat.id

        if new_status not in ("member", "administrator"):
            return

        if not is_valid(actor.id):
            try:
                bot.send_message(actor.id, "⛔ No estás autorizado para activar el bot en grupos.")
            except Exception:
                pass
            bot.leave_chat(chat_id)
            return

        try:
            register_group(chat_id, actor.id)
        except ValueError as e:
            try:
                bot.send_message(actor.id, f"⚠️ No se pudo activar en este grupo: {str(e)}")
            except Exception:
                pass
            bot.leave_chat(chat_id)
            return

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

# --- /activar dentro del grupo ---
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

# --- /admin (reutilizamos el panel con emojis) ---
@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
        return bot.reply_to(msg, "⛔ *Acceso denegado.* Use /admin en privado.")
    show_admin_menu(bot, msg.chat.id)

def main():
    ensure_files()
    register_admin_handlers(bot)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    main()
