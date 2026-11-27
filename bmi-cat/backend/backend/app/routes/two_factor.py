from fastapi import APIRouter, Depends, Request, Response

from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_bearer import get_bearer
from app.schemas.mfa_requests import MfaReauthRequest, MfaVerifyRequest, SetupConfirmRequest
from app.services.auth_service import AuthService
from app.security.web_session import is_web_client, web_session_payload

router = APIRouter()


def _user(auth: AuthService, token: str):
    return auth.user_for_access(token)


@router.get("/2fa/status")
def status(token: str = Depends(get_bearer), auth: AuthService = Depends(get_auth_service)):
    return auth.mfa_status(_user(auth, token))


@router.post("/2fa/setup")
def setup(request: Request, data: MfaReauthRequest, token: str = Depends(get_bearer), auth: AuthService = Depends(get_auth_service)):
    current = _user(auth, token)
    request.app.state.limiter.check("passkey", request, str(current.id))
    return auth.mfa_setup(current, data.password, data.google_id_token, data.code)


@router.post("/2fa/confirm")
def confirm(request: Request, data: SetupConfirmRequest, token: str = Depends(get_bearer), auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("passkey", request, data.setup_challenge)
    return auth.mfa_confirm(_user(auth, token), data.setup_challenge, data.code)


@router.post("/2fa/verify")
def verify(request: Request, response: Response, data: MfaVerifyRequest, auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("mfa", request, data.mfa_challenge)
    try: result = auth.mfa_verify_login(data.mfa_challenge, data.code)
    except Exception: request.app.state.limiter.failure("mfa", data.mfa_challenge); raise
    request.app.state.limiter.success("mfa", data.mfa_challenge)
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result

@router.post("/step-up/verify")
def step_up_verify(request: Request, response: Response, data: dict, auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("step_up", request, data.get('step_up_challenge', ''))
    result = auth.step_up_mfa_verify(data.get('step_up_challenge', ''), data.get('code', ''))
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result


@router.post("/2fa/disable")
def disable(request: Request, data: MfaReauthRequest, token: str = Depends(get_bearer), auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("passkey", request, str(_user(auth, token).id))
    return auth.mfa_disable(_user(auth, token), data.password, data.google_id_token, data.code)


@router.post("/2fa/recovery/regenerate")
def regenerate(request: Request, data: MfaReauthRequest, token: str = Depends(get_bearer), auth: AuthService = Depends(get_auth_service)):
    request.app.state.limiter.check("passkey", request, str(_user(auth, token).id))
    return auth.mfa_regenerate_recovery(_user(auth, token), data.password, data.google_id_token, data.code)
