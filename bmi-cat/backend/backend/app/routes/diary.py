from datetime import date
from fastapi import APIRouter, Depends
from app.dependencies.get_verified_user import get_verified_user
from app.dependencies.get_auth_service import get_auth_service
from app.schemas.meal_input import MealInput
from app.services.diary_service import DiaryService

router = APIRouter()


@router.get('/diary')
def read_diary(day: date, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DiaryService(auth.session, user['id']).read(day)


@router.post('/diary', status_code=201)
def add_meal(data: MealInput, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DiaryService(auth.session, user['id']).add(data)


@router.post('/diary/{entry_id}/remove')
def remove_meal(entry_id: int, user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    return DiaryService(auth.session, user['id']).remove(entry_id)
