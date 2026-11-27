import json
from pathlib import Path
from app.config import Settings


class FlutterConfig:
    """Jawna lista publicznych wartości. Nigdy nie eksportuj całego Settings/.env."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def write(self, output: Path, target: str = "web"):
        if target not in {"web", "android"}:
            raise ValueError("Nieobsługiwana platforma")
        public = {
            "API_BASE_URL": self.settings.android_api_base_url if target == "android" else self.settings.api_base_url,
            "GOOGLE_WEB_CLIENT_ID": self.settings.google_client_id,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(public, ensure_ascii=False), encoding="utf-8")
