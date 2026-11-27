from fastapi import APIRouter, Depends, Request, Response, HTTPException
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.schemas.login_request import LoginRequest
from app.security.web_session import is_web_client, web_session_payload

router = APIRouter()


@router.post("/login")
def login(request: Request, response: Response, data: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    subject = str(data.email).strip().lower()
    request.app.state.limiter.check("login", request, subject)
    try:
        result = auth.login(data, request)
    except HTTPException as error:
        if error.status_code == 401: request.app.state.limiter.failure("login", subject)
        raise
    request.app.state.limiter.success("login", subject)
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result
