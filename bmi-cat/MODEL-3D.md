# Model GLB kota

Model użytkowniczki zastąpił proceduralnego kota w CatAvatar. Źródłowy plik
`frontend/assets/avatar3d/cat.glb` pozostaje niezmieniony; licencja i autor
znajdują się w ATTRIBUTION.txt i stopce podglądu.

- `viewer.js`: ładowanie GLB, scena, oświetlenie, obrót i most ustawień Fluttera.
- `cat-material.js`: zachowanie map tekstur, tint umaszczenia i oczu oraz
  cienkie warstwy futra na powierzchni z drobnym, zapętlonym ruchem.
- `cat-shape.js`: łagodna deformacja tułowia. Model nie zawiera kości ani
  gotowych morph targets; wielkość kociaka jest skalą, nie osobnym modelem.
- `glb_avatar_web.dart`: lokalny iframe i sprawdzanie źródła wiadomości.
- Android: widok WebView z lokalnymi assetami obsługiwanymi pod prywatnym
  adresem HTTPS. Nie pobiera modelu ani biblioteki z CDN podczas działania.

Model jest bazowo krótkowłosym brytyjczykiem. Długi włos jest efektem warstwowym
na jego powierzchni, a nie symulacją każdego włosa. Wariant łysy ogranicza
warstwę futra i mapę normalnych, ale nie zmienia anatomii na kota rasy sfinks.

Testy: Flutter test obejmuje kreator i poprawność dołączonego GLB.
`frontend/test/browser/avatar_glb.cjs` (Node + Playwright, Edge) sprawdza
rzeczywisty WebGL, opcje, obrót i szerokość mobilną przy działającym serwerze.
Kompilacja Androida wymaga naprawienia lokalnej konfiguracji Gradle/Android SDK;
na tym stanowisku zatrzymała się przed kompilacją Kotlin przy AndroidLocationsBuildService.
