import 'dart:convert';

import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/auth/data/api_exception.dart';
import 'package:bmi_cat/features/auth/data/session_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class MemorySessionStore implements SessionStore {
  String? token;

  @override
  Future<void> clearToken() async => token = null;

  @override
  Future<String?> readToken() async => token;

  @override
  Future<void> writeToken(String value) async => token = value;
}

void main() {
  test('przywraca zapisaną sesję po ponownym uruchomieniu aplikacji', () async {
    final store = MemorySessionStore();
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/login')) {
        return http.Response(
            jsonEncode({
              'access_token': 'saved-token',
              'user': {'profile_complete': true, 'registration_verified': true},
            }),
            200);
      }
      expect(request.headers['Authorization'], 'Bearer saved-token');
      return http.Response(
          jsonEncode({
            'profile_complete': true,
            'registration_verified': true,
          }),
          200);
    });
    final first = AuthApi(client: client, sessionStore: store);

    await first.login('kot@example.com', 'correct horse battery staple');

    final reloaded = AuthApi(client: client, sessionStore: store);
    expect(await reloaded.restoreSession(), isTrue);
    expect(reloaded.needsVerification, isFalse);
  });

  test('usuwa zapisaną sesję, gdy token nie jest już ważny', () async {
    final store = MemorySessionStore()..token = 'expired-token';
    final api = AuthApi(
      sessionStore: store,
      client: MockClient((_) async =>
          http.Response(jsonEncode({'detail': 'Unauthorized'}), 401)),
    );

    expect(await api.restoreSession(), isFalse);
    expect(store.token, isNull);
  });

  test('mfa_required nie zapisuje sesji, a poprawny TOTP ją kończy', () async {
    final store = MemorySessionStore();
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/login')) return http.Response(jsonEncode({'mfa_required': true, 'mfa_challenge': 'x' * 32}), 200);
      return http.Response(jsonEncode({'access_token': 'totp-session', 'user': {'profile_complete': true, 'registration_verified': true}}), 200);
    });
    final api = AuthApi(client: client, sessionStore: store);
    await api.login('kot@example.com', 'hasło');
    expect(api.mfaRequired, isTrue);
    expect(store.token, isNull);
    await api.verifyMfa('123456');
    expect(api.mfaRequired, isFalse);
    expect(store.token, 'totp-session');
  });

  test('błędny kod zachowuje challenge, anulowanie go usuwa', () async {
    final api = AuthApi(client: MockClient((request) async => request.url.path.endsWith('/login')
        ? http.Response(jsonEncode({'mfa_required': true, 'mfa_challenge': 'x' * 32}), 200)
        : http.Response(jsonEncode({'detail': 'Nieprawidłowy kod 2FA.'}), 401)), sessionStore: MemorySessionStore());
    await api.login('kot@example.com', 'hasło');
    await expectLater(api.verifyMfa('000000'), throwsA(isA<ApiException>()));
    expect(api.mfaRequired, isTrue);
    api.cancelMfa();
    expect(api.mfaRequired, isFalse);
  });
}
