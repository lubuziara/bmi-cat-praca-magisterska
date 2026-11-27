import 'package:flutter_test/flutter_test.dart';
import 'package:bmi_cat/features/auth/validation/validate_email.dart';
import 'package:bmi_cat/features/auth/validation/validate_name.dart';
import 'package:bmi_cat/features/auth/validation/validate_password.dart';

void main() {
  test('Imię: cyfry, HTML i puste wartości są odrzucane', () {
    for (final name in ['666', 'Anna123', '<script>', '', '   ']) {
      expect(validateName(name), isNotNull);
    }
    for (final name in ['Łucja', 'Anna-Maria', 'O’Connor', '李', 'Anne Marie']) {
      expect(validateName(name), isNull, reason: name);
    }
  });
  test('E-mail i granice długości hasła', () {
    expect(validateEmail('anna@example.com'), isNull);
    expect(validateEmail('bad'), isNotNull);
    expect(validateEmail('a @example.com'), isNotNull);
    expect(validatePassword('x' * 11), isNotNull);
    expect(validatePassword('x' * 12), isNull);
    expect(validatePassword('x' * 128), isNull);
    expect(validatePassword('x' * 129), isNotNull);
  });
}
