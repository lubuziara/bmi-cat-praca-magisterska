import 'package:flutter/foundation.dart';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bmi_cat/app.dart';
import 'package:bmi_cat/features/avatar/models/avatar_settings.dart';
import 'package:bmi_cat/features/avatar/widgets/avatar_editor.dart';

import 'package:bmi_cat/features/auth/validation/parse_birth_date.dart';
import 'package:bmi_cat/features/auth/validation/validate_phone.dart';
import 'support/registration_api.dart';

void main() {
  setUpAll(() async {
    final font = FontLoader('BmiRoboto')
      ..addFont(rootBundle.load('assets/fonts/roboto-regular.ttf'));
    await font.load();
    final icons = FontLoader('MaterialIcons')
      ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
    await icons.load();
  });
  tearDownAll(() {
    debugDefaultTargetPlatformOverride = null;
  });
  test('Daty kalendarzowe i telefon międzynarodowy', () {
    expect(parseBirthDate('31.02.2024'), isNull);
    expect(parseBirthDate('29.02.2024'), DateTime(2024, 2, 29));
    expect(validatePhone('666'), isNotNull);
    expect(validatePhone('+48 123 456 789'), isNull);
  });
  testWidgets('Pełny kreator zapisuje właściciela, przybliżony wiek i avatar',
      (tester) async {
    debugDefaultTargetPlatformOverride = TargetPlatform.linux;
    addTearDown(() {
      debugDefaultTargetPlatformOverride = null;
    });
    tester.view.physicalSize = const Size(1100, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final api = RegistrationApi();
    await tester.pumpWidget(BmiCatApp(api: api));
    await tester.tap(find.text('Zarejestruj się'));
    await tester.pumpAndSettle();
    Future<void> fill(String label, String text) async {
      final field = find.widgetWithText(TextFormField, label);
      await tester.ensureVisible(field);
      await tester.enterText(field, text);
    }

    await fill('Imię', 'Anna');
    await fill('Nazwisko', 'Kowalska');
    await fill('Data urodzenia', '04.03.1995');
    await fill('Numer telefonu', '+48123456789');
    await fill('E-mail', 'anna@example.com');
    await fill('Hasło', 'Bardzo dlugie haslo!');
    await fill('Powtórz hasło', 'Bardzo dlugie haslo!');
    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Kobieta').last);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Dalej'));
    await tester.tap(find.text('Dalej'));
    await tester.pumpAndSettle();
    await fill('Imię kota', 'Luna');
    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Kotka').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byType(SwitchListTile));
    await tester.pumpAndSettle();
    await fill('Ile ma lat?', '2');
    await fill('Ile ma miesięcy?', '3');
    await tester.ensureVisible(find.text('Dalej'));
    await tester.tap(find.text('Dalej'));
    await tester.pumpAndSettle();
    expect(find.byType(AvatarEditor), findsOneWidget);
    await tester.tap(find.byType(DropdownButtonFormField<String>).at(1));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Fioletowy').last);
    await tester.tap(find.text('Fioletowy').last);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Zarejestruj konto'));
    await tester.tap(find.text('Zarejestruj konto'));
    await tester.pumpAndSettle();
    expect(api.payload!['last_name'], 'Kowalska');
    expect(api.payload!['cat']['estimated_age_months'], 27);
    expect(api.payload!['cat']['avatar']['coat'], 'purple');
    expect(find.text('Potwierdź rejestrację'), findsOneWidget);
    expect(tester.takeException(), isNull);
    debugDefaultTargetPlatformOverride = null;
  });
  for (final width in [320.0, 1100.0]) {
    testWidgets('Edytor 3D i opcje mieszczą się na ekranie $width',
        (tester) async {
      debugDefaultTargetPlatformOverride = TargetPlatform.linux;
      addTearDown(() {
        debugDefaultTargetPlatformOverride = null;
      });
      tester.view.physicalSize = Size(width, 1100);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(MaterialApp(
          home: Scaffold(
              body: SingleChildScrollView(
                  child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: AvatarEditor(
                          value: const AvatarSettings(),
                          onChanged: (_) {}))))));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      debugDefaultTargetPlatformOverride = null;
      expect(find.byType(DropdownButtonFormField<String>), findsNWidgets(5));
      expect(tester.takeException(), isNull);
      debugDefaultTargetPlatformOverride = null;
    });
  }
}
