from fastapi import APIRouter, Depends, Request
from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_bearer import get_bearer
from app.services.verification_service import VerificationService
from app.schemas.verification_request import VerificationRequest
from app.schemas.send_verification_request import SendVerificationRequest

router = APIRouter()


@router.post("/verification/send")
def send_verification(request: Request, data: SendVerificationRequest, token=Depends(get_bearer), auth=Depends(get_auth_service)):
    user = auth.current_user(token)
    service = VerificationService(auth.session, user["id"])
    request.app.state.limiter.check("verification", request, user["email"])
    return service.send(data.channel, request.app.state.mailer, request.app.state.sms)
