from jwt import PyJWKClient

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

GOOGLE_JWK_CLIENT = PyJWKClient(GOOGLE_JWKS_URL, cache_jwk_set=True, lifespan=3600)
