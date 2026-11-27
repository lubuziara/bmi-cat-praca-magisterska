from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        settings = request.app.state.settings
        direct_ip = request.client.host if request.client else ""
        forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
        trusted_https = direct_ip in settings.trusted_proxies and forwarded_proto == "https"
        secure_request = request.url.scheme == "https" or trusted_https
        if settings.environment == "production" and not secure_request:
            response = JSONResponse(status_code=400, content={"detail": "HTTPS jest wymagany."})
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), geolocation=(), microphone=(), payment=(), usb=()"
        # Keeps Google popup flows working while isolating this origin.
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
        response.headers["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        response.headers["X-Frame-Options"] = "DENY"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
