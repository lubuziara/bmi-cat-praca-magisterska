from contextlib import asynccontextmanager
from app.services.calendar_sync_worker import CalendarSyncWorker


@asynccontextmanager
async def app_lifespan(app):
    worker = CalendarSyncWorker(app.state.database, app.state.settings)
    app.state.calendar_sync = worker
    worker.start()
    try:
        yield
    finally:
        worker.stop()
