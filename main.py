from telebot import TeleBot
from config import TOKEN
from storage import ensure_files
from group_handlers import register_group_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from admin_handlers import register_admin_handlers

# Inicializar datos y bot
ensure_files()
bot = TeleBot(TOKEN)

# Registrar módulos
register_group_handlers(bot)
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "👋 ¡Hola! Usa tus comandos en el grupo o /admin en privado.")

print("🤖 Bot modular en ejecución...")
bot.infinity_polling()
