from fastapi import APIRouter, Depends, Request, Response, HTTPException
from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_bearer import get_bearer
from app.security.web_session import is_web_client, web_session_payload
from app.services.passkey_service import PasskeyService, challenge_fingerprint
from app.schemas.mfa_requests import MfaReauthRequest

router = APIRouter()
def user(auth, token): return auth.user_for_access(token)
@router.post('/passkeys/register/options')
def register_options(request: Request, data: MfaReauthRequest, token: str = Depends(get_bearer), auth=Depends(get_auth_service)):
    current = user(auth, token)
    request.app.state.limiter.check('passkey', request, str(current.id))
    auth._require_reauthentication(current, data.password, data.google_id_token, data.code)
    return PasskeyService(auth.session, auth.settings).registration_options(current)
@router.post('/passkeys/register/verify')
def register_verify(request: Request, data: dict, token: str = Depends(get_bearer), auth=Depends(get_auth_service)):
    current = user(auth, token); request.app.state.limiter.check('passkey', request, str(current.id)); return PasskeyService(auth.session, auth.settings).registration_verify(current, data['credential'], data.get('name'))
@router.post('/passkeys/login/options')
def login_options(request: Request, auth=Depends(get_auth_service)):
    request.app.state.limiter.check('passkey', request)
    return PasskeyService(auth.session, auth.settings).login_options()
@router.post('/passkeys/login/verify')
def login_verify(request: Request, response: Response, data: dict, auth=Depends(get_auth_service)):
    request.app.state.limiter.check('passkey', request, challenge_fingerprint(data.get('credential')))
    result = auth.complete_primary_login(PasskeyService(auth.session, auth.settings).login_verify(data['credential'], request=request), auth_method='passkey', request=request)
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result
@router.post('/step-up/passkey/options')
def step_up_options(request: Request, data: dict, auth=Depends(get_auth_service)):
    request.app.state.limiter.check('step_up', request, data.get('step_up_challenge', ''))
    return auth.step_up_passkey_options(data.get('step_up_challenge', ''))
@router.post('/step-up/passkey/verify')
def step_up_verify(request: Request, response: Response, data: dict, auth=Depends(get_auth_service)):
    request.app.state.limiter.check('step_up', request, data.get('step_up_challenge', ''))
    result = auth.step_up_passkey_verify(data.get('step_up_challenge', ''), data.get('credential'))
    return web_session_payload(response, result, auth.settings) if is_web_client(request) else result
@router.get('/passkeys')
def list_keys(token: str = Depends(get_bearer), auth=Depends(get_auth_service)): return PasskeyService(auth.session, auth.settings).list(user(auth, token))

@router.delete('/passkeys/{passkey_id}')
def delete_key(passkey_id: int, request: Request, data: MfaReauthRequest, token: str = Depends(get_bearer), auth=Depends(get_auth_service)):
    request.app.state.limiter.check('passkey', request, str(passkey_id))
    current_user = user(auth, token)
    auth._require_reauthentication(current_user, data.password, data.google_id_token, data.code)
    return PasskeyService(auth.session, auth.settings).delete(current_user, passkey_id)
