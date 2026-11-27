import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';
import 'package:bmi_cat/core/theme/app_theme.dart';
import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/home/screens/home_screen.dart';
import 'package:bmi_cat/features/health/screens/documents_screen.dart';
import 'package:bmi_cat/features/health/screens/bmi_screen.dart';
import 'package:bmi_cat/features/health/screens/calorie_screen.dart';
import 'package:bmi_cat/features/avatar/widgets/cat_avatar.dart';

class HealthApiFake extends AuthApi {
  List<Map<String, dynamic>> writes = [];
  List<Map<String, dynamic>> documents = [];
  @override
  Future<Map<String, dynamic>> request(String path,
      {Map<String, dynamic>? body, bool get = false, bool remove = false}) async {
    if (!get) writes.add({'path': path, ...?body});
    if (path.startsWith('diary'))
      return {
        'totals': {'kcal': 0, 'protein': 0, 'fat': 0, 'carbs': 0},
        'target_kcal': 200
      };
    if (path == 'settings')
      return {
        'first_name': 'Anna',
        'last_name': 'Kowalska',
        'cat_name': 'Luna',
        'email': 'test@example.com',
        'phone': '+48123456789',
        'notifications': true,
        'target_kcal': 200
      };
    if (path == 'calendar-connections') return {'connections': <dynamic>[]};
    if (path.startsWith('calendar')) return {'events': <dynamic>[]};
    if (path == 'bmi')
      return {
        'details': {'value': 24.5}
      };
    if (path == 'documents') {
      if (body != null)
        documents.add({
          'id': 1,
          'title': body['title'],
          'occurred_at': body['occurred_at']
        });
      return {'documents': documents};
    }
    throw StateError(path);
  }
}

class TestPicker extends ImagePicker {
  @override
  Future<XFile?> pickImage(
          {required ImageSource source,
          double? maxWidth,
          double? maxHeight,
          int? imageQuality,
          CameraDevice preferredCameraDevice = CameraDevice.rear,
          bool requestFullMetadata = true}) async =>
      XFile.fromData(
          base64Decode(
              'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZ1cAAAAASUVORK5CYII='),
          name: 'scan.png',
          mimeType: 'image/png');
}

Widget app(Widget screen) => MaterialApp(
    theme: AppTheme.light,
    locale: const Locale('pl'),
    supportedLocales: const [Locale('pl')],
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
    home: screen);

void main() {
  for (final width in [320.0, 1100.0]) {
    testWidgets('Menu routes and notifications fit $width', (tester) async {
      debugDefaultTargetPlatformOverride = TargetPlatform.linux;
      addTearDown(() => debugDefaultTargetPlatformOverride = null);
      tester.view.physicalSize = Size(width, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final api = HealthApiFake();
      await tester.pumpWidget(app(HomeScreen(api: api, profile: {
        'first_name': 'Anna',
        'cat': {'name': 'Luna', 'avatar': <String, dynamic>{}}
      })));
      await tester.pumpAndSettle();
      expect(find.byType(CatAvatar), findsOneWidget);
      for (final label in [
        'Kalendarz',
        'Kalkulator BMI',
        'Miautatu — kalorie',
        'Dokumentacja medyczna',
        'Ustawienia'
      ]) {
        await tester.tap(find.byIcon(Icons.menu));
        await tester.pumpAndSettle();
        expect(find.byType(CatAvatar), findsNothing,
            reason: 'Model 3D nie może przechwytywać dotyku nad menu.');
        await tester.tap(find.text(label));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull, reason: label);
        await tester.tap(find.byType(BackButton));
        await tester.pumpAndSettle();
      }
      await tester.tap(find.byTooltip('Powiadomienia'));
      await tester.pumpAndSettle();
      expect(find.text('Najbliższe 7 dni'), findsOneWidget);
      expect(tester.takeException(), isNull);
      debugDefaultTargetPlatformOverride = null;
    });
  }

  testWidgets(
      'Document preview requires acceptance; rejection makes no API write',
      (tester) async {
    tester.view.physicalSize = const Size(1100, 1500);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final api = HealthApiFake();
    await tester
        .pumpWidget(app(DocumentsScreen(api: api, picker: TestPicker())));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Wybierz zdjęcie'));
    await tester.pumpAndSettle();
    expect(find.text('Podgląd przed zapisaniem'), findsOneWidget);
    expect(api.writes, isEmpty);
    await tester.tap(find.text('Odrzuć zdjęcie'));
    await tester.pumpAndSettle();
    expect(api.writes, isEmpty);
    await tester.tap(find.text('Wybierz zdjęcie'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Akceptuję — zapisz PDF'));
    await tester.pumpAndSettle();
    expect(api.writes.length, 1);
    expect(api.writes.single['path'], 'documents');
    expect(find.text('Podgląd przed zapisaniem'), findsNothing);
    expect(find.text('Dokument od weterynarza'), findsOneWidget);
  });

  testWidgets('BMI validates before saving and accepts decimal comma',
      (tester) async {
    tester.view.physicalSize = const Size(1000, 1300);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final api = HealthApiFake();
    await tester.pumpWidget(app(BmiScreen(api: api)));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Oblicz i zapisz w kalendarzu'));
    await tester.pumpAndSettle();
    expect(api.writes, isEmpty);
    await tester.enterText(find.byType(TextFormField).first, '40,5');
    await tester.enterText(find.byType(TextFormField).last, '16');
    await tester.tap(find.text('Oblicz i zapisz w kalendarzu'));
    await tester.pumpAndSettle();
    expect(api.writes.single['chest_cm'], 40.5);
    expect(find.text('24.5%'), findsOneWidget);
  });

  testWidgets('Calorie goal applies a 20 percent adjustment to maintenance',
      (tester) async {
    tester.view.physicalSize = const Size(1000, 1800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final api = HealthApiFake();
    await tester.pumpWidget(app(CalorieScreen(api: api, profile: const {})));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('Oblicz kalorie'));
    await tester.tap(find.text('Oblicz kalorie'));
    await tester.pumpAndSettle();
    expect(find.text('238 kcal / dzień'), findsOneWidget);

    await tester
        .ensureVisible(find.byType(DropdownButtonFormField<CalorieGoal>));
    await tester.tap(find.byType(DropdownButtonFormField<CalorieGoal>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Schudnąć').last);
    await tester.pumpAndSettle();
    expect(find.text('190 kcal / dzień'), findsOneWidget);

    await tester
        .ensureVisible(find.byType(DropdownButtonFormField<CalorieGoal>));
    await tester.tap(find.byType(DropdownButtonFormField<CalorieGoal>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Przytyć').last);
    await tester.pumpAndSettle();
    expect(find.text('285 kcal / dzień'), findsOneWidget);
    expect(
        find.textContaining('Zmiana masy ciała kota powinna'), findsOneWidget);
  });
}
