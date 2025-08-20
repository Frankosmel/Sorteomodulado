# main.py

from telebot import TeleBot
from telebot.types import Message, ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import math

from config import (
    TOKEN, ADMINS, CONTACT_ADMIN_USERNAME, SUPPORT_CHAT_LINK,
    PLANS, VIGENCIA_DIAS,
    USD_TO_CUP_TRANSFER, SALDO_DIVISOR, ROUND_TO,
    PAYPAL_FEE_PCT, PAYPAL_FEE_FIXED,
    PAYMENT_INFO,
)
from storage import ensure_files
from auth import is_valid, register_group, get_info, remaining_days
from admin_handlers import register_admin_handlers, show_admin_menu

bot = TeleBot(TOKEN, parse_mode="Markdown")

# ───────── Helpers de rol ─────────
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# ───────── Teclados ─────────
def user_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("💳 Ver planes"), KeyboardButton("📊 Mi estado"))
    kb.row(KeyboardButton("📞 Contactar administrador"))
    return kb

def admin_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("/admin"))
    kb.row(KeyboardButton("📊 Mi estado"))
    return kb

def plans_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for p in PLANS:
        kb.row(p['label'])
    kb.row("Cancelar")
    return kb

def payment_methods_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(PAYMENT_INFO['saldo']['label'])
    kb.row(PAYMENT_INFO['cup']['label'])
    kb.row(PAYMENT_INFO['paypal']['label'])
    kb.row("Cancelar")
    return kb

# ───────── Cálculos ─────────
def label_to_plan(label: str):
    for p in PLANS:
        if p['label'] == label:
            return p
    return None

def compute_paypal_gross(price_usd: float) -> float:
    bruto = (price_usd + PAYPAL_FEE_FIXED) / (1.0 - PAYPAL_FEE_PCT)
    return round(bruto, 2)

def usd_to_cup_transfer(amount_usd: float) -> int:
    return int(round(amount_usd * USD_TO_CUP_TRANSFER))

def usd_to_cup_saldo(amount_usd: float) -> int:
    base = (amount_usd * USD_TO_CUP_TRANSFER) / SALDO_DIVISOR
    ajustado = math.ceil(base / ROUND_TO) * ROUND_TO
    return int(ajustado)

# ───────── Estado de compra ─────────
# uid -> { plan_key, plan_label, price_usd, cup_transfer, cup_saldo, paypal_gross, method }
PENDING_PAY: dict[int, dict] = {}

# ───────── /start y /status ─────────
@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    if msg.chat.type != 'private':
        return
    uid = msg.from_user.id

    if is_admin(uid):
        show_admin_menu(bot, msg.chat.id)
        return

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

    kb = admin_menu_kb() if is_admin(uid) else user_menu_kb()
    if is_valid(uid):
        info = get_info(uid)
        dias = remaining_days(uid)
        bot.send_message(
            msg.chat.id,
            f"📊 *Estado de tu suscripción*\n\n"
            f"Plan: *{info.get('plan_label', info.get('plan','—'))}*\n"
            f"Vence: *{info.get('vence','—')}*\n"
            f"Días restantes: *{dias}*",
            reply_markup=kb
        )
    else:
        bot.send_message(msg.chat.id, "ℹ️ No tienes una suscripción activa.", reply_markup=kb)

@bot.message_handler(commands=["planes"])
def cmd_planes(msg: Message):
    if msg.chat.type != 'private':
        return
    if is_admin(msg.from_user.id):
        return bot.send_message(msg.chat.id, "👑 Eres administrador. Usa /admin para gestionar.", reply_markup=admin_menu_kb())

    lines = [p['label'] for p in PLANS]
    text = "💳 *Planes disponibles (USD)*\n\n" + "\n".join(lines)
    bot.send_message(msg.chat.id, text, reply_markup=plans_keyboard())

@bot.message_handler(func=lambda m: (
    m.chat.type=='private' and m.from_user.id not in ADMINS and m.text in ["💳 Ver planes", "📊 Mi estado", "📞 Contactar administrador"]
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

# ───────── Flujo de compra (texto): plan → método ─────────
@bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id not in ADMINS)
def flow_plan_and_payment_text(msg: Message):
    text = (msg.text or "").strip()

    # Cancelación
    if text.lower() == "cancelar":
        PENDING_PAY.pop(msg.from_user.id, None)
        return bot.send_message(msg.chat.id, "❎ Operación cancelada.", reply_markup=user_menu_kb())

    # Selección de plan
    plan = label_to_plan(text)
    if plan:
        price_usd = float(plan.get('price_usd', 0.0))
        cup_transfer = usd_to_cup_transfer(price_usd)   # 380 por USD
        cup_saldo    = usd_to_cup_saldo(price_usd)      # (380 / 2.5) redondeado ↑ x10
        paypal_gross = compute_paypal_gross(price_usd)  # bruto con fees

        PENDING_PAY[msg.from_user.id] = {
            "plan_key":     plan['key'],
            "plan_label":   plan['label'],
            "price_usd":    price_usd,
            "cup_transfer": cup_transfer,
            "cup_saldo":    cup_saldo,
            "paypal_gross": paypal_gross,
            "method":       None,
        }

        resumen = (
            "🧾 *Has seleccionado:*\n"
            f"{plan['label']}\n\n"
            "💰 *Montos por método de pago*\n"
            f"• {PAYMENT_INFO['saldo']['label']}: *{cup_saldo}* CUP (regla 380÷2.5, redondeo ↑x10)\n"
            f"• {PAYMENT_INFO['cup']['label']}: *{cup_transfer}* CUP (tasa 380)\n"
            f"• {PAYMENT_INFO['paypal']['label']}: *${paypal_gross:.2f}* (incluye comisiones)\n\n"
            "Seleccione ahora el *método de pago*:"
        )
        return bot.send_message(msg.chat.id, resumen, reply_markup=payment_methods_keyboard())

    # Elección de método
    pending = PENDING_PAY.get(msg.from_user.id)
    if pending and text in [
        PAYMENT_INFO['saldo']['label'],
        PAYMENT_INFO['cup']['label'],
        PAYMENT_INFO['paypal']['label']
    ]:
        if text == PAYMENT_INFO['saldo']['label']:
            pending["method"] = "saldo"
            instr = (
                PAYMENT_INFO['saldo']['instruccion']
                + f"\n\n📌 *Monto a pagar (CUP)*: {pending['cup_saldo']} CUP"
                + f"\n👤 Beneficiario (saldo): {PAYMENT_INFO['saldo']['numero']}"
            )
        elif text == PAYMENT_INFO['cup']['label']:
            pending["method"] = "cup"
            instr = (
                PAYMENT_INFO['cup']['instruccion']
                + f"\n\n📌 *Monto a transferir (CUP)*: {pending['cup_transfer']} CUP"
                + f"\n💳 Tarjeta: {PAYMENT_INFO['cup']['tarjeta']}"
                + f"\n🔢 Número a confirmar: {PAYMENT_INFO['cup']['numero_confirmacion']}"
            )
        else:
            pending["method"] = "paypal"
            instr = (
                PAYMENT_INFO['paypal']['instruccion']
                + f"\n\n📌 *Monto exacto (USD)*: ${pending['paypal_gross']:.2f}"
                + f"\n📧 PayPal: {PAYMENT_INFO['paypal']['email']}"
                + f"\n👤 Nombre: {PAYMENT_INFO['paypal']['nombre']}"
            )

        PENDING_PAY[msg.from_user.id] = pending
        instr += "\n\n📷 Envíe ahora la *captura del pago* (foto o archivo) aquí en el chat."
        return bot.send_message(msg.chat.id, instr)

# ───────── Captura: handlers específicos (garantiza reenvío + confirmación) ─────────
@bot.message_handler(content_types=['photo'], func=lambda m: m.chat.type=='private' and m.from_user.id not in ADMINS)
def handle_payment_capture_photo(msg: Message):
    pending = PENDING_PAY.get(msg.from_user.id)
    if not pending:
        return bot.reply_to(
            msg,
            "ℹ️ Aún no has seleccionado un plan y método de pago.\n"
            "Toca *“💳 Ver planes”*, elige un plan y luego un método para enviar la captura.",
            reply_markup=user_menu_kb()
        )

    uid = msg.from_user.id
    user_mention = f"@{msg.from_user.username}" if msg.from_user.username else "(sin @username)"
    contact_link = f"https://t.me/{msg.from_user.username}" if msg.from_user.username else f"tg://user?id={uid}"
    metodo = pending['method'] or "—"

    admin_caption = (
        "📥 *Nuevo pago recibido*\n\n"
        f"👤 Usuario: {user_mention}\n"
        f"🆔 ID: {uid}\n"
        f"🔗 Contacto: {contact_link}\n\n"
        f"📦 Plan: {pending['plan_label']}\n"
        f"💲 Precio USD: ${pending['price_usd']:.2f}\n"
        f"💳 Método: {PAYMENT_INFO.get(metodo, {}).get('label', '—')}\n"
        f"💵 Monto Transferencia (CUP): {pending['cup_transfer']} CUP\n"
        f"📱 Monto Saldo (CUP): {pending['cup_saldo']} CUP\n"
        f"🅿️ Monto PayPal (USD): ${pending['paypal_gross']:.2f}\n"
    )

    file_id = msg.photo[-1].file_id
    for admin_id in ADMINS:
        try:
            bot.send_photo(admin_id, file_id, caption=admin_caption, parse_mode="Markdown")
        except Exception:
            pass

    bot.reply_to(
        msg,
        "✅ Captura recibida. Un administrador verificará tu pago y activará tu plan. ¡Gracias!",
        reply_markup=user_menu_kb()
    )
    PENDING_PAY.pop(uid, None)

@bot.message_handler(content_types=['document'], func=lambda m: m.chat.type=='private' and m.from_user.id not in ADMINS)
def handle_payment_capture_document(msg: Message):
    pending = PENDING_PAY.get(msg.from_user.id)
    if not pending:
        return bot.reply_to(
            msg,
            "ℹ️ Aún no has seleccionado un plan y método de pago.\n"
            "Toca *“💳 Ver planes”*, elige un plan y luego un método para enviar la captura.",
            reply_markup=user_menu_kb()
        )

    uid = msg.from_user.id
    user_mention = f"@{msg.from_user.username}" if msg.from_user.username else "(sin @username)"
    contact_link = f"https://t.me/{msg.from_user.username}" if msg.from_user.username else f"tg://user?id={uid}"
    metodo = pending['method'] or "—"

    admin_caption = (
        "📥 *Nuevo pago recibido*\n\n"
        f"👤 Usuario: {user_mention}\n"
        f"🆔 ID: {uid}\n"
        f"🔗 Contacto: {contact_link}\n\n"
        f"📦 Plan: {pending['plan_label']}\n"
        f"💲 Precio USD: ${pending['price_usd']:.2f}\n"
        f"💳 Método: {PAYMENT_INFO.get(metodo, {}).get('label', '—')}\n"
        f"💵 Monto Transferencia (CUP): {pending['cup_transfer']} CUP\n"
        f"📱 Monto Saldo (CUP): {pending['cup_saldo']} CUP\n"
        f"🅿️ Monto PayPal (USD): ${pending['paypal_gross']:.2f}\n"
    )

    for admin_id in ADMINS:
        try:
            bot.send_document(admin_id, msg.document.file_id, caption=admin_caption, parse_mode="Markdown")
        except Exception:
            pass

    bot.reply_to(
        msg,
        "✅ Captura recibida. Un administrador verificará tu pago y activará tu plan. ¡Gracias!",
        reply_markup=user_menu_kb()
    )
    PENDING_PAY.pop(uid, None)

# ───────── Activación en grupos (modelo A) ─────────
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

# ───────── /admin (panel) ─────────
@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if msg.chat.type != 'private' or not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "⛔ *Acceso denegado.* Use /admin en privado.")
    show_admin_menu(bot, msg.chat.id)

# ───────── Arranque ─────────
def main():
    ensure_files()
    register_admin_handlers(bot)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    main()
