from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.database.models.user import User
from app.database.models.auth_token import AuthToken


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def by_email(self, email: str):
        return self.session.scalar(select(User).where(User.email == email))

    def by_google_subject(self, subject: str):
        return self.session.scalar(select(User).where(User.google_subject == subject))

    def create(self, **fields):
        user = User(**fields)
        self.session.add(user)
        self.session.flush()
        return user

    def revoke_tokens(self, user_id: int, purpose: str | None = None):
        query = delete(AuthToken).where(AuthToken.user_id == user_id)
        if purpose:
            query = query.where(AuthToken.purpose == purpose)
        self.session.execute(query)
