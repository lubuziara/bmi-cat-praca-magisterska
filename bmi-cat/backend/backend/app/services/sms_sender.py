from pathlib import Path
import secrets
from fastapi import HTTPException


class FileSmsProvider:
    """Development/test-only SMS inbox."""
    def __init__(self, settings):
        self.directory = Path(settings.sms_outbox_dir)

    def send(self, phone: str, code: str):
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / f"{secrets.token_hex(12)}.txt").write_text(
            f"Do: {phone}\nBMI Cat: kod potwierdzenia {code}. Ważny 10 minut.\n", encoding="utf-8")


class SmsProviderNotConfigured:
    def send(self, phone: str, code: str):
        raise HTTPException(503, "Wysyłka SMS jest chwilowo niedostępna.")


class SmsSender:
    def __init__(self, settings):
        self.provider = FileSmsProvider(settings) if settings.sms_provider == "file" else SmsProviderNotConfigured()

    def send(self, phone: str, code: str):
        self.provider.send(phone, code)
