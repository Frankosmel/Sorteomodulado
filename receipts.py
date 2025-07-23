# receipts.py

from telebot import TeleBot
from telebot.types import Message
from storage import load, save
from config import FILES, PLANS
from datetime import datetime

# Archivo donde guardaremos los recibos
RECEIPTS_FILE = FILES["receipts"]

# Chat de admins donde reenviamos cada recibo
ADMIN_GROUP_ID = -1002605404513

def register_payment_handlers(bot: TeleBot):
    """
    Next‐step handler para procesar la captura del recibo tras las instrucciones de pago.
    """

    @bot.message_handler(content_types=['photo', 'text'])
    def process_receipt(msg: Message):
        user_id = msg.from_user.id
        # Recuperamos plan pendientement almacenado
        data = getattr(bot, 'user_data', {}).get(user_id, {})
        plan_key = data.get("plan")
        if not plan_key:
            # No hay plan pendiente → salimos
            return

        timestamp = datetime.utcnow().isoformat()

        # Cargamos recibos previos
        receipts = load('receipts')

        # Buscamos datos del plan en PLANS
        plan = next((p for p in PLANS if p["key"] == plan_key), None)
        plan_label = plan['label'] if plan else plan_key
        plan_price = f"{plan['price']} CUP" if plan else ""

        # Construimos el registro
        rec = {
            "plan_key":      plan_key,
            "plan_label":    plan_label,
            "plan_price":    plan_price,
            "timestamp":     timestamp,
            "telegram_user": msg.from_user.username or msg.from_user.first_name,
            "user_id":       user_id,
            "notes":         None,
            "photo_file_id": None
        }

        if msg.content_type == 'photo':
            rec["photo_file_id"] = msg.photo[-1].file_id
        else:
            rec["notes"] = msg.text

        receipts.setdefault(str(user_id), []).append(rec)
        save('receipts', receipts)

        # Notificamos a admins
        caption = (
            f"📥 *Nuevo pago recibido*\n\n"
            f"• Usuario: @{rec['telegram_user']} (`{user_id}`)\n"
            f"• Plan: {rec['plan_label']} — {rec['plan_price']}\n"
            f"• Fecha: `{timestamp}`\n"
        )
        if rec["photo_file_id"]:
            bot.send_photo(
                ADMIN_GROUP_ID,
                rec["photo_file_id"],
                caption=caption,
                parse_mode='Markdown'
            )
        else:
            extra = f"\n📝 *Notas:* {rec['notes']}" if rec['notes'] else ""
            bot.send_message(
                ADMIN_GROUP_ID,
                caption + extra,
                parse_mode='Markdown'
            )

        # Confirmación al usuario
        bot.send_message(
            user_id,
            "✅ *Recibo recibido.*\n"
            "En breve un administrador validará tu pago y activará tu suscripción.",
            parse_mode='Markdown'
        )

        # Limpiamos la sesión temporal
        bot.user_data.pop(user_id, None)
