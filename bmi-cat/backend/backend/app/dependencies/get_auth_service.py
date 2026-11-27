from fastapi import Request
from app.services.auth_service import AuthService


def get_auth_service(request: Request):
    with request.app.state.database.sessions() as session:
        yield AuthService(session, request.app.state.settings)
