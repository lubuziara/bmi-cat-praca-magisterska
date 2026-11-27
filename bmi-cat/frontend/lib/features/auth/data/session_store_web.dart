import 'session_store_contract.dart';

class BrowserSessionStore implements SessionStore {
  // Web credentials are deliberately never persisted in browser storage.
  Future<String?> readToken() async => null;
  Future<void> writeToken(String token) async {}
  Future<void> clearToken() async {}
}
