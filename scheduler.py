# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from zoneinfo import ZoneInfo
from storage import load, save
from config import FILES

# Instancia global del scheduler
sched = BackgroundScheduler()

# Nombre del archivo de jobs
JOBS_FILE = FILES['jobs']

# Asegura que exista jobs.json al arrancar
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")


def load_jobs(bot):
    """
    Carga todos los jobs guardados en jobs.json y los programa de nuevo en el scheduler.
    Usa la zona horaria de cada grupo si está configurada en grupos.json.
    """
    jobs_data = load('jobs')
    grupos     = load('grupos')

    for job_id, job in jobs_data.items():
        chat_id = job['chat_id']
        run_at_iso = job['run_at']
        # Determina la zona horaria del grupo, por defecto UTC
        tz_name = grupos.get(str(chat_id), {}).get('timezone', 'UTC')
        tz = ZoneInfo(tz_name)

        # Parse ISO y asigna tz
        run_at = datetime.fromisoformat(run_at_iso)
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=tz)

        # Crea el trigger con fecha y zona
        trigger = DateTrigger(run_date=run_at, timezone=tz)

        # Función que dispara el sorteo programado
        def _job_action(chat=chat_id):
            bot.do_draw(int(chat))

        # Añade al scheduler
        sched.add_job(
            func=_job_action,
            trigger=trigger,
            id=job_id,
            replace_existing=True
        )

    sched.start()
    print(f"[Scheduler] Scheduler iniciado y {len(jobs_data)} jobs cargados.")


def schedule_raffle(bot, chat_id: int, run_at: datetime):
    """
    Programa un nuevo sorteo:
      - Crea un ID único por chat y timestamp.
      - Guarda en jobs.json.
      - Añade al scheduler en memoria.
    """
    jobs_data = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at.timestamp())}"

    # Guarda en almacenamiento persistente
    jobs_data[job_id] = {
        "chat_id": str(chat_id),
        "run_at":  run_at.isoformat()
    }
    save('jobs', jobs_data)

    # Recupera zona del grupo
    grupos = load('grupos')
    tz_name = grupos.get(str(chat_id), {}).get('timezone', 'UTC')
    tz = ZoneInfo(tz_name)

    # Asegura que run_at tenga tzinfo
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=tz)

    trigger = DateTrigger(run_date=run_at, timezone=tz)

    # Acción a ejecutar
    def _job_action():
        bot.do_draw(int(chat_id))

    sched.add_job(
        func=_job_action,
        trigger=trigger,
        id=job_id,
        replace_existing=True
    )

    print(f"[Scheduler] Programando job {job_id} → {run_at.isoformat()} en grupo {chat_id}")
