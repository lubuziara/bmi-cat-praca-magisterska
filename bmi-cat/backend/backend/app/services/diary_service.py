from app.database.models.app_preference import AppPreference
from fastapi import HTTPException
from sqlalchemy import select
from app.database.models.cat import Cat
from app.database.models.meal_entry import MealEntry
from app.services.food_catalog import DEMO_FOOD, DEFAULT_KCAL


class DiaryService:
    def __init__(self, session, user_id):
        self.session = session
        self.user_id = user_id
        self.cat = session.scalar(select(Cat).where(Cat.owner_id == user_id).order_by(Cat.id))
        if self.cat is None:
            raise HTTPException(404, 'Najpierw dodaj profil kota.')

    def read(self, day):
        rows = self.session.scalars(select(MealEntry).where(
            MealEntry.cat_id == self.cat.id, MealEntry.day == day).order_by(MealEntry.id)).all()
        totals = {key: 0.0 for key in ('kcal', 'protein', 'fat', 'carbs')}
        entries = []
        for row in rows:
            nutrients = {key: DEMO_FOOD[key] * row.grams / 100 for key in totals}
            for key in totals:
                totals[key] += nutrients[key]
            entries.append({'id': row.id, 'name': DEMO_FOOD['name'], 'food_id': row.food_id,
                            'period': row.period, 'grams': row.grams,
                            **{key: round(value, 2) for key, value in nutrients.items()}})
        return {'day': day, 'cat_name': self.cat.name, 'entries': entries,
                'totals': {key: round(value, 2) for key, value in totals.items()},
                'target_kcal': (self.session.get(AppPreference, self.user_id).target_kcal
                    if self.session.get(AppPreference, self.user_id) else DEFAULT_KCAL), 'foods': [DEMO_FOOD]}

    def add(self, data):
        self.session.add(MealEntry(cat_id=self.cat.id, **data.model_dump()))
        self.session.commit()
        return self.read(data.day)

    def remove(self, entry_id):
        entry = self.session.scalar(select(MealEntry).where(
            MealEntry.id == entry_id, MealEntry.cat_id == self.cat.id))
        if entry is None:
            raise HTTPException(404, 'Nie znaleziono posiłku.')
        day = entry.day
        self.session.delete(entry)
        self.session.commit()
        return self.read(day)
