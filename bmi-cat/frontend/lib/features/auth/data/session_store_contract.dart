abstract interface class SessionStore {
  Future<String?> readToken();
  Future<void> writeToken(String token);
  Future<void> clearToken();
}
