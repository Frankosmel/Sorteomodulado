# auth.py

from datetime import datetime, timedelta
from storage import load, save
from config import VIGENCIA_DIAS

def is_valid(user_id: int) -> bool:
    """True si el usuario está autorizado y su plan no ha vencido."""
    auth = load('autorizados')
    info = auth.get(str(user_id))
    if not info:
        return False
    exp = datetime.fromisoformat(info['vence'])
    return datetime.utcnow() <= exp

def add_authorized(user_id: int, username: str, plan: str):
    """
    Registra un nuevo usuario autorizado.
    - user_id: ID de Telegram
    - username: @usuario
    - plan: nombre de plan (Básico, Dúo, Trío, Trimestre Básico, …)
    """
    auth = load('autorizados')
    now = datetime.utcnow()
    exp = now + timedelta(days=VIGENCIA_DIAS if "1 mes" in plan else VIGENCIA_DIAS*3)
    auth[str(user_id)] = {
        'nombre':    username,
        'username':  username,
        'plan':      plan,
        'pago':      now.date().isoformat(),
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
    plan = info.get('plan', 'Básico')
    # límites según plan
    limites = {
        'Básico': 1, 'Dúo': 2, 'Trío': 3,
        'Trimestre Básico': 1, 'Trimestre Dúo': 2, 'Trimestre Trío': 3
    }
    max_grupos = limites.get(plan, 1)
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
