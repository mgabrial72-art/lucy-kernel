"""
Helper centralizado para timezone de Sao Paulo.
Usa zoneinfo (biblioteca padrao do Python 3.9+), sem depender de pytz.
"""
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    import pytz
    SAO_PAULO_TZ = pytz.timezone("America/Sao_Paulo")

def now_sp():
    """Retorna datetime atual no timezone de Sao Paulo."""
    return datetime.now(SAO_PAULO_TZ)
