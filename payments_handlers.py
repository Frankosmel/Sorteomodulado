# payments_handlers.py

from telebot import TeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from config import PLANS, PAYMENT_INFO, ADMINS, FILES
from storage import load, save
from datetime import datetime, timedelta
import os

RECEIPTS_FILE = FILES["receipts"]

def register_payment_handlers(bot: TeleBot):
    """
    Manejadores para flujo de contratación de planes:
      - Elección de plan (/start)
      - Elección de método de pago
      - Envío de captura y datos
      - Notificación a admins
      - Almacenamiento de recibo
    """

    # --- Callback de elección de plan ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
    def on_plan_selected(cq):
        user_id = cq.from_user.id
        plan_key = cq.data  # ej. "plan_1m1g"
        # Buscar datos del plan
        plan = next((p for p in PLANS if p["key"] == plan_key), None)
        if not plan:
            return bot.answer_callback_query(cq.id, "Plan no válido.")
        # Guardamos en memoria temporal
        bot.user_data = getattr(bot, 'user_data', {})
        bot.user_data[user_id] = {"plan": plan_key}
        # Mostrar métodos de pago
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton("💳 Pago con Tarjeta", callback_data="pay_tarjeta"),
            InlineKeyboardButton("📱 Pago por SMS/Saldo móvil", callback_data="pay_sms"),
            InlineKeyboardButton("🔙 Cancelar", callback_data="pay_cancel")
        )
        bot.edit_message_text(
            chat_id=user_id,
            message_id=cq.message.message_id,
            text=(
                f"Has seleccionado *{plan['label']}*.\n\n"
                "Elige tu método de pago:"
            ),
            parse_mode='Markdown',
            reply_markup=kb
        )

    # --- Cancelar flujo ---
    @bot.callback_query_handler(func=lambda c: c.data == "pay_cancel")
    def on_pay_cancel(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        bot.send_message(
            uid,
            "❌ Contratación cancelada.",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.user_data.pop(uid, None)

    # --- Método: Tarjeta ---
    @bot.callback_query_handler(func=lambda c: c.data == "pay_tarjeta")
    def on_pay_tarjeta(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        plan_key = bot.user_data.get(uid, {}).get("plan")
        if not plan_key:
            return bot.send_message(uid, "🚫 Error interno, vuelve a /start.")
        info = PAYMENT_INFO
        texto = (
            "💳 *Pago con Tarjeta*\n\n"
            f"Envía exactamente este mensaje como comprobante:\n\n"
            f"• Plan: *{plan_key}*\n"
            f"• Monto: *{next(p['price'] for p in PLANS if p['key']==plan_key)}* CUP\n"
            f"• Tarjeta: `{info['tarjeta']}`\n"
            f"• Número de confirmación SMS que recibas\n\n"
            "Luego adjunta captura de pantalla de la transferencia."
        )
        bot.send_message(uid, texto, parse_mode='Markdown')

        bot.register_next_step_handler(cq.message, process_receipt)

    # --- Método: SMS / Saldo móvil ---
    @bot.callback_query_handler(func=lambda c: c.data == "pay_sms")
    def on_pay_sms(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        plan_key = bot.user_data.get(uid, {}).get("plan")
        if not plan_key:
            return bot.send_message(uid, "🚫 Error interno, vuelve a /start.")
        info = PAYMENT_INFO
        texto = (
            "📱 *Pago por SMS o Saldo móvil*\n\n"
            f"Envía exactamente este mensaje como comprobante:\n\n"
            f"• Plan: *{plan_key}*\n"
            f"• Monto: *{next(p['price'] for p in PLANS if p['key']==plan_key)}* CUP\n"
            f"• Envía un SMS al número `{info['sms_num']}` o paga con saldo móvil\n"
            f"• Luego adjunta captura de pantalla del SMS o del pago\n\n"
            "También puedes enviar datos de tu usuario de Telegram para contacto."
        )
        bot.send_message(uid, texto, parse_mode='Markdown')

        bot.register_next_step_handler(cq.message, process_receipt)

    # --- Recepción de recibo/captura ---
    def process_receipt(msg):
        uid = msg.from_user.id
        data = bot.user_data.get(uid, {})
        plan_key = data.get("plan")
        if not plan_key:
            return bot.reply_to(msg, "⚠️ Sesión expirada, inicia con /start.")
        # Guardar recibo: suponemos que el usuario envió foto o texto
        receipts = load('receipts')
        now = datetime.utcnow().isoformat()
        entry = {
            "user_id": uid,
            "plan": plan_key,
            "received_at": now,
            "text": msg.text or "",
            "has_photo": bool(msg.photo),
            "file_id": msg.photo[-1].file_id if msg.photo else None
        }
        receipts.setdefault(str(uid), []).append(entry)
        save('receipts', receipts)

        # Notificar a super‐admins
        for admin in ADMINS:
            caption = (
                f"📥 *Nuevo Comprobante*\n\n"
                f"• Usuario: `{uid}`\n"
                f"• Plan: *{plan_key}*\n"
                f"• Fecha/Hora: `{now}`\n"
            )
            if msg.photo:
                bot.send_photo(admin, msg.photo[-1].file_id, caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(admin, caption + f"\nMensaje:\n{msg.text}", parse_mode='Markdown')

        bot.send_message(
            uid,
            "✅ ¡Recibo recibido! En breve activaré tu suscripción. Gracias por tu pago.",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.user_data.pop(uid, None)
