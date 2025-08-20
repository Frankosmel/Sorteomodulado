# main.py
# ──────────────────────────────────────────────────────────────────────────────
# FLUJO DEL BOT (CLIENTE)
# - Menú: Ver planes / Mi estado / Contactar administrador
# - Compra: seleccionar plan → seleccionar método → enviar captura
# - Cálculos:
#   * Saldo móvil: (USD * 380) / 2.5, redondeado hacia arriba al múltiplo de 10
#   * Transferencia CUP: USD * 380
#   * PayPal: bruto para cubrir fees (pct + fijo)
# - Reenvío a Admin: captura + datos copiable (usuario, ID, enlace, plan, montos)
#
# ACTIVACIÓN EN GRUPOS (MODELO A)
# - Solo un usuario autorizado puede activar el bot en un grupo
# - Si no está autorizado o excede cupo, el bot se retira
#
# INTEGRACIÓN ADMIN
# - /admin se maneja en admin_handlers.py (ya existente)
# ──────────────────────────────────────────────────────────────────────────────

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

# Instancia principal del bot
bot = TeleBot(TOKEN, parse_mode="Markdown")

# ──────────────────────────────────────────────────────────────────────────────
# UTILIDADES: TECLADOS Y CÁLCULOS DE MONTOS
# ──────────────────────────────────────────────────────────────────────────────

def user_menu_kb():
    """
    Teclado de usuario (privado) para acceso rápido a opciones.
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("💳 Ver planes"), KeyboardButton("📊 Mi estado"))
    kb.row(KeyboardButton("📞 Contactar administrador"))
    return kb

def plans_keyboard():
    """
    Teclado de selección de planes (usa 'label' de cada plan).
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for p in PLANS:
        kb.row(p['label'])
    kb.row("Cancelar")
    return kb

def payment_methods_keyboard():
    """
    Teclado para elegir el método de pago.
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(PAYMENT_INFO['saldo']['label'])
    kb.row(PAYMENT_INFO['cup']['label'])
    kb.row(PAYMENT_INFO['paypal']['label'])
    kb.row("Cancelar")
    return kb

def label_to_plan(label: str):
    """
    Dado un label (texto visible), encuentra el plan correspondiente.
    """
    for p in PLANS:
        if p['label'] == label:
            return p
    return None

def compute_paypal_gross(price_usd: float) -> float:
    """
    Calcula el monto BRUTO que el cliente debe enviar por PayPal para que el NETO
    recibido sea 'price_usd', considerando PAYPAL_FEE_PCT y PAYPAL_FEE_FIXED.
    Formula: bruto = (price_usd + fijo) / (1 - pct)
    """
    bruto = (price_usd + PAYPAL_FEE_FIXED) / (1.0 - PAYPAL_FEE_PCT)
    return round(bruto, 2)

def usd_to_cup_transfer(amount_usd: float) -> int:
    """
    Convierte USD a CUP para Transferencia CUP, usando la tasa fija 380.
    Ejemplo: $1 → 380 CUP
    """
    return int(round(amount_usd * USD_TO_CUP_TRANSFER))

def usd_to_cup_saldo(amount_usd: float) -> int:
    """
    Convierte USD a CUP para pago por SALDO MÓVIL:
      1) base = (USD * 380) / 2.5
      2) redondear HACIA ARRIBA al múltiplo de 10 más cercano
         (ej.: 152 → 160, 346 → 350)
    """
    base = (amount_usd * USD_TO_CUP_TRANSFER) / SALDO_DIVISOR
    ajustado = math.ceil(base / ROUND_TO) * ROUND_TO
    return int(ajustado)

# Estado de flujo de pago por usuario (en memoria)
# Cada entrada: { plan_key, plan_label, price_usd, cup_transfer, cup_saldo, paypal_gross, method }
PENDING_PAY: dict[int, dict] = {}

# ──────────────────────────────────────────────────────────────────────────────
# MENÚ DEL CLIENTE
# ──────────────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    """
    Saludo y menú principal. Si el usuario está autorizado, muestra su estado.
    """
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
    """
    Estado de la suscripción del usuario.
    """
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
    """
    Muestra los planes disponibles como lista y despliega teclado para seleccionar.
    """
    if msg.chat.type != 'private':
        return

    lines = [p['label'] for p in PLANS]
    text = "💳 *Planes disponibles (USD)*\n\n" + "\n".join(lines)
    bot.send_message(msg.chat.id, text, reply_markup=plans_keyboard())

@bot.message_handler(func=lambda m: m.chat.type=='private' and m.text in ["💳 Ver planes", "📊 Mi estado", "📞 Contactar administrador"])
def handle_user_buttons(msg: Message):
    """
    Botones rápidos del teclado del cliente.
    """
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
# FLUJO DE COMPRA: SELECCIONAR PLAN → MÉTODO → CAPTURA
# ──────────────────────────────────────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.chat.type=='private')
def flow_plan_and_payment(msg: Message):
    """
    Controlador general del flujo de compra en privado.
    - Si escribe 'Cancelar' en cualquier punto, aborta el flujo.
    - Si selecciona un PLAN (coincide con label), pasamos a métodos de pago
      mostrando montos para cada método.
    - Si selecciona un MÉTODO, mostramos instrucciones específicas y pedimos captura.
    - Si envía una FOTO/DOCUMENTO con la captura, se reenvía a los admins con datos.
    """
    text = (msg.text or "").strip()

    # Cancelación global del flujo
    if text.lower() == "cancelar":
        PENDING_PAY.pop(msg.from_user.id, None)
        return bot.send_message(msg.chat.id, "❎ Operación cancelada.", reply_markup=user_menu_kb())

    # ¿Seleccionó un plan? (coincide con algún label)
    plan = label_to_plan(text)
    if plan:
        price_usd = float(plan.get('price_usd', 0.0))
        # Calculamos montos según el método:
        cup_transfer = usd_to_cup_transfer(price_usd)   # 380 por USD
        cup_saldo    = usd_to_cup_saldo(price_usd)      # (380 / 2.5), redondeo ↑ múltiplo de 10
        paypal_gross = compute_paypal_gross(price_usd)  # bruto con fees

        # Guardamos estado para el usuario
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

    # ¿Está en flujo y acaba de elegir método de pago?
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
        elif text == PAYMENT_INFO['paypal']['label']:
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

    # ¿Envió la captura (foto/documento)?
    if pending and (msg.photo or msg.document):
        uid = msg.from_user.id
        info = pending
        user_mention = f"@{msg.from_user.username}" if msg.from_user.username else "(sin @username)"
        contact_link = f"https://t.me/{msg.from_user.username}" if msg.from_user.username else f"tg://user?id={uid}"
        metodo = info['method']

        # Redactamos un resumen COPIABLE para los admins
        admin_caption = (
            "📥 *Nuevo pago recibido*\n\n"
            f"👤 Usuario: {user_mention}\n"
            f"🆔 ID: {uid}\n"
            f"🔗 Contacto: {contact_link}\n\n"
            f"📦 Plan: {info['plan_label']}\n"
            f"💲 Precio USD: ${info['price_usd']:.2f}\n"
            f"💳 Método: {PAYMENT_INFO[metodo]['label']}\n"
            f"💵 Monto Transferencia (CUP): {info['cup_transfer']} CUP\n"
            f"📱 Monto Saldo (CUP): {info['cup_saldo']} CUP\n"
            f"🅿️ Monto PayPal (USD): ${info['paypal_gross']:.2f}\n"
        )

        # Reenvío de la captura a todos los admins
        for admin_id in ADMINS:
            try:
                if msg.photo:
                    file_id = msg.photo[-1].file_id
                    bot.send_photo(admin_id, file_id, caption=admin_caption, parse_mode="Markdown")
                else:
                    bot.send_document(admin_id, msg.document.file_id, caption=admin_caption, parse_mode="Markdown")
            except Exception:
                pass

        bot.reply_to(
            msg,
            "✅ Captura recibida. Un administrador verificará tu pago y activará tu plan pronto. ¡Gracias!",
            reply_markup=user_menu_kb()
        )
        # Limpiamos el estado del usuario
        PENDING_PAY.pop(uid, None)
        return

# ──────────────────────────────────────────────────────────────────────────────
# ACTIVACIÓN EN GRUPOS (MODELO A)
# - Solo quienes están autorizados pueden activar el bot en grupos
# - Si el actor no está autorizado o excede cupo, salimos del grupo
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
# PANEL ADMIN (REUTILIZA TU admin_handlers.py)
# ──────────────────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
        return bot.reply_to(msg, "⛔ *Acceso denegado.* Use /admin en privado.")
    show_admin_menu(bot, msg.chat.id)

# ──────────────────────────────────────────────────────────────────────────────
# ARRANQUE
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ensure_files()
    register_admin_handlers(bot)   # registra todos los handlers de administración
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    main()
