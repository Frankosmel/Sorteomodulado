from telebot import TeleBot
from storage import load, save
from auth import is_valid, register_group
from zoneinfo import ZoneInfo
from config import FILES

def register_group_handlers(bot: TeleBot):
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_members(msg):
        bot_id = bot.get_me().id
        chat_id = str(msg.chat.id)
        participantes = load('participantes')
        invitaciones = load('invitaciones')
        participantes.setdefault(chat_id, {})
        invitaciones.setdefault(chat_id, {})

        # --- ACTIVACIÓN DEL BOT EN EL GRUPO ---
        if any(u.id == bot_id for u in msg.new_chat_members):
            adder = msg.from_user.id

            # Si el usuario que invita no está autorizado o su plan venció, salimos
            if not is_valid(adder):
                bot.send_message(
                    msg.chat.id,
                    "⛔ Acceso no autorizado o pago vencido. "
                    "Contacta con un administrador para renovar tu suscripción."
                )
                bot.leave_chat(msg.chat.id)
                return

            # Registramos el grupo en grupos.json (autorizado_por, creado)
            register_group(msg.chat.id, adder)

            # Almacenamos zona horaria por defecto "UTC" si no existe
            grupos = load('grupos')
            info = grupos.setdefault(chat_id, {})  # register_group ya puso activado_por y creado
            info.setdefault('timezone', 'UTC')
            save('grupos', grupos)

            # Mensaje de bienvenida + guía de uso
            bot.send_message(
                msg.chat.id,
                "✅ *Bot activado en este grupo.* 🎉\n\n"
                "• Quién lo activó: `{}`\n"
                "• Zona horaria por defecto: *UTC*\n\n"
                "Ahora puedes gestionar tu grupo de sorteos desde tu chat privado:\n"
                "👉 Envía `/misgrupos` al bot en privado para ver las opciones."
                .format(adder),
                parse_mode='Markdown'
            )

        # --- REGISTRO DE INVITACIONES AL GRUPO ---
        for new_user in msg.new_chat_members:
            # Saltamos el propio bot
            if new_user.id == bot_id:
                continue

            uid = str(new_user.id)
            adder = msg.from_user

            # Si el usuario aún no está en participantes, lo registramos
            if uid not in participantes[chat_id]:
                participantes[chat_id][uid] = {
                    "nombre": new_user.first_name,
                    "username": new_user.username
                }
                # Incrementamos el conteo de invitaciones
                inv_id = str(adder.id)
                invitaciones[chat_id][inv_id] = invitaciones[chat_id].get(inv_id, 0) + 1

        # Guardamos cambios en JSON
        save('participantes', participantes)
        save('invitaciones', invitaciones)
