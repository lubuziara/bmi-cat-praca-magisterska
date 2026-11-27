import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bmi_cat/app.dart';
import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/auth/data/api_exception.dart';

class FakeAuthApi extends AuthApi {
  int calls = 0;
  @override
  Future<void> login(String email, String password) async {
    calls++;
    throw const ApiException('Nieprawidłowy e-mail lub hasło.');
  }
}

void main() {
  setUpAll(() async {
    final font = FontLoader('BmiRoboto');
    font.addFont(rootBundle.load('assets/fonts/roboto-regular.ttf'));
    await font.load();
    final icons = FontLoader('MaterialIcons');
    icons.addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
    await icons.load();
  });
  testWidgets('Puste logowanie nie wywołuje API; hasło można pokazać',
      (tester) async {
    final api = FakeAuthApi();
    await tester.pumpWidget(BmiCatApp(api: api));
    await tester.tap(find.widgetWithText(FilledButton, 'Zaloguj się'));
    await tester.pumpAndSettle();
    expect(find.text('Podaj adres e-mail.'), findsOneWidget);
    expect(find.text('Podaj hasło.'), findsOneWidget);
    expect(api.calls, 0);
    await tester.tap(find.byTooltip('Pokaż hasło'));
    await tester.pump();
    expect(find.byTooltip('Ukryj hasło'), findsOneWidget);
  });

  testWidgets('Błąd API jest widoczny i formularz można wysłać ponownie',
      (tester) async {
    final api = FakeAuthApi();
    await tester.pumpWidget(BmiCatApp(api: api));
    await tester.enterText(
        find.byType(TextFormField).at(0), 'anna@example.com');
    await tester.enterText(find.byType(TextFormField).at(1), 'wrong');
    await tester.tap(find.widgetWithText(FilledButton, 'Zaloguj się'));
    await tester.pumpAndSettle();
    expect(find.text('Nieprawidłowy e-mail lub hasło.'), findsOneWidget);
    expect(api.calls, 1);
    expect(
        tester
            .widget<FilledButton>(
                find.widgetWithText(FilledButton, 'Zaloguj się'))
            .onPressed,
        isNotNull);
  });

  testWidgets('Linki prowadzą do rejestracji i odzyskiwania hasła',
      (tester) async {
    await tester.pumpWidget(const BmiCatApp());
    await tester.ensureVisible(find.text('Zarejestruj się'));
    await tester.tap(find.text('Zarejestruj się'));
    await tester.pumpAndSettle();
    expect(find.text('Utwórz konto'), findsOneWidget);
    await tester.enterText(find.byType(TextFormField).first, '666');
    await tester.ensureVisible(find.widgetWithText(FilledButton, 'Dalej'));
    await tester.tap(find.widgetWithText(FilledButton, 'Dalej'));
    await tester.pumpAndSettle();
    expect(find.text('Imię może zawierać litery, spacje, apostrof i łącznik.'),
        findsOneWidget);
    await tester.ensureVisible(find.text('Wróć do logowania'));
    await tester.tap(find.text('Wróć do logowania'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Nie pamiętasz hasła?'));
    await tester.pumpAndSettle();
    expect(find.text('Odzyskaj hasło'), findsOneWidget);
  });

  for (final width in [320.0, 390.0, 768.0, 1440.0]) {
    testWidgets('Układ bez przepełnień przy szerokości $width', (tester) async {
      tester.view.physicalSize = Size(width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(const BmiCatApp());
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.ensureVisible(find.text('Zarejestruj się'));
      await tester.tap(find.text('Zarejestruj się'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('Duży tekst i klawiatura nie blokują formularza', (tester) async {
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1;
    tester.view.viewInsets = const FakeViewPadding(bottom: 280);
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.view.reset);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(const BmiCatApp());
    await tester.pumpAndSettle();
    await tester
        .ensureVisible(find.widgetWithText(FilledButton, 'Zaloguj się'));
    await tester.tap(find.widgetWithText(FilledButton, 'Zaloguj się'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('Podaj hasło.'), findsOneWidget);
  });
}
