# template_handlers.py
from telebot import TeleBot
from telebot.types import Message
from storage import load, save
from config import FILES

def register_template_handlers(bot: TeleBot):
    @bot.message_handler(commands=['set_template'])
    def set_template(msg: Message):
        """
        /set_template <tipo> "Texto…"
        Variables admitidas: {USUARIO}, {CHAT}, {GANADOR}, {FECHA}
        """
        partes = msg.text.split(' ', 1)
        if len(partes) < 2 or ' ' not in partes[1]:
            return bot.reply_to(msg,
                "❌ Uso:\n"
                "/set_template <tipo> \"Texto con {USUARIO}, {CHAT}, {GANADOR}, {FECHA}\"\n"
                "Ej: /set_template welcome \"¡Hola {USUARIO}! Bienvenido a {CHAT}.\""
            )
        tipo, texto = partes[1].split(' ', 1)
        texto = texto.strip('"“”')
        tpl = load('templates')
        chat = str(msg.chat.id)
        tpl.setdefault(chat, {})[tipo] = texto
        save('templates', tpl)
        bot.reply_to(msg, f"✅ Plantilla *{tipo}* guardada.", parse_mode='Markdown')

    @bot.message_handler(commands=['get_templates'])
    def get_templates(msg: Message):
        tpl = load('templates').get(str(msg.chat.id), {})
        if not tpl:
            return bot.reply_to(msg, "ℹ️ No hay plantillas definidas.")
        texto = "📋 *Plantillas definidas:*\n"
        for t, body in tpl.items():
            texto += f"• `{t}` → {body}\n"
        bot.reply_to(msg, texto, parse_mode='Markdown')

# Función auxiliar para usar en draw_handlers.py
def render_template(chat_id: int, tipo: str, **vars) -> str | None:
    tpl = load('templates').get(str(chat_id), {}).get(tipo)
    if not tpl:
        return None
    for k, v in vars.items():
        tpl = tpl.replace(f"{{{k}}}", str(v))
    return tpl
