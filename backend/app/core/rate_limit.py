from slowapi import Limiter
from slowapi.util import get_ipaddr

from app.core import config as app_config

LIMITER = Limiter(
    key_func=get_ipaddr,
    default_limits=[app_config.settings.RATE_LIMIT_DEFAULT],
)
