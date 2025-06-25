from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from storage import load, save
from config import FILES
from draw_handlers import do_draw  # Importa la función que ejecuta el sorteo

# Inicializa el scheduler en UTC para evitar errores de zona
sched = BackgroundScheduler(timezone="UTC")

JOBS_FILE = FILES.get("jobs", "jobs.json")

# Asegura que exista jobs.json
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")

def load_jobs(bot):
    """
    Carga y programa todos los jobs guardados en jobs.json.
    """
    jobs = load('jobs')
    for job_id, job in jobs.items():
        run_time = datetime.fromisoformat(job['run_at'])
        print(f"[Scheduler] Cargando job {job_id} para {run_time} en grupo {job['chat_id']}")
        sched.add_job(
            func=lambda chat_id=job['chat_id']: _run_scheduled_draw(bot, chat_id),
            trigger='date',
            run_date=run_time,
            id=job_id
        )
    sched.start()
    print("[Scheduler] Scheduler iniciado y jobs cargados.")

def schedule_raffle(bot, chat_id: str, run_at: datetime):
    """
    Programa (y persiste) un nuevo sorteo para chat_id en la fecha/hora run_at.
    """
    jobs = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        "run_at": run_at.isoformat()
    }
    save('jobs', jobs)
    print(f"[Scheduler] Programando job {job_id} para {run_at} en grupo {chat_id}")
    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, chat_id),
        trigger='date',
        run_date=run_at,
        id=job_id
    )

def _run_scheduled_draw(bot, chat_id):
    """
    Job que se ejecuta al llegar la fecha: anuncia y ejecuta el sorteo.
    """
    print(f"[Scheduler] Ejecutando sorteo programado en grupo {chat_id}")
    bot.send_message(int(chat_id), "⏳ ¡Comienza el sorteo programado!")
    do_draw(bot, chat_id)
