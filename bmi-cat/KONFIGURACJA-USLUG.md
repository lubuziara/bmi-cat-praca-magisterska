# Baza danych, e-mail i SMS

Flutter (web i Android) łączy się z FastAPI. Backend korzysta z bazy i usług
wysyłających wiadomości. Klucze i hasła usług pozostają w głównym `.env`,
nie w kodzie ani zasobach Fluttera.

## Baza danych

Obecna konfiguracja korzysta z SQLite. Faktyczne położenie pliku określa
`BMI_DATABASE_URL` w głównym `.env`. Zachowujemy istniejące dane.
Tabele obejmują użytkowników, profile właścicieli, koty, tokeny oraz wyzwania
weryfikacyjne. Baza przechowuje hashe haseł.

Polecenie `python tools/init_database.py`, uruchomione w środowisku backendu,
tworzy brakujące tabele i sprawdza integralność SQLite. Nie usuwa rekordów
i nie zastępuje migracji przy przyszłych zmianach istniejących tabel.

## E-mail — Brevo przez istniejącą obsługę SMTP

1. Utwórz konto Brevo i skonfiguruj zweryfikowanego nadawcę oraz domenę
   zgodnie z instrukcjami panelu.
2. W panelu SMTP pobierz login SMTP i wygeneruj klucz SMTP.
3. Uzupełnij istniejące pola w głównym `.env`:

```dotenv
BMI_MAIL_MODE=smtp
BMI_SMTP_HOST=smtp-relay.brevo.com
BMI_SMTP_PORT=587
BMI_SMTP_USER=LOGIN_Z_PANELU_SMTP
BMI_SMTP_PASSWORD=KLUCZ_SMTP_NIE_KLUCZ_API
BMI_MAIL_FROM=ZWERYFIKOWANY_ADRES_NADAWCY
```

4. Uruchom ponownie backend. Obecny kod używa STARTTLS na porcie 587.
5. Sprawdź potwierdzenie rejestracji i odzyskiwanie hasła na własnym koncie.
   Dostarczenie wiadomości wymaga sprawnej konfiguracji konta i nadawcy.

Do czasu konfiguracji zostaje `BMI_MAIL_MODE=local`: pliki `.eml` trafiają
do katalogu określonego przez `BMI_OUTBOX_DIR`, bez wysyłki do odbiorców.

Dokumentacja: https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP

## SMS — proponowany dostawca SMSAPI

Aktualnie działa wyłącznie lokalny tryb testowy, zgodnie z wcześniejszym
ustaleniem. Pliki z kodami trafiają do `BMI_SMS_OUTBOX_DIR`.

Do rzeczywistej wysyłki potrzebne będą konto SMSAPI, token API z uprawnieniem
wysyłania SMS, skonfigurowany nadawca i środki na wysyłkę zgodnie z warunkami
dostawcy. Po wyborze usługi trzeba dodać adapter SMSAPI w backendzie oraz
obsługę błędów dostawcy. Samo wpisanie tokenu do `.env` jeszcze nie uruchomi SMS.
Nie wprowadzamy obecnie nieobsługiwanych pól ani nie wysyłamy płatnych SMS-ów.

Dokumentacja: https://www.smsapi.pl/docs
