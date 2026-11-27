from app.database.models.app_preference import AppPreference
from app.database.models.user import User
from app.database.models.owner_profile import OwnerProfile
from app.services.diary_service import DiaryService


class PreferencesService:
    def __init__(self, session, user_id):
        self.session = session
        self.user_id = user_id
        self.cat = DiaryService(session, user_id).cat

    def read(self):
        user = self.session.get(User, self.user_id)
        owner = self.session.get(OwnerProfile, self.user_id)
        prefs = self.session.get(AppPreference, self.user_id)
        return dict(first_name=user.first_name, last_name=owner.last_name,
                    cat_name=self.cat.name, email=user.email, phone=owner.phone,
                    notifications=prefs.notifications if prefs else True,
                    target_kcal=prefs.target_kcal if prefs else 200)

    def save(self, data):
        prefs = self.session.get(AppPreference, self.user_id)
        if prefs is None:
            prefs = AppPreference(user_id=self.user_id)
            self.session.add(prefs)
        prefs.notifications = data.notifications
        prefs.target_kcal = data.target_kcal
        self.session.get(User, self.user_id).first_name = data.first_name
        self.session.get(OwnerProfile, self.user_id).last_name = data.last_name
        self.cat.name = data.cat_name
        self.session.commit()
        return self.read()
