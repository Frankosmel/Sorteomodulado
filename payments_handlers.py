from telebot import TeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    Message
)
from config import PLANS, PAYMENT_INFO, ADMINS, FILES
from storage import load, save
from datetime import datetime

RECEIPTS_FILE = FILES["receipts"]
ADMIN_GROUP_ID = -1002605404513

def register_payment_handlers(bot: TeleBot):
    bot.user_data = {}

    @bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
    def on_plan_selected(cq):
        user_id = cq.from_user.id
        plan_key = cq.data
        plan = next((p for p in PLANS if p["key"] == plan_key), None)
        if not plan:
            return bot.answer_callback_query(cq.id, "❌ Plan inválido.")

        bot.user_data[user_id] = {"plan": plan_key}

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
                f"🌟 *Has seleccionado:* {plan['label']}\n\n"
                f"💰 *Precio:* {plan['price']} CUP\n\n"
                "Elige tu método de pago:"
            ),
            parse_mode='Markdown',
            reply_markup=kb
        )
        bot.answer_callback_query(cq.id)

    @bot.callback_query_handler(func=lambda c: c.data == "pay_cancel")
    def on_pay_cancel(cq):
        uid = cq.from_user.id
        bot.answer_callback_query(cq.id)
        bot.send_message(
            uid,
            "❌ *Contratación cancelada.*",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        bot.user_data.pop(uid, None)

    @bot.callback_query_handler(func=lambda c: c.data in ("pay_tarjeta", "pay_sms"))
    def on_payment_method(cq):
        uid = cq.from_user.id
        method = cq.data
        bot.answer_callback_query(cq.id)
        data = bot.user_data.get(uid, {})
        plan_key = data.get("plan")
        if not plan_key:
            return bot.send_message(uid, "🚫 *Error interno.* Vuelve a /start.", parse_mode='Markdown')

        plan = next(p for p in PLANS if p['key'] == plan_key)
        info = PAYMENT_INFO

        if method == "pay_tarjeta":
            texto = (
                "💳 *Pago con Tarjeta*\n\n"
                f"• *Plan:* {plan['label']}\n"
                f"• *Monto:* {plan['price']} CUP\n"
                f"• Tarjeta:* `{info['tarjeta']}`\n"
                f"• Número de confirmación al `{info['sms_num']}`\n\n"
                "✏️ *Adjunta la captura* de la transferencia y tu `@usuario`."
            )
        else:
            texto = (
                "📱 *Pago por SMS / Saldo Móvil*\n\n"
                f"• *Plan:* {plan['label']}\n"
                f"• *Monto:* {plan['price']} CUP\n"
                f"• Número:* `{info['sms_num']}`\n\n"
                "✏️ *Adjunta la captura* del SMS o comprobante y tu `@usuario`."
            )

        sent = bot.send_message(uid, texto, parse_mode='Markdown')
        bot.register_next_step_handler(sent, process_receipt)

    def process_receipt(msg: Message):
        uid = msg.from_user.id
        data = bot.user_data.get(uid, {})
        plan_key = data.get("plan")
        if not plan_key:
            return bot.reply_to(msg, "⚠️ *Sesión expirada.* Usa /start nuevamente.", parse_mode='Markdown')

        receipts = load('receipts')
        now = datetime.utcnow().isoformat()
        entry = {
            "user_id": uid,
            "plan_key": plan_key,
            "plan_label": next(p['label'] for p in PLANS if p['key'] == plan_key),
            "received_at": now,
            "notes": msg.text or "",
            "has_photo": bool(msg.photo),
            "file_id": msg.photo[-1].file_id if msg.photo else None
        }
        receipts.setdefault(str(uid), []).append(entry)
        save('receipts', receipts)

        username = msg.from_user.username or msg.from_user.first_name
        caption = (
            f"📥 *Nuevo Comprobante:*\n\n"
            f"• Usuario: `@{username}` (`{uid}`)\n"
            f"• Plan: {entry['plan_label']}\n"
            f"• Fecha: `{now}`\n"
        )

        for admin in ADMINS:
            if entry["has_photo"]:
                bot.send_photo(admin, entry["file_id"], caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(admin, caption + (f"\n📝 Notas: {entry['notes']}" if entry['notes'] else ""), parse_mode='Markdown')

        if ADMIN_GROUP_ID:
            if entry["has_photo"]:
                bot.send_photo(ADMIN_GROUP_ID, entry["file_id"], caption=caption, parse_mode='Markdown')
            else:
                bot.send_message(ADMIN_GROUP_ID, caption + (f"\n📝 Notas: {entry['notes']}" if entry['notes'] else ""), parse_mode='Markdown')

        # Marcar usuario como autorizado provisionalmente
        autorizados = load("autorizados")
        usuarios = set(autorizados.get("users", []))
        usuarios.add(uid)
        autorizados["users"] = list(usuarios)
        save("autorizados", autorizados)

        texto = (
            "✅ *Recibo recibido.*\n"
            "Ahora para completar la activación, por favor:\n\n"
            "📩 *Reenvía cualquier mensaje* desde el grupo donde deseas usar el bot.\n"
            "Esto me permitirá obtener correctamente el ID del grupo.\n\n"
            "🔐 Asegúrate de ser administrador del grupo."
        )
        bot.send_message(uid, texto, parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_group_id)

    def process_group_id(msg: Message):
        uid = msg.from_user.id
        if not msg.forward_from_chat or msg.forward_from_chat.type != "supergroup":
            return bot.send_message(uid, "🚫 Debes reenviar un *mensaje* desde el grupo donde deseas activar el bot.", parse_mode='Markdown')

        group_id = msg.forward_from_chat.id
        grupos_aut = load("grupos_autorizados")
        grupos = set(grupos_aut.get("grupos", []))
        grupos.add(group_id)
        grupos_aut["grupos"] = list(grupos)
        save("grupos_autorizados", grupos_aut)

        bot.send_message(uid, f"🎉 ¡Perfecto! El grupo ha sido autorizado correctamente.\n\nPuedes usar el bot ahí con total funcionalidad.", parse_mode='Markdown')
