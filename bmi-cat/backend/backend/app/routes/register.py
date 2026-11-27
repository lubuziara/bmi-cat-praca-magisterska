from fastapi import APIRouter, Depends, Request, Response
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.schemas.register_request import RegisterRequest
from app.security.web_session import is_web_client, web_session_payload

router = APIRouter()


@router.post("/register", status_code=201)
def register(request: Request, response: Response, data: RegisterRequest, auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("passkey", request, str(data.email).strip().lower())
    result = auth.register(data)
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result
