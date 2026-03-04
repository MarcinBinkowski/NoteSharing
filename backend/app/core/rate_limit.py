from slowapi import Limiter
from slowapi.util import get_ipaddr

LIMITER = Limiter(
    key_func=get_ipaddr,
    default_limits=["60/minute"],
)
