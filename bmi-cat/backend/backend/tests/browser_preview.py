"""Isolated API fixture for frontend/test/browser/health_flow.cjs.

Run from the workspace: python outputs/bmi-cat/backend/tests/browser_preview.py
Never connects to the application's normal database or external mail services.
"""
import sys
from pathlib import Path
import uvicorn
from PIL import Image, ImageDraw, ImageFont

backend = Path(__file__).resolve().parents[1]
workspace = backend.parents[2]
sys.path.insert(0, str(backend))
from app.main import create_app
from app.config import Settings
from app.database.models.owner_profile import OwnerProfile
from fastapi.testclient import TestClient
from test_registration import ACCOUNT


def main():
    folder = workspace / 'work/health-preview'
    folder.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (1200, 1600), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(backend.parent / 'frontend/assets/fonts/roboto-regular.ttf'), 36)
    draw.rectangle((60, 60, 1140, 180), fill='#eadcf5')
    for index, line in enumerate(['BMI Cat - DOKUMENT TESTOWY', 'Przykladowa wizyta kontrolna',
                                  'Kot: Luna', 'To syntetyczny dokument do testu aplikacji.',
                                  'Nie zawiera danych medycznych.']):
        draw.text((90, 100 + index * 100), line, font=font, fill='#392744')
    image.save(folder / 'scan.png')
    app = create_app(Settings(database_url=f'sqlite:///{folder / "preview.db"}',
                              outbox_dir=str(folder / 'mail'), sms_outbox_dir=str(folder / 'sms'), _env_file=None))
    with TestClient(app) as client:
        response = client.post('/api/auth/register', json={**ACCOUNT, 'email': 'health-preview@example.com'})
        if response.status_code == 201:
            with app.state.database.sessions() as session:
                owner = session.get(OwnerProfile, response.json()['user']['id'])
                owner.email_verified = owner.phone_verified = True
                session.commit()
    uvicorn.run(app, host='127.0.0.1', port=8002)


if __name__ == '__main__':
    main()
