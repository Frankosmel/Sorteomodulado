# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from storage import load, save
from config import FILES, VIGENCIA_DIAS

# --- Scheduler global con manejo de misfires/coalescing ---
sched = BackgroundScheduler(
    job_defaults={
        'coalesce': False,            # No juntar múltiples ejecuciones en una
        'misfire_grace_time': 3600    # Hasta 1 hora de gracia para ejecutar jobs perdidos
    }
)

JOBS_FILE = FILES["jobs"]  # ruta a jobs.json

# -------------------------------------------------------------------
#  Inicialización de jobs.json
# -------------------------------------------------------------------
try:
    with open(JOBS_FILE, 'r'):
        pass
except FileNotFoundError:
    with open(JOBS_FILE, 'w') as f:
        f.write("{}")

# -------------------------------------------------------------------
#  Carga y arranque inicial de jobs almacenados
# -------------------------------------------------------------------
def load_jobs(bot):
    """
    Carga los sorteos programados desde jobs.json y los encola en APScheduler.
    Debe llamarse al arrancar el bot.
    """
    jobs = load('jobs')
    for job_id, job in jobs.items():
        run_time = datetime.fromisoformat(job['run_at'])
        sched.add_job(
            func=lambda jid=job_id: _run_scheduled_draw(bot, jid),
            trigger='date',
            run_date=run_time,
            id=job_id,
            misfire_grace_time=3600
        )
    sched.start()
    print(f"[Scheduler] Scheduler iniciado y jobs cargados.")

# -------------------------------------------------------------------
#  Programación de un nuevo sorteo
# -------------------------------------------------------------------
def schedule_raffle(bot, chat_id: str, run_at: datetime):
    """
    Programa un nuevo sorteo para chat_id en la fecha run_at.
    
    - chat_id: string del ID de grupo.
    - run_at: un datetime AWARE (con tzinfo) o NAIVE que se asume en UTC.
    """
    # Convertir a UTC
    if run_at.tzinfo is not None:
        run_at_utc = run_at.astimezone(timezone.utc)
    else:
        run_at_utc = run_at.replace(tzinfo=timezone.utc)

    jobs = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at_utc.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        "run_at": run_at_utc.isoformat()
    }
    save('jobs', jobs)

    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, job_id),
        trigger='date',
        run_date=run_at_utc,
        id=job_id,
        misfire_grace_time=3600
    )
    print(f"[Scheduler] Programando job {job_id} → {run_at_utc} (UTC) para grupo {chat_id}")

# -------------------------------------------------------------------
#  Ejecución interna del sorteo programado
# -------------------------------------------------------------------
def _run_scheduled_draw(bot, job_id: str):
    """
    Helper interno que dispara el sorteo y lo anuncia en el grupo.
    Borra el job tras ejecutarlo.
    """
    jobs = load('jobs')
    job = jobs.get(job_id)
    if not job:
        return
    chat_id = job['chat_id']

    # … aquí tu lógica de sorteo (por ejemplo enviar "/sortear" o elección directa)

    # Eliminamos el job tras ejecutarlo
    del jobs[job_id]
    save('jobs', jobs)
    try:
        sched.remove_job(job_id)
    except:
        pass

# -------------------------------------------------------------------
#  Recordatorios de suscripción (5 días antes)
# -------------------------------------------------------------------
def reminder_job(bot):
    """
    Envía un aviso a cada usuario autorizado 5 días antes del vencimiento.
    Se ejecuta a diario (cron UTC).
    """
    auth = load('autorizados')
    ahora = datetime.utcnow().replace(tzinfo=timezone.utc)
    for uid, info in auth.items():
        vence = datetime.fromisoformat(info['vence'])
        if vence.tzinfo is None:
            vence = vence.replace(tzinfo=timezone.utc)
        dias_rest = (vence - ahora).days
        if dias_rest == 5:
            bot.send_message(
                int(uid),
                f"⏳ Tu suscripción vence en 5 días ({vence.date()}). "
                "Usa /misuscripciones para ver detalles o /admin para renovar."
            )

def start_reminders(bot):
    """
    Programa el job diario que ejecuta reminder_job cada medianoche UTC.
    Debe llamarse al arrancar el bot.
    """
    if not sched.get_job('daily_reminder'):
        sched.add_job(
            func=lambda: reminder_job(bot),
            trigger='cron',
            hour=0, minute=0,  # UTC
            id='daily_reminder',
            misfire_grace_time=3600
        )
    print(f"[Scheduler] Recordatorios programados (5 días antes).")

# -------------------------------------------------------------------
#  Gestión de zona horaria por grupo
# -------------------------------------------------------------------
def set_group_timezone(chat_id: str, tz: str):
    """
    Guarda la zona horaria para un grupo en grupos.json.
    - chat_id: ID del chat (string).
    - tz: identificador de ZoneInfo, p.ej. "America/Havana".
    """
    ZoneInfo(tz)  # valida
    grupos = load('grupos')
    info = grupos.setdefault(str(chat_id), {})
    info['timezone'] = tz
    save('grupos', grupos)
    print(f"[Scheduler] Zona horaria de grupo {chat_id} actualizada a {tz}")
