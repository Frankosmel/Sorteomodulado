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
    exp = datetime.fromisoformat(info['vence'])
    return datetime.utcnow() <= exp

def add_authorized(user_id: int, username: str, plan_key: str):
    """
    Registra un nuevo usuario autorizado.
    - user_id: ID de Telegram
    - username: @usuario
    - plan_key: clave del plan, e.g. 'plan_1m1g'
    """
    # Buscamos el plan en la configuración
    plan = next((p for p in PLANS if p['key'] == plan_key), None)
    if not plan:
        raise ValueError(f"Plan desconocido: {plan_key}")

    # Determinamos duración en días
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
    # límites según plan_key
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

    # registrar
    grupos.setdefault(str(chat_id), {
        'activado_por': added_by,
        'creado':       datetime.utcnow().date().isoformat()
    })
    save('grupos', grupos)
