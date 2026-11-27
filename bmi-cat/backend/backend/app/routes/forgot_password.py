from fastapi import APIRouter, Depends, Request
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.schemas.forgot_request import ForgotRequest

router = APIRouter()


@router.post("/forgot-password")
def forgot_password(request: Request, data: ForgotRequest, auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("forgot", request, str(data.email).strip().lower())
    return auth.request_reset(data, request.app.state.mailer)
