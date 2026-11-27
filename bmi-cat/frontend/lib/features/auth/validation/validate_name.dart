String? validateName(String? value) {
  final name = (value ?? '').trim();
  if (name.isEmpty || name.length > 80) {
    return 'Podaj imię (od 1 do 80 znaków).';
  }
  if (!RegExp(r"^[\p{L}]+(?:[ '\u2019-][\p{L}]+)*$", unicode: true)
      .hasMatch(name)) {
    return 'Imię może zawierać litery, spacje, apostrof i łącznik.';
  }
  return null;
}
