from datetime import datetime, timedelta
from storage import load, save
from config import VIGENCIA_DIAS

def is_valid(user_id):
    """
    Devuelve True si el usuario está autorizado y su plan no ha vencido.
    """
    auth = load('autorizados')
    info = auth.get(str(user_id))
    if not info:
        return False
    exp = datetime.fromisoformat(info['vence'])
    return datetime.utcnow() <= exp

def add_authorized(user_id, nombre, plan):
    """
    Registra un nuevo usuario autorizado con vigencia de VIGENCIA_DIAS días.
    """
    auth = load('autorizados')
    now = datetime.utcnow()
    exp = now + timedelta(days=VIGENCIA_DIAS)
    auth[str(user_id)] = {
        'nombre': nombre,
        'plan': plan,
        'pago': now.date().isoformat(),
        'vence': exp.isoformat()
    }
    save('autorizados', auth)

def register_group(chat_id, added_by):
    """
    Guarda en qué grupos está activo el bot y quién lo activó.
    """
    gr = load('grupos')
    gr.setdefault(str(chat_id), {
        'activado_por': added_by,
        'creado': datetime.utcnow().date().isoformat()
    })
    save('grupos', gr)
