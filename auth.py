# auth.py

from datetime import datetime, timedelta
from storage import load, save
from config import FILES, PLANS

AUTH_FILE = FILES["autorizados"]

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
    Registra un nuevo usuario autorizado según plan_key.
    - user_id: ID de Telegram
    - username: '@usuario'
    - plan_key: clave de plan en PLANS
    """
    # Buscar plan en config
    plan = next((p for p in PLANS if p["key"] == plan_key), None)
    if not plan:
        raise ValueError(f"Plan {plan_key} no existe")
    now = datetime.utcnow()
    duration = plan.get("duration_days", 30)
    exp = now + timedelta(days=duration)

    auth = load('autorizados')
    auth[str(user_id)] = {
        'nombre':    username,
        'username':  username,
        'plan_key':  plan_key,
        'plan_label':plan['label'],
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
    plan_key = info['plan_key']
    # determinar max_groups desde PLANS
    plan = next((p for p in PLANS if p["key"]==plan_key), {})
    max_grupos = plan.get("max_groups", 1)

    grupos = load('grupos')
    actuales = sum(1 for g in grupos.values() if g.get('activado_por')==added_by)
    if actuales >= max_grupos:
        raise ValueError("Límite de grupos alcanzado")
    # registrar
    grupos.setdefault(str(chat_id), {
        'activado_por': added_by,
        'creado':       datetime.utcnow().date().isoformat()
    })
    save('grupos', grupos)
