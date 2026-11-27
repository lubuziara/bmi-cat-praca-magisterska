import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bmi_cat/core/theme/app_theme.dart';
import 'package:bmi_cat/features/home/screens/home_screen.dart';
import 'package:bmi_cat/features/diary/screens/dashboard_screen.dart';
import 'package:bmi_cat/features/diary/widgets/nutrient_bar.dart';
import 'diary_test.dart' show DiaryApiFake;

void main() {
  for (final width in [320.0, 1100.0]) {
    testWidgets('Home footer and plus fit $width; return refreshes totals',
        (tester) async {
      debugDefaultTargetPlatformOverride = TargetPlatform.linux;
      addTearDown(() => debugDefaultTargetPlatformOverride = null);
      tester.view.physicalSize = Size(width, 950);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final api = DiaryApiFake();
      await tester.pumpWidget(MaterialApp(
          theme: AppTheme.light,
          home: HomeScreen(api: api, profile: {
            'first_name': 'Gaba',
            'cat': {'name': 'Luna', 'avatar': <String, dynamic>{}}
          })));
      await tester.pumpAndSettle();
      expect(find.byType(NutrientBar), findsOneWidget);
      expect(find.byType(DashboardScreen), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.tap(find.byTooltip('Przejdź do dziennika posiłków'));
      await tester.pumpAndSettle();
      expect(find.byType(DashboardScreen), findsOneWidget);
      expect(find.text('Rano'), findsOneWidget);
      api.data = {
        ...api.data,
        'totals': {'kcal': 50, 'protein': 5, 'fat': 3, 'carbs': .75}
      };
      await tester.pageBack();
      await tester.pumpAndSettle();
      expect(find.byType(DashboardScreen), findsNothing);
      expect(
          tester.widget<NutrientBar>(find.byType(NutrientBar)).totals['kcal'],
          50);
      expect(tester.takeException(), isNull);
      debugDefaultTargetPlatformOverride = null;
    });
  }
}
