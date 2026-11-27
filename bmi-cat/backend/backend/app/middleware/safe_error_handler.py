import logging

from fastapi import Request
from fastapi.responses import JSONResponse


async def safe_error_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled API error")
    return JSONResponse(status_code=500, content={"detail": "Wystąpił błąd serwera. Spróbuj ponownie później."})
