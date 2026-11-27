# Panel, kalendarz i dokumentacja

Menu w lewym górnym rogu prowadzi do kalendarza, kalkulatora BMI, Miautatu, dokumentacji i ustawień. Dzwonek pokazuje wizyty i leki zaplanowane na najbliższe 7 dni. Są to powiadomienia wewnątrz aplikacji, bez powiadomień systemowych w tle.

## Dokumenty

„Zrób zdjęcie” korzysta z aparatu udostępnionego przez urządzenie; w przeglądarce komputerowej może otworzyć wybór pliku. „Wybierz zdjęcie” otwiera pliki/galerię urządzenia. Po wyborze pojawia się podgląd i tytuł. Odrzucenie niczego nie wysyła do API. Akceptacja zapisuje PDF, podgląd JPG i wydarzenie z datą oraz godziną dodania.

Biblioteka pozwala wrócić do dokumentu, powiększyć go, pobrać PDF i usunąć po potwierdzeniu. Dokument można też otworzyć z kalendarza. Usunięcie atomowo usuwa PDF, podgląd i powiązane wydarzenie. Zdjęcia są poprawiane według orientacji EXIF i przekształcane na RGB; limit to 8 MB i 24 megapiksele. Obsługiwane są JPEG, PNG i WebP. PDF nie zawiera OCR.

Dokumenty są przechowywane w aktualnej bazie SQLite w osobnej tabeli. API wymaga zalogowanego, zweryfikowanego właściciela i sprawdza jego uprawnienia do każdego pliku; nie udostępnia publicznych adresów dokumentów. Kopia bazy obejmuje też dokumenty. Obsługa poczty i SMS pozostaje w trybie lokalnych plików.

## Kalendarz i obliczenia

- Dzienna kaloryka i makroskładniki są agregowane z zapisanych posiłków.
- Można dodać pojedynczą wizytę lub przyjęcie leku, z datą, godziną i notatką, oraz usunąć wpis.
- Dokumenty dodają wpis automatycznie.
- Kalkulator zachowuje ilustrację `wymiary.png` i wzór prototypu: `((klatka / 0.7062 - noga) / 0.9156) - noga`. Jest to szacowany udział tkanki tłuszczowej FBMI (%), a nie BMI człowieka. Odrzucamy wyniki poza 0–100% i nie stosujemy ludzkich kategorii masy ciała. Ostatni pomiar w danym dniu zastępuje wcześniejszy; daty są rozdzielone.
- Miautatu udostępnia dziennik i orientacyjny kalkulator `RER = 70 × kg^0.75`, z mnożnikiem 1,2 po kastracji albo 1,4 bez kastracji dla zdrowego dorosłego kota o prawidłowej kondycji. Cel można zapisać i zmienić w ustawieniach.

W ustawieniach można zmieniać imię, nazwisko, imię kota, cel kalorii i widoczność powiadomień. Zweryfikowane e-mail i telefon są wyświetlane jako dane do odczytu; ich zmiana wymagałaby osobnego przepływu ponownej weryfikacji.

## Google i Outlook — połączenie konta

Implementacja synchronizuje **BMI Cat → zewnętrzny kalendarz główny** co około minutę, gdy serwer API działa. Obsługuje tworzenie, aktualizowanie i usuwanie zarządzanych wpisów, odnawianie tokenów i ponawianie po błędzie. Nie importuje cudzych wydarzeń z Google/Outlook do BMI Cat. Do dostawcy wysyłane są tytuł i czas, bez skanów, PDF-ów i notatek medycznych.

Potrzebna jest jednorazowa konfiguracja aplikacji OAuth. Wypełnij odpowiednie pola w **jednym głównym `.env`**, a następnie uruchom ponownie API:

```dotenv
BMI_GOOGLE_CALENDAR_CLIENT_ID=
BMI_GOOGLE_CALENDAR_CLIENT_SECRET=
BMI_OUTLOOK_CLIENT_ID=
BMI_OUTLOOK_CLIENT_SECRET=
BMI_CALENDAR_TOKEN_KEY=
```

Klucz `BMI_CALENDAR_TOKEN_KEY` został już wygenerowany lokalnie; nie kasuj go i nie zmieniaj po połączeniu kont. Służy do szyfrowania tokenów w bazie. Nie jest eksportowany do Fluttera. Pozostałe pola pozostają puste do czasu konfiguracji kont dostawców; ekran jasno pokazuje ten stan.

### Google

1. W Google Cloud wybierz projekt i włącz **Google Calendar API**.
2. W Google Auth Platform skonfiguruj odbiorców aplikacji. W trybie testowym dodaj swój adres do użytkowników testowych.
3. Utwórz klienta OAuth typu **Web application**. Jako autoryzowany adres przekierowania wpisz dokładnie `http://localhost:8000/api/auth/calendar-connections/google/callback`.
4. Zapisz identyfikator i sekret w polach `BMI_GOOGLE_CALENDAR_CLIENT_ID` oraz `BMI_GOOGLE_CALENDAR_CLIENT_SECRET`.
5. Po restarcie API otwórz **Kalendarz → ikona synchronizacji → Google Calendar → Połącz konto**. Zaloguj się w nowej karcie i zaakceptuj dostęp.

Używane zakresy: `openid` (identyfikacja konta przy ponownym połączeniu) i `calendar.events` (wydarzenia). Tryb offline umożliwia odświeżanie dostępu. W aplikacji Google w trybie testowym dostęp może wygasać i wymagać ponownego połączenia.

### Outlook

1. W Microsoft Entra zarejestruj aplikację obsługującą konta organizacyjne oraz osobiste Microsoft.
2. Dodaj platformę **Web** z adresem przekierowania `http://localhost:8000/api/auth/calendar-connections/outlook/callback`.
3. Dodaj delegowane uprawnienie Microsoft Graph **Calendars.ReadWrite** i utwórz sekret klienta.
4. Wpisz Application (client) ID do `BMI_OUTLOOK_CLIENT_ID`, a **wartość** sekretu do `BMI_OUTLOOK_CLIENT_SECRET`.
5. Uruchom API ponownie i wybierz **Outlook → Połącz konto**. Aplikacja poprosi też o `offline_access`.

Nie trzeba kupować domeny do testów na tym komputerze. Gdy zmienisz adres API, zaktualizuj `BMI_API_BASE_URL` i identyczne adresy przekierowania u obu dostawców. Na fizycznym telefonie localhost wskazuje telefon, więc konfiguracja serwera musi uwzględniać dostępny adres komputera/serwera.

Odłączenie usuwa zapisane dane dostępu i zatrzymuje synchronizację, pozostawiając istniejące wpisy u dostawcy. Ponowne połączenie po odłączeniu może utworzyć nowe kopie tych wpisów. Zmiany wprowadzone ręcznie u dostawcy nie wracają do BMI Cat. Lokalny worker zakłada jeden proces API; przed wdrożeniem z wieloma workerami trzeba przenieść synchronizację do osobnego procesu z blokadą współdzieloną.

## Testy i pliki

Backend: `backend/tests/test_health.py` oraz `backend/tests/test_calendar_sync.py`. Frontend: `frontend/test/health_test.dart`; przebieg przeglądarkowy: `frontend/test/browser/health_flow.cjs` korzystający z osobnego API testowego na porcie 8002. Testy dostawców stosują kontrolowane odpowiedzi; prawdziwe konta nie były podłączane. Nowe modele, schematy, serwisy i ekrany są rozdzielone na pliki. Dotychczasowe tabele i konta nie zostały wyczyszczone.

Po dodaniu pluginów do istniejącego Fluttera 3.27 odśwież cache kompilacji (`flutter clean`, następnie `flutter pub get` i build). Nieaktualny rejestr pluginów może powodować błąd wyboru zdjęcia mimo poprawnych testów formularza.

Android ma adapter aparatu/galerii oraz systemowy zapis PDF. Obsługi aparatu na fizycznym telefonie i aktualnego APK nie zweryfikowano w tym środowisku; istniejący problem konfiguracji lokalnego Android SDK pozostaje osobną kwestią.

Źródła: [Google OAuth dla serwera webowego](https://developers.google.com/identity/protocols/oauth2/web-server), [Google Calendar — tworzenie wydarzeń](https://developers.google.com/workspace/calendar/api/guides/create-events), [Microsoft OAuth authorization code](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow), [Microsoft Graph — wydarzenia](https://learn.microsoft.com/en-us/graph/api/calendar-post-events?view=graph-rest-1.0), [AAHA — żywienie zdrowych kotów](https://www.aaha.org/resources/2021-aaha-nutrition-and-weight-management-guidelines/feeding-plans-for-healthy-appropriate-weight-cats-and-dogs/), [badanie z wariantem wzoru 0,7062](https://new.scielo.br/j/pvb/a/DWgBN3Qnx8dGGRRGV3M79kf/?ilang=en&lang=en).
