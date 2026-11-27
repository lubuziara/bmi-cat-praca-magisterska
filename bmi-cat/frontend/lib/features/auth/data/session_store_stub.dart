import 'session_store_contract.dart';

class BrowserSessionStore implements SessionStore {
  Future<String?> readToken() async => null;

  Future<void> writeToken(String token) async {}

  Future<void> clearToken() async {}
}
