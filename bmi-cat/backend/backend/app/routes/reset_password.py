from fastapi import APIRouter, Depends, Request
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.schemas.reset_request import ResetRequest

router = APIRouter()


@router.post("/reset-password")
def reset_password(request: Request, data: ResetRequest, auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("reset", request)
    return auth.reset_password(data)
