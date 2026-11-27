from fastapi import APIRouter, Depends
from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_bearer import get_bearer
from app.schemas.mfa_requests import MfaReauthRequest
router = APIRouter()
@router.get('/sessions')
def list_sessions(token: str = Depends(get_bearer), auth=Depends(get_auth_service)): return auth.sessions(token)
@router.delete('/sessions/{session_id}')
def revoke_session(session_id: str, token: str = Depends(get_bearer), auth=Depends(get_auth_service)): return auth.revoke_session(token, session_id) or {'message': 'Sesja unieważniona.'}
@router.post('/sessions/revoke-others')
def revoke_others(data: MfaReauthRequest, token: str = Depends(get_bearer), auth=Depends(get_auth_service)):
    user = auth.user_for_access(token)
    auth._require_reauthentication(user, data.password, data.google_id_token, data.code)
    return auth.revoke_others(token) or {'message': 'Pozostałe sesje unieważnione.'}
