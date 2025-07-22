# payments_handlers.py

from telebot import TeleBot
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, Message
)
from storage import load, save
from config import FILES, ADMINS
from datetime import datetime

# Definición de planes y sus precios en CUP
PLANS = {
    "1mes_1grupo":    {"label": "1 mes – 1 grupo (500 CUP)",   "price": 500},
    "1mes_2grupos":   {"label": "1 mes – 2 grupos (900 CUP)",  "price": 900},   # 10% dto.
    "3meses_3grupos": {"label": "3 meses – 3 grupos (2 700 CUP)", "price": 2700} # 10% dto.
}

# Métodos de pago disponibles
METHODS = {
    "tarjeta":     {"label": "Tarjeta (100 %)"},
    "saldo_movil": {"label": "Saldo Móvil (50 %) al 56246700"}
}

RECEIPTS_FILE = FILES["receipts"]

# Asegura que exista receipts.json
try:
    with open(RECEIPTS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(RECEIPTS_FILE, 'w') as f:
        f.write("{}")

def register_payment_handlers(bot: TeleBot):
    """Módulo para selección de plan y recepción de comprobantes."""

    # — Paso 1: Mostrar planes disponibles
    @bot.message_handler(commands=['planes'])
    def show_plans(msg):
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for plan in PLANS.values():
            kb.add(KeyboardButton(plan["label"]))
        kb.add(KeyboardButton("🔙 Cancelar"))
        bot.send_message(
            msg.chat.id,
            "💳 *Planes de Suscripción*\n\n"
            "Selecciona el plan que deseas contratar:",
            parse_mode='Markdown',
            reply_markup=kb
        )
        bot.user_data[msg.chat.id] = {"stage": "await_plan"}

    # — Paso 2: Capturar plan y mostrar métodos de pago
    @bot.message_handler(func=lambda m: m.chat.id in getattr(bot, 'user_data', {}) 
                                   and bot.user_data[m.chat.id].get("stage")=="await_plan")
    def pick_method(msg):
        text = msg.text.strip()
        if text == "🔙 Cancelar":
            bot.send_message(msg.chat.id, "❌ Operación cancelada.", reply_markup=ReplyKeyboardRemove())
            bot.user_data.pop(msg.chat.id, None)
            return

        # Buscamos el plan por etiqueta
        for key, plan in PLANS.items():
            if plan["label"] == text:
                bot.user_data[msg.chat.id] = {
                    "stage":      "await_method",
                    "plan_key":   key,
                    "plan_label": plan["label"],
                    "plan_price": plan["price"]
                }
                kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for method in METHODS.values():
                    kb.add(KeyboardButton(method["label"]))
                kb.add(KeyboardButton("🔙 Cancelar"))
                return bot.send_message(
                    msg.chat.id,
                    f"💰 *Métodos de Pago*\n\nPlan: *{plan['label']}*\nSelecciona tu método:",
                    parse_mode='Markdown',
                    reply_markup=kb
                )

        return bot.reply_to(msg, "❌ Selección inválida. Usa /planes para volver a empezar.")

    # — Paso 3: Capturar método y pedir comprobante
    @bot.message_handler(func=lambda m: m.chat.id in getattr(bot, 'user_data', {}) 
                                   and bot.user_data[m.chat.id].get("stage")=="await_method")
    def ask_receipt(msg):
        text = msg.text.strip()
        if text == "🔙 Cancelar":
            bot.send_message(msg.chat.id, "❌ Operación cancelada.", reply_markup=ReplyKeyboardRemove())
            bot.user_data.pop(msg.chat.id, None)
            return

        for mk, method in METHODS.items():
            if method["label"] == text:
                data = bot.user_data[msg.chat.id]
                data.update({"stage": "await_receipt", "method_key": mk, "method_label": method["label"]})
                bot.user_data[msg.chat.id] = data
                return bot.send_message(
                    msg.chat.id,
                    "📸 *Envía ahora la captura* del comprobante como foto, junto con tu `ID` y `@usuario` en la leyenda.",
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardRemove()
                )

        return bot.reply_to(msg, "❌ Método inválido. Usa /planes para reiniciar.")

    # — Paso 4: Recibir foto y datos, guardar y reenviar
    @bot.message_handler(content_types=['photo'])
    def handle_receipt_photo(msg: Message):
        if msg.chat.id not in getattr(bot, 'user_data', {}) \
        or bot.user_data[msg.chat.id].get("stage") != "await_receipt":
            return

        data        = bot.user_data[msg.chat.id]
        plan_key    = data["plan_key"]
        method_key  = data["method_key"]
        plan_label  = data["plan_label"]
        method_label= data["method_label"]
        caption     = msg.caption or ""
        timestamp   = datetime.utcnow().isoformat()

        entry = {
            "user":          msg.chat.id,
            "caption":       caption,
            "photo_file_id": msg.photo[-1].file_id,
            "plan_key":      plan_key,
            "plan_label":    plan_label,
            "method_key":    method_key,
            "method_label":  method_label,
            "when":          timestamp
        }

        # Guardar en receipts.json
        receipts = load('receipts')
        receipts.setdefault(plan_key, []).append(entry)
        save('receipts', receipts)

        # Reenviar a admins y soporte
        texto = (
            f"💰 *Nuevo Pago – {plan_label}*\n"
            f"Usuario: `{msg.chat.id}`\n"
            f"Método: *{method_label}*\n"
            f"Cuando: {timestamp}\n"
            f"— Leyenda: {caption}"
        )
        for aid in ADMINS:
            bot.send_photo(aid, msg.photo[-1].file_id, caption=texto, parse_mode='Markdown')
        support_chat = "-1002605404513"
        bot.send_photo(support_chat, msg.photo[-1].file_id, caption=texto, parse_mode='Markdown')

        # Confirmación usuario
        bot.reply_to(
            msg,
            "✅ Recibido tu comprobante, te contactaré pronto para confirmar.",
            parse_mode='Markdown'
        )
        bot.user_data.pop(msg.chat.id, None)
