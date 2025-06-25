from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from config import ADMINS
from datetime import datetime

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(commands=['misgrupos'])
    def mis_grupos(msg):
        uid = msg.from_user.id
        gr = load('grupos')
        own = {gid:info for gid,info in gr.items() if info['activado_por']==uid}
        if not own:
            bot.reply_to(msg, "ℹ️ No tienes grupos activos.")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for gid in own:
            kb.add(KeyboardButton(f"Gestionar {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))

        bot.send_message(uid, "📂 Tus Grupos Activos:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.chat.type=='private' and m.from_user.id in ADMINS)
    def handle_owner_selection(msg):
        text = msg.text
        uid = msg.from_user.id
        gr = load('grupos')

        # Salir
        if text == "🔙 Salir":
            bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())
            return

        # Seleccionó gestionar un grupo
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            if gid not in gr or gr[gid]['activado_por'] != uid:
                bot.reply_to(msg, "⚠️ No eres dueño de ese grupo.")
                return

            # Monta menú específico para este grupo
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"))
            kb.add(KeyboardButton("🏆 Ver top invitadores"))
            kb.add(KeyboardButton("🔄 Reiniciar sorteo"))
            kb.add(KeyboardButton("🔙 Volver"))
            # Guarda contexto temporalmente
            bot.current_group = gid
            bot.send_message(uid, f"⚙️ Gestionando Grupo {gid}:", reply_markup=kb)
            return

        # Acciones dentro de un grupo seleccionado
        gid = getattr(bot, 'current_group', None)
        if not gid:
            bot.reply_to(msg, "⚠️ Primero selecciona un grupo con /misgrupos.")
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
            for i,(uid2,count) in enumerate(top[:10], start=1):
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

        elif text == "🔙 Volver":
            bot.send_message(uid, "🔙 Regresa al menú con /misgrupos", reply_markup=ReplyKeyboardRemove())
