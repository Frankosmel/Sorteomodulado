# payments_handlers.py

from telebot import TeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from config import FILES
from storage import load, save
from datetime import datetime

RECEIPTS_FILE = FILES["receipts"]

def register_payment_handlers(bot: TeleBot):
    """
    Maneja la lógica de selección de plan, 
    captura de pago y notificación a admins.
    """

    # 1) CallbackQuery que llega al pulsar uno de los botones de plan
    @bot.callback_query_handler(lambda cq: cq.data.startswith("plan_"))
    def handle_plan_selection(cq):
        plan = cq.data  # e.g. 'plan_1m1g', 'plan_3m3g', etc.
        user_id = cq.from_user.id

        # Mensaje explicativo con datos de pago y solicitud de captura
        text = (
            f"📦 *Has elegido el paquete* `{plan}`\n\n"
            "🔸 *Métodos de pago disponibles:*\n"
            "  • Tarjeta: `9204 1299 7691 8161` (tu banco te enviará SMS con un código)\n"
            "  • Saldo móvil (50% recargo): envía al 56246700\n\n"
            "✏️ *Ahora*, por favor envíame una captura de pantalla\n"
            "   del comprobante de la transferencia o pago.\n\n"
            "⚠️ Incluye en el mensaje:\n"
            "   • Tu @usuario de Telegram\n"
            "   • Fecha y hora de la operación\n"
            "   • Código SMS o referencia bancaria\n\n"
            "_Cuando lo reciba, se lo reenviaré a los super-admins para verificar_"
        )
        bot.send_message(
            user_id,
            text,
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

        # Guardo en receipts.json un registro preliminar
        receipts = load("receipts")
        receipts[str(user_id)] = {
            "plan": plan,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"  # pendiente de verificación
        }
        save("receipts", receipts)


    # 2) Cuando el usuario envíe cualquier documento o foto, lo tomamos
    @bot.message_handler(content_types=['photo', 'document'])
    def handle_payment_proof(msg):
        uid = msg.from_user.id
        receipts = load("receipts")
        rec = receipts.get(str(uid))

        if not rec or rec.get("status") != "pending":
            # No hay plan seleccionado o ya procesado
            return bot.reply_to(
                msg,
                "❌ No detecté ningún plan pendiente. "
                "Primero selecciona un paquete con /start.",
                parse_mode='Markdown'
            )

        # Guardamos el file_id de la foto/documento
        file_id = None
        if msg.photo:
            file_id = msg.photo[-1].file_id
        else:
            file_id = msg.document.file_id

        rec["proof_file_id"] = file_id
        rec["received_at"] = datetime.utcnow().isoformat()
        rec["status"] = "awaiting_approval"
        save("receipts", receipts)

        bot.reply_to(
            msg,
            "✅ Captura recibida. En breve un super-admin la validará.",
            parse_mode='Markdown'
        )

        # Reenvío al canal/admins
        admin_text = (
            f"📥 *Nuevo comprobante de pago*\n\n"
            f"• Usuario: `{uid}`\n"
            f"• Plan: `{rec['plan']}`\n"
            f"• Fecha pago: {rec['received_at']}\n\n"
            "_Pulsa el botón para Aprobar o Rechazar_"
        )
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{uid}"),
            InlineKeyboardButton("⛔ Rechazar", callback_data=f"reject_{uid}")
        )
        # reemplaza -100XXXXX por tu chat de admins
        ADMIN_GROUP = -1002605404513
        bot.send_message(
            ADMIN_GROUP,
            admin_text,
            parse_mode='Markdown',
            reply_markup=kb
        )

    # 3) Super-admin aprueba o rechaza
    @bot.callback_query_handler(lambda cq: cq.data.startswith(("approve_","reject_")))
    def handle_admin_approval(cq):
        action, uid_str = cq.data.split("_", 1)
        uid = int(uid_str)
        receipts = load("receipts")
        rec = receipts.get(uid_str)

        if not rec:
            return cq.answer("❌ Registro no encontrado.", show_alert=True)

        if action == "approve":
            # marcar autorizado
            from auth import add_authorized
            username = cq.from_user.username or ""
            add_authorized(uid, f"@{username}")
            rec["status"] = "approved"
            # calcular vencimiento
            exp_date = (datetime.utcnow() + timedelta(days=VIGENCIA_DIAS)).date().isoformat()
            rec["expires_at"] = exp_date
            bot.send_message(
                uid,
                f"🎉 *Pago verificado!* Tu plan `{rec['plan']}` "
                f"estará activo hasta el *{exp_date}*.",
                parse_mode='Markdown'
            )
            cq.answer("Usuario autorizado y plan activado.", show_alert=False)

        else:  # reject
            rec["status"] = "rejected"
            bot.send_message(
                uid,
                "❌ Lo siento, tu comprobante no fue válido. "
                "Por favor intenta de nuevo o contacta soporte.",
                parse_mode='Markdown'
            )
            cq.answer("Pago rechazado.", show_alert=False)

        save("receipts", receipts)
