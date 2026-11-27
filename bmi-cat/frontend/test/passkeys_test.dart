import 'dart:convert';
import 'package:bmi_cat/features/auth/data/auth_api.dart';
import 'package:bmi_cat/features/auth/data/passkey_webauthn_stub.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class FakeWebAuthn implements PasskeyWebAuthn { bool get supported => true; Future<Map<String, dynamic>> create(Map<String, dynamic> _) async => {'rawId': 'id', 'response': {'clientDataJSON': 'data', 'attestationObject': 'object'}}; Future<Map<String, dynamic>> get(Map<String, dynamic> _) async => {'rawId': 'id', 'response': {'clientDataJSON': 'data', 'authenticatorData': 'auth', 'signature': 'signature'}}; }
void main() {
  test('rejestracja pobiera options i wysyła tylko odpowiedź do verify', () async { final paths = <String>[]; final api = AuthApi(client: MockClient((r) async { paths.add(r.url.path); return http.Response(jsonEncode(r.url.path.endsWith('options') ? {'challenge':'YQ','user':{'id':'Yg'}} : {'id': 1}), 200); })); await api.registerPasskey(FakeWebAuthn()); expect(paths, containsAll(['/api/auth/passkeys/register/options','/api/auth/passkeys/register/verify'])); });
  test('logowanie passkey tworzy normalną sesję', () async { final api = AuthApi(client: MockClient((r) async => http.Response(jsonEncode(r.url.path.endsWith('options') ? {'challenge':'YQ'} : {'access_token':'memory-only','user':{'profile_complete':true,'registration_verified':true}}), 200))); await api.loginPasskey(FakeWebAuthn()); expect(api.needsVerification, isFalse); });
  test('błąd verify nie tworzy sesji', () async { final api = AuthApi(client: MockClient((r) async => http.Response(jsonEncode(r.url.path.endsWith('options') ? {'challenge':'YQ'} : {'detail':'expired'}), r.url.path.endsWith('options') ? 200 : 401))); await expectLater(api.loginPasskey(FakeWebAuthn()), throwsA(isA<Object>())); expect(await api.restoreSession(), isFalse); });
  test('lista i usunięcie passkey używają uwierzytelnionego API', () async { final api = AuthApi(client: MockClient((r) async => http.Response(jsonEncode(r.method == 'GET' ? [{'id':1,'name':'Laptop'}] : {'message':'ok'}), 200))); expect((await api.passkeys()).single['name'], 'Laptop'); await api.deletePasskey(1, password:'hasło', code:'123456'); });
}
