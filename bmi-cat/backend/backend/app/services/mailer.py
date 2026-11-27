from email.message import EmailMessage
from pathlib import Path
import secrets
import smtplib
import ssl
from app.config import Settings


class Mailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_reset(self, email: str, token: str):
        settings = self.settings
        message = EmailMessage()
        message["Subject"] = "BMI Cat — ustaw nowe hasło"
        message["From"] = settings.mail_from
        message["To"] = email
        # Fragment nie trafia do logów serwera HTTP ani nagłówka Referer.
        link = f"{settings.frontend_url.rstrip('/')}/#/reset-password?token={token}"
        message.set_content(f"Aby ustawić nowe hasło, otwórz:\n{link}\n\nLink jest ważny przez 30 minut i działa raz.\nJeśli nie prosisz o zmianę hasła, zignoruj wiadomość.")
        if settings.mail_mode == "local":
            if settings.environment == "production":
                raise ValueError("Local mail outbox is unavailable in production")
            directory = Path(settings.outbox_dir)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{secrets.token_hex(12)}.eml").write_bytes(message.as_bytes())
            return
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)

    def send_verification(self, email: str, code: str):
        message = EmailMessage()
        message["Subject"] = "BMI Cat — potwierdź rejestrację"
        message["From"] = self.settings.mail_from
        message["To"] = email
        message.set_content(f"Twój kod potwierdzenia rejestracji: {code}\nKod jest ważny przez 10 minut.\n")
        if self.settings.mail_mode == "local":
            if self.settings.environment == "production":
                raise ValueError("Local mail outbox is unavailable in production")
            directory = Path(self.settings.outbox_dir)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"verify-{secrets.token_hex(12)}.eml").write_bytes(message.as_bytes())
            return
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if self.settings.smtp_user:
                smtp.login(self.settings.smtp_user, self.settings.smtp_password)
            smtp.send_message(message)
