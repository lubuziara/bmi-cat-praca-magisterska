import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bmi_cat/core/theme/app_theme.dart';
import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/diary/screens/dashboard_screen.dart';
import 'package:bmi_cat/features/diary/widgets/add_meal_sheet.dart';

class DiaryApiFake extends AuthApi {
  Map<String, dynamic>? added;
  Map<String, dynamic> data = {
    'entries': <dynamic>[],
    'totals': {'kcal': 0, 'protein': 0, 'fat': 0, 'carbs': 0},
    'target_kcal': 200,
    'foods': [
      {
        'id': 'demo-chicken-can',
        'name': 'Puszka z kurczakiem',
        'description': 'Dane demonstracyjne',
        'kcal': 100,
        'protein': 10,
        'fat': 6,
        'carbs': 1.5
      }
    ]
  };
  @override
  Future<Map<String, dynamic>> request(String path,
      {Map<String, dynamic>? body, bool get = false, bool remove = false}) async {
    if (body != null) {
      added = body;
      final g = body['grams'] as double;
      data = {
        ...data,
        'entries': [
          {
            'id': 1,
            'name': 'Puszka z kurczakiem',
            'period': body['period'],
            'grams': g,
            'kcal': g
          }
        ],
        'totals': {
          'kcal': g,
          'protein': g * .1,
          'fat': g * .06,
          'carbs': g * .015
        }
      };
    }
    return data;
  }
}

void main() {
  setUpAll(() async {
    final font = FontLoader('BmiRoboto')
      ..addFont(rootBundle.load('assets/fonts/roboto-regular.ttf'));
    await font.load();
    final icons = FontLoader('MaterialIcons')
      ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
    await icons.load();
  });
  for (final width in [360.0, 1100.0]) {
    testWidgets('Dashboard fits $width and displays daily footer',
        (tester) async {
      tester.view.physicalSize = Size(width, 950);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(MaterialApp(
          theme: AppTheme.light,
          debugShowCheckedModeBanner: false,
          home: DashboardScreen(api: DiaryApiFake(), profile: {
            'first_name': 'Gaba',
            'cat': {'name': 'Luna'}
          })));
      await tester.pumpAndSettle();
      expect(find.text('Rano'), findsOneWidget);
      expect(find.text('Wieczór'), findsOneWidget);
      expect(find.text('Węgle'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets('Add portion validates grams and updates totals', (tester) async {
    final api = DiaryApiFake();
    await tester.pumpWidget(MaterialApp(
        theme: AppTheme.light,
        home: DashboardScreen(api: api, profile: {
          'first_name': 'Anna',
          'cat': {'name': 'Luna'}
        })));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Dodaj posiłek — Rano'));
    await tester.pumpAndSettle();
    final field = find.widgetWithText(TextField, 'Ile zjadł kot?');
    for (final bad in ['0', '-5', 'NaN', '1001']) {
      await tester.enterText(field, bad);
      await tester.pump();
      expect(
          tester
              .widget<FilledButton>(
                  find.widgetWithText(FilledButton, 'Dodaj porcję'))
              .onPressed,
          isNull);
    }
    await tester.enterText(field, '50,5');
    await tester.pump();
    await tester.ensureVisible(find.text('Dodaj porcję'));
    await tester.tap(find.text('Dodaj porcję'));
    await tester.pumpAndSettle();
    expect(api.added!['grams'], 50.5);
    expect(api.added!['period'], 'morning');
    expect(find.byType(AddMealSheet), findsNothing);
    expect(find.text('Puszka z kurczakiem'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
