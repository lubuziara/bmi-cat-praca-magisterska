import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'passkey_webauthn_stub.dart';
export 'passkey_webauthn_stub.dart' show PasskeyWebAuthn;
PasskeyWebAuthn createPasskeyWebAuthn() => _AndroidPasskeyWebAuthn();
class _AndroidPasskeyWebAuthn implements PasskeyWebAuthn {
  static const _channel = MethodChannel('bmi-cat/passkeys');
  bool get supported => defaultTargetPlatform == TargetPlatform.android;
  Future<Map<String, dynamic>> create(Map<String, dynamic> options) => _call('create', options);
  Future<Map<String, dynamic>> get(Map<String, dynamic> options) => _call('get', options);
  Future<Map<String, dynamic>> _call(String method, Map<String, dynamic> options) async {
    if (!supported) throw UnsupportedError('Passkeys');
    final result = await _channel.invokeMethod<String>(method, {'options': jsonEncode(options)});
    if (result == null) throw PlatformException(code: 'unavailable');
    return Map<String, dynamic>.from(jsonDecode(result) as Map);
  }
}
