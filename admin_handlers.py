# admin_handlers.py

from telebot import TeleBot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from config import ADMINS, PLANS, VIGENCIA_DIAS
from storage import load
from auth import add_authorized, remove_authorized, list_authorized, is_valid
from datetime import datetime, timedelta
import re

# Estado temporal por admin para flujo "Autorizar"
PENDING_AUTH = {}

def _escape_md(text: str) -> str:
    """Escapa caracteres especiales de Markdown."""
    return re.sub(r'([_*[\]()~`>#+=|{}.!-])', r'\\\1', text)

def show_admin_menu(bot: TeleBot, chat_id: int):
    """Teclado principal del panel admin."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        KeyboardButton("👥 Autorizados"),
        KeyboardButton("✅ Autorizar"),
        KeyboardButton("🗑️ Desautorizar")
    )
    kb.row(
        KeyboardButton("⏳ Vencimientos"),
        KeyboardButton("🗂 Grupos"),
        KeyboardButton("📤 Mensajes")
    )
    kb.row(KeyboardButton("❌ Salir"))
    bot.send_message(
        chat_id,
        "👑 *Panel de Administración*\n\nSeleccione una opción:",
        parse_mode='Markdown',
        reply_markup=kb
    )

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(msg):
        if msg.chat.type != 'private' or msg.from_user.id not in ADMINS:
            return bot.reply_to(
                msg,
                "⛔ *Acceso denegado.* Use /admin en privado.",
                parse_mode='Markdown'
            )
        show_admin_menu(bot, msg.chat.id)

    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_admin(msg):
        text = (msg.text or "").strip()
        uid = msg.from_user.id

        if text == "❌ Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        if text == "👥 Autorizados":
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay usuarios autorizados.*", parse_mode='Markdown')
            resp = "👥 *Lista de Autorizados:*\n\n"
            for k, info in auth.items():
                exp = datetime.fromisoformat(info['vence']).date()
                usuario = _escape_md(info.get('username',''))
                plan = _escape_md(info.get('plan_label', info.get('plan','—')))
                price = info.get('price_usd', 0.0)
                resp += f"• {usuario} (`{k}`) — {plan} — ${price:.2f} — vence *{exp}*\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        if text == "✅ Autorizar":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(KeyboardButton("Cancelar"))
            bot.send_message(
                uid,
                "➕ *Autorizar*: añade o renueva un usuario.\n"
                "✏️ Envíe: `ID,@usuario`\n\nEjemplo: `12345,@pepito`",
                parse_mode='Markdown',
                reply_markup=kb
            )
            return bot.register_next_step_handler(msg, process_authorize, bot)

        if text == "🗑️ Desautorizar":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(KeyboardButton("Cancelar"))
            bot.send_message(
                uid,
                "➖ *Desautorizar*: quite acceso a un usuario.\n✏️ Envíe solo el `ID`.",
                parse_mode='Markdown',
                reply_markup=kb
            )
            return bot.register_next_step_handler(msg, process_deauthorize, bot)

        if text == "⏳ Vencimientos":
            auth = list_authorized()
            if not auth:
                return bot.send_message(uid, "ℹ️ *No hay usuarios autorizados.*", parse_mode='Markdown')
            resp = "⏳ *Vencimientos (días restantes)*\n\n"
            now = datetime.utcnow()
            for k, info in auth.items():
                dias = (datetime.fromisoformat(info['vence']) - now).days
                usuario = _escape_md(info.get('username',''))
                plan = _escape_md(info.get('plan_label', info.get('plan','—')))
                resp += f"• {usuario} (`{k}`) — {plan}: {max(dias,0)} día(s)\n"
            return bot.send_message(uid, resp, parse_mode='Markdown')

        # ─────────────────────────────────────────────────────────────
        # 🗂 Grupos (con estado de autorización y enlaces)
        # ─────────────────────────────────────────────────────────────
        if text == "🗂 Grupos":
            grupos = load('grupos')
            if not grupos:
                return bot.send_message(uid, "ℹ️ *No hay grupos registrados.*", parse_mode='Markdown')

            header = "🗂 *Grupos donde está el bot*\n"
            header += "_(Muestra si el dueño sigue autorizado o no, IDs y enlaces disponibles)_\n\n"

            lines = []
            for chat_id_str, ginfo in grupos.items():
                chat_id = int(chat_id_str)
                activador = ginfo.get('activado_por')
                creado = ginfo.get('creado', '—')

                # Determinar estado de autorización del dueño actual
                dueño_aut = is_valid(activador)
                estado = "✅ Autorizado" if dueño_aut else "❌ No autorizado"

                # Intentar obtener título y enlace del grupo
                title = str(chat_id)
                enlace = None
                try:
                    chat = bot.get_chat(chat_id)
                    if getattr(chat, "title", None):
                        title = chat.title
                    username = getattr(chat, "username", None)
                    if username:  # grupos/canales públicos
                        enlace = f"https://t.me/{username}"
                    else:
                        # Como fallback, intentar exportar un enlace (requiere permisos de admin del bot)
                        try:
                            enlace = bot.export_chat_invite_link(chat_id)
                        except Exception:
                            enlace = None
                except Exception:
                    pass

                # Construir línea (Markdown: mostramos URL en claro para que sea clicable)
                linea = (
                    f"• *{_escape_md(title)}* "
                    f"(`{chat_id}`)\n"
                    f"  Estado: *{estado}* — Activado por: `{activador}` — Desde: {creado}\n"
                )
                if enlace:
                    linea += f"  Enlace: {enlace}\n"
                else:
                    linea += f"  Enlace: —\n"
                lines.append(linea)

            # Telegram limita mensajes largos; si son muchas líneas, troceamos
            salida = header
            for bloque in _chunk_lines(lines, max_chars=3500):
                bot.send_message(uid, salida + bloque, parse_mode='Markdown')
                salida = ""  # solo encabezado en el primer bloque

            return

        if text == "📤 Mensajes":
            kb2 = ReplyKeyboardMarkup(resize_keyboard=True)
            kb2.row(KeyboardButton("A autorizados"), KeyboardButton("A grupos"))
            kb2.row(KeyboardButton("❌ Salir"))
            return bot.send_message(
                uid,
                "📤 *Mensajes*:\n"
                "→ *A autorizados*: envía texto a todos los usuarios autorizados.\n"
                "→ *A grupos*: envía texto a todos los grupos activos.",
                parse_mode='Markdown',
                reply_markup=kb2
            )

        if text == "A autorizados":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(KeyboardButton("Cancelar"))
            bot.send_message(
                uid,
                "✏️ *Escriba el mensaje* que enviará a todos los autorizados:",
                parse_mode='Markdown',
                reply_markup=kb
            )
            return bot.register_next_step_handler(msg, send_to_authorized, bot)

        if text == "A grupos":
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(KeyboardButton("Cancelar"))
            bot.send_message(
                uid,
                "✏️ *Escriba el mensaje* que enviará a todos los grupos:",
                parse_mode='Markdown',
                reply_markup=kb
            )
            return bot.register_next_step_handler(msg, send_to_groups, bot)

# ---------- Helpers de planes (ReplyKeyboard) ----------
def _plan_label_map():
    return {p['label']: p['key'] for p in PLANS}

def _build_plans_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    labels = [p['label'] for p in PLANS]
    for i in range(0, len(labels), 2):
        kb.row(*labels[i:i+2])
    kb.row("Cancelar")
    return kb

def _chunk_lines(lines, max_chars=3500):
    """Une líneas en bloques que no excedan max_chars (para no romper el límite de Telegram)."""
    bloques = []
    actual = ""
    for ln in lines:
        if len(actual) + len(ln) > max_chars:
            bloques.append(actual)
            actual = ""
        actual += ln
    if actual:
        bloques.append(actual)
    return bloques

def process_authorize(msg, bot: TeleBot):
    uid = msg.from_user.id
    if (msg.text or "").strip().lower() == "cancelar":
        return bot.send_message(uid, "❎ Operación cancelada.", reply_markup=ReplyKeyboardRemove())

    partes = [p.strip() for p in (msg.text or "").split(',')]
    if len(partes) != 2 or not partes[0].isdigit() or not partes[1].startswith('@'):
        return bot.reply_to(msg, "❌ Formato inválido. Use `ID,@usuario`.", parse_mode='Markdown')

    user_id = int(partes[0])
    username = partes[1]
    PENDING_AUTH[uid] = {"user_id": user_id, "username": username}

    kb = _build_plans_keyboard()
    bot.send_message(
        uid,
        "🌟 *Seleccione el plan* para este usuario (teclas de abajo):",
        parse_mode='Markdown',
        reply_markup=kb
    )
    return bot.register_next_step_handler(msg, process_plan_reply, bot)

def process_plan_reply(msg, bot: TeleBot):
    uid = msg.from_user.id
    choice = (msg.text or "").strip()

    if choice.lower() == "cancelar":
        PENDING_AUTH.pop(uid, None)
        return bot.send_message(uid, "❎ Operación cancelada.", reply_markup=ReplyKeyboardRemove())

    label_to_key = _plan_label_map()
    if choice not in label_to_key:
        kb = _build_plans_keyboard()
        bot.send_message(uid, "⚠️ Opción no válida. Elija un plan de la lista:", reply_markup=kb)
        return bot.register_next_step_handler(msg, process_plan_reply, bot)

    pending = PENDING_AUTH.get(uid)
    if not pending:
        return bot.send_message(uid, "⚠️ Sesión expirada. Vuelva a *Autorizar*.", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

    plan_key = label_to_key[choice]
    days = next((p.get('duration_days', VIGENCIA_DIAS) for p in PLANS if p['key'] == plan_key), VIGENCIA_DIAS)
    vence_date = (datetime.utcnow() + timedelta(days=days)).date().isoformat()

    add_authorized(pending["user_id"], pending["username"], plan_key)

    bot.send_message(
        uid,
        _escape_md(f"✅ Usuario {pending['username']} (`{pending['user_id']}`) autorizado con {choice}.\n"
                   f"📅 Vence el: *{vence_date}*"),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    try:
        bot.send_message(
            pending["user_id"],
            _escape_md(f"🎉 Hola {pending['username']}!\n"
                       f"Tu suscripción {choice} ha sido activada.\n"
                       f"📅 Vence el: *{vence_date}*"),
            parse_mode='Markdown'
        )
    except Exception:
        pass

    del PENDING_AUTH[uid]

def process_deauthorize(msg, bot: TeleBot):
    uid = msg.from_user.id
    if (msg.text or "").strip().lower() == "cancelar":
        return bot.send_message(uid, "❎ Operación cancelada.", reply_markup=ReplyKeyboardRemove())
    if not (msg.text or "").isdigit():
        return bot.reply_to(msg, "❌ ID inválido. Debe ser numérico.", parse_mode='Markdown')

    user_id = int(msg.text)
    success = remove_authorized(user_id)
    texto = "desautorizado" if success else "no estaba autorizado"
    bot.send_message(
        uid,
        f"🗑️ Usuario `{user_id}` {texto}.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

def send_to_authorized(msg, bot: TeleBot):
    if (msg.text or "").strip().lower() == "cancelar":
        return bot.send_message(msg.from_user.id, "❎ Operación cancelada.", reply_markup=ReplyKeyboardRemove())
    texto = msg.text
    for k in list_authorized().keys():
        try:
            bot.send_message(int(k), texto)
        except:
            pass
    bot.send_message(
        msg.from_user.id,
        "✅ Mensaje enviado a todos los autorizados.",
        reply_markup=ReplyKeyboardRemove()
    )

def send_to_groups(msg, bot: TeleBot):
    if (msg.text or "").strip().lower() == "cancelar":
        return bot.send_message(msg.from_user.id, "❎ Operación cancelada.", reply_markup=ReplyKeyboardRemove())
    texto = msg.text
    for chat_id in load('grupos').keys():
        try:
            bot.send_message(int(chat_id), texto)
        except:
            pass
    bot.send_message(
        msg.from_user.id,
        "✅ Mensaje reenviado a todos los grupos.",
        reply_markup=ReplyKeyboardRemove()
            )
