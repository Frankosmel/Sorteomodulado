# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from zoneinfo import ZoneInfo
from storage import load, save
from config import FILES

sched = BackgroundScheduler()
JOBS_FILE = FILES['jobs']

# Asegura que exista jobs.json
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")


def load_jobs(bot):
    """
    Carga todos los jobs programados desde el JSON y los
    añade al scheduler. Arranca el scheduler al final.
    """
    jobs = load('jobs')
    for job_id, job in jobs.items():
        chat_id = job['chat_id']
        run_at  = datetime.fromisoformat(job['run_at'])
        sched.add_job(
            func=lambda jid=job_id: _run_scheduled_draw(bot, jid),
            trigger='date',
            run_date=run_at,
            id=job_id
        )
        print(f"[Scheduler] Cargando job {job_id} → {run_at.isoformat()} en grupo {chat_id}")
    sched.start()
    print("[Scheduler] Scheduler iniciado y jobs cargados.")


def schedule_raffle(bot, chat_id: str, run_at: datetime):
    """
    Programa un sorteo para un chat dado en la fecha/hora `run_at`.
    Guarda en jobs.json y añade al scheduler.
    """
    jobs   = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        "run_at":  run_at.isoformat()
    }
    save('jobs', jobs)

    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, job_id),
        trigger='date',
        run_date=run_at,
        id=job_id
    )
    print(f"[Scheduler] Programando job {job_id} → {run_at.isoformat()} en grupo {chat_id}")


def _run_scheduled_draw(bot, job_id: str):
    """
    Función interna que ejecuta el sorteo programado:
    envía mensaje de inicio y luego dispara el comando /sortear.
    """
    jobs = load('jobs')
    job  = jobs.get(job_id)
    if not job:
        return
    chat_id = job['chat_id']
    bot.send_message(int(chat_id), "⏳ ¡Comienza el sorteo programado!")
    bot.send_message(int(chat_id), "/sortear")
    # opcional: eliminar job tras ejecución
    del jobs[job_id]
    save('jobs', jobs)
    try:
        sched.remove_job(job_id)
    except:
        pass
    print(f"[Scheduler] Ejecutando sorteo programado en grupo {chat_id}")


def set_group_timezone(chat_id: str, tz: str):
    """
    Guarda la zona horaria para un grupo en grupos.json.
    Esta zona se usará para interpretar los horarios de /agendar_sorteo.
    """
    # valida la zona
    ZoneInfo(tz)

    grupos = load('grupos')
    info   = grupos.setdefault(str(chat_id), {
        'activado_por': None,
        'creado':       datetime.utcnow().date().isoformat(),
    })
    info['timezone'] = tz
    save('grupos', grupos)
    print(f"[Scheduler] Zona horaria para grupo {chat_id} establecida a {tz}")
