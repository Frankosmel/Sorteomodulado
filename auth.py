# auth.py

from datetime import datetime, timedelta
from storage import load, save
from config import VIGENCIA_DIAS

def is_valid(user_id: int) -> bool:
    """
    Comprueba si un usuario está autorizado y su suscripción no ha vencido.
    
    :param user_id: ID de Telegram del usuario.
    :return: True si existe en autorizados.json y hoy <= fecha de vencimiento.
    """
    auth = load('autorizados')
    info = auth.get(str(user_id))
    if not info:
        return False
    try:
        exp = datetime.fromisoformat(info['vence'])
    except Exception:
        return False
    return datetime.utcnow() <= exp

def add_authorized(user_id: int, activado_por: int) -> None:
    """
    Añade un usuario al listado de autorizados con fecha de vencimiento y registro.
    
    :param user_id: ID de Telegram a autorizar.
    :param activado_por: ID de quien realiza la autorización.
    """
    auth = load('autorizados')
    now = datetime.utcnow()
    vence = now + timedelta(days=VIGENCIA_DIAS)
    auth[str(user_id)] = {
        'activado_por': activado_por,
        'pago': now.date().isoformat(),
        'vence': vence.isoformat()
    }
    save('autorizados', auth)

def remove_authorized(user_id: int) -> bool:
    """
    Elimina un usuario del listado de autorizados.
    
    :param user_id: ID de Telegram a desautorizar.
    :return: True si existía y fue eliminado, False si no estaba.
    """
    auth = load('autorizados')
    uid = str(user_id)
    if uid in auth:
        del auth[uid]
        save('autorizados', auth)
        return True
    return False

def list_authorized() -> dict:
    """
    Devuelve el diccionario completo de autorizados.
    
    Cada clave es el user_id (str) y el valor un dict con:
      - activado_por: quien autorizó
      - pago: fecha ISO de activación
      - vence: fecha ISO de vencimiento
    
    :return: contenido de autorizados.json
    """
    return load('autorizados')

def register_group(chat_id: int, activado_por: int) -> None:
    """
    Registra que un usuario activó el bot en un grupo.
    
    :param chat_id: ID del chat/grupo.
    :param activado_por: ID del usuario que autorizó el grupo.
    """
    gr = load('grupos')
    key = str(chat_id)
    now = datetime.utcnow().date().isoformat()
    gr.setdefault(key, {
        'activado_por': activado_por,
        'creado': now
    })
    save('grupos', gr)
