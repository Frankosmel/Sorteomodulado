from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load
from config import ADMINS

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(commands=['misgrupos'])
    def mis_grupos(msg):
        uid = msg.from_user.id
        gr = load('grupos')
        # Filtra sólo los grupos activados por este usuario
        own = {gid:info for gid,info in gr.items() if info['activado_por']==uid}
        if not own:
            bot.reply_to(msg, "ℹ️ No tienes grupos activos.")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        # Un botón por cada grupo
        for gid in own:
            kb.add(KeyboardButton(f"Grupo {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))

        bot.send_message(uid, "📂 Tus Grupos Activos:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner_selection(msg):
        text = msg.text
        uid = msg.from_user.id
        gr = load('grupos')
        # Si tocó “Salir”
        if text == "🔙 Salir":
            bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())
            return

        # Detecta selección de grupo
        if text.startswith("Grupo "):
            gid = text.split()[1]
            # Verifica que sea dueño
            info = gr.get(gid)
            if not info or info['activado_por']!=uid:
                bot.reply_to(msg, "⚠️ No eres dueño de ese grupo.")
                return
            # Muestra opciones para ese grupo
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Mostrar participantes"))
            kb.add(KeyboardButton("🏆 Mostrar top invitadores"))
            kb.add(KeyboardButton("🔙 Volver"))
            # Guarda contexto
            bot.send_message(uid, f"⚙️ Gestiona Grupo {gid}:", reply_markup=kb)
            # Registrar cuál es el grupo en contexto
            bot._current_group = gid  # atributo temporal

        elif msg.text in ["👥 Mostrar participantes", "🏆 Mostrar top invitadores"]:
            gid = getattr(bot, '_current_group', None)
            if not gid:
                bot.reply_to(msg, "⚠️ Primero selecciona un grupo con /misgrupos.")
                return
            if msg.text=="👥 Mostrar participantes":
                # Reusar la función de lista
                participantes = load('participantes').get(gid, {})
                texto = f"👥 *Participantes Grupo {gid}:*\n\n"
                for uid2, info in participantes.items():
                    if info.get("username"):
                        texto += f"• @{info['username']} — {info['nombre']}\n"
                    else:
                        texto += f"• {info['nombre']} — ID: {uid2}\n"
                bot.send_message(uid, texto, parse_mode='Markdown')
            else:
                invit = load('invitaciones').get(gid, {})
                texto = f"🏆 *Top Invitadores Grupo {gid}:*\n\n"
                top = sorted(invit.items(), key=lambda x: x[1], reverse=True)
                for i,(uid2,count) in enumerate(top[:10], start=1):
                    texto += f"{i}. ID {uid2} — {count} invitado(s)\n"
                bot.send_message(uid, texto, parse_mode='Markdown')
        # Si volvió
        elif text=="🔙 Volver":
            bot.send_message(uid, "🔙 Regresa al menú principal con /misgrupos", reply_markup=ReplyKeyboardRemove())
