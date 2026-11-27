# Dziennik żywienia

Panel główny po zalogowaniu i potwierdzeniu rejestracji zawiera Rano / Wieczór,
przyciski dodawania porcji, usuwanie wpisów, wybór dnia i dolne podsumowanie.
Wpisy są trwale zapisywane w tabeli meal_entries i ograniczone do kota właściciela.
Przykładowa puszka znajduje się w katalogu, nie jest automatycznie dopisywana jako zjedzona.

Domyślne 200 kcal/dzień to zaokrąglony punkt odniesienia dla zdrowego dorosłego
kota ok. 4 kg. Nie uwzględnia jeszcze rzeczywistej masy, aktywności, wieku czy
stanu zdrowia. Nie należy używać go jako indywidualnego planu żywienia.
Źródło punktu odniesienia RER: https://www.aaha.org/resources/2021-aaha-aafp-feline-life-stage-guidelines/nutrition-and-weight-young-adult-cats/

Białko, tłuszcze i węglowodany pokazują spożycie, bez wymyślonych norm docelowych.
Dane przykładowej puszki są demonstracyjne, nie pochodzą z etykiety producenta.
Wartości podano na 100 g karmy; ilość porcji przeliczana jest na serwerze.

API: GET /api/auth/diary?day=YYYY-MM-DD, POST /api/auth/diary,
POST /api/auth/diary/{id}/remove. Wszystkie wymagają zweryfikowanego konta.
Testy: backend/tests/test_diary.py i frontend/test/diary_test.dart.

Ekran główny pokazuje avatar kota i podsumowanie dzisiejszego spożycia. Okrągły plus obok podsumowania otwiera osobny dziennik posiłków. Powrót do ekranu głównego odświeża dane z bazy.
