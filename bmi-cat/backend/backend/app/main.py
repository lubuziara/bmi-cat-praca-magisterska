from app.routes import diary, health, calendar_connections
from app.services.app_lifespan import app_lifespan
from app.middleware.request_size_limit import RequestSizeLimit
from app.routes import registered_profile, verification_status, send_verification, confirm_verification
from app.services.sms_sender import SmsSender
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.middleware.validation_error_handler import validation_error_handler
from app.middleware.safe_error_handler import safe_error_handler
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.database.database import Database
from app.security.rate_limiter import create_rate_limiter
from app.services.mailer import Mailer
from app.middleware.security_headers import SecurityHeaders
from app.routes import login, register, forgot_password, reset_password, google_login, me, logout, refresh, two_factor, passkeys, sessions, security_events


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    app = FastAPI(title="BMI Cat API", version="0.1.0", lifespan=app_lifespan)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, safe_error_handler)
    app.state.settings = settings
    app.state.database = Database(settings.database_url)
    app.state.database.initialize()
    app.state.mailer = Mailer(settings)
    app.state.sms = SmsSender(settings)
    app.state.limiter = create_rate_limiter(settings)
    app.add_middleware(RequestSizeLimit)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=True, allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-BMI-Client"])
    app.add_middleware(SecurityHeaders)
    for route in [calendar_connections, health, diary, login, register, forgot_password, reset_password, google_login, me, logout, refresh, two_factor, passkeys, sessions, security_events, verification_status, send_verification, confirm_verification, registered_profile]:
        app.include_router(route.router, prefix="/api/auth", tags=["auth"])
    return app

