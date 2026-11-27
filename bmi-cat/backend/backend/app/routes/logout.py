from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.security.web_session import REFRESH_COOKIE, clear_web_session_cookies, is_web_client, require_csrf

router = APIRouter()


@router.post("/logout")
def logout(request: Request, response: Response, auth: AuthService = Depends(get_auth_service)):
    if is_web_client(request):
        require_csrf(request)
        raw = request.cookies.get(REFRESH_COOKIE)
        if not raw:
            raise HTTPException(401, "Zaloguj się, aby kontynuować.")
        result = auth.logout_refresh(raw)
        clear_web_session_cookies(response, auth.settings)
        return result
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Zaloguj się, aby kontynuować.")
    return auth.logout(authorization[7:])
