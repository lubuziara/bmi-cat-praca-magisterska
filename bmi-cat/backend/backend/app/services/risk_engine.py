import time
from dataclasses import dataclass
from sqlalchemy import select
from app.database.models.security_event import SecurityEvent
from app.security.client_ip import resolve_client_ip

@dataclass(frozen=True)
class RiskResult:
    score: int
    level: str
    signals: tuple[str, ...]
    action: str

class RiskEngine:
    WEIGHTS = {
        'new_device': 25, 'new_ip': 10, 'platform_changed': 15,
        'failed_login': 30, 'failed_mfa': 30, 'recent_recovery_code': 15,
        'refresh_token_reuse': 90,
        'mfa_success': -20, 'passkey': -30,
    }
    THRESHOLDS = ((85, 'critical', 'block'), (60, 'high', 'strong_step_up'),
                  (30, 'medium', 'step_up'), (0, 'low', 'allow'))
    WINDOW_SECONDS = 24 * 60 * 60

    def __init__(self, session, settings=None): self.session, self.settings = session, settings

    @staticmethod
    def _platform(user_agent: str) -> str:
        value = user_agent.lower()
        for name in ('android', 'windows', 'iphone', 'ipad', 'macintosh', 'linux'):
            if name in value: return name
        return 'other'

    def evaluate(self, user_id: int, *, request=None, auth_method='password', mfa_used=False) -> RiskResult:
        now = int(time.time())
        events = self.session.scalars(select(SecurityEvent).where(
            SecurityEvent.user_id == user_id, SecurityEvent.created_at >= now - self.WINDOW_SECONDS
        )).all()
        ua = request.headers.get('user-agent', '')[:255] if request else ''
        ip = resolve_client_ip(request, self.settings) if request else None
        successful = [e for e in events if e.event_type in ('login_success', 'passkey_login_success') and e.success]
        signals = []
        known_ips = {e.ip for e in successful if e.ip}
        # No durable server-side device binding exists yet. IP and User-Agent
        # must not turn an unverified client into a trusted device.
        if successful: signals.append('new_device')
        if successful and ip and ip not in known_ips: signals.append('new_ip')
        platforms = {self._platform(e.user_agent or '') for e in successful}
        if successful and ua and self._platform(ua) not in platforms: signals.append('platform_changed')
        if sum(e.event_type == 'login_failed' for e in events) >= 3: signals.append('failed_login')
        if sum(e.event_type == 'mfa_failed' for e in events) >= 2: signals.append('failed_mfa')
        if any(e.event_type == 'recovery_code_used' for e in events): signals.append('recent_recovery_code')
        if any(e.event_type == 'refresh_token_reuse_detected' for e in events): signals.append('refresh_token_reuse')
        if auth_method == 'passkey': signals.append('passkey')
        if mfa_used: signals.append('mfa_success')
        score = max(0, min(100, sum(self.WEIGHTS[s] for s in signals)))
        level, action = next((level, action) for threshold, level, action in self.THRESHOLDS if score >= threshold)
        return RiskResult(score, level, tuple(signals), action)
