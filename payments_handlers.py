# payments_handlers.py

from telebot import TeleBot, types
from storage import load, save
from config import FILES, VIGENCIA_DIAS, VIGENCIA_TRIMESTRAL
from datetime import datetime, timedelta

RECEIPTS_FILE = FILES["receipts"]

def register_payment_handlers(bot: TeleBot):
    """
    Manejadores para flujo de contratación de planes:
      - Selección de plan (callback_query)
      - Recepción de datos de pago y captura
      - Almacenamiento en receipts.json
      - Notificación a super-admins para aprobación
    """
    # Aseguramos que exista receipts.json
    try:
        with open(RECEIPTS_FILE, 'r'):
            pass
    except FileNotFoundError:
        with open(RECEIPTS_FILE, 'w') as f:
            f.write("{}")

    @bot.callback_query_handler(lambda cq: cq.data and cq.data.startswith("plan_"))
    def handle_plan_selection(cq: types.CallbackQuery):
        uid = cq.from_user.id
        data = cq.data  # ej. "plan_1m1g"
        # Mapeo de planes
        planes = {
            "plan_1m1g": {"meses": 1, "grupos": 1, "precio": 500},
            "plan_1m2g": {"meses": 1, "grupos": 2, "precio": 900},   # 10% dto
            "plan_1m3g": {"meses": 1, "grupos": 3, "precio": 1200},  # 20% dto
            "plan_3m3g": {"meses": 3, "grupos": 3, "precio": 1800}   # 25% dto
        }
        plan = planes.get(data)
        if not plan:
            return bot.answer_callback_query(cq.id, "Plan desconocido.")
        # Guardamos solicitud en receipts.json
        receipts = load("receipts")
        rec_id = f"{uid}_{int(datetime.utcnow().timestamp())}"
        receipts[rec_id] = {
            "user_id": uid,
            "plan_key": data,
            "meses": plan["meses"],
            "grupos": plan["grupos"],
            "precio": plan["precio"],
            "status": "pending",
            "requested_at": datetime.utcnow().isoformat(),
            "payment_info": None,
            "screenshot_file_id": None
        }
        save("receipts", receipts)
        # Pedimos datos de pago
        bot.send_message(
            uid,
            f"🔔 Has elegido *{plan['meses']} mes(es), hasta {plan['grupos']} grupo(s)* por *{plan['precio']} CUP*.\n\n"
            "➤ Envía ahora los datos de tu pago:\n"
            "• Tipo de pago: Tarjeta / Saldo Móvil\n"
            "• Número o refererencia de la transferencia\n"
            "• Envíame una captura de pantalla del comprobante",
            parse_mode='Markdown'
        )
        # Guardamos en el objeto de colección next_step
        bot.register_next_step_handler_by_chat_id(uid, collect_payment_info, rec_id)

    def collect_payment_info(msg: types.Message, rec_id: str):
        uid = msg.from_user.id
        receipts = load("receipts")
        receipt = receipts.get(rec_id)
        if not receipt or receipt["user_id"] != uid:
            return bot.reply_to(msg, "⚠️ No se encontró tu solicitud. Vuelve a pulsar el plan.")
        # Si envía foto, la guardamos
        if msg.content_type == "photo":
            file_id = msg.photo[-1].file_id
            receipt["screenshot_file_id"] = file_id
            save("receipts", receipts)
            # Continuamos pidiendo confirmación
            bot.send_message(
                uid,
                "✅ Captura recibida.\n"
                "✏️ Ahora envía un mensaje con el método de pago y número de referencia.\n"
                "_Ejemplo:_ `Tarjeta 9204 1299 7691 8161 — Ref: 56246700`",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, finalize_payment_info, rec_id)
        else:
            # Interpretamos texto como info
            receipt["payment_info"] = msg.text.strip()
            save("receipts", receipts)
            if not receipt.get("screenshot_file_id"):
                # Solicitamos captura si no llegó
                bot.send_message(
                    uid,
                    "⚠️ Por favor, envía también la captura del pago.",
                    parse_mode='Markdown'
                )
                bot.register_next_step_handler(msg, collect_payment_info, rec_id)
            else:
                return finalize_payment_info(msg, rec_id)

    def finalize_payment_info(msg: types.Message, rec_id: str):
        uid = msg.from_user.id
        receipts = load("receipts")
        receipt = receipts.get(rec_id)
        if not receipt:
            return
        # Comprobamos que tenemos ambos info y screenshot
        if not receipt.get("payment_info") or not receipt.get("screenshot_file_id"):
            return bot.send_message(uid, "⚠️ Falta información o captura. Por favor envía todo.")
        # Marcamos como awaiting_approval
        receipt["status"] = "awaiting_approval"
        receipt["submitted_at"] = datetime.utcnow().isoformat()
        save("receipts", receipts)
        # Notificamos al usuario
        bot.send_message(
            uid,
            "📬 Tu comprobante ha sido enviado y está pendiente de aprobación.\n"
            "Te avisaré cuando esté activo.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        # Reenviamos a cada admin
        for admin_id in bot.config.ADMINS:
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{rec_id}"),
                types.InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{rec_id}")
            )
            bot.send_photo(
                admin_id,
                photo=receipt["screenshot_file_id"],
                caption=(
                    f"🆔 *Solicitud*: `{rec_id}`\n"
                    f"👤 Usuario: `{uid}`\n"
                    f"📦 Plan: {receipt['meses']}m, {receipt['grupos']}g — {receipt['precio']} CUP\n"
                    f"✏️ Pago: {receipt['payment_info']}\n"
                    f"⏳ Estado: *Pendiente*"
                ),
                parse_mode='Markdown',
                reply_markup=kb
            )

    @bot.callback_query_handler(lambda cq: cq.data and cq.data.startswith(("approve_", "reject_")))
    def handle_approval(cq: types.CallbackQuery):
        data = cq.data  # e.g. "approve_uid_timestamp"
        action, rec_id = data.split("_", 1)
        receipts = load("receipts")
        receipt = receipts.get(rec_id)
        if not receipt:
            return bot.answer_callback_query(cq.id, "Solicitud no encontrada.")
        if action == "approve":
            # Calculamos fecha de expiración
            meses = receipt["meses"]
            if meses == 3:
                delta = timedelta(days=VIGENCIA_TRIMESTRAL)
            else:
                delta = timedelta(days=VIGENCIA_DIAS * meses)
            expira = datetime.utcnow() + delta
            # Agregamos a autorizados
            from auth import add_authorized
            add_authorized(receipt["user_id"], None, vence=expira.isoformat())
            receipt["status"] = "approved"
            receipt["approved_at"] = datetime.utcnow().isoformat()
            save("receipts", receipts)
            # Avisamos al usuario
            bot.send_message(
                receipt["user_id"],
                f"✅ Tu suscripción ha sido *aprobada*.\n"
                f"Válida hasta: `{expira.date()}`.",
                parse_mode='Markdown'
            )
            bot.answer_callback_query(cq.id, "✅ Aprobado")
        else:
            # Rechazo
            receipt["status"] = "rejected"
            receipt["rejected_at"] = datetime.utcnow().isoformat()
            save("receipts", receipts)
            bot.send_message(
                receipt["user_id"],
                "❌ Lo siento, tu comprobante ha sido *rechazado*.\n"
                "Puedes intentar enviar uno nuevo.",
                parse_mode='Markdown'
            )
            bot.answer_callback_query(cq.id, "❌ Rechazado")
