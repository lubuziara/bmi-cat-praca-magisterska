import 'dart:convert';
import 'package:bmi_cat/features/auth/data/api_exception.dart';
import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/auth/data/session_store.dart';
import 'package:bmi_cat/features/auth/data/passkey_webauthn_stub.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class MemoryStore implements SessionStore {
  String? token;
  @override Future<void> clearToken() async => token = null;
  @override Future<String?> readToken() async => token;
  @override Future<void> writeToken(String value) async => token = value;
}
Map<String, dynamic> session() => {'access_token': 'session', 'user': {'profile_complete': true, 'registration_verified': true}};
AuthApi apiFor(Future<http.Response> Function(http.Request) fn, MemoryStore store) => AuthApi(client: MockClient(fn), sessionStore: store);
class FakePasskey implements PasskeyWebAuthn { @override bool get supported => true; @override Future<Map<String, dynamic>> create(Map<String, dynamic> _) async => {}; @override Future<Map<String, dynamic>> get(Map<String, dynamic> _) async => {'rawId': 'id', 'response': {'clientDataJSON': 'data'}}; }

void main() {
  test('low completes normal login', () async {
    final s = MemoryStore(); final a = apiFor((_) async => http.Response(jsonEncode(session()), 200), s);
    await a.login('cat@example.com', 'password'); expect(s.token, 'session'); expect(a.stepUpRequired, isFalse);
  });
  test('medium opens step-up without a session', () async {
    final s = MemoryStore(); final a = apiFor((_) async => http.Response(jsonEncode({'step_up_required': true, 'step_up_challenge': 'c', 'methods': ['totp']}), 200), s);
    await a.login('cat@example.com', 'password'); expect(a.stepUpRequired, isTrue); expect(a.allowsStepUpMethod('totp'), isTrue); expect(s.token, isNull);
  });
  test('strong step-up has no session before confirmation', () async {
    final s = MemoryStore(); final a = apiFor((_) async => http.Response(jsonEncode({'step_up_required': true, 'step_up_challenge': 'c', 'methods': ['passkey']}), 200), s);
    await a.login('cat@example.com', 'password'); expect(a.allowsStepUpMethod('passkey'), isTrue); expect(s.token, isNull);
  });
  test('valid step-up completes login', () async {
    final s = MemoryStore(); final a = apiFor((r) async => http.Response(jsonEncode(r.url.path.endsWith('/login') ? {'mfa_required': true, 'mfa_challenge': 'c'} : session()), 200), s);
    await a.login('cat@example.com', 'password'); await a.verifyMfa('123456'); expect(s.token, 'session'); expect(a.stepUpRequired, isFalse);
  });
  test('passkey step-up uses its transaction and saves a session only after verify', () async {
    final paths = <String>[]; final s = MemoryStore(); final a = apiFor((r) async { paths.add(r.url.path); if (r.url.path.endsWith('/login')) return http.Response(jsonEncode({'step_up_required': true, 'step_up_challenge': 'c', 'methods': ['passkey']}), 200); if (r.url.path.endsWith('/options')) return http.Response(jsonEncode({'challenge': 'YQ'}), 200); return http.Response(jsonEncode(session()), 200); }, s);
    await a.login('cat@example.com', 'password'); expect(s.token, isNull); await a.verifyStepUpPasskey(FakePasskey()); expect(paths, containsAll(['/api/auth/step-up/passkey/options', '/api/auth/step-up/passkey/verify'])); expect(s.token, 'session');
  });
  test('invalid step-up creates no session', () async {
    final s = MemoryStore(); final a = apiFor((r) async => http.Response(jsonEncode(r.url.path.endsWith('/login') ? {'mfa_required': true, 'mfa_challenge': 'c'} : {'detail': 'invalid'}), r.url.path.endsWith('/login') ? 200 : 401), s);
    await a.login('cat@example.com', 'password'); await expectLater(a.verifyMfa('000000'), throwsA(isA<ApiException>())); expect(s.token, isNull);
  });
  test('blocked login creates no session and reveals no internals', () async {
    final s = MemoryStore(); final a = apiFor((_) async => http.Response(jsonEncode({'detail': 'Logowanie chwilowo niedostępne. Spróbuj ponownie później.'}), 401), s);
    await expectLater(a.login('cat@example.com', 'password'), throwsA(predicate((Object e) => e is ApiException && !e.message.contains('risk')))); expect(s.token, isNull);
  });
  test('expired and cancelled challenges are cleared', () async {
    final s = MemoryStore(); final a = apiFor((r) async => http.Response(jsonEncode(r.url.path.endsWith('/login') ? {'mfa_required': true, 'mfa_challenge': 'c'} : {'detail': 'expired'}), r.url.path.endsWith('/login') ? 200 : 401), s);
    await a.login('cat@example.com', 'password'); await expectLater(a.verifyMfa('123456'), throwsA(isA<ApiException>())); expect(a.stepUpRequired, isFalse);
    await a.login('cat@example.com', 'password'); a.cancelMfa(); expect(a.stepUpRequired, isFalse);
  });
  test('step-up without a challenge cannot create a session', () async {
    final s = MemoryStore(); final a = apiFor((_) async => http.Response(jsonEncode({'step_up_required': true, 'methods': ['passkey']}), 200), s);
    await expectLater(a.login('cat@example.com', 'password'), throwsA(isA<ApiException>())); expect(s.token, isNull);
  });
}
