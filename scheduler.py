from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from storage import load, save
from config import FILES, VIGENCIA_DIAS

sched = BackgroundScheduler()
JOBS_FILE = FILES["jobs"]

# Asegura que exista jobs.json
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")

def load_jobs(bot):
    """Carga los sorteos programados desde jobs.json y los encola."""
    jobs = load('jobs')
    for job_id, job in jobs.items():
        run_time = datetime.fromisoformat(job['run_at'])
        sched.add_job(
            func=lambda jid=job_id: _run_scheduled_draw(bot, jid),
            trigger='date',
            run_date=run_time,
            id=job_id
        )
    sched.start()
    print(f"[Scheduler] Scheduler iniciado y jobs cargados.")

def schedule_raffle(bot, chat_id: str, run_at: datetime):
    """Programa un nuevo sorteo para chat_id en la fecha run_at."""
    jobs = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        "run_at": run_at.isoformat()
    }
    save('jobs', jobs)
    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, job_id),
        trigger='date',
        run_date=run_at,
        id=job_id
    )
    print(f"[Scheduler] Programando job {job_id} → {run_at} en grupo {chat_id}")

def _run_scheduled_draw(bot, job_id: str):
    """Helper interno que dispara el sorteo y lo anuncia."""
    jobs = load('jobs')
    job = jobs.get(job_id)
    if not job:
        return
    chat_id = job['chat_id']
    # enviamos el comando sortear automáticamente
    bot.send_message(int(chat_id), "⏳ ¡Comienza el sorteo programado!")
    bot.send_message(int(chat_id), "/sortear")
    # opcionalmente, eliminamos el job tras ejecutarlo:
    del jobs[job_id]
    save('jobs', jobs)
    sched.remove_job(job_id)

# ------------------ Recordatorios de suscripción ------------------

def reminder_job(bot):
    """Envía un aviso a cada autorizado 5 días antes del vencimiento."""
    auth = load('autorizados')
    ahora = datetime.utcnow()
    for uid, info in auth.items():
        vence = datetime.fromisoformat(info['vence'])
        dias_rest = (vence - ahora).days
        if dias_rest == 5:
            bot.send_message(
                int(uid),
                f"⏳ Tu suscripción vence en 5 días ({vence.date()}). "
                "Usa /misuscripciones para ver detalles o /admin para renovar."
            )

def start_reminders(bot):
    """Programa el job diario que ejecuta reminder_job cada medianoche UTC."""
    sched.add_job(
        func=lambda: reminder_job(bot),
        trigger='cron',
        hour=0, minute=0,  # UTC
        id='daily_reminder'
    )
    print(f"[Scheduler] Recordatorios programados (5 días antes).")
