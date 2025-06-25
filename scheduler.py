from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from storage import load, save
from config import FILES

sched = BackgroundScheduler()
JOBS_FILE = FILES.get("jobs", "jobs.json")

# Asegura que exista jobs.json
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")

def load_jobs(bot):
    jobs = load('jobs')
    for job_id, job in jobs.items():
        run_time = datetime.fromisoformat(job['run_at'])
        sched.add_job(
            func=lambda jid=job_id: bot.send_message(
                int(job['chat_id']),
                "⏳ ¡Comienza el sorteo programado!"
            ) or bot.send_message(int(job['chat_id']), "/sortear"),
            trigger='date',
            run_date=run_time,
            id=job_id
        )
    sched.start()

def schedule_raffle(bot, chat_id: str, run_at: datetime):
    jobs = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        "run_at": run_at.isoformat()
    }
    save('jobs', jobs)
    sched.add_job(
        func=lambda: bot.send_message(int(chat_id), "⏳ ¡Comienza el sorteo programado!") or bot.send_message(int(chat_id), "/sortear"),
        trigger='date',
        run_date=run_at,
        id=job_id
    )
