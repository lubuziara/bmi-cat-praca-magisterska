import base64
from sqlalchemy import select
from fastapi import HTTPException
from app.database.models.medical_document import MedicalDocument
from app.database.models.calendar_record import CalendarRecord
from app.services.calendar_service import CalendarService
from app.services.image_pdf_converter import ImagePdfConverter


class DocumentService:
    def __init__(self, session, user_id):
        self.session = session
        self.calendar = CalendarService(session, user_id)
        self.cat_id = self.calendar.cat.id

    def read(self):
        # Do not select image/PDF blobs when listing the library.
        rows = self.session.execute(select(MedicalDocument.id, MedicalDocument.title,
            MedicalDocument.occurred_at).where(MedicalDocument.cat_id == self.cat_id)
            .order_by(MedicalDocument.id.desc())).all()
        return {'documents': [dict(row._mapping) for row in rows]}

    def get(self, document_id):
        row = self.session.scalar(select(MedicalDocument).where(
            MedicalDocument.id == document_id, MedicalDocument.cat_id == self.cat_id))
        if row is None:
            raise HTTPException(404, 'Nie znaleziono dokumentu.')
        return row

    def preview(self, document_id):
        row = self.get(document_id)
        return dict(id=row.id, title=row.title, occurred_at=row.occurred_at,
                    image_base64=base64.b64encode(row.preview).decode())

    def save(self, data):
        preview, pdf = ImagePdfConverter().convert(data.image_base64)
        row = MedicalDocument(cat_id=self.cat_id, title=data.title,
            occurred_at=data.occurred_at.isoformat(), preview=preview, pdf=pdf)
        self.session.add(row)
        self.session.flush()
        self.session.add(CalendarRecord(cat_id=self.cat_id, source_key=f'document-{row.id}',
            day=data.occurred_at.date(), occurred_at=row.occurred_at, kind='document',
            title=data.title, details={'document_id': row.id}))
        self.session.commit()
        return {'id': row.id, 'title': row.title}

    def remove(self, document_id):
        row = self.get(document_id)
        event = self.session.scalar(select(CalendarRecord).where(
            CalendarRecord.cat_id == self.cat_id, CalendarRecord.source_key == f'document-{row.id}'))
        if event:
            self.session.delete(event)
        self.session.delete(row)
        self.session.commit()
        return {'ok': True}
