from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import load, save
from scheduler import set_group_timezone
from config import ADMINS, FILES
from draw_handlers import do_draw

def register_owner_handlers(bot: TeleBot):
    @bot.message_handler(commands=['misgrupos'])
    def mis_grupos(msg):
        if msg.chat.type != 'private':
            return
        uid = msg.from_user.id
        # Carga grupos y filtra por activado_por
        grupos = load('grupos')
        propios = {gid:info for gid,info in grupos.items() if info.get('activado_por') == uid}
        if not propios:
            return bot.reply_to(msg, "ℹ️ No tienes ningún grupo activado.")

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for gid in propios:
            kb.add(KeyboardButton(f"Gestionar {gid}"))
        kb.add(KeyboardButton("🔙 Salir"))
        bot.send_message(uid,
            "📂 *Tus Grupos Activos:*\n\n"
            "Selecciona uno para gestionar:", 
            parse_mode='Markdown',
            reply_markup=kb
        )

    @bot.message_handler(func=lambda m: m.chat.type=='private')
    def handle_owner_selection(msg):
        uid  = msg.from_user.id
        text = msg.text.strip()
        grupos = load('grupos')

        # Cerrar menú
        if text == "🔙 Salir":
            return bot.send_message(uid, "✅ Menú cerrado.", reply_markup=ReplyKeyboardRemove())

        # Gestionar grupo
        if text.startswith("Gestionar "):
            gid = text.split()[1]
            info = grupos.get(gid)
            if not info or info.get('activado_por') != uid:
                return bot.reply_to(msg, "⚠️ No puedes gestionar ese grupo.")

            # Construir menú específico
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("👥 Ver participantes"))
            kb.add(KeyboardButton("🏆 Ver top invitadores"))
            kb.add(KeyboardButton("🔄 Reiniciar sorteo"))
            kb.add(KeyboardButton("🗑️ Borrar lista de sorteo"))
            kb.add(KeyboardButton("🌐 Cambiar zona horaria"))
            kb.add(KeyboardButton("🔙 Salir"))

            # Guarda contexto
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[uid] = gid

            return bot.send_message(uid,
                f"⚙️ *Gestión Grupo {gid}*\n\n"
                "Selecciona una opción del menú:",
                parse_mode='Markdown',
                reply_markup=kb
            )

        # Las demás acciones requieren contexto de grupo
        gid = getattr(bot, 'user_data', {}).get(uid)
        if not gid:
            return

        # Mostrar participantes
        if text == "👥 Ver participantes":
            partes = load('participantes').get(gid, {})
            msg_text = f"👥 *Participantes Grupo {gid}:*\n\n"
            for uid2, info in partes.items():
                if info.get('username'):
                    msg_text += f"• @{info['username']} — {info['nombre']}\n"
                else:
                    msg_text += f"• {info['nombre']} — ID: {uid2}\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # Mostrar top invitadores
        if text == "🏆 Ver top invitadores":
            invs = load('invitaciones').get(gid, {})
            if not invs:
                return bot.send_message(uid, "📉 No hay invitados registrados.")
            top = sorted(invs.items(), key=lambda x:x[1], reverse=True)[:10]
            msg_text = f"🏆 *Top Invitadores Grupo {gid}:*\n\n"
            for i,(uid2,count) in enumerate(top, start=1):
                msg_text += f"{i}. ID {uid2} — {count} invitado(s)\n"
            return bot.send_message(uid, msg_text, parse_mode='Markdown')

        # Reiniciar sorteo (vaciar lista)
        if text == "🔄 Reiniciar sorteo":
            sorteos = load('sorteo')
            sorteos[gid] = {}
            save('sorteo', sorteos)
            return bot.send_message(uid, f"🔁 Sorteo del grupo {gid} ha sido reiniciado.")

        # Borrar lista de sorteo (eliminar clave)
        if text == "🗑️ Borrar lista de sorteo":
            sorteos = load('sorteo')
            if gid in sorteos:
                del sorteos[gid]
                save('sorteo', sorteos)
                return bot.send_message(uid, f"🗑️ Lista de sorteo del grupo {gid} borrada.")
            else:
                return bot.send_message(uid, "ℹ️ No había lista de sorteo activa.")

        # Cambiar zona horaria
        if text == "🌐 Cambiar zona horaria":
            prompt = bot.send_message(uid,
                "✏️ Envía: `<chat_id>,<Zona>`\n"
                "Ejemplo: `-1001234567890,America/Havana`"
            )
            return bot.register_next_step_handler(prompt, cambiar_zona)

    def cambiar_zona(msg):
        try:
            chat_id, tz = map(str.strip, msg.text.split(','))
            # Validar zona
            from zoneinfo import ZoneInfo
            ZoneInfo(tz)
            set_group_timezone(chat_id, tz)
            bot.send_message(msg.from_user.id,
                f"✅ Zona horaria de *{chat_id}* actualizada a *{tz}*",
                parse_mode='Markdown'
            )
        except Exception:
            bot.send_message(msg.from_user.id,
                "❌ Formato inválido o zona no reconocida.\n"
                "Usa: `-1001234567890,America/Havana`",
                parse_mode='Markdown'
                            )
