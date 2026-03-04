import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_ph.hash, password)


async def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*, False for any failure.

    Handles all argon2-cffi exception variants to avoid 500 errors on
    malformed stored hashes.
    """
    try:
        return await asyncio.to_thread(_ph.verify, hashed, plain)
    except VerifyMismatchError, VerificationError, InvalidHashError:
        return False
