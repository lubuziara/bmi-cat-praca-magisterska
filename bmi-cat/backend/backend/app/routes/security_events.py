from fastapi import APIRouter, Depends, Query
from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_bearer import get_bearer
from app.services.security_event_service import SecurityEventService
router = APIRouter()
@router.get('/security-events')
def events(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), token: str = Depends(get_bearer), auth=Depends(get_auth_service)):
    user = auth.user_for_access(token)
    return [{'id': e.id, 'event_type': e.event_type, 'created_at': e.created_at, 'success': e.success, 'severity': e.severity, 'client_type': e.client_type, 'device': e.device} for e in SecurityEventService(auth.session).list(user.id, offset, limit)]
