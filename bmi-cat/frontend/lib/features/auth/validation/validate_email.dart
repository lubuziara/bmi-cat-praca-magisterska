String? validateEmail(String? value) {
  final email = (value ?? '').trim();
  if (email.isEmpty) return 'Podaj adres e-mail.';
  if (email.length > 254 ||
      !RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email)) {
    return 'Podaj poprawny adres e-mail.';
  }
  return null;
}
