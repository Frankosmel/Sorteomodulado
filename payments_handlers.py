# payments_handlers.py

from telebot import TeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    Message
)
from config import PLANS, PAYMENT_INFO, ADMINS, FILES
from storage import load, save
from datetime import datetime, timezone

# Archivo donde guardaremos los recibos
RECEIPTS_FILE = FILES["receipts"]

# ID del grupo o canal de admins donde reenviar pagos
ADMIN_GROUP_ID = -1002605404513

def register_payment_handlers(bot: TeleBot):
    """
    Flujo completo de contratación de planes:
      1) El usuario selecciona un plan (callback "plan_<key>")
      2) Se muestran los métodos de pago ajustados con emojis e instrucciones
      3) El usuario envía la captura + su @usuario
      4) Se guarda el recibo y se notifica a cada super‐admin y al grupo de admins
    """

    # 1) Usuario selecciona un plan
    @bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
    def on_plan_selected(cq):
        user_id = cq.from_user.id
        plan_key = cq.data  # ej. "plan_1m1g"
        plan = next((p for p in PLANS if p["key"] == plan_key), None)
        if not plan:
            return bot.answer_callback_query(cq.id, "❌ Plan inválido.")

        # Guardamos plan en memoria temporal
        bot.user_data = getattr(bot, 'user_data', {})
        bot.user_data[user_id] = {"plan": plan_key}

        # Teclado con métodos de pago
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton("💳 Pago con Tarjeta", callback_data="pay_tarjeta"),
            InlineKeyboardButton("📱 Pago por SMS/Saldo móvil", callback_data="pay_sms"),
            InlineKeyboardButton("🔙 Cancelar", callback_data="pay_cancel")
        )

        # Editamos el mensaje del menú de planes
        bot.edit_message_text(
            chat_id=user_id,
            message_id=cq.message.message_id,
            text=(
                f"🌟 *Has seleccionado:* {plan['label']}\n\n"
                f"💰 *Monto a enviar:* `{plan['price']} CUP`\n\n"
                "Elige tu método de pago:"
            ),
            parse_mode='Markdown',
            reply_markup=kb
        )
        bot.answer_callback_query(cq.id)


    # 2) Cancelar contratación
    @bot.callback_query_handler(func=lambda c: c.data == "pay_cancel")
    def on_pay_cancel(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        bot.send_message(
            uid,
            "❌ *Contratación cancelada.*\n\n"
            "Si cambias de opinión, vuelve a /start para escoger plan.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        bot.user_data.pop(uid, None)


    # 3) Pago con tarjeta
    @bot.callback_query_handler(func=lambda c: c.data == "pay_tarjeta")
    def on_pay_tarjeta(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        data = bot.user_data.get(uid, {})
        plan_key = data.get("plan")
        if not plan_key:
            return bot.send_message(
                uid,
                "🚫 *Error interno.* Por favor vuelve a /start.",
                parse_mode='Markdown'
            )

        plan = next(p for p in PLANS if p["key"] == plan_key)
        info = PAYMENT_INFO

        texto = (
            "💳 *Pago con Tarjeta*\n\n"
            f"• *Plan:* {plan['label']}\n"
            f"• *Monto:* `{plan['price']} CUP`\n"
            f"• *Tarjeta:* `{info['tarjeta']}`\n"
            "• Envía el número de confirmación que recibas por SMS al número anterior.\n\n"
            "✏️ Ahora, por favor, *adjunta la captura* de la transferencia y tu *@usuario*."
        )
        msg = bot.send_message(uid, texto, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_receipt)


    # 4) Pago por SMS / Saldo móvil
    @bot.callback_query_handler(func=lambda c: c.data == "pay_sms")
    def on_pay_sms(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        data = bot.user_data.get(uid, {})
        plan_key = data.get("plan")
        if not plan_key:
            return bot.send_message(
                uid,
                "🚫 *Error interno.* Por favor vuelve a /start.",
                parse_mode='Markdown'
            )

        plan = next(p for p in PLANS if p["key"] == plan_key)
        info = PAYMENT_INFO

        texto = (
            "📱 *Pago por SMS o Saldo Móvil*\n\n"
            f"• *Plan:* {plan['label']}\n"
            f"• *Monto:* `{plan['price']} CUP`\n"
            f"• *Envía tu pago al número:* `{info['saldo_movil']}`\n"
            "• Recibirás un SMS con un código de confirmación.\n\n"
            "✏️ Ahora, por favor, *adjunta la captura* del SMS o comprobante y tu *@usuario*."
        )
        msg = bot.send_message(uid, texto, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_receipt)


    # 5) Procesar recibo (foto o texto)
    def process_receipt(msg: Message):
        uid = msg.from_user.id
        data = bot.user_data.get(uid, {})
        plan_key = data.get("plan")
        if not plan_key:
            return bot.reply_to(
                msg,
                "⚠️ *Sesión expirada.* Inicia de nuevo con /start.",
                parse_mode='Markdown'
            )

        # Cargamos y guardamos el recibo
        receipts = load('receipts')
        now = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        entry = {
            "user_id":     uid,
            "plan_key":    plan_key,
            "plan_label":  next(p['label'] for p in PLANS if p['key']==plan_key),
            "plan_price":  f"{next(p['price'] for p in PLANS if p['key']==plan_key)} CUP",
            "received_at": now,
            "has_photo":   bool(msg.photo),
            "file_id":     msg.photo[-1].file_id if msg.photo else None,
            "notes":       msg.text or ""
        }
        receipts.setdefault(str(uid), []).append(entry)
        save('receipts', receipts)

        # Preparar notificación
        caption = (
            f"📥 *Nuevo Pago Recibido*\n\n"
            f"• Usuario: @{msg.from_user.username or msg.from_user.first_name} (`{uid}`)\n"
            f"• Plan: {entry['plan_label']} — {entry['plan_price']}\n"
            f"• Fecha: `{now}`\n"
        )

        # Enviar a cada super-admin
        for admin in ADMINS:
            if entry["has_photo"]:
                bot.send_photo(admin, entry["file_id"], caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(admin, caption + (f"\n📝 Notas: {entry['notes']}" if entry['notes'] else ""), parse_mode='Markdown')

        # Enviar al grupo de admins
        if ADMIN_GROUP_ID:
            if entry["has_photo"]:
                bot.send_photo(ADMIN_GROUP_ID, entry["file_id"], caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(ADMIN_GROUP_ID, caption + (f"\n📝 Notas: {entry['notes']}" if entry['notes'] else ""), parse_mode='Markdown')

        # Confirmación al usuario
        bot.send_message(
            uid,
            "✅ *Recibo recibido.*\n"
            "En breve un administrador validará tu pago y activará tu suscripción.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        bot.user_data.pop(uid, None)
