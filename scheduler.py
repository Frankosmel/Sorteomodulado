from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from storage import load, save
from config import FILES
from draw_handlers import do_draw
from zoneinfo import ZoneInfo

# Archivos de datos
JOBS_FILE  = FILES["jobs"]
GROUPS_FILE = FILES["grupos"]

# Inicializar Scheduler (sin timezone global)
sched = BackgroundScheduler()

# Asegura que exista jobs.json
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")

# Asegura que exista grupos.json
try:
    with open(GROUPS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(GROUPS_FILE, 'w') as f:
        f.write("{}")


def get_group_timezone(chat_id: str) -> str:
    """
    Lee la zona horaria configurada para el grupo, o 'UTC' por defecto.
    """
    groups = load('grupos')
    info = groups.get(chat_id, {})
    return info.get('timezone', 'UTC')


def set_group_timezone(chat_id: str, tz_name: str):
    """
    Actualiza la zona horaria para un grupo en grupos.json.
    """
    groups = load('grupos')
    groups.setdefault(chat_id, {})
    groups[chat_id]['timezone'] = tz_name
    save('grupos', groups)


def load_jobs(bot):
    """
    Carga y programa todos los jobs guardados en jobs.json.
    """
    jobs = load('jobs')
    for job_id, job in jobs.items():
        run_time = datetime.fromisoformat(job['run_at'])
        print(f"[Scheduler] Cargando job {job_id} → {run_time} en grupo {job['chat_id']}")
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
    Programa (y persiste) un nuevo sorteo para chat_id en la fecha/hora run_at,
    usando la zona horaria configurada para ese grupo.
    """
    tz_name = get_group_timezone(chat_id)
    run_at_tz = run_at.replace(tzinfo=ZoneInfo(tz_name))

    jobs = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at_tz.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        "run_at": run_at_tz.isoformat()
    }
    save('jobs', jobs)

    print(f"[Scheduler] Programando job {job_id} → {run_at_tz} en grupo {chat_id}")
    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, chat_id),
        trigger='date',
        run_date=run_at_tz,
        id=job_id
    )


def _run_scheduled_draw(bot, chat_id: str):
    """
    Job que se ejecuta al llegar la fecha: anuncia y ejecuta el draw.
    """
    print(f"[Scheduler] Ejecutando sorteo programado en grupo {chat_id}")
    bot.send_message(int(chat_id), "⏳ ¡Comienza el sorteo programado!")
    do_draw(bot, chat_id)
