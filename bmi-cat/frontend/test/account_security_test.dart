import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/auth/screens/account_security_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class SecurityApiFake extends AuthApi {
  bool failRevoke = false; int sessionCalls = 0; int eventOffset = 0;
  List<Map<String, dynamic>> sessionData = [
    {'id':'current-family-secret','device':'Chrome na Windows','auth_method':'password','mfa_used':true,'is_current':true},
    {'id':'other-family-secret','device':'BMICat na Android','auth_method':'passkey','mfa_used':false,'is_current':false},
  ];
  @override Future<dynamic> request(String path, {Map<String, dynamic>? body, bool get = false, bool remove = false}) async {
    if (path == '2fa/status') return {'enabled': false};
    if (path == 'passkeys') return [];
    if (path == 'sessions') { sessionCalls++; return sessionData; }
    if (path.startsWith('security-events')) { eventOffset++; return path.contains('offset=0') ? [{'event_type':'refresh_token_reuse_detected','severity':'critical','created_at':2}] : [{'event_type':'mfa_failed','severity':'warning','created_at':3}]; }
    if (remove && path.startsWith('sessions/')) { if (failRevoke) throw Exception(); sessionData = [sessionData.first]; return {}; }
    if (path == 'sessions/revoke-others') { sessionData = [sessionData.first]; return {}; }
    return {};
  }
}

Widget screen(SecurityApiFake api) => MaterialApp(home: AccountSecurityScreen(api: api));
void main() {
  testWidgets('pokazuje sesje, bieżące urządzenie i ukrywa jego revoke', (tester) async { final api = SecurityApiFake(); await tester.pumpWidget(screen(api)); await tester.pumpAndSettle(); expect(find.textContaining('To urządzenie'), findsOneWidget); expect(find.text('Wyloguj urządzenie'), findsOneWidget); expect(find.textContaining('current-family-secret'), findsNothing); });
  testWidgets('revoke innej sesji odświeża widok po sukcesie', (tester) async { final api = SecurityApiFake(); await tester.pumpWidget(screen(api)); await tester.pumpAndSettle(); await tester.tap(find.text('Wyloguj urządzenie')); await tester.pumpAndSettle(); await tester.tap(find.text('Wyloguj').last); await tester.pumpAndSettle(); expect(find.text('BMICat na Android'), findsNothing); });
  testWidgets('błąd revoke pozostawia sesję', (tester) async { final api = SecurityApiFake()..failRevoke = true; await tester.pumpWidget(screen(api)); await tester.pumpAndSettle(); await tester.tap(find.text('Wyloguj urządzenie')); await tester.pumpAndSettle(); await tester.tap(find.text('Wyloguj').last); await tester.pumpAndSettle(); expect(find.text('BMICat na Android'), findsOneWidget); });
  testWidgets('mapuje historię i pobiera starszą stronę', (tester) async { final api = SecurityApiFake(); await tester.pumpWidget(screen(api)); await tester.pumpAndSettle(); await tester.drag(find.byType(ListView).first, const Offset(0, -1200)); await tester.pumpAndSettle(); expect(find.text('Wykryto podejrzaną próbę użycia sesji'), findsOneWidget); await tester.tap(find.text('Pokaż starsze')); await tester.pumpAndSettle(); expect(find.text('Nieudana weryfikacja 2FA'), findsOneWidget); });
  testWidgets('pusty stan sesji i historii', (tester) async { final api = SecurityApiFake()..sessionData = []; await tester.pumpWidget(screen(api)); await tester.pumpAndSettle(); expect(find.text('Nie masz innych aktywnych sesji.'), findsOneWidget); });
}
