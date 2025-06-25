from telebot import TeleBot
from config import TOKEN
from storage import ensure_files
from group_handlers import register_group_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from admin_handlers import register_admin_handlers
from owner_handlers import register_owner_handlers

# Inicializar datos y bot
ensure_files()
bot = TeleBot(TOKEN)

# Registrar todos los módulos/manejadores
register_group_handlers(bot)
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)

# Comando /start
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "👋 ¡Hola! Usa tus comandos en el grupo o /admin en privado.")

# Eliminar cualquier webhook activo antes de usar polling
bot.remove_webhook()

print("🤖 Bot modular en ejecución...")
bot.infinity_polling()
