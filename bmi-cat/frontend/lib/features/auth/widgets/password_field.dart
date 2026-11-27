import 'package:flutter/material.dart';
part 'password_field_state.dart';

class PasswordField extends StatefulWidget {
  final TextEditingController controller;
  final String label;
  final String? Function(String?)? validator;
  final bool newPassword;
  final VoidCallback? onSubmitted;
  const PasswordField(
      {super.key,
      required this.controller,
      this.label = 'Hasło',
      this.validator,
      this.newPassword = false,
      this.onSubmitted});
  @override
  State<PasswordField> createState() => _PasswordFieldState();
}
