import 'dart:html' as html;

String? currentCsrfToken() {
  for (final cookie in html.document.cookie?.split(';') ?? const <String>[]) {
    final pair = cookie.trim().split('=');
    if (pair.length == 2 && pair.first == 'bmi_csrf') return pair.last;
  }
  return null;
}
