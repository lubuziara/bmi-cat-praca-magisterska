import 'dart:typed_data';
import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'api_exception.dart';
import 'auth_http_client.dart';
import 'csrf_token.dart';
import 'session_store.dart';
import 'passkey_webauthn.dart';

class AuthApi {
  static const defaultUrl = String.fromEnvironment('API_BASE_URL',
      defaultValue: 'http://localhost:8000');
  final String baseUrl;
  final http.Client client;
  final SessionStore _sessionStore;
  String? _token;
  String? _mfaChallenge;
  List<String> _stepUpMethods = const [];
  bool _riskStepUp = false;
  bool get mfaRequired => _mfaChallenge != null;
  // Kept only in the API instance; never persist a pending verification.
  bool get stepUpRequired => _mfaChallenge != null;
  List<String> get stepUpMethods => List.unmodifiable(_stepUpMethods);
  bool allowsStepUpMethod(String method) => _stepUpMethods.contains(method);
  bool needsVerification = false;
  AuthApi(
      {String? baseUrl,
      http.Client? client,
      SessionStore? sessionStore})
      : baseUrl = baseUrl ?? defaultUrl,
        client = client ?? createAuthHttpClient(),
        _sessionStore = sessionStore ?? BrowserSessionStore();

  Future<dynamic> request(String path,
      {Map<String, dynamic>? body, bool get = false, bool remove = false}) async {
    try {
      final headers = {
        'Content-Type': 'application/json',
        if (kIsWeb) 'X-BMI-Client': 'web',
        if (kIsWeb && (path == 'refresh' || path == 'logout'))
          if (currentCsrfToken() != null) 'X-CSRF-Token': currentCsrfToken()!,
        if (_token != null) 'Authorization': 'Bearer $_token'
      };
      final uri = Uri.parse('$baseUrl/api/auth/$path');
      final response = await (get
              ? client.get(uri, headers: headers)
              : remove ? client.delete(uri, headers: headers, body: jsonEncode(body ?? {})) : client.post(uri,
                  headers: headers, body: jsonEncode(body ?? {})))
          .timeout(const Duration(seconds: 15));
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (response.statusCode >= 400) {
        final detail = data is Map ? data['detail'] : null;
        throw ApiException(
            detail is String ? detail : 'Sprawdź poprawność wpisanych danych.',
            response.statusCode);
      }
      return data;
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw const ApiException('Serwer nie odpowiada. Spróbuj ponownie.');
    } catch (_) {
      throw const ApiException(
          'Nie udało się połączyć. Sprawdź połączenie i spróbuj ponownie.');
    }
  }

  Future<Uint8List> download(String path) async {
    final response = await client.get(Uri.parse('$baseUrl/api/auth/$path'),
        headers: {
          if (_token != null) 'Authorization': 'Bearer $_token'
        }).timeout(const Duration(seconds: 30));
    if (response.statusCode != 200)
      throw const ApiException('Nie udało się pobrać dokumentu.');
    return response.bodyBytes;
  }

  Future<void> login(String email, String password) async {
    try {
      final data = await request('login',
          body: {'email': email.trim(), 'password': password});
      await _handleLogin(data);
    } on ApiException catch (error) {
      if (_isTemporarilyBlocked(error)) {
        throw const ApiException('Ze względów bezpieczeństwa nie możemy teraz zakończyć logowania. Spróbuj ponownie później lub użyj innej metody logowania.');
      }
      rethrow;
    }
  }

  Future<void> googleLogin(String idToken) async {
    final data = await request('google', body: {'id_token': idToken});
    await _handleLogin(data);
  }

  Future<void> registerProfile(Map<String, dynamic> profile) async {
    final data = await request('register', body: profile);
    await _saveSession(data);
  }

  Future<void> forgotPassword(String email) async {
    await request('forgot-password', body: {'email': email.trim()});
  }

  Future<void> resetPassword(String token, String password) async {
    await request('reset-password',
        body: {'token': token, 'password': password});
  }

  Future<Map<String, dynamic>> me() async => Map<String, dynamic>.from(await request('me', get: true) as Map);

  Future<bool> restoreSession() async {
    if (kIsWeb) {
      try {
        final data = await request('refresh');
        _token = data['access_token'] as String;
        final user = await me();
        needsVerification = user['profile_complete'] == true &&
            user['registration_verified'] != true;
        return true;
      } on ApiException catch (error) {
        if (error.status == 401 || error.status == 403) {
          _token = null;
          return false;
        }
        rethrow;
      }
    }
    final token = await _sessionStore.readToken();
    if (token == null || token.isEmpty) return false;
    _token = token;
    try {
      final user = await me();
      needsVerification = user['profile_complete'] == true &&
          user['registration_verified'] != true;
      return true;
    } on ApiException catch (error) {
      if (error.status == 401) {
        _token = null;
        await _sessionStore.clearToken();
        return false;
      }
      rethrow;
    }
  }

  Future<void> _saveSession(Map<String, dynamic> data) async {
    final token = data['access_token'] as String;
    _token = token;
    needsVerification = data['user']['profile_complete'] == true &&
        data['user']['registration_verified'] != true;
    if (!kIsWeb) await _sessionStore.writeToken(token);
  }

  Future<void> _handleLogin(Map<String, dynamic> data) async {
    if (data['mfa_required'] == true || data['step_up_required'] == true) {
      final challenge = data['step_up_challenge'] as String? ??
          data['mfa_challenge'] as String?;
      if (challenge == null || challenge.isEmpty) {
        // A session must never be created from an incomplete step-up response.
        throw const ApiException('Nie udało się rozpocząć dodatkowej weryfikacji. Zaloguj się ponownie.');
      }
      _mfaChallenge = challenge;
      _riskStepUp = data['step_up_required'] == true;
      final methods = data['methods'];
      _stepUpMethods = methods is List
          ? methods.whereType<String>().toList(growable: false)
          : const ['totp', 'recovery_code'];
      return;
    }
    await _saveSession(data);
  }

  bool _isTemporarilyBlocked(ApiException error) =>
      error.status == 401 && error.message == 'Logowanie chwilowo niedostępne. Spróbuj ponownie później.';

  Future<void> verifyMfa(String code) async {
    final challenge = _mfaChallenge;
    if (challenge == null) throw const ApiException('Sesja weryfikacji wygasła. Zaloguj się ponownie.');
    try {
      await _saveSession(await request(_riskStepUp ? 'step-up/verify' : '2fa/verify', body: _riskStepUp ? {'step_up_challenge': challenge, 'code': code} : {'mfa_challenge': challenge, 'code': code}));
      _clearStepUp();
    } on ApiException catch (error) {
      final message = error.message.toLowerCase();
      if (_riskStepUp || message.contains('wygas') || message.contains('weryfik') || message.contains('expired')) _clearStepUp();
      rethrow;
    }
  }

  Future<void> verifyStepUpPasskey(PasskeyWebAuthn webauthn) async {
    final challenge = _mfaChallenge;
    if (!_riskStepUp || challenge == null || !allowsStepUpMethod('passkey')) throw const ApiException('Sesja weryfikacji wygasła. Zaloguj się ponownie.');
    try {
      final options = await request('step-up/passkey/options', body: {'step_up_challenge': challenge});
      final credential = await webauthn.get(Map<String, dynamic>.from(options as Map));
      await _saveSession(await request('step-up/passkey/verify', body: {'step_up_challenge': challenge, 'credential': credential}));
      _clearStepUp();
    } on ApiException { _clearStepUp(); rethrow; }
  }
  void _clearStepUp() { _mfaChallenge = null; _stepUpMethods = const []; _riskStepUp = false; }
  void cancelMfa() => _clearStepUp();
  Future<Map<String, dynamic>> mfaStatus() async => Map<String, dynamic>.from(await request('2fa/status', get: true) as Map);
  Future<Map<String, dynamic>> startMfaSetup({String? password, String? googleIdToken, String? code}) async => Map<String, dynamic>.from(await request('2fa/setup', body: {'password': password, 'google_id_token': googleIdToken, 'code': code}) as Map);
  Future<Map<String, dynamic>> confirmMfaSetup(String challenge, String code) async => Map<String, dynamic>.from(await request('2fa/confirm', body: {'setup_challenge': challenge, 'code': code}) as Map);
  Future<Map<String, dynamic>> regenerateRecovery({String? password, String? googleIdToken, required String code}) async => Map<String, dynamic>.from(await request('2fa/recovery/regenerate', body: {'password': password, 'google_id_token': googleIdToken, 'code': code}) as Map);
  Future<void> disableMfa({String? password, String? googleIdToken, required String code}) async =>
      request('2fa/disable', body: {'password': password, 'google_id_token': googleIdToken, 'code': code});

  Future<List<Map<String, dynamic>>> passkeys() async => (await request('passkeys', get: true) as List).map((v) => Map<String, dynamic>.from(v as Map)).toList();
  Future<void> registerPasskey(PasskeyWebAuthn webauthn, {String? name, String? password, String? googleIdToken, String? code}) async {
    if (!webauthn.supported) throw UnsupportedError('Passkeys');
    final options = await request('passkeys/register/options', body: {'password': password, 'google_id_token': googleIdToken, 'code': code});
    final credential = await webauthn.create(Map<String, dynamic>.from(options as Map));
    await request('passkeys/register/verify', body: {'credential': credential, if (name != null && name.trim().isNotEmpty) 'name': name.trim()});
  }
  Future<void> loginPasskey(PasskeyWebAuthn webauthn) async {
    if (!webauthn.supported) throw UnsupportedError('Passkeys');
    final options = await request('passkeys/login/options');
    final credential = await webauthn.get(Map<String, dynamic>.from(options as Map));
    await _handleLogin(await request('passkeys/login/verify', body: {'credential': credential}));
  }
  Future<void> deletePasskey(int id, {String? password, String? googleIdToken, required String code}) async => request('passkeys/$id', remove: true, body: {'password': password, 'google_id_token': googleIdToken, 'code': code});
  Future<List<Map<String, dynamic>>> sessions() async => (await request('sessions', get: true) as List).map((v) => Map<String, dynamic>.from(v as Map)).toList();
  Future<void> revokeSession(String id) async => request('sessions/$id', remove: true);
  Future<void> revokeOtherSessions({String? password, String? googleIdToken, required String code}) async => request('sessions/revoke-others', body: {'password': password, 'google_id_token': googleIdToken, 'code': code});
  Future<List<Map<String, dynamic>>> securityEvents(int offset) async => (await request('security-events?offset=$offset&limit=20', get: true) as List).map((v) => Map<String, dynamic>.from(v as Map)).toList();

  Future<void> logout() async {
    try {
      await request('logout');
    } finally {
      _token = null;
      _clearStepUp();
      if (!kIsWeb) await _sessionStore.clearToken();
    }
  }
}
