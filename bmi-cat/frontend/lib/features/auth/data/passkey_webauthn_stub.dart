abstract class PasskeyWebAuthn {
  bool get supported;
  Future<Map<String, dynamic>> create(Map<String, dynamic> options);
  Future<Map<String, dynamic>> get(Map<String, dynamic> options);
}

PasskeyWebAuthn createPasskeyWebAuthn() => _UnsupportedPasskeyWebAuthn();
class _UnsupportedPasskeyWebAuthn implements PasskeyWebAuthn {
  bool get supported => false;
  Future<Map<String, dynamic>> create(Map<String, dynamic> _) => throw UnsupportedError('Passkeys');
  Future<Map<String, dynamic>> get(Map<String, dynamic> _) => throw UnsupportedError('Passkeys');
}
