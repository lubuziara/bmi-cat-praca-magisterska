from fastapi import APIRouter, Depends, Request
from app.dependencies.get_auth_service import get_auth_service
from app.services.auth_service import AuthService
from app.dependencies.get_bearer import get_bearer

router = APIRouter()


@router.get("/me")
def me(request: Request, token: str = Depends(get_bearer), auth: AuthService = Depends(get_auth_service)):
    return auth.current_user(token)
