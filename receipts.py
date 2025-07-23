# receipts.py

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from storage import load, save
from config import FILES
from datetime import datetime

# Archivo donde guardaremos los recibos
RECEIPTS_FILE = FILES["receipts"]

# Chat de admins donde reenviamos cada recibo
ADMIN_GROUP_ID = -1002605404513

# Definición de planes y sus precios
PLAN_DETAILS = {
    "plan_1m1g": { "name": "1 mes — 1 grupo", "price": "300 CUP" },
    "plan_1m2g": { "name": "1 mes — 2 grupos", "price": "550 CUP" },
    "plan_1m3g": { "name": "1 mes — 3 grupos", "price": "700 CUP" },
    "plan_3m3g": { "name": "3 meses — 3 grupos", "price": "1 800 CUP" }
}

def register_payment_handlers(bot: TeleBot):
    """
    Registra:
      1) Callback para cuando el usuario elige un plan.
      2) Next‐step handler para procesar la captura del recibo.
    """

    @bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
    def handle_plan_selection(call):
        user_id = call.from_user.id
        plan_key = call.data
        details = PLAN_DETAILS.get(plan_key)

        # Validación
        if not details:
            bot.answer_callback_query(call.id, "❌ Plan no reconocido.")
            return

        bot.answer_callback_query(call.id)  # elimina el círculo de carga

        # Mensaje con instrucciones de pago
        msg = bot.send_message(
            user_id,
            f"🌟 *Has seleccionado:* {details['name']} — {details['price']}\n\n"
            "Para completar tu suscripción, realiza el pago usando uno de estos métodos:\n\n"
            "• 💳 *Tarjeta:* `9204 1299 7691 8161`\n"
            "• 📱 *Saldo móvil* (50% descuento): envía al `56246700`\n\n"
            "✏️ Ahora envía la *captura de pantalla* del pago (foto) y tu *@usuario* de Telegram.",
            parse_mode='Markdown'
        )

        # Registramos el next step para procesar la captura
        bot.register_next_step_handler(msg, process_receipt, plan_key)

    def process_receipt(msg: Message, plan_key: str):
        """
        Al llegar la captura (foto o texto), guardamos el recibo
        y lo reenviamos al grupo de admins para activación manual.
        """
        user_id = msg.from_user.id
        timestamp = datetime.utcnow().isoformat()
        receipts = load('receipts')

        # Construimos el registro
        rec = {
            "plan_key":      plan_key,
            "plan_name":     PLAN_DETAILS[plan_key]["name"],
            "plan_price":    PLAN_DETAILS[plan_key]["price"],
            "timestamp":     timestamp,
            "telegram_user": msg.from_user.username or msg.from_user.first_name,
            "user_id":       user_id,
            "notes":         None,
            "photo_file_id": None
        }

        # Si es foto, guardamos file_id; si es texto, lo ponemos en notes
        if msg.content_type == 'photo':
            rec["photo_file_id"] = msg.photo[-1].file_id
        else:
            rec["notes"] = msg.text

        # Añadimos al JSON bajo su user_id
        receipts.setdefault(str(user_id), []).append(rec)
        save('receipts', receipts)

        # Preparamos el mensaje para los admins
        caption = (
            f"📥 *Nuevo pago recibido*\n\n"
            f"• Usuario: @{rec['telegram_user']} (`{user_id}`)\n"
            f"• Plan: {rec['plan_name']} — {rec['plan_price']}\n"
            f"• Fecha: {timestamp}\n"
        )

        # Reenviamos al grupo de admins
        if rec["photo_file_id"]:
            bot.send_photo(
                ADMIN_GROUP_ID,
                rec["photo_file_id"],
                caption=caption,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                ADMIN_GROUP_ID,
                caption + f"\n📝 *Notas:* {rec['notes']}",
                parse_mode='Markdown'
            )

        # Confirmación al usuario
        bot.send_message(
            user_id,
            "✅ *Recibo recibido.*\n"
            "En breve un administrador validará tu pago y activará tu suscripción.",
            parse_mode='Markdown'
        )
