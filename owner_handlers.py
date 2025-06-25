from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(commands=['misgrupos'])
    def mis_grupos(msg):
        if msg.chat.type != 'private':
            return
        uid = msg.from_user.id
        gr = load('grupos')
        own = {gid: info for gid, info in gr.items() if info['activado_por'] == uid}
        if not own:
            bot.reply_to(msg, "ℹ️ No tienes grupos activos.")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for gid in own:
            kb.add(KeyboardButton(f"Gestionar {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))

        bot.send_message(uid, "📂 Tus Grupos Activos:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.chat.type == 'private')
    def handle_owner_selection(msg):
        uid = msg.from_user.id
        gr = load('grupos')
        text = msg.text

        # Salir
        if text == "🔙 Salir":
            bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())
            return

        # Seleccionó gestionar un grupo
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = gr.get(gid)
            if not info or info['activado_por'] != uid:
                bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")
                return

            # Menú para el grupo seleccionado
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"))
            kb.add(KeyboardButton("🏆 Ver top invitadores"))
            kb.add(KeyboardButton("🔄 Reiniciar sorteo"))
            kb.add(KeyboardButton("🗑️ Borrar lista de sorteo"))
            kb.add(KeyboardButton("🔙 Volver"))

            # Guardar contexto
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid

            bot.send_message(uid, f"⚙️ Gestionando Grupo {gid}:", reply_markup=kb)
            return

        # Acciones de gestión, requiere contexto
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return

        if text == "👥 Ver participantes":
            part = load('participantes').get(gid, {})
            texto = f"👥 *Participantes Grupo {gid}:*\n\n"
            for uid2, info in part.items():
                if info.get('username'):
                    texto += f"• @{info['username']} — {info['nombre']}\n"
                else:
                    texto += f"• {info['nombre']} — ID: {uid2}\n"
            bot.send_message(uid, texto, parse_mode='Markdown')

        elif text == "🏆 Ver top invitadores":
            inv = load('invitaciones').get(gid, {})
            texto = f"🏆 *Top Invitadores Grupo {gid}:*\n\n"
            top = sorted(inv.items(), key=lambda x: x[1], reverse=True)
            for i, (uid2, count) in enumerate(top[:10], start=1):
                texto += f"{i}. ID {uid2} — {count} invitado(s)\n"
            bot.send_message(uid, texto, parse_mode='Markdown')

        elif text == "🔄 Reiniciar sorteo":
            sorteos = load('sorteo')
            if gid in sorteos:
                sorteos[gid] = {}
                save('sorteo', sorteos)
                bot.send_message(uid, f"🔁 Sorteo en Grupo {gid} reiniciado.")
            else:
                bot.send_message(uid, "ℹ️ No hay sorteo activo para reiniciar.")

        elif text == "🗑️ Borrar lista de sorteo":
            sorteos = load('sorteo')
            if gid in sorteos:
                del sorteos[gid]
                save('sorteo', sorteos)
                bot.send_message(uid, f"🗑️ Lista de sorteo de Grupo {gid} borrada.")
            else:
                bot.send_message(uid, "ℹ️ No hay lista de sorteo para borrar.")

        elif text == "🔙 Volver":
            bot.send_message(uid, "🔙 Regresa al menú con /misgrupos", reply_markup=ReplyKeyboardRemove())
