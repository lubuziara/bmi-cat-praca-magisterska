import hmac
import secrets

from fastapi import HTTPException, Request, Response

REFRESH_COOKIE = "bmi_refresh"
CSRF_COOKIE = "bmi_csrf"
WEB_CLIENT_HEADER = "X-BMI-Client"


def is_web_client(request: Request) -> bool:
    return request.headers.get(WEB_CLIENT_HEADER) == "web"


def require_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(403, "Nieprawidłowy token CSRF.")


def set_web_session_cookies(response: Response, refresh_token: str, settings) -> None:
    cookie_options = {
        "max_age": settings.refresh_seconds,
        "path": "/api/auth",
        "secure": settings.cookie_secure,
        "samesite": "lax",
    }
    response.set_cookie(REFRESH_COOKIE, refresh_token, httponly=True, **cookie_options)
    response.set_cookie(CSRF_COOKIE, secrets.token_urlsafe(32), httponly=False, **cookie_options)


def clear_web_session_cookies(response: Response, settings) -> None:
    cookie_options = {"path": "/api/auth", "secure": settings.cookie_secure, "samesite": "lax"}
    response.delete_cookie(REFRESH_COOKIE, httponly=True, **cookie_options)
    response.delete_cookie(CSRF_COOKIE, httponly=False, **cookie_options)


def web_session_payload(response: Response, data: dict, settings) -> dict:
    if "refresh_token" not in data:
        return data
    set_web_session_cookies(response, data["refresh_token"], settings)
    return {key: value for key, value in data.items() if key not in {"refresh_token", "refresh_expires_in"}}
