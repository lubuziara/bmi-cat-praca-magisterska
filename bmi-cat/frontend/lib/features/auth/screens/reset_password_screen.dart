import 'package:flutter/material.dart';
import '../data/auth_api.dart';
import '../validation/validate_password.dart';
import '../widgets/auth_shell.dart';
import '../widgets/password_field.dart';
import '../widgets/form_message.dart';
import '../widgets/submit_button.dart';
part 'reset_password_screen_state.dart';

class ResetPasswordScreen extends StatefulWidget {
  final AuthApi api;
  final String token;
  const ResetPasswordScreen(
      {super.key, required this.api, required this.token});
  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}
