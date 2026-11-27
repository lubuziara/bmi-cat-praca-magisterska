from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.dependencies.get_verified_user import get_verified_user
from app.dependencies.get_auth_service import get_auth_service
from app.schemas.event_input import EventInput
from app.schemas.bmi_input import BmiInput
from app.schemas.document_input import DocumentInput
from app.schemas.preference_input import PreferenceInput
from app.services.calendar_service import CalendarService
from app.services.bmi_service import BmiService
from app.services.document_service import DocumentService
from app.services.preferences_service import PreferencesService

router = APIRouter()


@router.get('/calendar')
def calendar(start: date, end: date, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    if end < start or (end-start).days > 366:
        raise HTTPException(422, 'Wybierz zakres do 366 dni.')
    return {'events': CalendarService(auth.session, user['id']).read(start, end)}


@router.post('/calendar', status_code=201)
def add_event(data: EventInput, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return CalendarService(auth.session, user['id']).add(data)


@router.post('/calendar/{record_id}/remove')
def remove_event(record_id: int, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return CalendarService(auth.session, user['id']).remove(record_id)


@router.post('/bmi')
def bmi(data: BmiInput, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return BmiService(auth.session, user['id']).calculate(data)


@router.get('/documents')
def documents(user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DocumentService(auth.session, user['id']).read()


@router.post('/documents', status_code=201)
def save_document(data: DocumentInput, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DocumentService(auth.session, user['id']).save(data)


@router.get('/documents/{document_id}')
def preview_document(document_id: int, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DocumentService(auth.session, user['id']).preview(document_id)


@router.get('/documents/{document_id}/pdf')
def download_document(document_id: int, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    row = DocumentService(auth.session, user['id']).get(document_id)
    return Response(row.pdf, media_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="bmi-cat-dokument-{row.id}.pdf"'})


@router.post('/documents/{document_id}/remove')
def remove_document(document_id: int, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DocumentService(auth.session, user['id']).remove(document_id)


@router.get('/settings')
def settings(user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return PreferencesService(auth.session, user['id']).read()


@router.post('/settings')
def save_settings(data: PreferenceInput, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return PreferencesService(auth.session, user['id']).save(data)
