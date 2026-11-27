import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings


@pytest.fixture
def client(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", outbox_dir=str(tmp_path / 'outbox'), sms_outbox_dir=str(tmp_path / 'sms'), cookie_secure=False, mfa_totp_encryption_key=Fernet.generate_key().decode(), password_breach_check_enabled=False, _env_file=None))
    with TestClient(app) as client:
        yield client
    app.state.database.engine.dispose()
