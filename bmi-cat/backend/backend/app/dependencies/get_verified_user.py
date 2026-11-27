from fastapi import Depends, HTTPException
from app.dependencies.get_auth_service import get_auth_service
from app.dependencies.get_bearer import get_bearer
from app.database.models.owner_profile import OwnerProfile


def get_verified_user(token=Depends(get_bearer), auth=Depends(get_auth_service)):
    user = auth.current_user(token)
    profile = auth.session.get(OwnerProfile, user["id"])
    if not profile or not (profile.email_verified and profile.phone_verified):
        raise HTTPException(403, "Potwierdź e-mail i telefon, aby korzystać z tej funkcji.")
    return user
