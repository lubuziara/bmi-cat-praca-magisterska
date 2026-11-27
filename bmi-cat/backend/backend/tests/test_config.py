import json
from pathlib import Path
from dotenv import dotenv_values
from app.config import Settings
from app.services.flutter_config import FlutterConfig


def test_root_env_is_independent_of_working_directory(tmp_path, monkeypatch):
    expected = Path(__file__).resolve().parents[2] / ".env"
    assert Path(Settings.model_config["env_file"]) == expected
    (tmp_path / ".env").write_text("BMI_GOOGLE_CLIENT_ID=wrong-directory", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BMI_GOOGLE_CLIENT_ID", raising=False)
    assert Settings().google_client_id == dotenv_values(expected).get("BMI_GOOGLE_CLIENT_ID", "")


def test_flutter_exports_only_public_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BMI_GOOGLE_CLIENT_ID=public-client\nBMI_SMTP_PASSWORD=private-password\nBMI_FUTURE_API_KEY=private-api-key\nBMI_API_BASE_URL=https://api.example.com\nBMI_ANDROID_API_BASE_URL=https://mobile.example.com\n", encoding="utf-8")
    settings = Settings(_env_file=env_file)
    assert settings.smtp_password == "private-password"
    output = tmp_path / "generated" / "public.json"
    FlutterConfig(settings).write(output)
    assert json.loads(output.read_text(encoding="utf-8")) == {
        "API_BASE_URL": "https://api.example.com", "GOOGLE_WEB_CLIENT_ID": "public-client"}
    assert "private" not in output.read_text(encoding="utf-8")
    FlutterConfig(settings).write(output, "android")
    assert json.loads(output.read_text(encoding="utf-8"))["API_BASE_URL"] == "https://mobile.example.com"
