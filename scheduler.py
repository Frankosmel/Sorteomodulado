from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from storage import load, save
from config import FILES, VIGENCIA_DIAS

# Scheduler global
sched = BackgroundScheduler()

# Ruta del fichero de jobs
JOBS_FILE = FILES["jobs"]

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
        # El run_at ya se guarda como ISO con zona o sin ella
        run_time = datetime.fromisoformat(job['run_at'])
        sched.add_job(
            func=lambda jid=job_id: _run_scheduled_draw(bot, jid),
            trigger='date',
            run_date=run_time,
            id=job_id
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
    
    La llamada típica vendrá de owner_handlers después de parsear la zona local.
    """
    # Convierte a UTC si viene con ZoneInfo
    if run_at.tzinfo is not None:
        run_at_utc = run_at.astimezone(timezone.utc)
    else:
        # sin tzinfo, lo tomamos ya en UTC
        run_at_utc = run_at.replace(tzinfo=timezone.utc)
    
    jobs = load('jobs')
    job_id = f"raffle_{chat_id}_{int(run_at_utc.timestamp())}"
    jobs[job_id] = {
        "chat_id": chat_id,
        # Guardamos ISO con offset UTC
        "run_at": run_at_utc.isoformat()
    }
    save('jobs', jobs)
    
    sched.add_job(
        func=lambda: _run_scheduled_draw(bot, job_id),
        trigger='date',
        run_date=run_at_utc,
        id=job_id
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
    # Anunciamos
    bot.send_message(int(chat_id), "⏳ ¡Comienza el sorteo programado!")
    bot.send_message(int(chat_id), "/sortear")
    # Eliminamos del scheduler y del JSON
    del jobs[job_id]
    save('jobs', jobs)
    try:
        sched.remove_job(job_id)
    except Exception:
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
            # asumimos ISO naive en UTC
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
    # Evitamos duplicar si ya existe
    if not sched.get_job('daily_reminder'):
        sched.add_job(
            func=lambda: reminder_job(bot),
            trigger='cron',
            hour=0, minute=0,  # UTC
            id='daily_reminder'
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
    # valida la zona
    ZoneInfo(tz)  # lanzará excepción si inválido
    grupos = load('grupos')
    info = grupos.setdefault(str(chat_id), {})
    info['timezone'] = tz
    save('grupos', grupos)
    print(f"[Scheduler] Zona horaria de grupo {chat_id} actualizada a {tz}")
