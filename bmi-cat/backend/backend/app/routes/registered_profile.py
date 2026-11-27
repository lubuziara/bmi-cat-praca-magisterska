from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_verified_user import get_verified_user
from app.database.models.owner_profile import OwnerProfile
from app.database.models.cat import Cat

router = APIRouter()


@router.get("/profile")
def registered_profile(user=Depends(get_verified_user), auth=Depends(get_auth_service)):
    profile = auth.session.get(OwnerProfile, user["id"])
    cat = auth.session.scalar(select(Cat).where(Cat.owner_id == user["id"]).order_by(Cat.id))
    return {"owner": {**user, "last_name": profile.last_name, "gender": profile.gender,
                      "birth_date": profile.birth_date, "phone": profile.phone},
            "cat": {"id": cat.id, "name": cat.name, "gender": cat.gender, "birth_date": cat.birth_date,
                    "estimated_age_months": cat.estimated_age_months, "age_recorded_on": cat.age_recorded_on,
                    "avatar": cat.avatar} if cat else None}
