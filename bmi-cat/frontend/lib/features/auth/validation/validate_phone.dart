String? validatePhone(String? value) {
  final phone = (value ?? '').replaceAll(RegExp(r'[ ()-]'), '');
  return RegExp(r'^\+[1-9][0-9]{7,14}$').hasMatch(phone)
      ? null
      : 'Podaj telefon z kierunkowym kraju, np. +48 123 456 789.';
}
