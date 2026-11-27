import time
from app.database.models.security_event import SecurityEvent
from app.security.client_ip import resolve_client_ip
class SecurityEventService:
    allowed_metadata = {'reason', 'provider', 'client_type', 'risk_level', 'signals'}
    def __init__(self, session): self.session = session
    def record(self, user_id, event_type, *, session_id=None, success=True, severity='info', metadata=None, request=None):
        safe = {k: v for k, v in (metadata or {}).items() if k in self.allowed_metadata and isinstance(v, (str, int, bool))}
        self.session.add(SecurityEvent(user_id=user_id, session_id=session_id, event_type=event_type, created_at=int(time.time()), success=success, severity=severity, ip=resolve_client_ip(request) if request else None, user_agent=request.headers.get('user-agent', '')[:255] if request else None, client_type='web' if request and request.headers.get('x-bmi-client') == 'web' else 'other', metadata_json=safe))
    def list(self, user_id, offset=0, limit=50):
        from sqlalchemy import select
        return self.session.scalars(select(SecurityEvent).where(SecurityEvent.user_id == user_id).order_by(SecurityEvent.created_at.desc(), SecurityEvent.id.desc()).offset(offset).limit(min(limit, 100))).all()
