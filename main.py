from telebot import TeleBot
from config import TOKEN
from storage import ensure_files
from group_handlers import register_group_handlers
from raffle_handlers import register_referral_handlers, register_raffle_handlers
from admin_handlers import register_admin_handlers
from owner_handlers import register_owner_handlers
from draw_handlers import do_draw      # ← aquí cambias

# Inicializar datos y bot
ensure_files()
bot = TeleBot(TOKEN)

# Registrar módulos/manejadores
register_group_handlers(bot)
register_referral_handlers(bot)
register_raffle_handlers(bot)
register_admin_handlers(bot)
register_owner_handlers(bot)
# No es necesario registrar nada más: owner_handlers invoca do_draw directamente

# Comando /start…
bot.remove_webhook()
print("🤖 Bot modular con scheduler en ejecución…")
bot.infinity_polling()
