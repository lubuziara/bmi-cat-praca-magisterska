from fastapi import APIRouter, Depends, Request, Response

from app.dependencies.get_auth_service import get_auth_service
from app.schemas.refresh_request import RefreshRequest
from app.services.auth_service import AuthService
from app.security.web_session import REFRESH_COOKIE, is_web_client, require_csrf, web_session_payload
from app.security.token_digest import token_digest

router = APIRouter()


@router.post("/refresh")
def refresh_session(request: Request, response: Response, data: RefreshRequest | None = None,
                    auth: AuthService = Depends(get_auth_service)):
    if is_web_client(request):
        require_csrf(request)
        raw = request.cookies.get(REFRESH_COOKIE)
        if not raw:
            from fastapi import HTTPException
            raise HTTPException(401, "Sesja wygasła. Zaloguj się ponownie.")
        request.app.state.limiter.check("refresh", request, token_digest(raw))
        return web_session_payload(response, auth.refresh_session(raw), auth.settings)
    if data is None:
        from fastapi import HTTPException
        raise HTTPException(422, "Brak refresh tokenu.")
    request.app.state.limiter.check("refresh", request, token_digest(data.refresh_token))
    return auth.refresh_session(data.refresh_token)
