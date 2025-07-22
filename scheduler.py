# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from storage import load, save
from config import FILES
import random

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
    """
    # Convertir a UTC si viene con tzinfo
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
        id=job_id
    )
    print(f"[Scheduler] Programando job {job_id} → {run_at_utc} (UTC) para grupo {chat_id}")

# -------------------------------------------------------------------
#  Ejecución interna del sorteo programado
# -------------------------------------------------------------------
def _run_scheduled_draw(bot, job_id: str):
    """
    Helper interno que dispara el sorteo:
    - Selecciona un ganador al azar de los inscritos.
    - Envía mensaje al grupo.
    - Limpia la lista de sorteo y elimina el job.
    """
    jobs = load('jobs')
    job = jobs.get(job_id)
    if not job:
        return
    chat_id = job['chat_id']

    # Carga participantes
    sorteos = load('sorteo')
    participantes = sorteos.get(chat_id, {})
    if not participantes:
        bot.send_message(int(chat_id), "⚠️ No había participantes para el sorteo programado.")
    else:
        # Elegir ganador
        ganador_id, info = random.choice(list(participantes.items()))
        nombre = info.get('nombre', '')
        username = info.get('username')
        if username:
            menc = f"@{username}"
        else:
            menc = f"[{nombre}](tg://user?id={ganador_id})"
        
        # Anunciar
        bot.send_message(
            int(chat_id),
            f"🎉 *Ganador del sorteo programado:*\n\n"
            f"¡Felicidades {menc}! 🎊",
            parse_mode='Markdown'
        )

    # Limpiar la lista de ese chat
    if chat_id in sorteos:
        del sorteos[chat_id]
        save('sorteo', sorteos)

    # Eliminar job
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
    ZoneInfo(tz)  # valida zona o lanza excepción
    grupos = load('grupos')
    info = grupos.setdefault(str(chat_id), {})
    info['timezone'] = tz
    save('grupos', grupos)
    print(f"[Scheduler] Zona horaria de grupo {chat_id} actualizada a {tz}")
