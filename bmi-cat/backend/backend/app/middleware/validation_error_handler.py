from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Nie odsyłamy wartości pól (zwłaszcza haseł) w odpowiedzi walidacyjnej.
    return JSONResponse(status_code=422, content={"detail": "Sprawdź poprawność wpisanych danych.",
        "fields": [str(error["loc"][-1]) for error in exc.errors()]})
