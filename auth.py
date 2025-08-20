# auth.py

from datetime import datetime, timedelta
from storage import load, save
from config import PLANS

def is_valid(user_id: int) -> bool:
    """True si el usuario está autorizado y su plan no ha vencido."""
    auth = load('autorizados')
    info = auth.get(str(user_id))
    if not info:
        return False
    try:
        exp = datetime.fromisoformat(info['vence'])
    except Exception:
        return False
    return datetime.utcnow() <= exp

def add_authorized(user_id: int, username: str, plan_key: str):
    """Registra o renueva un usuario con plan y vencimiento según configuración."""
    plan = next((p for p in PLANS if p['key'] == plan_key), None)
    if not plan:
        raise ValueError(f"Plan desconocido: {plan_key}")

    duration = plan.get('duration_days', 30)
    now = datetime.utcnow()
    exp = now + timedelta(days=duration)

    auth = load('autorizados')
    auth[str(user_id)] = {
        'nombre':    username,
        'username':  username,
        'plan':      plan_key,
        'pago':      now.isoformat(),
        'vence':     exp.isoformat()
    }
    save('autorizados', auth)

def remove_authorized(user_id: int) -> bool:
    """Quita la autorización; devuelve True si existía."""
    auth = load('autorizados')
    if str(user_id) in auth:
        del auth[str(user_id)]
        save('autorizados', auth)
        return True
    return False

def list_authorized() -> dict:
    """Devuelve el dict completo de autorizados."""
    return load('autorizados')

def get_info(user_id: int) -> dict | None:
    return load('autorizados').get(str(user_id))

def remaining_days(user_id: int) -> int:
    info = get_info(user_id)
    if not info:
        return -1
    try:
        delta = datetime.fromisoformat(info['vence']) - datetime.utcnow()
        return max(delta.days, 0)
    except Exception:
        return -1

def register_group(chat_id: int, added_by: int):
    """
    Registra el grupo si el usuario aún no supera su cuota.
    Lanza ValueError si ya tiene el máximo de grupos.
    """
    auth = load('autorizados')
    info = auth.get(str(added_by))
    if not info:
        raise ValueError("Usuario no autorizado")

    plan_key = info.get('plan')
    limits = {
        'plan_1m1g': 1,
        'plan_1m2g': 2,
        'plan_1m3g': 3,
        'plan_3m3g': 3
    }
    max_grupos = limits.get(plan_key, 1)

    grupos = load('grupos')
    actuales = sum(1 for g in grupos.values() if g.get('activado_por') == added_by)
    if actuales >= max_grupos:
        raise ValueError("Límite de grupos alcanzado")

    grupos.setdefault(str(chat_id), {
        'activado_por': added_by,
        'creado':       datetime.utcnow().date().isoformat()
    })
    save('grupos', grupos)
