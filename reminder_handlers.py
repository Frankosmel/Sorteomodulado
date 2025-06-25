from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from storage import load
from config import FILES

sched = BackgroundScheduler()

def reminder_job(bot):
    auth = load('autorizados')
    hoy = datetime.utcnow()
    for uid, info in auth.items():
        exp = datetime.fromisoformat(info['vence'])
        dias = (exp - hoy).days
        if dias == 5:
            bot.send_message(
                int(uid),
                f"⏳ Tu suscripción vence en 5 días ({exp.date()}). Usa /admin para renovar."
            )

def start_reminders(bot):
    sched.add_job(reminder_job, 'cron', hour=0, minute=0, args=[bot])
    sched.start()

def register_subscription_handlers(bot):
    @bot.message_handler(commands=['misuscripciones'])
    def misuscripciones(msg):
        uid = str(msg.from_user.id)
        auth = load('autorizados')
        info = auth.get(uid)
        if not info:
            bot.reply_to(msg, "❌ No tienes suscripción activa.")
            return
        exp = datetime.fromisoformat(info['vence'])
        dias = (exp - datetime.utcnow()).days
        bot.reply_to(
            msg,
            f"✅ Tu suscripción vence el {exp.date()} ({dias} días restantes)."
        )
