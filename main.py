# main.py

from telebot import TeleBot
from telebot.types import Message, ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, ADMINS, CONTACT_ADMIN_USERNAME, SUPPORT_CHAT_LINK
from storage import ensure_files
from auth import is_valid, register_group, get_info, remaining_days
from admin_handlers import register_admin_handlers, show_admin_menu
from datetime import datetime

bot = TeleBot(TOKEN, parse_mode="Markdown")

# ──────────────────────────────────────────────────────────────────────────────
# UTIL: detección de rol
# ──────────────────────────────────────────────────────────────────────────────
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ──────────────────────────────────────────────────────────────────────────────
# Teclados
# ──────────────────────────────────────────────────────────────────────────────
def user_menu_kb():
    """Teclado de usuario (cliente) en privado."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("💳 Ver planes"), KeyboardButton("📊 Mi estado"))
    kb.row(KeyboardButton("📞 Contactar administrador"))
    return kb

def admin_menu_kb():
    """Teclado básico para administradores (atajo a /admin)."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("/admin"))
    kb.row(KeyboardButton("📊 Mi estado"))  # opcional, útil para admins que también son clientes
    return kb

# ──────────────────────────────────────────────────────────────────────────────
# /start y /status
# ──────────────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    if msg.chat.type != 'private':
        return

    uid = msg.from_user.id

    # Si es admin, abre el panel de administración (y no mostramos menú de cliente)
    if is_admin(uid):
        # Opción A: abrir panel directamente
        show_admin_menu(bot, msg.chat.id)
        # Opción B (alternativa): si prefieres no abrir directo, comenta la línea de arriba
        # y descomenta la siguiente para mostrar un teclado con /admin
        # bot.send_message(msg.chat.id, "👑 Eres administrador. Usa /admin para abrir el panel.", reply_markup=admin_menu_kb())
        return

    # Cliente (no admin)
    if is_valid(uid):
        info = get_info(uid)
        dias = remaining_days(uid)
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

    uid = msg.from_user.id

    # Permitimos que el admin consulte su propio estado sin que aparezca el menú de cliente
    if is_valid(uid):
        info = get_info(uid)
        dias = remaining_days(uid)
        kb = admin_menu_kb() if is_admin(uid) else user_menu_kb()
        bot.send_message(
            msg.chat.id,
            f"📊 *Estado de tu suscripción*\n\n"
            f"Plan: *{info.get('plan_label', info.get('plan','—'))}*\n"
            f"Vence: *{info.get('vence','—')}*\n"
            f"Días restantes: *{dias}*",
            reply_markup=kb
        )
    else:
        # Si no tiene suscripción, para admin mostramos teclado admin; para cliente, teclado cliente
        kb = admin_menu_kb() if is_admin(uid) else user_menu_kb()
        bot.send_message(msg.chat.id, "ℹ️ No tienes una suscripción activa.", reply_markup=kb)

# ──────────────────────────────────────────────────────────────────────────────
# /planes (cliente)  — NO mostrar a admins
# ──────────────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["planes"])
def cmd_planes(msg: Message):
    if msg.chat.type != 'private':
        return
    if is_admin(msg.from_user.id):
        # Evitamos mostrar catálogo de cliente a admins
        return bot.send_message(msg.chat.id, "👑 Eres administrador. Usa /admin para gestionar planes y usuarios.", reply_markup=admin_menu_kb())

    from config import PLANS
    text = "💳 *Planes disponibles (USD)*\n\n"
    for p in PLANS:
        text += f"{p['label']}\n"
    bot.send_message(msg.chat.id, text, reply_markup=user_menu_kb())

# ──────────────────────────────────────────────────────────────────────────────
# Botones del cliente (filtrados para NO admins)
# ──────────────────────────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: (
    m.chat.type=='private'
    and m.from_user.id not in ADMINS
    and m.text in ["💳 Ver planes", "📊 Mi estado", "📞 Contactar administrador"]
))
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

# ──────────────────────────────────────────────────────────────────────────────
# Activación en grupos (modelo A)
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# /activar (en grupo)
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# /admin (panel de administración)
# ──────────────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if msg.chat.type != 'private' or not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "⛔ *Acceso denegado.* Use /admin en privado.")
    show_admin_menu(bot, msg.chat.id)

# ──────────────────────────────────────────────────────────────────────────────
# Arranque
# ──────────────────────────────────────────────────────────────────────────────
def main():
    ensure_files()
    register_admin_handlers(bot)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    main()
