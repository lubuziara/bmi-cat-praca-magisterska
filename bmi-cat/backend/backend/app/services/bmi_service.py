from fastapi import HTTPException
from sqlalchemy import select
from app.database.models.calendar_record import CalendarRecord
from app.services.calendar_service import CalendarService


class BmiService:
    def __init__(self, session, user_id):
        self.calendar = CalendarService(session, user_id)
        self.session = session

    def calculate(self, data):
        # Original prototype formula, estimating body fat (%), not human BMI.
        value = ((data.chest_cm / 0.7062 - data.leg_cm) / 0.9156) - data.leg_cm
        if not 0 < value < 100:
            raise HTTPException(422, 'Wynik poza zakresem 0–100%. Sprawdź obwód klatki i długość odcinka nogi według ilustracji.')
        key = f'bmi-{data.occurred_at.date()}'
        row = self.session.scalar(select(CalendarRecord).where(
            CalendarRecord.cat_id == self.calendar.cat.id, CalendarRecord.source_key == key))
        if row is None:
            row = CalendarRecord(cat_id=self.calendar.cat.id, source_key=key, kind='bmi')
            self.session.add(row)
        row.day = data.occurred_at.date()
        row.occurred_at = data.occurred_at.isoformat()
        row.title = f'Pomiar FBMI: {value:.1f}%'
        row.details = {'chest_cm': data.chest_cm, 'leg_cm': data.leg_cm, 'value': round(value, 2)}
        self.session.commit()
        return self.calendar.serialize(row)
