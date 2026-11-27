String? validatePassword(String? value) {
  if ((value ?? '').length < 12) {
    return 'Hasło musi mieć co najmniej 12 znaków.';
  }
  if (value!.length > 128) return 'Hasło może mieć najwyżej 128 znaków.';
  return null;
}
