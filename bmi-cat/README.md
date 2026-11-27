# BMI Cat — karty 1–2: logowanie i rejestracja

Nowa baza projektu: **FastAPI + Flutter (web i Android)**. Oryginalny ZIP pozostaje bez zmian. Z poprzedniej aplikacji wykorzystano logo wiszącego kota `assets/pngegg.png`.

## Co działa

- E-mail i hasło, widoczność hasła, komunikaty błędów i stan oczekiwania.
- Rejestracja w trzech krokach: dane właściciela, dane kota i edytowalny avatar 3D, a następnie potwierdzenie e-maila i telefonu.
- Odzyskiwanie hasła i ustawienie nowego przez jednorazowy link.
- Prosty ekran potwierdzenia zalogowania i wylogowanie, aby sprawdzić cały przepływ.
- Jasnoróżowe tło, fioletowe zaokrąglone pola, oryginalne logo.
- Responsywny układ, przewijanie z klawiaturą, powiększanie tekstu, polskie etykiety i dostępne nazwy kontrolek.

**Google:** kod integracji web/Android i weryfikacja tokenu w API są przygotowane. Bez konfiguracji przycisk jest wyłączony i oznaczony „Google — wkrótce”. Nie wykonano logowania prawdziwym kontem Google; testy backendu zastępują weryfikator kontrolowanymi odpowiedziami.

**Poczta:** domyślnie wiadomości trafiają do lokalnych plików `.eml` w `outbox/`; nic nie jest wysyłane na prawdziwe adresy. Do rzeczywistej wysyłki trzeba ustawić SMTP. Lokalny folder poczty służy wyłącznie do developmentu i nie może być publicznie udostępniany.

## Karta 2 — dane właściciela i kota

Kreator zawiera:

1. **Właściciel:** imię, nazwisko, płeć (z opcją niepodawania), data urodzenia, telefon z kierunkowym kraju, e-mail, hasło i powtórzenie hasła.
2. **Kot:** imię, płeć (także „nie wiem”) oraz dokładna data urodzenia **albo** przybliżony wiek w latach i miesiącach. W bazie przybliżenie jest zapisywane w miesiącach wraz z datą pomiaru. Nie udajemy, że znamy dokładne urodziny znalezionego kota.
3. **Avatar 3D:** obracany, stylizowany model z rzeczywistą geometrią, renderowany bez dodatkowych serwisów i bez przesyłania danych na zewnątrz. Jest to model proceduralny Fluttera, a nie obrazek ani zewnętrzny plik GLB.

Domyślnie: biały, krótkowłosy kot dorosły, średnia sylwetka i zielone oczy. Do wyboru są wszystkie zamówione długości sierści, 10 umaszczeń, 10 wariantów oczu, kociak/kot dorosły i 5 sylwetek. „Trikolor” to drobne łaty, a „rudo-czarno-biały” to większe plamy — rozróżnienie przyjęte na potrzeby dwóch osobnych pozycji w briefie. Sierść i gabaryty zmieniają geometrię, a umaszczenie i oczy materiały modelu.

Po zatwierdzeniu rejestracji zapisujemy właściciela i kota w jednej transakcji. Wygląd trafia do `cats.avatar` jako ustawienia z `schema_version=1`. Po potwierdzeniu konta ten sam avatar jest odtwarzany na ekranie konta. Automatyczny wzrost i zmiany sylwetki według BMI, a także późniejszy edytor danych profilu, należą do następnego etapu.

### Potwierdzanie rejestracji

- E-mail i telefon wymagają osobnych 6-cyfrowych kodów.
- Każdy kod jest ważny 10 minut, ma 5 prób i działa raz. W bazie zapisujemy hash Argon2id, a nie kod.
- Nowy kod można wysłać po 60 sekundach; dodatkowy limit wynosi 6 wysyłek na konto w 10 minut.
- Nie wysyłamy kodów automatycznie po stworzeniu konta. Użytkownik wybiera „Wyślij kod e-mailem” i „Wyślij kod SMS”.
- Po obu potwierdzeniach włącza się „Przejdź do konta”. Ponowne logowanie konta oczekującego na weryfikację prowadzi z powrotem do ekranu potwierdzania.
- Nieweryfikowane konto ma sesję do dokończenia weryfikacji, ale endpoint pełnego profilu zwraca 403. `get_verified_user` jest wspólną kontrolą dostępu do przyszłych funkcji wymagających potwierdzenia. Dokumentacja medyczna nie została jeszcze zaimplementowana.

SMS działa **wyłącznie testowo**: pliki `.txt` trafiają do `backend/sms_outbox/` (ustawienie `BMI_SMS_OUTBOX_DIR` w głównym `.env`). Otwórz najnowszy plik i przepisz kod. Dla poczty lokalnej plik `verify-*.eml` trafia do katalogu `BMI_OUTBOX_DIR`. Żaden endpoint nie zwraca kodu. Dla SMTP używane są dotychczasowe ustawienia; integracja z dostawcą prawdziwych SMS-ów nie jest jeszcze dodana.

Nowe tabele: `owner_profiles`, `cats`, `verification_challenges`. Dodanie tabel nie zmienia ani nie kasuje istniejących użytkowników. Wykonano kopię lokalnej bazy przed uruchomieniem nowej wersji. Stare konta nie mają automatycznie wymyślonych danych właściciela i kota — pełny przepływ dotyczy nowych rejestracji.

Testy nowej karty: `backend/tests/test_registration.py` i `frontend/test/registration_test.dart`; kod modelu w `frontend/lib/features/avatar/`. Pozostałe testy pozostają w dotychczasowych folderach. Test obejmuje też przejście przez cały kreator, zmianę umaszczenia i zgodność danych przekazanych do API. Układ edytora sprawdzono przy 320 i 1100 px. Budowa Android APK nadal ma opisane niżej ograniczenie środowiska; nowej karty nie testowano na urządzeniu Android.

## Jeden plik konfiguracji

Edytuj wyłącznie **`bmi-cat/.env`**. `.env.example` jest pustym wzorem do odtworzenia konfiguracji, nie drugim aktywnym plikiem. Backend odnajduje główny `.env` niezależnie od katalogu uruchomienia. Usunięto dawny wzór `backend/.env.example`.

- `BMI_GOOGLE_CLIENT_ID`: publiczny identyfikator OAuth klienta WEB Google. Ten sposób logowania nie wymaga client secret ani ogólnego Google API key.
- `BMI_API_BASE_URL` / `BMI_ANDROID_API_BASE_URL`: adres API dla webu / Androida.
- `BMI_SMTP_*` i `BMI_MAIL_FROM`: konfiguracja rzeczywistej poczty.
- `BMI_DATABASE_URL`: połączenie z bazą. Obecny lokalny `.env` zachowuje bazę używaną przez podgląd.

`tools/export_flutter_config.py` tworzy ignorowany przez Git plik w `.dart_tool/` tylko z **dwoma publicznymi wartościami**: adresem API i Google Client ID. Nigdy nie przekazuj całego `.env` do Fluttera przez `--dart-define-from-file` i nie dodawaj `.env` do assets. Tajne klucze kolejnych usług pozostają w backendzie.

Po zmianie `.env`: zrestartuj API oraz uruchom `run-local.ps1 -Service BuildWeb` (dla statycznego podglądu) lub `WebDev`. Zmienne środowiskowe systemu mają standardowo pierwszeństwo przed `.env`, np. podczas wdrożenia.

## Struktura

```text
backend/
  app/
    routes/                  # osobny plik dla każdego endpointu
    schemas/                 # osobne modele danych wejściowych
    validation/              # reguły danych
    database/models/         # User, AuthToken
    database/crud/           # operacje na bazie
    services/                # logowanie, Google i poczta
    security/                # hashowanie i ograniczenie prób
    dependencies/            # sesja bazy i odczyt tokenu
    middleware/              # bezpieczne odpowiedzi
    main.py                  # składanie aplikacji
  tests/
frontend/
  lib/core/theme/            # wspólna stylistyka
  lib/features/auth/
    data/                    # klient API
    validation/              # walidatory formularzy
    widgets/                 # wspólne elementy interfejsu
    screens/                 # ekrany i osobne pliki ich stanu
  test/
```

Każda klasa i funkcja najwyższego poziomu kodu aplikacji ma osobny plik. Metody pozostają w swoich klasach. Zmianę wyglądu pól robimy w jednym motywie, a zmianę adresu serwera przez konfigurację, bez przepisywania ekranów.

## Uruchomienie na standardowej instalacji

Wymagania: Python 3.12+, Flutter z Dartem 3.6+, do Androida także Android SDK oraz JDK zgodny z Gradle. Projekt przygotowano i przetestowano na Flutterze 3.27 / Darcie 3.6.1; dlatego integracja Google używa wersji 6.2.2 zgodnej z tym SDK. Nie aktualizuj samego pakietu Google do 7.x bez migracji API Fluttera.

Backend — terminal w `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
# Jedyny .env jest w głównym katalogu bmi-cat.
# Jeśli go brakuje: Copy-Item ..\.env.example ..\.env
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --port 8000
```

Frontend — drugi terminal w głównym katalogu `bmi-cat/` (skrypt automatycznie odczyta `.env`):

```powershell
.\run-local.ps1 -Service WebDev
```

API: `http://localhost:8000/docs`. Nie ma domyślnego konta ani hasła — utwórz własne konto formularzem rejestracji. Dane developerskie są przechowywane w lokalnym SQLite.

Jeżeli na tym komputerze nie ma polecenia `python`, skrypty `run-local.ps1` mogą użyć środowiska pobranego podczas tej sesji Codex. Otwórz dwa terminale w katalogu tego README:

```powershell
.\run-local.ps1 -Service Api
.\run-local.ps1 -Service Web
```

Drugi skrypt serwuje skompilowaną wersję webową pod `http://localhost:5173`. Po zmianach kodu lub `.env` przebuduj ją przez `.\run-local.ps1 -Service BuildWeb` albo użyj `.\run-local.ps1 -Service WebDev`. Zrestartuj API po zmianach `.env`.

## Android

Emulator Androida widzi serwer komputera pod adresem `10.0.2.2`:

```powershell
# Z głównego katalogu projektu; adres emulatora pochodzi z .env.
.\run-local.ps1 -Service BuildAndroid
```

Na fizycznym telefonie użyj osiągalnego adresu serwera. Lokalny HTTP jest dopuszczony tylko w konfiguracji debug. Wydanie produkcyjne wymaga HTTPS, własnego podpisu APK i konfiguracji środowiska. Szablon podpisu debug nie jest podpisem do publikacji w sklepie.

## Reset hasła

W trybie lokalnym:

1. Utwórz konto i wybierz „Nie pamiętasz hasła?”.
2. Otwórz najnowszy plik `.eml` w `backend/outbox/` (w skrypcie Codex: `work/runtime/outbox/`).
3. Otwórz link w wiadomości i ustaw nowe hasło.
4. Stare hasło, stary link i wcześniejsze sesje przestają działać.

Link otwiera wersję webową również po żądaniu wysłanym z Androida. Natywne Android App Links można dodać po ustaleniu domeny.

Dla prawdziwej poczty ustaw `BMI_MAIL_MODE=smtp`, host, port 587, użytkownika, hasło i adres nadawcy. Połączenie używa STARTTLS. Ustaw również właściwe `BMI_FRONTEND_URL`.

## Konfiguracja Google

- Utwórz klienta OAuth typu web w swoim projekcie Google i wpisz dozwolony origin frontendu (lokalnie `http://localhost:5173`).
- Ustaw ten identyfikator w backendzie jako `BMI_GOOGLE_CLIENT_ID`.
- Skrypt `run-local.ps1` przekazuje ten sam identyfikator Flutterowi automatycznie. Nie wpisuj go ponownie w kodzie ani osobnym pliku.
- Logowanie Google jest nadal integracją przygotowaną do konfiguracji; uzupełnianie pełnego profilu kont utworzonych wcześniej lub przez Google pozostaje osobnym przepływem.
- Dla Androida dodaj klienta Android z nazwą pakietu `pl.bmicat.bmi_cat` i odciskiem SHA certyfikatu podpisującego. Identyfikator klienta web jest używany jako `serverClientId`.
- API weryfikuje podpis, termin ważności, odbiorcę tokenu i potwierdzenie e-maila. Nie łączy automatycznie istniejącego konta hasłowego tylko na podstawie e-maila.

Dokumentacja integracji: https://pub.dev/packages/google_sign_in/versions/6.2.2 oraz https://pub.dev/packages/google_sign_in_web/versions/0.12.4+4 .

## Podstawowe zabezpieczenia

- Argon2id dla haseł; wymagane 12–128 znaków przy rejestracji i zmianie hasła.
- Losowe tokeny sesji i resetowania; w bazie wyłącznie skróty SHA-256 tokenów.
- Sesja ważna godzinę, link resetujący 30 minut. Reset unieważnia wszystkie wcześniejsze tokeny użytkownika.
- Token sesji pozostaje tylko w pamięci aplikacji. Odświeżenie strony wymaga ponownego logowania; nie zapisujemy tokenów w localStorage.
- SQLAlchemy i parametryzowane zapytania, unikalny e-mail, minimalne odpowiedzi API.
- Walidacja po obu stronach; API nie odsyła treści niepoprawnych pól ani haseł.
- Ogólny błąd logowania i ogólna odpowiedź resetowania hasła.
- Limit 10 prób na minutę na IP i endpoint; CORS dopuszcza tylko skonfigurowane originy.
- Konfiguracja poza kodem, `.env`, bazy i lokalna poczta ignorowane przez Git.

To etap developerski. Zgodnie z planem użytkowniczki 2FA i pełne utwardzenie wdrożenia są później. Przed publikacją: konfiguracja HTTPS, prawdziwej poczty i dostawcy SMS, migracje zmian istniejącego schematu bazy, podpisy Androida i współdzielony limiter zamiast pamięci jednego procesu. SQLite i `create_all` służą pierwszej karcie, nie aktualizują istniejących schematów.

Argon2 jest również używany w oficjalnym przewodniku FastAPI: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ .

## Testy

```powershell
# backend/
python -m pytest -q
# frontend/
flutter analyze
flutter test
# Z głównego katalogu projektu:
.\run-local.ps1 -Service BuildWeb
```

Sprawdzone: **49 testów backendu i 17 testów Fluttera** oraz kompilacja webowa. Testy obejmują m.in. `666` w imieniu, imiona z polskimi znakami, e-maile, długość haseł, błędne logowanie, tokeny, wylogowanie, wygasanie i jednokrotne użycie resetu, walidację Google, CORS, limit prób oraz układ 320/390/768/1440 px i tekst 200% z klawiaturą. Podgląd wizualny: `frontend/test/goldens/login.png`.

Testy API zgłaszają dwa ostrzeżenia o wycofywanych interfejsach zależności Starlette/httpx/anyio; nie są to nieudane testy.

## Wynik weryfikacji Androida w tej sesji

Kompilacja APK **nie zakończyła się sukcesem**. Zainstalowano brakujące Android SDK Platform 35 i Build-Tools 33.0.1, ale kompilator Javy zgłosił `AccessDeniedException` przy odczycie `core-for-system-modules.jar` i pliku JAR w cache Gradle. Dotyczy to uprawnień środowiska wykonawczego, również po przyznaniu dostępu do SDK. Nie powstał plik APK i nie przeprowadzono testu na emulatorze ani telefonie. Źródła Androida są w projekcie; budowę trzeba dokończyć w środowisku z działającym dostępem Javy do SDK i cache. Wynik webowy i 66 testów pozostają poprawne.


Panel główny, kalendarz, dokumentacja PDF i konfiguracja Google/Outlook: [KALENDARZ-I-DOKUMENTY.md](KALENDARZ-I-DOKUMENTY.md).
