from fastapi import APIRouter, Depends, Request, Response
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.schemas.google_request import GoogleRequest
from app.services.google_auth_service import GoogleAuthService
from app.security.web_session import is_web_client, web_session_payload

router = APIRouter()


@router.post("/google")
def google_login(request: Request, response: Response, data: GoogleRequest, auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("login", request)
    result = GoogleAuthService(auth).login(data.id_token, request)
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result
