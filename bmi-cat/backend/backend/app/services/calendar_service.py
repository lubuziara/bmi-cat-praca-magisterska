from datetime import date
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, func
from app.database.models.calendar_record import CalendarRecord
from app.database.models.meal_entry import MealEntry
from app.services.diary_service import DiaryService
from app.services.food_catalog import DEMO_FOOD


class CalendarService:
    def __init__(self, session, user_id):
        self.session = session
        self.cat = DiaryService(session, user_id).cat

    def serialize(self, row):
        return dict(id=row.id, key=row.source_key, day=row.day.isoformat(),
                    occurred_at=row.occurred_at, kind=row.kind, title=row.title, details=row.details)

    def read(self, start=date.min, end=date.max):
        records = self.session.scalars(select(CalendarRecord).where(
            CalendarRecord.cat_id == self.cat.id, CalendarRecord.day >= start,
            CalendarRecord.day <= end)).all()
        events = [self.serialize(row) for row in records]
        meals = self.session.execute(select(MealEntry.day, func.sum(MealEntry.grams)).where(
            MealEntry.cat_id == self.cat.id, MealEntry.day >= start, MealEntry.day <= end
        ).group_by(MealEntry.day)).all()
        for day, grams in meals:
            totals = {key: round(DEMO_FOOD[key] * grams / 100, 2) for key in ('kcal', 'protein', 'fat', 'carbs')}
            events.append(dict(id=None, key=f'meal-{day}', day=day.isoformat(), occurred_at=None,
                               kind='nutrition', title=f"Żywienie: {totals['kcal']:g} kcal", details=totals))
        return sorted(events, key=lambda event: (event['day'], event['occurred_at'] or '', event['key']))

    def add(self, data):
        row = CalendarRecord(cat_id=self.cat.id, source_key=f'event-{uuid4().hex}',
            day=data.occurred_at.date(), occurred_at=data.occurred_at.isoformat(),
            kind=data.kind, title=data.title, details={'note': data.note})
        self.session.add(row)
        self.session.commit()
        return self.serialize(row)

    def remove(self, record_id):
        row = self.session.scalar(select(CalendarRecord).where(
            CalendarRecord.id == record_id, CalendarRecord.cat_id == self.cat.id))
        if row is None:
            raise HTTPException(404, 'Nie znaleziono wydarzenia.')
        if row.kind == 'document':
            raise HTTPException(409, 'Usuń dokument w bibliotece dokumentacji.')
        self.session.delete(row)
        self.session.commit()
        return {'ok': True}
