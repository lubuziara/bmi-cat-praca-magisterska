from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import delete
from app.dependencies.get_verified_user import get_verified_user
from app.dependencies.get_auth_service import get_auth_service
from app.database.models.calendar_connection import CalendarConnection
from app.database.models.calendar_oauth_state import CalendarOAuthState
from app.services.calendar_oauth_service import CalendarOAuthService

router = APIRouter()


@router.get('/calendar-connections')
def connections(request: Request, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    oauth = CalendarOAuthService(auth.session, request.app.state.settings)
    result = []
    for provider in ['google', 'outlook']:
        connection = auth.session.get(CalendarConnection, (user['id'], provider))
        result.append(dict(provider=provider, configured=oauth.configured(provider), connected=connection is not None,
                           error=connection.error if connection else None,
                           last_sync=connection.last_sync if connection else None))
    return {'connections': result}


@router.post('/calendar-connections/{provider}/connect')
def connect(provider: str, request: Request, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return CalendarOAuthService(auth.session, request.app.state.settings).start(provider, user['id'])


@router.get('/calendar-connections/{provider}/callback', response_class=HTMLResponse)
def callback(provider: str, request: Request, state: str, code: str | None = None, error: str | None = None):
    # OAuth opens a separate browser tab; only the single-use state links it to a user.
    with request.app.state.calendar_sync.lock, request.app.state.database.sessions() as session:
        try:
            CalendarOAuthService(session, request.app.state.settings).finish(provider, state, code, error)
        except HTTPException:
            return HTMLResponse('<html lang="pl"><meta charset="utf-8"><h1>Nie połączono kalendarza</h1><p>Odmówiono dostępu, połączenie wygasło lub dostawca nie odpowiedział. Wróć do BMI Cat i spróbuj ponownie.</p></html>', status_code=400)
    return HTMLResponse('<html lang="pl"><meta charset="utf-8"><h1>Kalendarz połączony</h1><p>Możesz zamknąć tę kartę i wrócić do BMI Cat. Synchronizacja rozpocznie się w ciągu minuty.</p></html>')


@router.post('/calendar-connections/{provider}/disconnect')
def disconnect(provider: str, request: Request, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    CalendarOAuthService(auth.session, request.app.state.settings).config(provider)
    with request.app.state.calendar_sync.lock:
        auth.session.execute(delete(CalendarConnection).where(CalendarConnection.user_id == user['id'], CalendarConnection.provider == provider))
        auth.session.execute(delete(CalendarOAuthState).where(CalendarOAuthState.user_id == user['id'], CalendarOAuthState.provider == provider))
        auth.session.commit()
    return {'ok': True}
