# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from storage import load, save
from config import FILES

sched = BackgroundScheduler()
JOBS_FILE = FILES["jobs"]

# Inicializar jobs.json si falta
try:
    with open(JOBS_FILE,'r'): pass
except FileNotFoundError:
    with open(JOBS_FILE,'w') as f: f.write("{}")

def load_jobs(bot):
    jobs = load('jobs')
    for jid, job in jobs.items():
        run_time = datetime.fromisoformat(job['run_at'])
        sched.add_job(
            func=lambda j=jid: _run_scheduled_draw(bot, j),
            trigger='date',
            run_date=run_time,
            id=jid
        )
    sched.start()
    print(f"[Scheduler] Scheduler iniciado y jobs cargados.")

def schedule_raffle(bot, chat_id: str, run_at: datetime, name: str):
    # convertir a UTC si tiene tzinfo, o asumir UTC
    run_utc = run_at.astimezone(timezone.utc) if run_at.tzinfo else run_at.replace(tzinfo=timezone.utc)
    jobs = load('jobs')
    jid = f"raffle_{chat_id}_{int(run_utc.timestamp())}"
    jobs[jid] = {
        "chat_id": chat_id,
        "run_at": run_utc.isoformat(),
        "name": name
    }
    save('jobs', jobs)
    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, jid),
        trigger='date',
        run_date=run_utc,
        id=jid
    )
    print(f"[Scheduler] Job {jid} programado para {run_utc} UTC.")

def cancel_scheduled_raffle(bot, jid: str):
    jobs = load('jobs')
    if jid in jobs:
        try:
            sched.remove_job(jid)
        except:
            pass
        del jobs[jid]
        save('jobs', jobs)
        print(f"[Scheduler] Job {jid} cancelado.")

def _run_scheduled_draw(bot, jid: str):
    jobs = load('jobs')
    job = jobs.get(jid)
    if not job:
        return
    chat_id = job['chat_id']
    name    = job.get('name', 'Sorteo')
    bot.send_message(int(chat_id), f"⏳ ¡Comienza el sorteo programado «{name}»!")
    bot.send_message(int(chat_id), "/sortear")
    del jobs[jid]
    save('jobs', jobs)
    try:
        sched.remove_job(jid)
    except:
        pass

def start_reminders(bot):
    if not sched.get_job('daily_reminder'):
        sched.add_job(
            func=lambda: reminder_job(bot),
            trigger='cron', hour=0, minute=0,
            id='daily_reminder'
        )
    print(f"[Scheduler] Recordatorios programados (5 días antes).")

def reminder_job(bot):
    auth = load('autorizados')
    ahora = datetime.utcnow().replace(tzinfo=timezone.utc)
    for uid, info in auth.items():
        vence = datetime.fromisoformat(info['vence'])
        if vence.tzinfo is None:
            vence = vence.replace(tzinfo=timezone.utc)
        if (vence - ahora).days == 5:
            bot.send_message(
                int(uid),
                f"⏳ Tu suscripción vence en 5 días ({vence.date()}). Usa /misuscripciones o /admin."
            )
