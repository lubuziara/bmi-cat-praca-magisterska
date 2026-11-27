import 'dart:async';
import 'dart:convert';
import 'dart:js_util' as js;
import 'dart:typed_data';
import 'dart:html' as html;
import 'passkey_webauthn_stub.dart';
export 'passkey_webauthn_stub.dart' show PasskeyWebAuthn;

PasskeyWebAuthn createPasskeyWebAuthn() => _BrowserPasskeyWebAuthn();

class _BrowserPasskeyWebAuthn implements PasskeyWebAuthn {
  dynamic get _credentials => js.getProperty(html.window.navigator, 'credentials');
  bool get supported => js.hasProperty(html.window.navigator, 'credentials') && js.hasProperty(_credentials, 'create');

  Future<Map<String, dynamic>> create(Map<String, dynamic> options) async {
    final credential = await js.promiseToFuture(js.callMethod(_credentials, 'create', [js.jsify({'publicKey': _decodeOptions(options)})]));
    return _credential(credential, 'attestationObject');
  }

  Future<Map<String, dynamic>> get(Map<String, dynamic> options) async {
    final credential = await js.promiseToFuture(js.callMethod(_credentials, 'get', [js.jsify({'publicKey': _decodeOptions(options)})]));
    return _credential(credential, 'authenticatorData');
  }

  Map<String, dynamic> _decodeOptions(Map<String, dynamic> value) {
    final result = Map<String, dynamic>.from(value);
    for (final key in ['challenge']) { if (result[key] is String) result[key] = _decode(result[key]); }
    final user = result['user']; if (user is Map && user['id'] is String) user['id'] = _decode(user['id']);
    for (final key in ['excludeCredentials', 'allowCredentials']) {
      final items = result[key];
      if (items is List) for (final item in items) { if (item is Map && item['id'] is String) item['id'] = _decode(item['id']); }
    }
    return result;
  }

  Map<String, dynamic> _credential(dynamic credential, String primary) {
    final response = js.getProperty(credential, 'response');
    final data = <String, dynamic>{'clientDataJSON': _encode(js.getProperty(response, 'clientDataJSON')), primary: _encode(js.getProperty(response, primary))};
    if (primary == 'authenticatorData') {
      data['signature'] = _encode(js.getProperty(response, 'signature'));
      final userHandle = js.getProperty(response, 'userHandle'); if (userHandle != null) data['userHandle'] = _encode(userHandle);
    }
    return {'id': js.getProperty(credential, 'id'), 'rawId': _encode(js.getProperty(credential, 'rawId')), 'type': js.getProperty(credential, 'type'), 'response': data};
  }

  Uint8List _decode(String value) => base64Url.decode(base64Url.normalize(value));
  String _encode(dynamic value) => base64UrlEncode(_bytes(value)).replaceAll('=', '');
  Uint8List _bytes(dynamic value) {
    if (value is ByteBuffer) return value.asUint8List();
    if (value is Uint8List) return value;
    return Uint8List.fromList(List<int>.from(js.dartify(value) as List));
  }
}
