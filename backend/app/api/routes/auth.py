import secrets
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.dependencies import get_current_user_required, get_users_repo
from app.core.config import Settings
from app.core.constants import AUTH_ACCESS_COOKIE, AUTH_REFRESH_COOKIE
from app.core.exceptions import NotAuthorizedError
from app.core.jwk import GOOGLE_AUTH_BASE
from app.core.rate_limit import LIMITER
from app.repositories.protocols import UserRepository
from app.schemas.responses import TokenResponse, UserResponse
from app.schemas.user import User
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, token_resp: TokenResponse, settings: Settings) -> None:
    response.set_cookie(
        key=AUTH_ACCESS_COOKIE,
        value=token_resp.access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        path="/api",
    )
    if token_resp.refresh_token:
        response.set_cookie(
            key=AUTH_REFRESH_COOKIE,
            value=token_resp.refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/auth",
        )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        AUTH_ACCESS_COOKIE,
        path="/api",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        AUTH_ACCESS_COOKIE,
        path="/",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        AUTH_REFRESH_COOKIE,
        path="/api/auth",
        secure=not settings.DEBUG,
        httponly=True,
        samesite="lax",
    )


def _google_redirect_uri(settings: Settings) -> str:
    return f"{settings.BACKEND_URL}/api/auth/callback/google"


@router.get("/login/google", operation_id="loginGoogle")
@LIMITER.limit("10/minute")
async def login_google(request: Request) -> RedirectResponse:
    settings = request.app.state.settings
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    request.session["oauth_nonce"] = nonce
    params = urlencode(
        {
            "response_type": "code",
            "scope": "openid email profile",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": _google_redirect_uri(settings),
            "state": state,
            "nonce": nonce,
        }
    )
    return RedirectResponse(f"{GOOGLE_AUTH_BASE}?{params}")


@router.get(
    "/callback/google",
    name="authCallbackGoogle",
    operation_id="authCallbackGoogle",
)
@LIMITER.limit("10/minute")
async def auth_callback_google(
    request: Request,
    users: Annotated[UserRepository, Depends(get_users_repo)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    settings = request.app.state.settings
    frontend = settings.FRONTEND_URL
    expected_state = request.session.pop("oauth_state", None)
    expected_nonce = request.session.pop("oauth_nonce", None)

    if error or not code:
        return RedirectResponse(f"{frontend}/login?error=oauth_denied")

    if (
        expected_state is None
        or state is None
        or not secrets.compare_digest(state, expected_state)
    ):
        return RedirectResponse(f"{frontend}/login?error=oauth_invalid_state")

    try:
        token_resp = await auth_service.google_callback(
            users,
            code,
            _google_redirect_uri(settings),
            nonce=expected_nonce,
            app_settings=settings,
        )
    except NotAuthorizedError:
        return RedirectResponse(f"{frontend}/login?error=oauth_failed")

    response = RedirectResponse(f"{frontend}/")
    _set_auth_cookies(response, token_resp, settings)
    return response


@router.post(
    "/refresh",
    status_code=204,
    operation_id="refreshToken",
)
@LIMITER.limit("10/minute")
async def refresh_token(
    request: Request,
    users: Annotated[UserRepository, Depends(get_users_repo)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias=AUTH_REFRESH_COOKIE)] = None,
) -> Response:
    settings = request.app.state.settings
    if not refresh_token_cookie:
        response = JSONResponse({"detail": "Authentication required"}, status_code=401)
        _clear_auth_cookies(response, settings)
        return response

    try:
        token_resp = await auth_service.refresh(users, refresh_token_cookie, app_settings=settings)
    except NotAuthorizedError as exc:
        response = JSONResponse({"detail": exc.detail}, status_code=401)
        _clear_auth_cookies(response, settings)
        return response

    response = Response(status_code=204)
    _set_auth_cookies(response, token_resp, settings)
    return response


@router.get(
    "/me",
    response_model=UserResponse,
    operation_id="getCurrentUser",
)
@LIMITER.limit("20/minute")
async def get_current_user(
    request: Request,
    user: Annotated[User, Depends(get_current_user_required)],
) -> UserResponse:
    """Return the authenticated user from the access token."""
    return UserResponse(id=user.id, email=user.email)


@router.post(
    "/logout",
    status_code=204,
    operation_id="logout",
)
async def logout(request: Request) -> Response:
    settings = request.app.state.settings
    response = Response(status_code=204)
    _clear_auth_cookies(response, settings)
    return response
